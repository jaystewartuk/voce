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
from voce.markdown import tables
from voce.markdown.inline import inline


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


_CONTROL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")
_HEADING = re.compile(r"^ {0,3}(#{1,6})\s+(.*?)(?:\s+#+)?\s*$")
_ITEM = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$")
_TASK = re.compile(r"^\[([ xX])\]\s+(.*)$")
_FENCE = re.compile(r"^(\s*)(`{3,}|~{3,})\s*\{?\.?([\w+#.-]*)")
_RULE = re.compile(r"^ {0,3}([-*_])(\s*\1){2,}\s*$")
_BLOCK_HTML = re.compile(r"^</?(details|summary|div|p|br|hr|img|table|thead|tbody|tr|td|th|picture|source|"
                         r"center|section|figure|figcaption|video|audio|iframe)\b", re.I)
_NAVIGATION = re.compile(r"(\[[^\]]+\]\([^)]+\)\s*(·\s*|\|\s*)?)+")


def is_navigation(raw: str) -> bool:
    """Breadcrumbs and Next/Previous links: shown, not read."""
    t = raw.strip()
    return bool(_NAVIGATION.fullmatch(t)) or t.startswith(("Next:", "Previous:", "Back to the ["))


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

        if tables.is_table_start(lines, i):
            flush()
            rows, aligns, header = [], [], False
            while i < len(lines) and lines[i].strip() and "|" in lines[i]:
                if tables.is_divider(lines[i]):
                    header = len(rows) == 1
                    aligns = tables.alignments(lines[i])
                else:
                    rows.append([inline(cell) for cell in tables.split_row(lines[i])])
                i += 1
            for block in tables.table_blocks(rows, aligns, header, Block):
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
