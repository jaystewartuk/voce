"""Tables: rows padded into aligned columns when they fit, each row one block that is read cell by cell."""

from __future__ import annotations

import re

from voce.speech import spoken_code

TABLE_WIDTH = 88     # widest table laid out in aligned columns
COLUMN_GAP = " │ "
_DIVIDER = re.compile(r"^\s*\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)*\|?\s*$")


def is_divider(line: str) -> bool:
    return bool(_DIVIDER.fullmatch(line.strip()))


def split_row(line: str) -> list[str]:
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|") and not s.endswith("\\|"):
        s = s[:-1]
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", s)]


def is_table_start(lines: list[str], i: int) -> bool:
    s = lines[i].strip()
    if not s or "|" not in s or is_divider(s):
        return False
    if s.startswith("|"):
        return True
    return i + 1 < len(lines) and is_divider(lines[i + 1]) and "|" in lines[i + 1]


def alignments(divider: str) -> list[str]:
    return ["center" if c.startswith(":") and c.endswith(":") else "right" if c.endswith(":") else "left"
            for c in split_row(divider)]


def spoken_cell(cell: str, spans: list) -> str:
    """A table cell as the voice says it: inline code read the way a person reads code aloud."""
    out, pos = [], 0
    for start, end, roles in spans:
        if "code" in roles:
            out += [cell[pos:start], " ", spoken_code(cell[start:end]), " "]
            pos = end
    out.append(cell[pos:])
    return re.sub(r"\s+", " ", "".join(out)).strip()


def table_blocks(rows: list[list[tuple[str, list]]], aligns: list[str], header: bool, block) -> list:
    """Table rows as blocks: padded into aligned columns when they fit, joined plainly when they don't.

    ``block`` is the Block class, passed in so this module does not import the block parser it serves.
    """
    columns = max(len(r) for r in rows)
    rows = [r + [("", [])] * (columns - len(r)) for r in rows]
    aligns = (aligns + ["left"] * columns)[:columns]
    widths = [max(len(r[c][0]) for r in rows) for c in range(columns)]
    fits = sum(widths) + len(COLUMN_GAP) * (columns - 1) <= TABLE_WIDTH
    blocks = []
    for n, row in enumerate(rows):
        text, spans = "", []
        for c, (cell, cell_spans) in enumerate(row):
            if c:
                text += COLUMN_GAP
            pad = widths[c] - len(cell) if fits else 0
            left = pad if aligns[c] == "right" else pad // 2 if aligns[c] == "center" else 0
            offset = len(text) + left
            spans += [(a + offset, z + offset, roles) for a, z, roles in cell_spans]
            text += " " * left + cell + " " * (pad - left)
        text = text.rstrip()
        is_header = header and n == 0
        if is_header and text:
            spans = [(0, len(text), frozenset({"bold"})), *spans]
        say = ", ".join(spoken_cell(cell, cell_spans) for cell, cell_spans in row if cell)
        blocks.append(block("row", text, spans, say=say))
        if is_header and fits:
            blocks.append(block("rule", "─┼─".join("─" * w for w in widths), spoken=False))
    return blocks
