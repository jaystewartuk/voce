"""Markdown into blocks of display text, keeping inline styles as spans over that text.

The text of a block is what is shown, and (for blocks that are spoken) what the voice reads. Bold, italic, code,
links and struck-through text become spans over that plain text, so the voice never hears the markup and the
screen can still show it.

This is not a full CommonMark parser. It covers what notes, documentation and chat replies actually use:
headings, paragraphs, nested lists and task lists, block quotes, fenced code, tables, rules and a little HTML.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from voce import highlight

Span = tuple[int, int, frozenset]  # (start, end, roles) over a block's text


@dataclass
class Block:
    kind: str                # h1..h6, p, li, quote, code, row, rule, html, meta, hr
    text: str                # what is shown (and said, if spoken)
    spans: list = field(default_factory=list)  # inline styles, or syntax roles for code
    prefix: str = ""         # bullet, number or checkbox shown before the text
    indent: int = 0          # list nesting depth
    spoken: bool = True
    section: str = ""        # the h1 or h2 this block sits under, lower case
    ordered: bool = False    # a numbered list item
    lang: str = ""           # a code block's language
    say: str = ""            # what to say instead of the text (table rows)


# ---------------------------------------------------------------- inline markup

_ESCAPABLE = set("\\`*_{}[]()#+-.!|>~<")
_LINK = re.compile(r"!?\[((?:[^\[\]]|\[[^\]]*\])*)\]\(([^)]*)\)")
_AUTOLINK = re.compile(r"<((?:https?://|mailto:)[^>\s]+)>")
_TAG = re.compile(r"<!--.*?-->|</?[A-Za-z][A-Za-z0-9-]*(?:\s[^<>]*)?/?>", re.S)
_BREAK = re.compile(r"<br\s*/?>", re.I)
_ENTITY = re.compile(r"&(nbsp|amp|lt|gt|quot|apos|#\d+|#x[0-9a-fA-F]+);")
_ENTITIES = {"nbsp": " ", "amp": "&", "lt": "<", "gt": ">", "quot": '"', "apos": "'"}
_STRONG_STAR = re.compile(r"\*\*(?=\S)(.+?)(?<=\S)\*\*")
_STRONG_UNDERSCORE = re.compile(r"(?<!\w)__(?=\S)(.+?)(?<=\S)__(?!\w)")
_EM_STAR = re.compile(r"(?<![\w*])\*(?=[^\s*])(.+?)(?<=[^\s*])\*(?![\w*])")
_EM_UNDERSCORE = re.compile(r"(?<!\w)_(?=[^\s_])(.+?)(?<=[^\s_])_(?!\w)")
_STRIKE = re.compile(r"~~(?=\S)(.+?)(?<=\S)~~")


class _Out:
    """Collects plain text a character at a time, collapsing white space and remembering each character's style."""

    def __init__(self) -> None:
        self.chars: list[str] = []
        self.styles: list[frozenset] = []

    def add(self, text: str, style: frozenset) -> None:
        for ch in text:
            if ch.isspace():
                if not self.chars or self.chars[-1] == " ":
                    continue
                ch = " "
            self.chars.append(ch)
            self.styles.append(style)

    def result(self) -> tuple[str, list[Span]]:
        while self.chars and self.chars[-1] == " ":
            self.chars.pop()
            self.styles.pop()
        spans: list[Span] = []
        start = 0
        for k in range(1, len(self.styles) + 1):
            if k == len(self.styles) or self.styles[k] != self.styles[start]:
                if self.styles[start]:
                    spans.append((start, k, self.styles[start]))
                start = k
        return "".join(self.chars), spans


