"""Code, read the way a pairing partner says it out loud.

Names are said as words (``array_values`` is "array values", ``usort`` is "U sort"), a variable's dollar sign and
the brackets are silent, operators get the PHP manual's own names (``===`` is "is identical to", ``<=>`` is
"spaceship"), a string is read by its contents and a trailing comment as prose. A file path is read with its
slashes and its extension by letter: ``src/voce/cli.py`` is "source slash voce slash C L I dot P Y".

Each language has its own words and operator names in words.py, on top of what is common to all of them: a
Python line says "returns" for ``->`` and "floor divided by" for ``//``, and a JavaScript line says "is strictly
equal to" for ``===``, MDN's name. The rules were written for PHP first and the generic rules are PHP's. Checked
by ear with docs/hearing/check.py.
"""

from __future__ import annotations

import re
from functools import cache

from voce.speech.words import (
    CAST_TYPES,
    CODE_OPERATORS,
    COMMON_WORDS,
    FILE_EXTENSIONS,
    GENERIC,
    LINE_OPERATORS,
    STRING_PREFIXES,
    STRING_WORDS,
    Language,
    language,
)

_CAMEL = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")
# A path has a slash in it, or is a file name: a word, a dot, and an extension of letters.
_PATH = re.compile(r"~?/?(?:[\w.-]+/)+[\w.-]*|\.?[A-Za-z_][\w-]*(?:\.[A-Za-z]\w*)+")


def spoken_name(name: str, lang: Language = GENERIC) -> str:
    """A name as its words: ``checkInDate`` is "check In Date", ``strlen`` is "string length" in PHP."""
    words = lang.words
    if name in words:
        return words[name]
    if name in COMMON_WORDS:
        return COMMON_WORDS[name]
    if lang.dunder and re.fullmatch(r"__\w+__", name):
        return "dunder " + spoken_name(name.strip("_"), lang)
    if re.fullmatch(r"[A-Za-z][A-Za-z0-9]*", name):
        return " ".join(words.get(w, COMMON_WORDS.get(w, w)) for w in _CAMEL.split(name))
    return name


def spoken_path(path: str) -> str:
    """A file path or name, the way a person says it: slashes said, underscores silent, the extension by letter."""
    parts = []
    for n, segment in enumerate(path.split("/")):
        if not segment:
            parts.append("slash" if n == 0 else "")
            continue
        if segment == "..":
            parts.append("dot dot")
            continue
        stem, dot, ext = segment.rpartition(".")
        if dot and stem and ext.isalpha():
            words = [spoken_name(w) for w in re.split(r"[_\s-]+", stem.lstrip(".")) if w]
            parts.append(("dot " if stem.startswith(".") else "") + " ".join(words) + " dot "
                         + FILE_EXTENSIONS.get(ext.lower(), spoken_name(ext)))
        else:
            words = [spoken_name(w) for w in re.split(r"[_\s-]+", segment.lstrip(".")) if w]
            parts.append(("dot " if segment.startswith(".") else "") + " ".join(words))
    return re.sub(r"\s+", " ", " slash ".join(parts)).strip()


def spoken_code(code: str, lang: str | Language = GENERIC) -> str:
    """A bit of inline code, the way a person reads it aloud, in a language's own words if it is given."""
    lang = language(lang) if isinstance(lang, str) else lang
    s = code.strip()
    if s in CODE_OPERATORS:
        return CODE_OPERATORS[s]
    if _PATH.fullmatch(s):
        return spoken_path(s)
    if lang.dunder and re.fullmatch(r"__\w+__", s):
        return spoken_name(s, lang)
    s = re.sub(r"\(\s*\)", " ", s)                       # a call's empty brackets are not said
    s = re.sub(r"\$(?=[A-Za-z_])", "", s)                 # $reservation is "reservation"
    s = s.replace("?->", " nullsafe arrow ").replace("->", " arrow ").replace("=>", " double arrow ")
    s = s.replace("::", " double colon ")
    s = re.sub(r"(?<=\S)/(?=\S)", " slash ", s)          # a/b is "a slash b"
    s = re.sub(r"['\"`]", "", s)
    s = re.sub(r"[_\s\[\]]+", " ", s)                    # $guest['email'] is "guest email"
    return " ".join(w for w in (spoken_name(word, lang) for word in s.split(" ")) if w)


# ---------------------------------------------------------------- a line of code

_COMMENT_STARTS = {"//": r"//.*", "#": r"\#.*", "/*": r"/\*.*?(?:\*/|$)", "--": r"--.*", ";": r";.*"}
_TOKENS = r"""(?P<space>\s+)
      | (?P<comment>COMMENTS)
      | (?P<string>'(?:[^'\\]|\\.)*'?|"(?:[^"\\]|\\.)*"?|`(?:[^`\\]|\\.)*`?)
      | (?P<number>\d+(?:\.\d+)?)
      | (?P<var>\$+[A-Za-z_][A-Za-z0-9_]*)
      | (?P<name>[A-Za-z_][A-Za-z0-9_]*)
      | (?P<op><=>|===|!==|\?\?=|\*\*=|<<<|\?->|->|=>|::|==|!=|>=|<=|<>|\?\?|\?:|\?\.|:=|&&|\|\||\+\+|--|\+=|-=
            |\*=|/=|\.=|\*\*|//|>>|\.\.\.|\[\]|[-+*/%.<>!:|@^~\\(){}\[\];,=&?$])
      | (?P<other>.)"""


