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
from voce.speech import spoken_code

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
_HTML_TAGS = ("a|abbr|b|bdi|bdo|big|blockquote|br|center|cite|code|dd|del|details|dfn|div|dl|dt|em|figcaption|"
              "figure|font|h[1-6]|hr|i|img|ins|kbd|li|mark|ol|p|picture|pre|q|s|samp|section|small|source|span|"
              "strike|strong|sub|summary|sup|table|tbody|td|th|thead|tr|tt|u|ul|var|video|wbr")
# Only real HTML tags are removed, so generics such as List<String> or Map<K, V> stay as written.
_TAG = re.compile(rf"<!--.*?-->|</?(?:{_HTML_TAGS})(?:\s[^<>]*)?/?>", re.S | re.I)
_BREAK = re.compile(r"<br\s*/?>", re.I)
_ENTITY = re.compile(r"&(nbsp|amp|lt|gt|quot|apos|#\d{1,8}|#[xX][0-9a-fA-F]{1,8});")
_ENTITIES = {"nbsp": " ", "amp": "&", "lt": "<", "gt": ">", "quot": '"', "apos": "'"}
# Emphasis looks at most 2,000 characters ahead, so a paragraph full of stray asterisks stays fast.
_STRONG_STAR = re.compile(r"\*\*(?=\S)(.{1,2000}?)(?<=\S)\*\*")
_STRONG_UNDERSCORE = re.compile(r"(?<!\w)__(?=\S)(.{1,2000}?)(?<=\S)__(?!\w)")
_EM_STAR = re.compile(r"(?<![\w*])\*(?=[^\s*])(.{1,2000}?)(?<=[^\s*])\*(?![\w*])")
_EM_UNDERSCORE = re.compile(r"(?<!\w)_(?=[^\s_])(.{1,2000}?)(?<=[^\s_])_(?!\w)")
_STRIKE = re.compile(r"~~(?=\S)(.{1,2000}?)(?<=\S)~~")
_CONTROL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")


class _Out:
    """Collects plain text a character at a time, collapsing white space and remembering each character's style."""

    def __init__(self) -> None:
        self.chars: list[str] = []
        self.styles: list[frozenset] = []

    def add(self, text: str, style: frozenset) -> None:
        for ch in text:
            if (ch < " " and ch not in "\t\n\r") or ch == "\x7f":
                continue  # control characters can't be drawn
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
                out.add(_entity(m.group(1)) or m.group(0), style)
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


def _entity(name: str) -> str:
    """The character an entity stands for, or "" if it isn't one that can be shown."""
    if not name.startswith("#"):
        return _ENTITIES[name]
    try:
        code = int(name[2:], 16) if name[1:2] in "xX" and len(name) > 2 else int(name[1:])
    except ValueError:
        return ""
    if code < 32 or 0xD800 <= code <= 0xDFFF or code > 0x10FFFF:
        return ""
    return chr(code)


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


def _spoken_cell(cell: str, spans: list) -> str:
    """A table cell as the voice says it: inline code read the way a person reads code aloud."""
    out, pos = [], 0
    for start, end, roles in spans:
        if "code" in roles:
            out += [cell[pos:start], " ", spoken_code(cell[start:end]), " "]
            pos = end
    out.append(cell[pos:])
    return re.sub(r"\s+", " ", "".join(out)).strip()


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
        say = ", ".join(_spoken_cell(cell, cell_spans) for cell, cell_spans in row if cell)
        blocks.append(Block("row", text, spans, say=say))
        if is_header and fits:
            blocks.append(Block("rule", "─┼─".join("─" * w for w in widths), spoken=False))
    return blocks


def parse(md: str) -> list[Block]:
    """The blocks of a Markdown document, in order."""
    blocks: list[Block] = []
    para: list[str] = []
    lines = md.lstrip("\ufeff").splitlines()
    section, i = "", 0
    opened: list[int] = []                    # where each <details> still open began, as a block index
    hidden: list[tuple[int, bool]] = []       # blocks silenced by <details>, with whether they were spoken

    def add(block: Block) -> None:
        block.section = section
        if not (block.text.strip() or block.kind == "hr"):
            return
        if opened:
            hidden.append((len(blocks), block.spoken))
            block.spoken = False
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
                body.append(_CONTROL.sub("", raw[strip:].expandtabs(4)))
            code = "\n".join(body)
            add(Block("code", code, highlight.code_spans(code, lang), lang=lang))
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
            if i < len(lines):
                rest = lines[i].split("-->", 1)[1]
                if rest.strip():
                    lines[i] = rest  # text after the comment on the same line is read as usual
                    continue
            i += 1
            continue

        if _BLOCK_HTML.match(s):
            flush()
            for _ in re.findall(r"<details\b", s, re.I):
                opened.append(len(blocks))
            summary = re.search(r"<summary>(.*?)</summary>", s, re.I)
            if summary:
                text, spans = inline(summary.group(1))
                add(Block("html", "▸ " + text, [(a + 2, z + 2, r) for a, z, r in spans], spoken=False))
            text, spans = inline(re.sub(r"<summary>.*?</summary>", " ", s, flags=re.I))
            if text:  # <p>Real text.</p> and the like: the words inside are a paragraph
                add(Block("p", text, spans))
            for _ in re.findall(r"</details>", s, re.I):
                if opened:
                    opened.pop()
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
    if opened:  # a <details> never closed: read what follows it rather than silencing the rest of the file
        for b, was_spoken in hidden:
            if b >= opened[0]:
                blocks[b].spoken = was_spoken
    return blocks