def _walk(s: str, out: _Out, style: frozenset) -> None:
    i, n = 0, len(s)
    while i < n:
        c = s[i]
        if c == "\\" and i + 1 < n and s[i + 1] in _ESCAPABLE:
            out.add(s[i + 1], style)
            i += 2
            continue
        if c == "`":
            run = len(s[i:]) - len(s[i:].lstrip("`"))
            close = re.compile(rf"(?<!`)`{{{run}}}(?!`)").search(s, i + run)
            if close:
                code = s[i + run:close.start()]
                if len(code) > 2 and code[0] == " " and code[-1] == " " and code.strip():
                    code = code[1:-1]
                out.add(code, style | {"code"})
                i = close.end()
            else:
                out.add(s[i:i + run], style)
                i += run
            continue
        if c == "[" or (c == "!" and s.startswith("[", i + 1)):
            m = _LINK.match(s, i)
            if m:
                _walk(m.group(1), out, style | {"link"})
                i = m.end()
                continue
        if c == "<":
            m = _AUTOLINK.match(s, i)
            if m:
                out.add(m.group(1), style | {"link"})
                i = m.end()
                continue
            m = _TAG.match(s, i)
            if m:
                if _BREAK.fullmatch(m.group(0)):
                    out.add(" ", style)
                i = m.end()
                continue
        if c == "&":
            m = _ENTITY.match(s, i)
            if m:
                name = m.group(1)
                if name.startswith("#x"):
                    out.add(chr(int(name[2:], 16)), style)
                elif name.startswith("#"):
                    out.add(chr(int(name[1:])), style)
                else:
                    out.add(_ENTITIES[name], style)
                i = m.end()
                continue
        if c in "*_~":
            matched = False
            for pattern, role in ((_STRONG_STAR, "bold"), (_STRONG_UNDERSCORE, "bold"), (_STRIKE, "strike"),
                                  (_EM_STAR, "italic"), (_EM_UNDERSCORE, "italic")):
                m = pattern.match(s, i)
                if m:
                    _walk(m.group(1), out, style | {role})
                    i = m.end()
                    matched = True
                    break
            if matched:
                continue
        out.add(c, style)
        i += 1


def inline(s: str) -> tuple[str, list[Span]]:
    """Markdown inline syntax to plain text, with (start, end, roles) spans for the styles it carried.

    Roles are bold, italic, code, link and strike. White space is collapsed and trimmed.
    """
    out = _Out()
    _walk(s, out, frozenset())
    return out.result()


def plain(s: str) -> str:
    """Markdown inline syntax to plain text."""
    return inline(s)[0]


# ---------------------------------------------------------------- blocks

_HEADING = re.compile(r"^ {0,3}(#{1,6})\s+(.*?)(?:\s+#+)?\s*$")
_ITEM = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$")
_TASK = re.compile(r"^\[([ xX])\]\s+(.*)$")
_FENCE = re.compile(r"^(\s*)(`{3,}|~{3,})\s*\{?\.?([\w+#.-]*)")
_RULE = re.compile(r"^ {0,3}([-*_])(\s*\1){2,}\s*$")
_TABLE_DIVIDER = re.compile(r"^\s*\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)*\|?\s*$")
_BLOCK_HTML = re.compile(r"^</?(details|summary|div|p|br|hr|img|table|thead|tbody|tr|td|th|picture|source|"
                         r"center|section|figure|figcaption|video|audio|iframe)\b", re.I)
_NAVIGATION = re.compile(r"(\[[^\]]+\]\([^)]+\)\s*(·\s*|\|\s*)?)+")

TABLE_WIDTH = 88     # widest table laid out in aligned columns
COLUMN_GAP = " │ "


def is_navigation(raw: str) -> bool:
    """Breadcrumbs and Next/Previous links: shown, not read."""
    t = raw.strip()
    return bool(_NAVIGATION.fullmatch(t)) or t.startswith(("Next:", "Previous:", "Back to the ["))


def _split_row(line: str) -> list[str]:
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|") and not s.endswith("\\|"):
        s = s[:-1]
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", s)]


def _is_table_start(lines: list[str], i: int) -> bool:
    s = lines[i].strip()
    if not s or "|" not in s or _TABLE_DIVIDER.fullmatch(s):
        return False
    if s.startswith("|"):
        return True
    return i + 1 < len(lines) and bool(_TABLE_DIVIDER.fullmatch(lines[i + 1].strip())) and "|" in lines[i + 1]


def _table_blocks(rows: list[list[tuple[str, list]]], aligns: list[str], header: bool) -> list[Block]:
    """Table rows as blocks: padded into aligned columns when they fit, joined plainly when they don't."""
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
        say = ", ".join(cell for cell, _ in row if cell)
        blocks.append(Block("row", text, spans, say=say))
        if is_header and fits:
            blocks.append(Block("rule", "─┼─".join("─" * w for w in widths), spoken=False))
    return blocks


