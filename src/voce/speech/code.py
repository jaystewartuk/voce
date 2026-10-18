"""Code, read the way a pairing partner says it out loud.

Names are said as words (``array_values`` is "array values", ``usort`` is "U sort"), a variable's dollar sign and
the brackets are silent, operators get the PHP manual's own names (``===`` is "is identical to", ``<=>`` is
"spaceship"), a string is read by its contents and a trailing comment as prose. A file path is read with its
slashes and its extension by letter: ``src/voce/cli.py`` is "source slash voce slash C L I dot P Y".

The word tables are in words.py. The rules were written for PHP first and carry to any language with the same
symbols. Checked by ear with docs/hearing/check.py.
"""

from __future__ import annotations

import re

from voce.speech.words import (
    CAST_TYPES,
    CODE_OPERATORS,
    CODE_WORDS,
    FILE_EXTENSIONS,
    LINE_OPERATORS,
    STRING_PREFIXES,
    STRING_WORDS,
)

_CAMEL = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")
# A path has a slash in it, or is a file name: a word, a dot, and an extension of letters.
_PATH = re.compile(r"~?/?(?:[\w.-]+/)+[\w.-]*|\.?[A-Za-z_][\w-]*(?:\.[A-Za-z]\w*)+")


def spoken_name(name: str) -> str:
    """A name as its words: ``checkInDate`` is "check In Date", ``strlen`` is "string length"."""
    if name in CODE_WORDS:
        return CODE_WORDS[name]
    if re.fullmatch(r"[A-Za-z][A-Za-z0-9]*", name):
        return " ".join(CODE_WORDS.get(w, w) for w in _CAMEL.split(name))
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


def spoken_code(code: str) -> str:
    """A bit of inline code, the way a person reads it aloud."""
    s = code.strip()
    if s in CODE_OPERATORS:
        return CODE_OPERATORS[s]
    if _PATH.fullmatch(s):
        return spoken_path(s)
    s = re.sub(r"\(\s*\)", " ", s)                       # a call's empty brackets are not said
    s = re.sub(r"\$(?=[A-Za-z_])", "", s)                 # $reservation is "reservation"
    s = s.replace("?->", " nullsafe arrow ").replace("->", " arrow ").replace("=>", " double arrow ")
    s = s.replace("::", " double colon ")
    s = re.sub(r"(?<=\S)/(?=\S)", " slash ", s)          # a/b is "a slash b"
    s = re.sub(r"['\"`]", "", s)
    s = re.sub(r"[_\s\[\]]+", " ", s)                    # $guest['email'] is "guest email"
    words = []
    for word in s.split(" "):
        if word in CODE_WORDS:
            words.append(CODE_WORDS[word])
        elif re.fullmatch(r"[A-Za-z][A-Za-z0-9]*", word):
            words.append(spoken_name(word))
        else:
            words.append(word)
    return " ".join(w for w in words if w)


# ---------------------------------------------------------------- a line of code

_LINE_TOKEN = re.compile(
    r"""(?P<space>\s+)
      | (?P<comment>//.*|\#.*|/\*.*?(?:\*/|$))
      | (?P<string>'(?:[^'\\]|\\.)*'?|"(?:[^"\\]|\\.)*"?)
      | (?P<number>\d+(?:\.\d+)?)
      | (?P<var>\$+[A-Za-z_][A-Za-z0-9_]*)
      | (?P<name>[A-Za-z_][A-Za-z0-9_]*)
      | (?P<op><=>|===|!==|\?\?=|\*\*=|<<<|\?->|->|=>|::|==|!=|>=|<=|\?\?|\?:|&&|\|\||\+\+|--|\+=|-=|\*=|/=|\.=|\*\*
            |\.\.\.|\[\]|[-+*/%.<>!:|@^~\\(){}\[\];,=&?$])
      | (?P<other>.)""", re.X)
_CAST = re.compile(r"\((" + "|".join(CAST_TYPES) + r")\)")
_SIGNATURE = re.compile(r"\s*(public |protected |private |static )*function\b")


def _spoken_string(raw: str) -> str:
    body = raw[1:-1] if len(raw) > 1 and raw[-1] == raw[0] else raw[1:]
    if body in STRING_WORDS:
        return STRING_WORDS[body]
    if not re.search(r"[A-Za-z]", body):
        return "the string " + body
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", body):
        return spoken_code(body)  # a name in quotes, such as a callback or a key
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


def _spoken_operator(tok: str, line: str, end: int, after_value: bool) -> str:
    """An operator token, given what follows it in the line and whether a value came before it."""
    nxt = line[end:end + 1]
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


def spoken_line(line: str) -> str:
    """One line of code, the way a person reads it aloud."""
    words: list[str] = []
    previous = ""  # the kind of the last token that was not space, for [ and ...
    line = _CAST.sub(lambda m: f"cast to {m.group(1)} ", line)
    for m in _LINE_TOKEN.finditer(line):
        kind = m.lastgroup
        tok = m.group()
        if kind == "space":
            continue
        if kind == "comment":
            text = re.sub(r"^(//|#|/\*)\s*|\s*\*/$", "", tok).strip()
            if text:
                text = "and so on" if text in ("...", "…") else _spoken_comment(text)
                if words and not words[-1].endswith((".", ",")):
                    words.append(",")  # a comma: the voice pauses for over a second at a full stop
                words.append(text + ".")
            break
        if kind == "string":
            words.append(_spoken_string(tok))
        elif kind == "number":
            words.append(tok)
        elif kind == "var":
            words.append(spoken_code(tok.lstrip("$")))
        elif kind == "name":
            if tok in STRING_PREFIXES and line[m.end():m.end() + 1] in ("'", '"'):
                words.append(STRING_PREFIXES[tok])  # f"..." in Python is "f string ..."
            else:
                words.append(spoken_code(tok))
        elif kind == "op":
            words.append(_spoken_operator(tok, line, m.end(), previous in ("var", "name", "string", "number", "close")))
            if tok in (")", "]"):
                kind = "close"
        else:
            words.append(tok)
        previous = kind
    s = " ".join(w for w in words if w)
    s = re.sub(r"\s+([,.])", r"\1", s)
    s = re.sub(r"[,.](\s*[,.])+", lambda m: m.group()[-1], s)
    return s.strip(" ,.")
