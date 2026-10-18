"""The reader: plays a document sentence by sentence and draws it with the sentence and word highlighted."""

from __future__ import annotations

import curses
import time
from dataclasses import dataclass
from typing import Callable

from voce.document import Doc, load, minutes
from voce.playlist import Entry
from voce.sources.clips import ClipError, write_clipboard
from voce.state import State
from voce.ui.layout import Line, layout, word_at
from voce.ui.menu import menu
from voce.ui.terminal import DRAG, PRESS, RELEASE, WHEEL_DOWN, WHEEL_UP, Terminal
from voce.ui.theme import Theme
from voce.voices import FREE_CHARS, Voice

AHEAD = 8              # sentences fetched ahead of the one playing
MAX_WIDTH = 92         # the text column never gets wider than this
SPEEDS = [0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.75, 2.0]
KEYS = ["space pause", "←→ sentence", "↑↓ paragraph", "[ ] section", "+- speed", "n p file", "v voice", "m menu",
        "r restart", "c copy", "q quit"]
STATUS = {"playing": "▶ reading", "loading": "… fetching the voice", "gap": "▶ reading",
          "gap-start": "▶ next file", "paused": "⏸ paused (space to carry on)",
          "held": "⏸ paused (space to carry on)",
          "waiting": "Your turn: answer out loud, then press space for the answer", "end": "■ finished"}
HEADINGS = ("h1", "h2", "h3")
STALL_SECONDS = 5.0    # grace after a sentence's length before the player counts as stuck
ANCHOR = 0.4           # how far down the screen the sentence being read sits: above centre, so more lies ahead


def same_place(old: list, new: list, pos: int) -> int:
    """Where pos in the old units is in the new ones: the same words (the same repeat of them), else the same block."""
    if not old:
        return 0
    here = old[min(pos, len(old) - 1)]
    matches = [i for i, u in enumerate(new) if u.say == here.say]
    if matches:
        nth = sum(1 for u in old[:pos] if u.say == here.say)  # the third "Yes." stays the third "Yes."
        return matches[nth] if nth < len(matches) else min(matches, key=lambda i: abs(i - pos))
    in_block = [i for i, u in enumerate(new) if u.block == here.block]
    if in_block:
        return min(in_block, key=lambda i: abs(i - pos))
    return min(pos, len(new) - 1)


def key_hints(width: int) -> str:
    """As many key hints as fit, dropping from the middle so "q quit" always shows."""
    keys = list(KEYS)
    while len(keys) > 1 and len(" " + " · ".join(keys)) > width:
        keys.pop(-2)
    return (" " + " · ".join(keys))[:width]


@dataclass
class Options:
    one: bool = False         # stop at the end of the file instead of carrying on through the playlist
    quiz_only: bool = False
    skip_code: bool = False   # show code blocks without reading them
    speed: float = 1.0
    message: str = ""         # shown in the status bar when the reader opens