def parse(md: str) -> list[Block]:
    """The blocks of a Markdown document, in order."""
    blocks: list[Block] = []
    para: list[str] = []
    lines = md.splitlines()
    section, details, i = "", 0, 0

    def add(block: Block) -> None:
        block.section = section
        if details:
            block.spoken = False
        if block.text.strip() or block.kind == "hr":
            blocks.append(block)

    def flush() -> None:
        if para:
            raw = " ".join(para)
            text, spans = inline(raw)
            nav = is_navigation(raw)
            add(Block("meta" if nav else "p", text, spans, spoken=not nav))
            para.clear()

    while i < len(lines):
        line = lines[i]
        s = line.strip()

        fence = _FENCE.match(line)
        if fence:
            flush()
            indent, marker, lang = len(fence.group(1)), fence.group(2), fence.group(3).lower()
            closing = re.compile(rf"^\s*{re.escape(marker[0])}{{{len(marker)},}}\s*$")
            j = i + 1
            while j < len(lines) and not closing.match(lines[j]):
                j += 1
            body = []
            for raw in lines[i + 1:j]:
                strip = min(indent, len(raw) - len(raw.lstrip(" ")))
                body.append(raw[strip:].expandtabs(4))
            code = "\n".join(body)
            add(Block("code", code, highlight.code_spans(code, lang), spoken=False, lang=lang))
            i = j + 1
            continue

        if not s:
            flush()
            i += 1
            continue

        if s.startswith("<!--"):
            flush()
            while i < len(lines) and "-->" not in lines[i]:
                i += 1
            i += 1
            continue

        if _BLOCK_HTML.match(s):
            flush()
            if re.match(r"<details", s, re.I):
                details += 1
            summary = re.search(r"<summary>(.*?)</summary>", s, re.I)
            if summary:
                text, spans = inline(summary.group(1))
                add(Block("html", "▸ " + text, [(a + 2, z + 2, r) for a, z, r in spans], spoken=False))
            if re.search(r"</details>", s, re.I):
                details = max(0, details - 1)
            i += 1
            continue

        m = _HEADING.match(line)
        if m:
            flush()
            level = len(m.group(1))
            text, spans = inline(m.group(2))
            if level <= 2:
                section = text.lower()
            add(Block(f"h{level}", text, spans))
            i += 1
            continue

        if _RULE.match(line):
            flush()
            add(Block("hr", ""))
            i += 1
            continue

        if _is_table_start(lines, i):
            flush()
            rows, aligns, header = [], [], False
            while i < len(lines) and lines[i].strip() and "|" in lines[i]:
                s = lines[i].strip()
                if _TABLE_DIVIDER.fullmatch(s):
                    header = len(rows) == 1
                    aligns = ["center" if c.startswith(":") and c.endswith(":") else
                              "right" if c.endswith(":") else "left" for c in _split_row(s)]
                else:
                    rows.append([inline(cell) for cell in _split_row(s)])
                i += 1
            for block in _table_blocks(rows, aligns, header):
                add(block)
            continue

        if s.startswith(">"):
            flush()
            quote = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote.append(lines[i].strip()[1:].strip())
                i += 1
            text, spans = inline(" ".join(quote))
            add(Block("quote", text, spans))
            continue

        m = _ITEM.match(line)
        if m and not _RULE.match(line):
            flush()
            depth = len(m.group(1).expandtabs(4)) // 2
            marker = m.group(2)
            parts = [m.group(3)]
            i += 1
            while i < len(lines):
                nxt = lines[i]
                if not nxt.strip() or _ITEM.match(nxt) or _HEADING.match(nxt) or _FENCE.match(nxt) \
                        or nxt.strip().startswith(("<", "|", ">")):
                    break
                parts.append(nxt.strip())
                i += 1
            raw = " ".join(parts)
            ordered = marker[0].isdigit()
            prefix = marker.rstrip(".)") + ". " if ordered else "• "
            task = _TASK.match(raw)
            if task and not ordered:
                prefix = "☑ " if task.group(1) in "xX" else "☐ "
                raw = task.group(2)
            text, spans = inline(raw)
            add(Block("li", text, spans, prefix=prefix, indent=min(depth, 4), ordered=ordered,
                      spoken=not is_navigation(raw)))
            continue

        para.append(s)
        i += 1
    flush()
    return blocks
