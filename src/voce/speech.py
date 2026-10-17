"""Splitting text into sentences, and small rewrites so a voice reads it naturally."""

from __future__ import annotations

import re

ABBREVIATIONS = {"e.g", "i.e", "etc", "vs", "mr", "mrs", "ms", "dr", "st", "no", "approx", "inc", "ltd", "co",
                 "fig", "cf", "u.s", "u.k", "a.m", "p.m", "jan", "feb", "mar", "apr", "jun", "jul", "aug",
                 "sep", "sept", "oct", "nov", "dec"}
_BOUNDARY = re.compile(r"([.!?…]+[\"'”’)\]]*)(\s+)(?=[\"'“‘(\[]?[A-Z0-9])")


def sentences(text: str) -> list[tuple[int, int]]:
    """(start, end) of each sentence in text."""
    out, start = [], 0
    for m in _BOUNDARY.finditer(text):
        before = text[start:m.end(1)]
        last = re.search(r"(\S+)$", before)
        token = last.group(1).rstrip(".!?…\"'”’)]").lower() if last else ""
        if token in ABBREVIATIONS or re.fullmatch(r"[a-z]", token):
            continue
        if re.fullmatch(r"\d+", token) and m.group(1) == "." and text[m.end(2):m.end(2) + 1].isdigit():
            continue  # "version 3. 4 changes" is rare; "step 3. 4" is a list written inline
        out.append((start, m.end(1)))
        start = m.end(2)
    if start < len(text):
        out.append((start, len(text)))
    return [(a, b) for a, b in out if text[a:b].strip()]


_SYMBOLS = {"→": " to ", "←": " from ", "≈": " about ", "×": " times ", "−": " minus ", "&": " and ",
            "▸": "", "│": ", ", "☐": "", "☑": ""}
# Currency codes that mean something else in technical writing. Google reads "PHP 8" as "eight Philippine
# pesos", so before a version-like number (one or two digits, maybe dotted) these are spelled out: "P H P 8".
# Sums of money keep their code: "PHP 500", "PHP 1,500". Checked by ear with docs/hearing/check.py.
_VERSIONED_CODES = re.compile(r"\b(PHP|BSD|CRC|CVE)(?=\s+\d{1,2}(?:\.\d+)*(?!\d|,\d))")


# How a developer reads a bit of inline code aloud. Underscores are silent, so array_values is "array values".
# Some names are said in full or by their letters, so strlen is "string length" and usort is "U sort". A
# variable's dollar sign is not said, -> is "arrow", and an operator on its own is called by its name. Checked
# by ear with docs/hearing/check.py.
_CODE_OPERATORS = {
    "===": "identical", "!==": "not identical", "==": "equal", "!=": "not equal",
    ">=": "greater than or equal to", "<=": "less than or equal to", "<=>": "spaceship",
    "??=": "null coalescing assignment", "??": "null coalescing", "?:": "short ternary", "?->": "nullsafe arrow",
    "->": "arrow", "=>": "double arrow",
    "::": "double colon", "...": "three dots", "&": "ampersand", "&&": "and", "||": "or", "!": "not",
    "[]": "empty square brackets", "()": "empty brackets", "{}": "empty braces", "=": "equals", "+": "plus",
    "-": "minus", "*": "times", "/": "divided by", "%": "modulo", ".": "dot", ".=": "dot equals",
    "+=": "plus equals", "++": "plus plus", "--": "minus minus", "$": "dollar", "_": "underscore",
    "#": "hash", "@": "at", "|": "pipe", "<": "less than", ">": "greater than", "?": "question mark",
    ":": "colon", ";": "semicolon", "\\": "backslash",
}
_CODE_WORDS = {
    "str": "string", "Str": "string", "Arr": "array", "mb": "M B", "strlen": "string length",
    "strpos": "string position", "substr": "sub string",
    "strtoupper": "string to upper", "strtolower": "string to lower", "ucfirst": "U C first",
    "strcmp": "string compare", "strtotime": "string to time", "strval": "string value", "intval": "int value",
    "sprintf": "S print F", "printf": "print F", "intdiv": "int div", "usort": "U sort", "uasort": "U A sort",
    "uksort": "U K sort", "ksort": "K sort", "krsort": "K R sort", "asort": "A sort", "arsort": "A R sort",
    "rsort": "R sort", "isset": "is set", "foreach": "for each", "elseif": "else if", "fn": "F N",
    "json": "JSON", "html": "HTML", "url": "URL", "id": "I D", "db": "D B", "sql": "S Q L", "php": "P H P",
    "cli": "C L I", "api": "A P I", "uuid": "U U I D", "stdClass": "standard class", "len": "length",
    "pos": "position", "num": "number", "src": "source", "tmp": "temp", "cfg": "config", "ctx": "context",
    "req": "request", "res": "response", "err": "error", "msg": "message", "idx": "index", "val": "value",
    "obj": "object", "cb": "callback", "fmt": "format", "prev": "previous",
}
_CAMEL = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")