class Reader:
    """A small state machine driven by a 40 ms tick: loading → playing → gap → loading, with pauses and waits."""

    def __init__(self, term: Terminal, theme: Theme, options: Options, state: State, voice: Voice,
                 next_voice: Callable[[Voice], Voice | None], player, playlist: list[Entry], start: int) -> None:
        self.term, self.theme, self.options, self.state = term, theme, options, state
        self.voice, self.next_voice, self.player = voice, next_voice, player
        self.playlist, self.index = playlist, start
        self.speed = options.speed
        self.mode = "loading"
        self.message = options.message
        self.message_at = time.monotonic()
        self.gap_until = 0.0
        self.doc: Doc | None = None
        self.pos = 0
        self.future = None
        self.top = 0
        self.margin = 1
        self.scrolled = False  # the wheel moved the text away from the voice
        self._words, self._words_of = [0], None   # running word counts, and the units they were counted for
        self.press: tuple[int, int] | None = None       # where the left button went down: (line, offset)
        self.selection: tuple[tuple[int, int], tuple[int, int]] | None = None  # text dragged over, to copy
        self.width = 0
        self.lines: list[Line] = []
        self.where: dict[int, int] = {}
        self.quit = False
        self.ended = False
        self.mtime = 0.0
        self.next_check = 0.0
        self.deadline = 0.0     # when a sentence that hasn't finished counts as stuck
        self.held_left = 0.0
        self.said = False       # paused in the gap after a sentence: it has been read, so carry on to the next

    @property
    def units(self) -> list:
        return self.doc.units if self.doc else []

    def say(self, message: str) -> None:
        self.message, self.message_at = message, time.monotonic()

    # ---- files

    def open(self, index: int, fresh: bool = False) -> None:
        self.player.stop()
        self.index = index
        self.future = None
        self.width = 0
        self.top = 0
        self.ended = False
        path = self.playlist[index].path
        try:
            self.doc = load(path, self.options.quiz_only, self.options.skip_code)
            self.mtime = self.doc.path.stat().st_mtime
        except (OSError, UnicodeDecodeError) as e:
            self.doc = Doc(path, self.playlist[index].title, [])
            self.mode = "end"
            self.say(f"Couldn't read {path.name}: {str(e)[:60]}. n for the next file, q to quit.")
            return
        fresh = fresh or self.options.quiz_only
        self.pos = 0 if fresh else self.state.resume(self.doc.path, self.doc.units)
        if not self.doc.units:
            self.mode = "end"
            self.say("Nothing to read in this file. n for the next, q to quit.")
            return
        self.go(self.pos)

    def reload_if_changed(self) -> None:
        """Re-read the file when it changes on disk (checked once a second), keeping the place."""
        now = time.monotonic()
        if now < self.next_check or not self.doc:
            return
        self.next_check = now + 1.0
        try:
            mtime = self.doc.path.stat().st_mtime
        except OSError:
            return
        if mtime == self.mtime:
            return
        self.mtime = mtime
        old = self.doc
        try:
            doc = load(old.path, self.options.quiz_only, self.options.skip_code)
        except Exception as e:
            self.say(f"Couldn't reload the file: {str(e)[:60]}")
            return
        if not doc.units:
            return
        here = old.units[self.pos] if old.units else None
        pos = same_place(old.units, doc.units, self.pos)
        self.doc = doc
        self.width = 0
        self.say("File changed on disk, reloaded")
        changed = here is None or doc.units[pos].say != here.say
        if self.mode == "paused" or (changed and self.mode in ("playing", "held", "loading")):
            self.go(pos, keep_pause=self.mode == "paused")
        else:  # carry on: the sentence playing, the gap after it or a quiz wait stay as they are
            self.pos = pos
            self.prefetch()

    def go(self, pos: int, keep_pause: bool = False) -> None:
        self.player.stop()
        if self.press is None:  # unless a drag is under way: the text holds still and the selection stays
            self.scrolled = False
            self.selection = None
        self.pos = max(0, min(pos, len(self.units) - 1))
        self.said = False
        if not self.options.quiz_only:
            self.state.place(self.doc.path, self.units, self.pos)
            self.state.save()
        self.future = self.voice.want(self.units[self.pos].say)
        self.prefetch()
        self.mode = "paused" if keep_pause and self.mode in ("paused", "waiting", "held") else "loading"

    def prefetch(self) -> None:
        for unit in self.units[self.pos + 1:self.pos + 1 + AHEAD]:
            self.voice.want(unit.say)

    def next_file(self, step: int = 1) -> bool:
        nxt = self.index + step
        if 0 <= nxt < len(self.playlist):
            self.open(nxt, fresh=self.state.is_done(self.playlist[nxt].path))
            return True
        return False

    def finish(self) -> None:
        if not self.options.quiz_only:
            self.state.done(self.doc.path)
            self.state.save(force=True)
        self.ended = True
        if self.options.one or not self.next_file():
            self.mode = "end"
            more = "n for the next file, m for the menu, " if len(self.playlist) > 1 else ""
            self.say(f"Finished. {more}r to hear it again, q to quit.")
        elif self.units:  # next_file opened a file with something to read
            self.gap_until = time.monotonic() + 1.0
            self.mode = "gap-start"

    # ---- the clock

    def tick(self) -> None:
        self.reload_if_changed()
        now = time.monotonic()
        if self.mode == "loading" and self.future is not None and self.future.done():
            try:
                path, duration = self.future.result()
            except Exception as e:
                self.say(f"Couldn't get the voice: {str(e)[:70]}")
                self.mode = "paused"
                return
            self.player.play(path, duration, self.speed)
            self.mode = "playing"
            self.deadline = now + duration / self.speed + STALL_SECONDS
            if self.player.error:
                self.say(self.player.error)
                self.player.error = ""
            if self.voice.warning:
                self.say(self.voice.warning)
                self.voice.warning = ""
        elif self.mode == "playing" and not self.player.finished() and now > self.deadline:
            self.say("The audio player stopped responding; carrying on.")
            self.player.stop()
            self.gap_until = now
            self.mode = "gap"
        elif self.mode == "playing" and self.player.finished():
            unit = self.units[self.pos]
            if unit.wait:
                self.mode = "waiting"
            else:
                self.gap_until = now + unit.pause / self.speed
                self.mode = "gap"
        elif self.mode == "gap" and now >= self.gap_until:
            if self.pos + 1 < len(self.units):
                self.go(self.pos + 1)
            else:
                self.finish()
        elif self.mode == "gap-start" and now >= self.gap_until:
            self.mode = "loading"

    # ---- keys

    def key(self, k: int) -> None:
        units = self.units
        if k == ord("q"):
            self.quit = True
        elif k in (ord(" "), 10, 13):
            self.toggle()
        elif not units:
            if k in (ord("n"), ord("p")):
                self.next_file(1 if k == ord("n") else -1)
            elif k == ord("m"):
                self.menu()
        elif k in (curses.KEY_RIGHT, ord("l")):
            self.go(self.pos + 1, keep_pause=True)
        elif k in (curses.KEY_LEFT, ord("h")):
            self.go(self.pos - 1, keep_pause=True)
        elif k == ord("r"):
            self.go(0 if self.mode == "end" else self.pos)
        elif k in (curses.KEY_DOWN, ord("j")):
            block = units[self.pos].block
            self.go(next((i for i in range(self.pos + 1, len(units)) if units[i].block != block), self.pos),
                    keep_pause=True)
        elif k in (curses.KEY_UP, ord("k")):
            self.go(self.paragraph_start(), keep_pause=True)
        elif k in (ord("]"), curses.KEY_NPAGE):
            nxt = next((i for i in range(self.pos + 1, len(units)) if self.is_heading(i)), None)
            if nxt is not None:
                self.go(nxt, keep_pause=True)
        elif k in (ord("["), curses.KEY_PPAGE):
            heads = [i for i in range(self.pos) if self.is_heading(i)]
            if heads:
                self.go(heads[-1] if self.pos - heads[-1] > 2 or len(heads) == 1 else heads[-2], keep_pause=True)
        elif k in (ord("+"), ord("=")):
            self.set_speed(1)
        elif k in (ord("-"), ord("_")):
            self.set_speed(-1)
        elif k in (ord("n"), ord("p")):
            self.next_file(1 if k == ord("n") else -1)
        elif k == ord("v"):
            self.change_voice()
        elif k == ord("m"):
            self.menu()
        elif k == ord("c"):
            unit = units[self.pos]
            self.copy(self.doc.blocks[unit.block].text[unit.start:unit.end], "the sentence")
        elif k == ord("C"):
            self.copy(self.doc.blocks[units[self.pos].block].text, "the paragraph")
        elif k == ord("?"):
            self.say(" · ".join(KEYS))

    def copy(self, text: str, what: str) -> None:
        """Put text on the clipboard and say so."""
        try:
            write_clipboard(text)
        except ClipError as e:
            self.say(str(e))
            return
        self.say(f"Copied {what}")

    def toggle(self) -> None:
        """Space: pause, carry on, or move past a quiz question."""
        if self.mode == "waiting":
            self.go(self.pos + 1)
        elif self.mode == "playing" and self.player.can_pause:
            self.player.pause()
            self.mode = "held"
            self.held_left = self.deadline - time.monotonic()
        elif self.mode in ("playing", "loading", "gap", "gap-start"):
            self.said = self.mode == "gap"
            self.player.stop()
            self.mode = "paused"
        elif self.mode == "held":
            self.player.resume()
            self.scrolled = False  # carrying on brings the text back to the voice
            self.mode = "playing"
            self.deadline = time.monotonic() + self.held_left
        elif self.mode == "paused":
            if self.said and self.pos + 1 < len(self.units):
                self.go(self.pos + 1)
            else:
                self.go(self.pos)
        elif self.mode == "end":
            self.next_file()

    def is_heading(self, i: int) -> bool:
        block = self.units[i].block
        return block >= 0 and self.doc.blocks[block].kind in HEADINGS

    def paragraph_start(self) -> int:
        """The start of this paragraph, or of the previous one if already at the start."""
        units = self.units
        block = units[self.pos].block
        first = self.pos
        while first > 0 and units[first - 1].block == block:
            first -= 1
        if first == self.pos and first > 0:
            block = units[first - 1].block
            first -= 1
            while first > 0 and units[first - 1].block == block:
                first -= 1
        return first

    def set_speed(self, step: int) -> None:
        i = min(range(len(SPEEDS)), key=lambda j: abs(SPEEDS[j] - self.speed))
        self.speed = SPEEDS[max(0, min(len(SPEEDS) - 1, i + step))]
        self.state.set("speed", self.speed)
        self.say(f"Speed {self.speed:g}×")
        self.player.set_rate(self.speed)
        if self.mode == "playing" and not self.player.can_pause:
            self.go(self.pos)

    def change_voice(self) -> None:
        voice = self.next_voice(self.voice)
        if voice is None:
            self.say("Only Google voices can be switched here; set up Google to get eight of them.")
            return
        self.voice.close()
        self.voice = voice
        self.state.set("voice", voice.name)
        self.say(f"Voice: {voice.label} (each sentence is fetched once in a new voice, then kept)")
        self.go(self.pos, keep_pause=True)

    def menu(self) -> None:
        self.player.stop()
        was = self.mode
        footer = f"Google characters this month: {self.state.month_chars():,} of {FREE_CHARS:,} free" \
            if self.voice.uses_google else ""
        choice = menu(self.term, self.theme, self.state, self.playlist, self.index, footer)
        if choice is not None:
            self.open(choice)
        else:
            self.mode = "paused" if was != "end" else was
        self.width = 0

    def mouse(self, event: tuple[int, int, int]) -> None:
        """A click jumps to the sentence or code line under the pointer; a drag copies the text it crosses
        without moving the voice; the wheel scrolls the text."""
        button, x, y = event
        if not self.units:
            return
        h, _ = self.term.size()
        body = max(1, h - 3)
        if button in (WHEEL_UP, WHEEL_DOWN):
            step = 3 if button == WHEEL_DOWN else -3
            self.top = max(0, min(self.top + step, self.bottom(body)))
            self.scrolled = True
        elif button == PRESS:
            self.selection = None
            self.press = self.cell(x, y, body)
            if self.press is not None:
                self.scrolled = True  # the text holds still under the pointer while the button is down
        elif button == DRAG and self.press is not None:
            here = self.cell(x, y, body, clamp=True)
            self.selection = self.span(self.press, here) if here != self.press else None
        elif button == RELEASE and self.press is not None:
            press, self.press = self.press, None
            here = self.cell(x, y, body, clamp=True)
            if here != press:
                self.selection = self.span(press, here)
            if self.selection:
                text = self.selected_text()
                lines = text.count("\n") + 1
                self.copy(text, "the selection" if lines == 1 else f"{lines} lines")
            else:
                self.jump(*press)

    def cell(self, x: int, y: int, body: int, clamp: bool = False) -> tuple[int, int] | None:
        """The screen cell as (line, offset into its block's text); None if it is off the text, unless clamped."""
        if clamp:
            y = max(1, min(y, body))
        elif not 1 <= y <= body:
            return None
        n = self.top + y - 1
        if n >= len(self.lines):
            if not clamp or not self.lines:
                return None
            n = len(self.lines) - 1
        line = self.lines[n]
        at = line.start + max(0, x - self.margin - line.indent - len(line.prefix))
        return (n, min(at, max(line.start, line.end - 1)))

    @staticmethod
    def span(a: tuple[int, int], b: tuple[int, int]) -> tuple[tuple[int, int], tuple[int, int]]:
        """The selection between two cells, in order, taking in the cell at the far end."""
        lo, (n, at) = min(a, b), max(a, b)
        return lo, (n, at + 1)

    def selected_text(self) -> str:
        """The text under the selection as it is in the document: each block's run whole, blank lines between."""
        (n0, a0), (n1, z1) = self.selection
        runs: list[list[int]] = []  # [block, start, end], or [-1] for a blank line
        for n in range(n0, n1 + 1):
            line = self.lines[n]
            a = a0 if n == n0 else line.start
            z = min(z1, line.end) if n == n1 else line.end
            if line.block < 0:
                runs.append([-1])
            elif runs and runs[-1][0] == line.block:
                runs[-1][2] = z
            else:
                runs.append([line.block, a, z])
        pieces = ["" if b < 0 else self.doc.blocks[b].text[a:z].rstrip()
                  for b, *rest in runs for a, z in [rest or (0, 0)]]
        return "\n".join(pieces).strip("\n")

    def jump(self, n: int, at: int) -> None:
        """Start reading at the sentence or code line containing this offset of the line's block."""
        line = self.lines[n]
        if line.block < 0:
            return
        block = self.doc.blocks[line.block]
        units = self.units
        same = [i for i, u in enumerate(units) if u.block == line.block]
        if block.kind == "code" and not same:  # code that is shown but not read: a click copies it
            lines = block.text.count("\n") + 1
            self.copy(block.text + "\n", f"the code, {lines} line{'s' * (lines != 1)}")
            return
        if same:
            pick = next((i for i in same if units[i].start <= at < units[i].end), None)
            if pick is None:
                before = [i for i in same if units[i].start <= at]
                pick = before[-1] if before else same[0]
        else:  # an unspoken block (a Next link): the nearest block after it that is read
            after = [(u.block, i) for i, u in enumerate(units) if u.block > line.block]
            if not after:
                return
            pick = min(after)[1]
        self.go(pick)

    # ---- drawing

    def draw(self) -> None:
        h, w = self.term.size()
        width = max(20, min(w - 4, MAX_WIDTH))
        if width != self.width:
            self.width = width
            self.lines, self.where = layout(self.doc, width) if self.doc else ([], {})
        self.margin = max(1, (w - width) // 2)
        body = max(1, h - 3)
        self.term.scr.erase()
        unit = self.units[self.pos] if self.units else None
        word = None
        if unit and unit.block >= 0 and self.mode in ("playing", "held"):
            word = word_at(unit, self.doc.blocks[unit.block].text, self.player.position(), self.player.length)
        if unit and unit.block >= 0 and unit.block in self.where and not self.scrolled:
            self.follow(unit, body)
        self.top = max(0, min(self.top, self.bottom(body)))
        for row in range(body):
            n = self.top + row
            if n >= len(self.lines):
                break
            self.draw_line(row + 1, self.margin, self.lines[n], unit, word, self.selected_on(n))
        self.draw_bars(h, w)
        self.term.scr.refresh()

    def anchor(self, body: int) -> int:
        """The row the sentence being read is kept on."""
        return int(body * ANCHOR)

    def bottom(self, body: int) -> int:
        """The furthest the text scrolls: the last line can rise to the anchor, so the eye never drops at the end."""
        return max(0, len(self.lines) - 1 - self.anchor(body))

    def follow(self, unit, body: int) -> None:
        """Glide the text so the sentence being read sits on the anchor row, a frame at a time, easing in.

        The eye stays in one place and the words come to it. A sentence a few lines on takes a few frames to
        arrive; a jump to somewhere off screen snaps, as there is nothing continuous to follow."""
        first = self.where[unit.block]
        for n in range(first, len(self.lines)):
            line = self.lines[n]
            if line.block != unit.block:
                break
            if line.end > unit.start:
                first = n
                break
        goal = max(0, min(first - self.anchor(body), self.bottom(body)))
        gap = goal - self.top
        if abs(gap) > body:
            self.top = goal
        elif gap:
            self.top += max(1, abs(gap) // 4) * (1 if gap > 0 else -1)

    def selected_on(self, n: int) -> tuple[int, int] | None:
        """The selected character range of line n, if the selection reaches it."""
        if not self.selection:
            return None
        (n0, a0), (n1, z1) = self.selection
        if not n0 <= n <= n1:
            return None
        line = self.lines[n]
        return (a0 if n == n0 else line.start, min(z1, line.end) if n == n1 else line.end)

    def draw_line(self, y: int, x: int, line: Line, unit, word, selected=None) -> None:
        if line.block < 0:
            return
        block = self.doc.blocks[line.block]
        base = self.theme.base(block)
        self.term.put(y, x + line.indent, line.prefix, self.theme.prefix(block))
        if line.end <= line.start:
            return
        text = block.text
        cx = x + line.indent + len(line.prefix)
        here = unit is not None and unit.block == line.block
        sa, sz = (unit.start, unit.end) if here else (0, 0)
        wa, wz = word if word and here else (0, 0)
        ka, kz = selected or (0, 0)
        spans = [s for s in block.spans if s[0] < line.end and s[1] > line.start]
        cuts = {line.start, line.end}
        for c in (sa, sz, wa, wz, ka, kz, *(c for s in spans for c in s[:2])):
            if line.start < c < line.end:
                cuts.add(c)
        edges = sorted(cuts)
        for a, z in zip(edges, edges[1:]):
            roles = frozenset().union(*(r for s0, s1, r in spans if s0 <= a and z <= s1))
            mark = "selected" if kz > ka and ka <= a and z <= kz else \
                "word" if wz > wa and wa <= a and z <= wz else \
                "sentence" if sz > sa and sa <= a and z <= sz else None
            self.term.put(y, cx + (a - line.start), text[a:z], self.theme.text(block, base, roles, mark))

    def words(self) -> list[int]:
        """Words before each sentence, and the total last: counted once per document, not every frame."""
        if self._words_of is not self.units:
            counts, total = [0], 0
            for u in self.units:
                total += len(u.say.split())
                counts.append(total)
            self._words, self._words_of = counts, self.units
        return self._words

    def progress(self) -> float:
        """How far through the file the voice is, by words: 0 at the start, 1 once the last sentence is done."""
        words = self.words()
        if not words[-1]:
            return 0.0
        return 1.0 if self.mode == "end" else words[self.pos] / words[-1]

    def draw_bars(self, h: int, w: int) -> None:
        entry = self.playlist[self.index]
        title = self.doc.title if self.doc else entry.title
        brand = " voce "
        heading = f" {entry.part + ' · ' if entry.part else ''}{title} "
        top = (heading[:max(0, w - len(brand))].ljust(w - len(brand)) + brand)[:w]
        done = self.progress()
        fill = round(w * done)  # the title bar fills from the left as the file is read
        self.term.put(0, 0, top[:fill], self.theme.progress)
        self.term.put(0, fill, top[fill:], self.theme.bar)
        status = f" {STATUS.get(self.mode, self.mode)}"
        if self.message:
            status += f"   {self.message}"
        where = ""
        if self.units:
            words = self.words()
            left_minutes = minutes(words[-1] - words[self.pos], self.speed)
            where = f"{done:.0%} · " + \
                (f"{left_minutes:.0f} min left" if left_minutes >= 1 else "under a minute left")
        right = f"{self.speed:g}× · {self.voice.label} "
        room = max(0, w - len(right) - len(where) - 3)
        line = status[:max(0, room - 1)].ljust(room)
        self.term.put(h - 2, 0, (line + where + "   " + right).ljust(w)[:w], self.theme.bar)
        self.term.put(h - 1, 0, key_hints(w - 1), self.theme.dim)

    # ---- main loop

    def run(self) -> None:
        self.open(self.index)
        while not self.quit:
            k = self.term.read_key()
            if k == curses.KEY_RESIZE:
                self.width = 0
            elif k == curses.KEY_MOUSE:
                event = self.term.mouse_event()
                if event:
                    self.mouse(event)
            elif k != -1:
                self.key(k)
            if self.quit:
                break
            self.tick()
            if self.message and self.mode != "end" and time.monotonic() - self.message_at > 6:
                self.message = ""
            self.draw()
        self.player.stop()
        if self.doc and not self.options.quiz_only and not self.ended and self.units:
            self.state.place(self.doc.path, self.units, self.pos)
        self.state.save(force=True)
        self.voice.close()
