"""Keys and the mouse, including escape sequences the terminal's curses entry doesn't translate."""

from __future__ import annotations

import curses
import re
import sys

ESCAPES = {"[A": curses.KEY_UP, "[B": curses.KEY_DOWN, "[C": curses.KEY_RIGHT, "[D": curses.KEY_LEFT,
           "OA": curses.KEY_UP, "OB": curses.KEY_DOWN, "OC": curses.KEY_RIGHT, "OD": curses.KEY_LEFT,
           "[5~": curses.KEY_PPAGE, "[6~": curses.KEY_NPAGE}
_SGR_MOUSE = re.compile(r"\[<(\d+);(\d+);(\d+)([Mm])")

CLICK, WHEEL_UP, WHEEL_DOWN = 1, 4, 5
TICK_MS = 40  # how often the screen redraws while waiting for a key


def decode_sgr_mouse(seq: str) -> tuple[int, int, int] | None:
    """An SGR mouse report (without the leading ESC) as (button, x, y), or None if it isn't a click or wheel."""
    m = _SGR_MOUSE.fullmatch(seq)
    if not m:
        return None
    b, x, y, kind = int(m.group(1)), int(m.group(2)) - 1, int(m.group(3)) - 1, m.group(4)
    if kind == "M" and b & 3 == 0 and not b & 64 and not b & 32:
        return (CLICK, x, y)
    if kind == "M" and b in (64, 65):
        return (WHEEL_UP if b == 64 else WHEEL_DOWN, x, y)
    return None


class Terminal:
    def __init__(self, scr) -> None:
        self.scr = scr
        self.pending: list[tuple[int, int, int]] = []
        self.native_mouse = False

    def start(self) -> None:
        curses.curs_set(0)
        self.scr.keypad(True)
        self.scr.timeout(TICK_MS)
        self.enable_mouse()

    def stop(self) -> None:
        self.disable_mouse()

    def size(self) -> tuple[int, int]:
        return self.scr.getmaxyx()

    # ---- mouse

    def enable_mouse(self) -> None:
        """Ask curses for mouse events; if it can't on this terminal, ask the terminal directly (SGR encoding)."""
        try:
            available, _ = curses.mousemask(curses.ALL_MOUSE_EVENTS)
            curses.mouseinterval(0)
        except curses.error:
            available = 0
        self.native_mouse = bool(available)
        # SGR either way: curses decodes it when the terminal's kmous is "\E[<" (Ghostty, iTerm2, xterm),
        # and read_key decodes it when curses doesn't.
        sys.stdout.write("\033[?1006h" if available else "\033[?1000h\033[?1006h")
        sys.stdout.flush()

    def disable_mouse(self) -> None:
        sys.stdout.write("\033[?1006l" if self.native_mouse else "\033[?1006l\033[?1000l")
        sys.stdout.flush()

    def mouse_event(self) -> tuple[int, int, int] | None:
        """The next mouse event as (button, x, y), or None if it was something other than a click or the wheel."""
        if self.pending:
            return self.pending.pop(0)
        try:
            _, x, y, _, b = curses.getmouse()
        except curses.error:
            return None
        if b & (curses.BUTTON1_PRESSED | curses.BUTTON1_CLICKED):
            return (CLICK, x, y)
        if b & curses.BUTTON4_PRESSED:
            return (WHEEL_UP, x, y)
        if b & getattr(curses, "BUTTON5_PRESSED", 1 << 21):
            return (WHEEL_DOWN, x, y)
        return None

    # ---- keys

    def read_key(self) -> int:
        """A key, or -1 if none came within the tick. Raw arrow and mouse sequences become curses keys."""
        k = self.scr.getch()
        if k != 27:
            return k
        self.scr.nodelay(True)
        seq = ""
        try:
            for _ in range(24):
                c = self.scr.getch()
                if c == -1:
                    break
                seq += chr(c)
                if seq in ESCAPES:
                    return ESCAPES[seq]
                if seq.startswith("[<") and seq[-1] in "Mm":
                    event = decode_sgr_mouse(seq)
                    if event:
                        self.pending.append(event)
                        return curses.KEY_MOUSE
                    return -1
                if not seq.startswith("[<") and len(seq) >= 3:
                    break
        finally:
            self.scr.nodelay(False)
            self.scr.timeout(TICK_MS)
        return 27 if not seq else -1

    # ---- output

    def put(self, y: int, x: int, text: str, attr: int = 0) -> None:
        """Write text, clipped to the screen, never raising for the bottom-right corner."""
        h, w = self.scr.getmaxyx()
        if y < 0 or y >= h or x >= w or x < 0 or not text:
            return
        text = text[:max(0, w - x - (1 if y == h - 1 else 0))]
        try:
            self.scr.addstr(y, x, text, attr)
        except curses.error:
            pass
