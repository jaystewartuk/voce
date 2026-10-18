"""Laying blocks out as screen lines, and timing the word highlight within a sentence."""

from __future__ import annotations

import re
from dataclasses import dataclass

from voce.document import Doc, Unit

CODE_GUTTER = "▎ "
QUOTE_BAR = "│ "


@dataclass
class Line:
    block: int    # index into the document's blocks, or -1 for a blank line
    start: int    # character range of the block's text on this line
    end: int
    prefix: str   # drawn before the text: bullet, gutter, quote bar, rule
    indent: int


def wrap(text: str, width: int) -> list[tuple[int, int]]:
    """Spans (start, end) of text wrapped to width, breaking at spaces."""
    spans: list[tuple[int, int]] = []
    line_start: int | None = None
    line_end = 0
    for m in re.finditer(r"\S+", text):
        a, z = m.span()
        while z - a > width:  # a word longer than the line
            if line_start is not None:
                spans.append((line_start, line_end))
                line_start = None
            spans.append((a, a + width))
            a += width
        if line_start is None:
            line_start, line_end = a, z
        elif z - line_start > width:
            spans.append((line_start, line_end))
            line_start, line_end = a, z
        else:
            line_end = z
    if line_start is not None:
        spans.append((line_start, line_end))
    return spans or [(0, 0)]


def layout(doc: Doc, width: int) -> tuple[list[Line], dict[int, int]]:
    """Screen lines for the document at this width, and the first line of each block that can be read."""
    lines: list[Line] = []
    where: dict[int, int] = {}
    previous = None
    for b, block in enumerate(doc.blocks):
        if block.kind == "hr":
            lines.append(Line(-1, 0, 0, "", 0))
            lines.append(Line(b, 0, 0, "─" * min(width, 40), 0))
            previous = block
            continue
        gap = previous is not None and not (
            (block.kind == "li" and previous.kind == "li")
            or (block.kind in ("row", "rule") and previous.kind in ("row", "rule")))
        if gap:
            lines.append(Line(-1, 0, 0, "", 0))
        previous = block
        if block.kind == "code":
            where[b] = len(lines)
            lines += _code_lines(b, block.text, block.lang, width)
            continue
        indent = 2 * block.indent + (2 if block.kind == "quote" else 0)
        prefix = block.prefix if block.kind == "li" else QUOTE_BAR if block.kind == "quote" else ""
        avail = max(10, width - indent - len(prefix))
        where[b] = len(lines)
        for k, (a, z) in enumerate(wrap(block.text, avail)):
            lines.append(Line(b, a, z, prefix if k == 0 or block.kind == "quote" else " " * len(prefix), indent))
    return lines, where


def _code_lines(b: int, code: str, lang: str, width: int) -> list[Line]:
    """Code keeps its spacing: long lines are cut at the width and carried on under the gutter."""
    lines = [Line(b, 0, 0, CODE_GUTTER + lang, 0)] if lang else []
    avail = max(10, width - len(CODE_GUTTER))
    offset = 0
    for raw in code.split("\n"):
        for k in range(0, max(1, len(raw)), avail):
            lines.append(Line(b, offset + k, offset + min(len(raw), k + avail), CODE_GUTTER, 0))
        offset += len(raw) + 1
    return lines


def word_spans(text: str) -> list[tuple[int, int]]:
    return [m.span() for m in re.finditer(r"\S+", text)]


def word_at(unit: Unit, block_text: str, t: float, length: float) -> tuple[int, int] | None:
    """Which word of the unit is being spoken t seconds in, judged by word length and punctuation."""
    spans = [(a + unit.start, z + unit.start) for a, z in word_spans(block_text[unit.start:unit.end])]
    if not spans or length <= 0:
        return None
    weights = []
    for a, z in spans:
        w = block_text[a:z]
        weights.append(len(w) + 2 + (4 if w[-1] in ".!?:;" else 2 if w[-1] == "," else 0))
    lead, tail = 0.12, 0.35
    usable = max(0.1, length - lead - tail)
    pos = (t - lead) / usable * sum(weights)
    run = 0
    for span, w in zip(spans, weights):
        run += w
        if pos < run:
            return span
    return spans[-1]