@cache
def _tokens(comments: tuple) -> re.Pattern:
    """The tokeniser for a language, which differs only in how a comment starts: // is a comment in PHP and
    floor division in Python."""
    starts = "|".join(_COMMENT_STARTS[c] for c in comments) or "(?!x)x"
    return re.compile(_TOKENS.replace("COMMENTS", starts), re.X)
_CAST = re.compile(r"\((" + "|".join(CAST_TYPES) + r")\)")
_SIGNATURE = re.compile(r"\s*(public |protected |private |static )*function\b")


def _spoken_string(raw: str, lang: Language = GENERIC) -> str:
    body = raw[1:-1] if len(raw) > 1 and raw[-1] == raw[0] else raw[1:]
    if body in STRING_WORDS:
        return STRING_WORDS[body]
    if not re.search(r"[A-Za-z]", body):
        return "the string " + body
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", body):
        return spoken_code(body, lang)  # a name in quotes, such as a callback or a key
    body = re.sub(r"\\n", " new line ", body)
    body = body.replace("?->", " nullsafe arrow ").replace("->", " arrow ")
    body = re.sub(r"[{}$\[\]]", " ", body)
    body = re.sub(r"(?<=\w)_+(?=\w)", " ", body)
    body = body.replace("%.", " percent point ").replace("%", " percent ").replace("?", " question mark ")
    return re.sub(r"\s+", " ", body).strip()


def _spoken_comment(text: str) -> str:
    text = re.sub(r"\$(?=[A-Za-z_])", "", text)
    text = text.replace("[]", " empty array ").replace("=>", " double arrow ").replace("->", " arrow ")
    text = text.replace("\\n", " backslash n ").replace("...", " and so on ")
    text = re.sub(r"[\[\]_]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _spoken_operator(tok: str, line: str, end: int, after_value: bool, lang: Language) -> str:
    """An operator token, given what follows it in the line and whether a value came before it."""
    nxt = line[end:end + 1]
    if tok in ("*", "**") and not after_value:
        return "star" if tok == "*" else "double star"  # *args and **kwargs
    if tok in lang.operators:
        return lang.operators[tok]
    if tok == "[]":
        return "square brackets" if after_value else "empty array"
    if tok == "[":
        return "" if after_value else "array of"
    if tok == "...":
        if nxt == "$" or nxt.isalpha():  # the manual: a variable-length argument list, or unpacking
            return "variadic" if _SIGNATURE.match(line) else "unpack"
        return "and so on"
    if tok == "&" and nxt == "$":
        return "by reference"
    if tok == "$":
        return "dollar"
    if tok == "?":
        return "nullable" if nxt.isalpha() else "question mark"
    return LINE_OPERATORS.get(tok, tok)


def spoken_line(line: str, lang: str | Language = GENERIC) -> str:
    """One line of code, the way a person reads it aloud, in the language's own words if it is given."""
    lang = language(lang) if isinstance(lang, str) else lang
    words: list[str] = []
    previous = ""  # the kind of the last token that was not space, for [ and ...
    if lang is GENERIC or lang.name == "php":
        line = _CAST.sub(lambda m: f"cast to {m.group(1)} ", line)
    for m in _tokens(lang.comments).finditer(line):
        kind = m.lastgroup
        tok = m.group()
        if kind == "space":
            continue
        if kind == "comment":
            text = re.sub(r"^(//|#|/\*|--|;)\s*|\s*\*/$", "", tok).strip()
            if text:
                text = "and so on" if text in ("...", "…") else _spoken_comment(text)
                if words and not words[-1].endswith((".", ",")):
                    words.append(",")  # a comma: the voice pauses for over a second at a full stop
                words.append(text + ".")
            break
        if kind == "string":
            words.append(_spoken_string(tok, lang))
        elif kind == "number":
            words.append(tok)
        elif kind == "var":
            words.append(spoken_code(tok.lstrip("$"), lang))
        elif kind == "name":
            if tok in STRING_PREFIXES and line[m.end():m.end() + 1] in ("'", '"'):
                words.append(STRING_PREFIXES[tok])  # f"..." in Python is "f string ..."
            else:
                words.append(spoken_code(tok, lang))
        elif kind == "op":
            after_value = previous in ("var", "name", "string", "number", "close")
            words.append(_spoken_operator(tok, line, m.end(), after_value, lang))
            if tok in (")", "]"):
                kind = "close"
        else:
            words.append(tok)
        previous = kind
    s = " ".join(w for w in words if w)
    s = re.sub(r"\s+([,.])", r"\1", s)
    s = re.sub(r"[,.](\s*[,.])+", lambda m: m.group()[-1], s)
    return s.strip(" ,.")