def spoken_code(code: str) -> str:
    """A bit of inline code, the way a person reads it aloud."""
    s = code.strip()
    if s in _CODE_OPERATORS:
        return _CODE_OPERATORS[s]
    s = re.sub(r"\(\s*\)", " ", s)                       # a call's empty brackets are not said
    s = re.sub(r"\$(?=[A-Za-z_])", "", s)                 # $reservation is "reservation"
    s = s.replace("?->", " nullsafe arrow ").replace("->", " arrow ").replace("=>", " double arrow ")
    s = s.replace("::", " double colon ")
    s = re.sub(r"['\"`]", "", s)
    s = re.sub(r"[_\s\[\]]+", " ", s)                    # $guest['email'] is "guest email"
    words = []
    for word in s.split(" "):
        if word in _CODE_WORDS:
            words.append(_CODE_WORDS[word])
        elif re.fullmatch(r"[A-Za-z][A-Za-z0-9]*", word):
            words.append(" ".join(_CODE_WORDS.get(w, w) for w in _CAMEL.split(word)))
        else:
            words.append(word)
    return " ".join(w for w in words if w)


# A line of code, the way a person reads it aloud in a pair-programming session: names as above, operators by
# their real names from the PHP manual (so the listener learns them), brackets silent, a semicolon a comma, a
# string by its contents, and a trailing comment as prose after a comma (a full stop makes Google pause for over
# a second).
_LINE_OPERATORS = {
    "<=>": "spaceship", "===": "is identical to", "!==": "is not identical to", "??=": "null coalescing assignment",
    "**=": "power equals", "<<<": "heredoc", "?->": "nullsafe arrow", "->": "arrow", "=>": "double arrow",
    "::": "double colon", "==": "is equal to", "!=": "is not equal to", ">=": "is greater than or equal to",
    "<=": "is less than or equal to",
    "??": "null coalescing", "?:": "short ternary", "&&": "and", "||": "or", "++": "plus plus",
    "--": "minus minus", "+=": "plus equals", "-=": "minus equals", "*=": "times equals",
    "/=": "divided equals", ".=": "dot equals", "**": "to the power", "=": "equals", "+": "plus", "-": "minus",
    "*": "times", "/": "divided by", "%": "modulo", ".": "dot", "<": "less than", ">": "greater than",
    "!": "not", ":": "colon", "|": "pipe", "@": "at", "&": "ampersand", "^": "caret", "~": "tilde", "\\": "",
    "(": "", ")": "", "{": "", "}": "", "]": "", ";": ",", ",": ",",
}
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
_CAST = re.compile(r"\((int|integer|float|double|string|bool|boolean|array|object)\)")
_STRING_WORDS = {"": "the empty string", ",": "a comma", " ": "a space", "\\n": "a new line", ".": "a dot",
                 "-": "a dash", "/": "a slash", ", ": "a comma and a space", "&": "an ampersand", "|": "a pipe",
                 ":": "a colon", ";": "a semicolon", "=": "an equals sign", "?": "a question mark"}
_STRING_PREFIXES = {"f": "f string", "b": "byte string", "r": "raw string", "rb": "raw byte string",
                    "fr": "raw f string", "rf": "raw f string"}


def _spoken_string(raw: str) -> str:
    body = raw[1:-1] if len(raw) > 1 and raw[-1] == raw[0] else raw[1:]
    if body in _STRING_WORDS:
        return _STRING_WORDS[body]
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
            if tok in _STRING_PREFIXES and line[m.end():m.end() + 1] in ("'", '"'):
                words.append(_STRING_PREFIXES[tok])  # f"..." in Python is "f string ..."
            else:
                words.append(spoken_code(tok))
        elif kind == "op":
            after_value = previous in ("var", "name", "string", "number", "close")
            if tok == "[]":
                words.append("square brackets" if after_value else "empty array")
            elif tok == "[":
                if not after_value:
                    words.append("array of")
            elif tok == "...":
                nxt = line[m.end():m.end() + 1]
                if nxt == "$" or nxt.isalpha():
                    words.append("variadic" if re.match(r"\s*(public |protected |private |static )*function\b", line)
                                 else "spread")
                else:
                    words.append("and so on")
            elif tok == "$":
                words.append("dollar")
            elif tok == "?":
                words.append("nullable" if line[m.end():m.end() + 1].isalpha() else "question mark")
            elif tok == "$":
                words.append("dollar")
            else:
                words.append(_LINE_OPERATORS.get(tok, tok))
            if tok in (")", "]"):
                kind = "close"
        else:
            words.append(tok)
        previous = kind
    s = " ".join(w for w in words if w)
    s = re.sub(r"\s+([,.])", r"\1", s)
    s = re.sub(r"[,.](\s*[,.])+", lambda m: m.group()[-1], s)
    return s.strip(" ,.")


def speakable(s: str) -> str:
    """Small fixes so the voice reads the text naturally."""
    for symbol, words in _SYMBOLS.items():
        s = s.replace(symbol, words)
    s = re.sub(r"\be\.g\.,?", "for example,", s)
    s = re.sub(r"\bi\.e\.,?", "that is,", s)
    s = re.sub(r"\betc\.", "and so on.", s)
    s = re.sub(r"(?<=\s)vs\.?(?=\s)", "versus", s)
    s = _VERSIONED_CODES.sub(lambda m: " ".join(m.group(1)), s)
    s = re.sub(r"#(\d+)", r"\1", s)
    s = re.sub(r"~(?=\d)", "about ", s)
    s = re.sub(r"\s+([,.;:!?])", r"\1", s)
    s = re.sub(r",(\s*,)+", ",", s)
    return re.sub(r"\s+", " ", s).strip()
