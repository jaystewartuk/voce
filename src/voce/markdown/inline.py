"""Inline Markdown into plain text, keeping bold, italic, code, links and strikethrough as spans over it.

The voice never hears the markup and the screen can still show it. Each style is a role in a span's frozenset,
and nested styles combine: bold text with code inside it carries both roles.
"""

from __future__ import annotations

import re

Span = tuple[int, int, frozenset]  # (start, end, roles) over a block's text


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


