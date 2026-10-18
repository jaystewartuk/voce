"""The playlist menu: pick a file, see progress, restart a file."""

from __future__ import annotations

import curses

from voce.playlist import Entry
from voce.state import State
from voce.ui.terminal import PRESS, TICK_MS, WHEEL_DOWN, WHEEL_UP, Terminal
from voce.ui.theme import Theme

ENTER = (10, 13, curses.KEY_ENTER)


def menu(term: Terminal, theme: Theme, state: State, playlist: list[Entry], current: int,
         footer: str = "") -> int | None:
    """The chosen file's index, or None to go back. Enter or a click plays, r restarts, q goes back."""
    sel, top = max(0, current), 0
    rows: list[tuple[str, object]] = []
    for i, e in enumerate(playlist):
        if e.part and (i == 0 or e.part != playlist[i - 1].part):
            rows.append(("part", e.part))
        rows.append(("file", i))
    term.scr.timeout(-1)
    try:
        while True:
            h, w = term.size()
            term.scr.erase()
            term.put(0, 0, " voce · Enter plays · r restarts · q back".ljust(w)[:w], theme.bar)
            body = max(1, h - 3)
            sel_row = next(n for n, r in enumerate(rows) if r == ("file", sel))
            if sel_row < top + 1:
                top = max(0, sel_row - 1)
            if sel_row >= top + body:
                top = sel_row - body + 1
            for row in range(body):
                n = top + row
                if n >= len(rows):
                    break
                kind, val = rows[n]
                if kind == "part":
                    term.put(row + 1, 2, str(val), theme.heading)
                    continue
                e = playlist[val]
                mark = state.progress(e.path).replace("done", "✓")
                term.put(row + 1, 2, f"{mark:>4}  {e.title}"[:w - 4], theme.selected if val == sel else 0)
            if footer:
                term.put(h - 1, 0, f" {footer}"[:w - 1], theme.dim)
            term.scr.refresh()
            k = term.read_key()
            if k in (ord("q"), ord("m"), 27):
                return None
            if k in (curses.KEY_DOWN, ord("j")):
                sel = min(len(playlist) - 1, sel + 1)
            elif k in (curses.KEY_UP, ord("k")):
                sel = max(0, sel - 1)
            elif k in (*ENTER, ord(" ")):
                return sel
            elif k == ord("r"):
                state.restart(playlist[sel].path)
                state.save(force=True)
            elif k == curses.KEY_MOUSE:
                event = term.mouse_event()
                if not event:
                    continue
                button, _, y = event
                if button == PRESS and 1 <= y <= body and top + y - 1 < len(rows):
                    kind, val = rows[top + y - 1]
                    if kind == "file":
                        return int(val)
                elif button in (WHEEL_UP, WHEEL_DOWN):
                    sel = max(0, min(len(playlist) - 1, sel + (1 if button == WHEEL_DOWN else -1)))
    finally:
        term.scr.timeout(TICK_MS)
