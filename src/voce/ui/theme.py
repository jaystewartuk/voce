"""Colours and text attributes, in one place.

Colours are xterm-256 indices chosen to read on dark and light backgrounds alike, with 8-colour fallbacks.
The brand blue (index 33) marks headings and links; the sentence being read sits on a pale blue band, and the
word being spoken on a deep blue one.
"""

from __future__ import annotations

import curses

from voce.markdown import Block

ITALIC = getattr(curses, "A_ITALIC", 0)

#          name                 256 fg, 256 bg,  8 fg,                8 bg
_PAIRS = {"sentence":          (16, 153, curses.COLOR_BLACK, curses.COLOR_CYAN),
          "word":              (231, 25, curses.COLOR_WHITE, curses.COLOR_BLUE),
          "brand":             (33, -1, curses.COLOR_BLUE, -1),
          "dim":               (245, -1, curses.COLOR_WHITE, -1),
          "inline-code":       (173, -1, curses.COLOR_YELLOW, -1),
          "inline-code-lit":   (88, 153, curses.COLOR_RED, curses.COLOR_CYAN),
          "keyword":           (133, -1, curses.COLOR_MAGENTA, -1),
          "string":            (71, -1, curses.COLOR_GREEN, -1),
          "comment":           (244, -1, curses.COLOR_WHITE, -1),
          "number":            (173, -1, curses.COLOR_YELLOW, -1),
          "function":          (68, -1, curses.COLOR_BLUE, -1),
          "type":              (37, -1, curses.COLOR_CYAN, -1),
          "deleted":           (167, -1, curses.COLOR_RED, -1)}

# Syntax roles (from voce.highlight) to (pair, extra attributes).
_CODE = {"keyword": ("keyword", 0), "string": ("string", 0), "comment": ("comment", ITALIC),
         "number": ("number", 0), "function": ("function", 0), "type": ("type", 0), "builtin": ("type", 0),
         "decorator": ("number", 0), "variable": ("function", 0), "inserted": ("string", 0),
         "deleted": ("deleted", 0), "heading": ("brand", curses.A_BOLD), "prompt": ("dim", curses.A_BOLD)}

_DIM_KINDS = {"meta", "html", "rule", "hr"}


class Theme:
    def __init__(self) -> None:
        self.pairs: dict[str, int] = {}
        self.colour = False
        self.many = False

    def start(self) -> None:
        """Set up colour pairs (call once curses is running)."""
        if not curses.has_colors():
            return
        curses.start_color()
        try:
            curses.use_default_colors()
            default_bg = -1
        except curses.error:
            default_bg = curses.COLOR_BLACK
        many = self.many = curses.COLORS >= 256
        for n, (name, (fg, bg, fg8, bg8)) in enumerate(_PAIRS.items(), start=1):
            fg, bg = (fg, bg) if many else (fg8, bg8)
            try:
                curses.init_pair(n, fg, default_bg if bg == -1 else bg)
            except curses.error:
                continue
            self.pairs[name] = curses.color_pair(n)
        self.colour = True

    def pair(self, name: str) -> int:
        return self.pairs.get(name, 0)

    # ---- named attributes

    @property
    def bar(self) -> int:
        return curses.A_REVERSE

    @property
    def dim(self) -> int:
        return self.pair("dim") if self.many else curses.A_DIM  # 8-colour grey is unreadable on light themes

    @property
    def heading(self) -> int:
        return self.pair("brand") | curses.A_BOLD

    @property
    def selected(self) -> int:
        return curses.A_REVERSE

    @property
    def progress(self) -> int:
        """The part of the title bar behind you: the deep blue of the word being spoken."""
        return self.pair("word") | curses.A_BOLD if self.colour else curses.A_REVERSE | curses.A_BOLD

    def base(self, block: Block) -> int:
        """The attribute a block's text starts from."""
        if block.kind in ("h1", "h2"):
            return self.heading
        if block.kind.startswith("h"):
            return curses.A_BOLD
        if block.kind in _DIM_KINDS or (not block.spoken and block.kind != "code"):
            return self.dim
        return 0

    def prefix(self, block: Block) -> int:
        """The attribute for what comes before the text: bullets, numbers, gutters and rules."""
        return self.base(block) if block.kind == "li" else self.dim

    def text(self, block: Block, base: int, roles: frozenset, mark: str | None) -> int:
        """The attribute for a run of text with these roles, under the sentence or word highlight if marked."""
        if mark == "selected":  # text being dragged over to copy, shown the way the terminal would
            return curses.A_REVERSE
        if block.kind == "code":
            if mark == "word":
                return self.pair("word") | curses.A_BOLD if self.colour else curses.A_REVERSE | curses.A_BOLD
            if mark == "sentence":  # the line being read sits on the band, like a sentence of prose
                return self.pair("sentence") | (ITALIC if "comment" in roles else 0) if self.colour \
                    else base | curses.A_UNDERLINE
            for role in roles:
                if role in _CODE:
                    name, extra = _CODE[role]
                    return self.pair(name) | extra
            return base
        attr = base
        if "bold" in roles:
            attr |= curses.A_BOLD
        if "italic" in roles:
            attr |= ITALIC
        if "strike" in roles:
            attr |= curses.A_DIM
        if "link" in roles:
            attr |= curses.A_UNDERLINE
        if mark == "word":
            return self.pair("word") | curses.A_BOLD | (attr & (ITALIC | curses.A_UNDERLINE)) \
                if self.colour else curses.A_REVERSE | curses.A_BOLD
        if mark == "sentence":
            colour = self.pair("inline-code-lit") if "code" in roles else self.pair("sentence")
            return colour | (attr & ~curses.A_COLOR) if self.colour else attr | curses.A_UNDERLINE
        if "code" in roles:
            return (attr & ~curses.A_COLOR) | self.pair("inline-code")
        if "link" in roles and not attr & curses.A_COLOR:
            return attr | self.pair("brand")
        return attr
