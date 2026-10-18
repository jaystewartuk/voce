"""Where the document sits on the screen: the layout at this width, scrolling, the mouse's cell and the selection.

The reader decides what is happening in time (which sentence, playing or paused); the view decides where things
are in space. It keeps the sentence being read on one row, two fifths of the way down, and glides the text up to
meet it. A click is turned into a place in the document, a drag into a selection to copy.
"""

from __future__ import annotations

from voce.document import Doc, Unit
from voce.ui.layout import Line, layout
from voce.ui.terminal import Terminal
from voce.ui.theme import Theme

MAX_WIDTH = 92         # the text column never gets wider than this
ANCHOR = 0.4           # how far down the screen the sentence being read sits: above centre, so more lies ahead
BARS = 3               # rows taken by the title bar, the status bar and the key hints

Cell = tuple[int, int]  # (screen line, offset into that line's block text)


class View:
    def __init__(self, term: Terminal, theme: Theme) -> None:
        self.term, self.theme = term, theme
        self.width = 0
        self.margin = 1
        self.lines: list[Line] = []
        self.where: dict[int, int] = {}
        self.top = 0
        self.scrolled = False      # the wheel moved the text away from the voice
        self.pressed: Cell | None = None                  # where the left button went down
        self.selection: tuple[Cell, Cell] | None = None   # text dragged over, to copy

    # ---- size and layout

    @property
    def body(self) -> int:
        """Rows available for the text."""
        return max(1, self.term.size()[0] - BARS)

    def invalidate(self) -> None:
        """Lay the document out again at the next draw: after a resize, a reload or the menu."""
        self.width = 0

    def reset(self) -> None:
        """A new document: back to the top, laid out afresh."""
        self.invalidate()
        self.top = 0

    def fit(self, doc: Doc | None) -> None:
        """Lay the document out for the terminal's current width, if it has changed."""
        _, w = self.term.size()
        width = max(20, min(w - 4, MAX_WIDTH))
        if width != self.width:
            self.width = width
            self.lines, self.where = layout(doc, width) if doc else ([], {})
        self.margin = max(1, (w - width) // 2)

    # ---- scrolling

    def anchor(self) -> int:
        """The row the sentence being read is kept on."""
        return int(self.body * ANCHOR)

    def bottom(self) -> int:
        """The furthest the text scrolls: the last line can rise to the anchor, so the eye never drops at the end."""
        return max(0, len(self.lines) - 1 - self.anchor())

    def scroll(self, step: int) -> None:
        """The wheel: the text moves and stops following the voice until the next sentence."""
        self.top = max(0, min(self.top + step, self.bottom()))
        self.scrolled = True

    def follow_voice(self) -> None:
        """The text follows the voice again and the selection clears, unless a drag is under way."""
        if self.pressed is None:
            self.scrolled = False
            self.selection = None

    def follow(self, unit: Unit) -> None:
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
        goal = max(0, min(first - self.anchor(), self.bottom()))
        gap = goal - self.top
        if abs(gap) > self.body:
            self.top = goal
        elif gap:
            self.top += max(1, abs(gap) // 4) * (1 if gap > 0 else -1)

    # ---- the mouse

    def cell(self, x: int, y: int, clamp: bool = False) -> Cell | None:
        """The screen cell as (line, offset into its block's text); None if it is off the text, unless clamped."""
        body = self.body
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

    def press(self, x: int, y: int) -> None:
        self.selection = None
        self.pressed = self.cell(x, y)
        if self.pressed is not None:
            self.scrolled = True  # the text holds still under the pointer while the button is down

    def drag(self, x: int, y: int) -> None:
        if self.pressed is None:
            return
        here = self.cell(x, y, clamp=True)
        self.selection = self.span(self.pressed, here) if here != self.pressed else None

    def release(self, x: int, y: int) -> Cell | None:
        """The button comes up: the cell clicked if the pointer never moved, else None and a selection to copy."""
        if self.pressed is None:
            return None
        pressed, self.pressed = self.pressed, None
        here = self.cell(x, y, clamp=True)
        if here != pressed:
            self.selection = self.span(pressed, here)
        return None if self.selection else pressed

    @staticmethod
    def span(a: Cell, b: Cell) -> tuple[Cell, Cell]:
        """The selection between two cells, in order, taking in the cell at the far end."""
        lo, (n, at) = min(a, b), max(a, b)
        return lo, (n, at + 1)

    def selected_on(self, n: int) -> tuple[int, int] | None:
        """The selected character range of line n, if the selection reaches it."""
        if not self.selection:
            return None
        (n0, a0), (n1, z1) = self.selection
        if not n0 <= n <= n1:
            return None
        line = self.lines[n]
        return (a0 if n == n0 else line.start, min(z1, line.end) if n == n1 else line.end)

    def selected_text(self, doc: Doc) -> str:
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
        pieces = ["" if b < 0 else doc.blocks[b].text[a:z].rstrip()
                  for b, *rest in runs for a, z in [rest or (0, 0)]]
        return "\n".join(pieces).strip("\n")

    # ---- drawing

    def draw(self, doc: Doc | None, unit: Unit | None, word: tuple[int, int] | None) -> None:
        """The text rows: following the sentence being read unless the wheel has moved the text away."""
        self.fit(doc)
        if unit and unit.block >= 0 and unit.block in self.where and not self.scrolled:
            self.follow(unit)
        self.top = max(0, min(self.top, self.bottom()))
        for row in range(self.body):
            n = self.top + row
            if n >= len(self.lines):
                break
            self.draw_line(row + 1, self.lines[n], doc, unit, word, self.selected_on(n))

    def draw_line(self, y: int, line: Line, doc: Doc, unit: Unit | None, word, selected=None) -> None:
        """One screen line, cut at every style, sentence, word and selection edge, each piece in its attribute."""
        if line.block < 0:
            return
        block = doc.blocks[line.block]
        base = self.theme.base(block)
        x = self.margin + line.indent
        self.term.put(y, x, line.prefix, self.theme.prefix(block))
        if line.end <= line.start:
            return
        text = block.text
        cx = x + len(line.prefix)
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
