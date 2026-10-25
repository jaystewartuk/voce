"""Code, read the way a pairing partner says it out loud.

Names are said as words (``array_values`` is "array values", ``usort`` is "U sort"), a variable's dollar sign and
the brackets are silent, operators get the PHP manual's own names (``===`` is "is identical to", ``<=>`` is
"spaceship"), a string is read by its contents and a trailing comment as prose. A file path is read with its
slashes and its extension by letter: ``src/voce/cli.py`` is "source slash voce slash C L I dot P Y".

Each language has its own words and operator names in its own file in words/, on top of what is common to all of
them: a Python line says "returns" for ``->`` and "floor divided by" for ``//``, and a JavaScript line says "is
strictly equal to" for ``===``, MDN's name. The rules were written for PHP first and the generic rules are
PHP's. Checked by ear with docs/hearing/check.py.
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
# Inline code with an operator between spaces (`$a === $b`) is read as a line of code would be.
_EXPRESSION = re.compile(r"\s(===|!==|==|!=|<=>|<=|>=|=>|->|\?\?|&&|\|\||\*\*|[-+*/<>=])\s")
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
        return " ".join(_word(w, words) for w in _CAMEL.split(name))
    return name


def _word(w: str, words: dict) -> str:
    """One word of a name, by the language's table, then the common one, then as itself: Json is JSON, Id is I D."""
    for key in (w, w.lower()):
        if key in words:
            return words[key]
        if key in COMMON_WORDS:
            return COMMON_WORDS[key]
    return w


def spoken_path(path: str) -> str:
    """A file path or name, the way a person says it: slashes said, underscores silent, the extension by letter."""
    parts = []
    for segment in path.split("/"):
        if not segment:
            parts.append("")  # a leading slash is said once, by the join below
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
    if _EXPRESSION.search(s) or (_WHERE.search(s) and (lang is GENERIC or lang.name == "php")):
        return spoken_line(s, lang)
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
      | (?P<number>0[xX][\da-fA-F_]+|\d+(?:\.\d+)?)
      | (?P<var>\$+[A-Za-z_][A-Za-z0-9_]*)
      | (?P<name>[A-Za-z_][A-Za-z0-9_]*)
      | (?P<op><=>|===|!==|\?\?=|\*\*=|<<<|\?->|->|=>|::|==|!=|>=|<=|<>|\?\?|\?:|\?\.|:=|&&|\|\||\+\+|--|\+=|-=
            |\*=|/=|\.=|\*\*|//|>>|\.\.\.|\[\]|\{\}|[-+*/%.<>!:|@^~\\(){}\[\];,=&?$])
      | (?P<other>.)"""


@cache
def _tokens(comments: tuple) -> re.Pattern:
    """The tokeniser for a language, which differs only in how a comment starts: // is a comment in PHP and
    floor division in Python."""
    starts = "|".join(_COMMENT_STARTS[c] for c in comments) or "(?!x)x"
    return re.compile(_TOKENS.replace("COMMENTS", starts), re.X)
_CAST = re.compile(r"\((" + "|".join(CAST_TYPES) + r")\)")
_PHP_TAGS = re.compile(r"<\?php\b|<\?=|\?>")
_PHP_TAGS_SAID = {"<?php": "P H P open tag", "<?=": "P H P echo tag", "?>": "P H P close tag"}
_SIGNATURE = re.compile(r"\s*(public |protected |private |static )*function\b")
# A query builder's where with the operator left out, or written as '=': where('id', 1) is where id is equal to 1.
_WHERE = re.compile(r"\b(where|orWhere|whereNot|orWhereNot|having|orHaving)\(\s*(['\"][\w.]+['\"])\s*,\s*"
                    r"(?:'='\s*,\s*)?((?:[^,()\[\]]|\(\))+?)\s*\)")
# A line of words with a sentence's punctuation and none of code's: prose inside a string, a doc comment or a
# heredoc, read as prose.
_PROSE_LINE = re.compile(r"^[\w\s,.;:!?'\"-]+$")
# TypeScript's type parameters before a function's own: <T extends Foo, U>(x: T) => ..., said "generic T".
_TYPE_PARAMS = re.compile(r"<[A-Z]\w*(?:\s+extends\s+[^<>()]+)?(?:\s*,\s*[A-Z]\w*(?:\s+extends\s+[^<>()]+)?)*,?>\s*\(")
# A line of a doc comment that is an example of code rather than prose: const app = new Hono(), app.get(...).
_DOC_CODE = re.compile(r"(?:const|let|var|import|export|return|await|function|class|new|type|interface)\s|"
                       r"[\w$.]+\(.*\)\s*;?$|[\w$.\[\]]+\s*=\s")
# A JavaScript regular expression literal: /^text\/plain/i.
_REGEX = re.compile(r"/(?![/*])(?:\\.|\[(?:\\.|[^\]\\])*\]|[^/\\\n\[])+/[a-z]*")
# A Python line that opens a block, such as `for child in v._prev:`, which can look like prose but is code.
_PY_BLOCK = re.compile(r"\s*(if|elif|else|for|while|with|def|class|try|except|finally|async|match|case)\b[^:]*:")
# A docstring on a line of its own, or a line with only its opening or closing quotes: read as prose.
_DOCSTRING = re.compile(r"\s*[rRuU]?(?:\"\"\"|''')(.*?)(?:\"\"\"|''')?\s*$")
# A comment that is only an expression, such as `# other + self` or `# -self`: read as code.
_CODE_COMMENT = re.compile(r"-?\w+(?:\s+[-+*/]\s+-?\w+)+|-[A-Za-z_]\w*")


# "{$this->name}" and "$name" inside a double-quoted string are code: read them as code.
_INTERPOLATED = re.compile(r"\{\$([^}]*)\}|\$([A-Za-z_]\w*(?:->[A-Za-z_]\w*|\[[^\]]*\])*)")
# A line of a doc comment: its opening, its closing, or a continuation starting with a star.
_DOC_LINE = re.compile(r"^\s*(?:/\*\*?|\*/|\*)(?!\s*[\w$(]*\s*[*=;)])\s?(.*?)\s*(?:\*/)?\s*$")
_DOC_TAGS = {"return": "returns", "inheritdoc": "inherit doc", "var": "var", "param": "parameter"}
# Tags whose whole text is types and names rather than a type, a variable and a description.
_TYPE_TAGS = ("template", "method", "property", "property-read", "property-write", "mixin", "see", "uses",
              "extends", "implements", "phpstan-", "psalm-")


def _spoken_type(text: str, lang: Language) -> str:
    """A type in a doc comment: ``array<int, string>|null`` is "array of int, string, or null", ``?Foo`` is
    "nullable Foo", ``Foo[]`` is "Foo array", a namespace's backslashes are silent."""
    text = text.replace("|", " or ").replace("&", " and ")
    text = re.sub(r"\?(?=[\w\\])", "nullable ", text)
    text = re.sub(r"(\w)\s*[<{]", r"\1 of ", text)
    text = re.sub(r"[>}]", " ", text)
    text = re.sub(r"(\w)\[\]", r"\1 array", text)
    text = re.sub(r"\(\s*\)", " ", text).replace("):", " returning ").replace("(", " taking ").replace(")", " ")
    text = text.replace(" = ", " equals ").replace("=", " equals ")
    text = re.sub(r"[\\$]", " ", text)
    text = re.sub(r"(?<=[\w)])\s*,\s*(?=\w)", ", ", text)
    words = [spoken_name(w, lang) if re.fullmatch(r"\w+", w) else w for w in re.split(r"(\w+)", text)]
    return re.sub(r"\s+", " ", "".join(words)).strip()


def _doc_type(rest: str) -> tuple[str, str]:
    """The type at the start of a doc tag's text and what follows it. A type runs on past a space while a bracket
    is open or a closure's return type is still to come: ``array<int, string>``, ``\\Closure(TValue): bool``."""
    words = rest.split()
    taken = []
    while words:
        taken.append(words.pop(0))
        so_far = " ".join(taken)
        if (so_far.count("<") > so_far.count(">") or so_far.count("(") > so_far.count(")")
                or so_far.count("{") > so_far.count("}") or so_far.endswith(":")):
            continue
        break
    return " ".join(taken), " ".join(words)


def _spoken_doc(text: str, lang: Language) -> str:
    """A line of a doc comment as a person reads it: ``@param  array|string  $columns  The columns`` is
    "param array or string, columns, The columns"."""
    text = re.sub(r"\{@inherit[Dd]oc\}", "inherit doc", text)
    m = re.match(r"@([\w-]+)\s*(.*)$", text)
    if not m:
        if _DOC_CODE.match(text):
            return spoken_line(text, lang)  # an example in a doc comment, such as `const app = new Hono()`
        return _spoken_comment(text)
    tag, rest = m.group(1), m.group(2)
    said_tag = _DOC_TAGS.get(tag.lower(), tag.replace("-", " "))
    said_tag = " ".join(spoken_name(w, lang) for w in said_tag.split())
    if not rest:
        return said_tag
    if tag.lower().startswith(_TYPE_TAGS):
        return f"{said_tag} {_spoken_type(rest, lang)}"
    tag = said_tag
    if rest.startswith("$"):
        return f"{tag} {_spoken_comment(rest)}"
    kind, rest = _doc_type(rest)
    said = [tag, _spoken_type(kind, lang)]
    if rest:
        name = re.match(r"(&?\.{0,3}\$\w+)\s*(.*)$", rest)
        if name:
            var = name.group(1).replace("&", "by reference ").replace("...", "variadic ")
            said.append(", " + spoken_code(var, lang))
            rest = name.group(2)
        if rest:
            said.append(", " + _spoken_comment(rest))
    return re.sub(r"\s+", " ", " ".join(said)).replace(" ,", ",").strip()


def _spoken_string(raw: str, lang: Language = GENERIC) -> str:
    body = raw[1:-1] if len(raw) > 1 and raw[-1] == raw[0] else raw[1:]
    if body in STRING_WORDS:
        return STRING_WORDS[body]
    if body in CODE_OPERATORS:
        return CODE_OPERATORS[body]  # '>=' in a query builder's where
    if not re.search(r"[A-Za-z]", body):
        return "the string " + body
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", body):
        return spoken_code(body, lang)  # a name in quotes, such as a callback or a key
    if _PATH.fullmatch(body):
        return spoken_path(body)  # 'routes/web.php' is "routes slash web dot P H P"
    body = re.sub(r"\\n", " new line ", body)
    if lang.name == "python" and "{" in body:  # an f-string's fields are code: {self.data} is "self dot data"
        parts = re.split(r"(\{[^{}]+\})", body)  # the fields, and the text between them: f'**{n}' is "double star n"
        body = " ".join(spoken_code(p[1:-1], lang) if p.startswith("{") else
                        CODE_OPERATORS.get(p.strip(), p) if re.fullmatch(r"\s*[-+*/%=<>!&|^~]+\s*", p) else p
                        for p in parts)
        body = body.replace("(", " ").replace(")", " ").replace("=", " equals ")
    body = _INTERPOLATED.sub(lambda m: " " + spoken_code(m.group(1) or m.group(2), lang) + " ", body)
    body = body.replace("?->", " nullsafe arrow ").replace("->", " arrow ")
    body = re.sub(r"[{}$\[\]]", " ", body)
    body = re.sub(r"(?<=\w)_+(?=\w)", " ", body)
    body = re.sub(r"(?<=\w):(?=\w)", " colon ", body)  # 'make:cast', 'auth:sanctum': the voice garbles a bare colon
    body = body.replace("%.", " percent point ").replace("%", " percent ")
    body = re.sub(r"(?<![A-Za-z])\?", " question mark ", body)  # a placeholder, not a question's own mark
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
    if tok == "..." and not (nxt == "$" or nxt.isalpha() or nxt in "[{("):
        return "and so on"  # Loading... in a JSX element's text, or an elided line
    if tok in lang.operators:
        return lang.operators[tok]
    if tok == "[]":
        return "square brackets" if after_value else "empty array"
    if tok == "(" and nxt == ")" and not after_value and lang.name == "python":
        return "empty tuple"
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
        return "nullable" if nxt.isalpha() or nxt == "\\" else "question mark"
    return LINE_OPERATORS.get(tok, tok)


def _balanced(text: str) -> bool:
    """No square bracket or brace left open, so a colon after it is not a slice's or a dict's."""
    return text.count("[") == text.count("]") and text.count("{") == text.count("}")


def is_prose_line(line: str) -> bool:
    """Four or more words, a sentence's punctuation and nothing that only code has, such as a camelCase or a
    snake_case name."""
    return bool(_PROSE_LINE.match(line) and len(line.split()) >= 4 and re.search(r"[.,;:!?](\s|$)", line.strip())
                and not re.search(r"[a-z][A-Z]|\w_\w|^\s*_|_\s*$", line))


def spoken_line(line: str, lang: str | Language = GENERIC) -> str:
    """One line of code, the way a person reads it aloud, in the language's own words if it is given."""
    lang = language(lang) if isinstance(lang, str) else lang
    python, ts = lang.name == "python", lang.name == "typescript"
    if python:
        doc = _DOCSTRING.match(line)
        if doc:
            return _spoken_comment(doc.group(1)).rstrip(".")
    if is_prose_line(line) and not (python and _PY_BLOCK.match(line)):
        return line.strip().rstrip(".")
    if "/*" in lang.comments:
        doc = _DOC_LINE.match(line)
        if doc:
            return _spoken_doc(doc.group(1), lang).rstrip(".") if doc.group(1) else ""
    words: list[str] = []
    previous = ""  # the kind of the last token that was not space, for [ and ...
    ternaries = 0  # a ? waiting for its :
    depth, arrows = 0, []  # open brackets, and the depth at each fn whose => is still to come
    generics = 0  # TypeScript's type arguments still open: Promise<User> is "Promise of User"
    lambdas: list[int] = []  # the depth at each Python lambda whose colon is still to come
    block_said = False  # the colon that opens a Python block has been read
    jsx = lang.name in ("javascript", "typescript")
    tags, skip = 0, 0  # JSX tags still open (<div ... >), and where the tokens a tag's reading took up end
    if lang is GENERIC or lang.name == "php":
        line = _CAST.sub(lambda m: f"cast to {m.group(1)} ", line)
        line = re.sub(r"^(\s*)#\[", r"\1attribute [", line)  # #[AsCommand] is an attribute, not a comment
        line = _PHP_TAGS.sub(lambda m: f" {_PHP_TAGS_SAID[m.group()]} ", line)
        line = _WHERE.sub(r"\1(\2 == \3)", line)  # where('id', 1) and where('id', '=', 1) are both where id = 1
    for m in _tokens(lang.comments).finditer(line):
        kind = m.lastgroup
        tok = m.group()
        if m.start() < skip or kind == "space" or (tok == "." and m.end() == len(line.rstrip())):
            continue  # a full stop ending the line is prose's, not code's
        if kind == "comment":
            text = re.sub(r"^(//|#|/\*|--|;)\s*|\s*\*/$", "", tok).strip()
            if text:
                if text in ("...", "…"):
                    text = "and so on"
                elif _CODE_COMMENT.fullmatch(text):
                    text = spoken_line(text, lang)  # `# other + self` is "other plus self"
                else:
                    text = _spoken_comment(text)
                if words and not words[-1].endswith((".", ",")):
                    words.append(",")  # a comma: the voice pauses for over a second at a full stop
                words.append(text + ".")
            break
        if kind == "string":
            words.append(_spoken_string(tok, lang))
        elif kind == "number":
            # 0x30 is "hex 30", 0xFF "hex F F": the voice says the letters of a hex number one by one
            words.append("hex " + " ".join(re.findall(r"\d+|[a-fA-F]", tok[2:])) if tok[:2] in ("0x", "0X") else tok)
        elif kind == "var":
            words.append(spoken_code(tok.lstrip("$"), lang))
        elif kind == "name":
            if tok == "fn" and lang.name in ("php", "code"):
                arrows.append(depth)
            if tok == "lambda" and python:
                lambdas.append(depth)
            if tok in STRING_PREFIXES and line[m.end():m.end() + 1] in ("'", '"'):
                words.append(STRING_PREFIXES[tok])  # f"..." in Python is "f string ..."
            else:
                words.append(spoken_code(tok, lang))
        elif kind == "op":
            after_value = previous in ("var", "name", "string", "number", "close")
            if tok == "=" and words and words[-1] == "square brackets":
                words[-1] = "append"  # $list[] = $item: the manual's "append"
                continue
            depth += (tok == "(") - (tok == ")")
            said = _spoken_operator(tok, line, m.end(), after_value, lang)
            if tok == "=>" and arrows and depth == arrows[-1] and lang.name in ("php", "code"):
                arrows.pop()
                said = "returns"  # the => of fn ($x) => $x * 2: the arrow function returns its expression
            rest = line[m.start():]
            if ts and tok == "<" and previous == "name" and line[m.start() - 1:m.start()].isalnum() \
                    and line[m.end():m.end() + 1] not in (" ", "=", "/"):
                said, generics = "of", generics + 1  # a type argument, not less than: Array<T> is "Array of T"
            elif ts and tok == "<" and (_TYPE_PARAMS.match(rest) or (not after_value and not rest[1:].strip())):
                said, generics = "generic", generics + 1  # const first = <T>(items: T[]) => items[0]
            elif jsx and tok == "<>":
                said = "fragment"  # <> opens a fragment
            elif jsx and tok == "!" and line[m.end():m.end() + 1] == "<":
                said = ""  # Hello!</h1>: the element's text ends with its own mark
            elif jsx and tok == "<" and re.match(r"</>", rest):
                said, skip = "end fragment", m.start() + 3
            elif jsx and tok == "<" and (re.match(r"</[A-Za-z]", rest) or (
                    re.match(r"<[A-Za-z]", rest) and not line[m.start() - 1:m.start()].isalnum())):
                tags += 1  # a JSX element: <div> is "div", </div> is "end div", <App /> is "App"
                said, skip = ("end", m.start() + 2) if rest.startswith("</") else ("", 0)
            elif jsx and tok == "/" and (not after_value or words[-1:] in (["return"], ["not"])) \
                    and _REGEX.match(rest):
                # a regular expression is said by the words in it, not symbol by symbol: /^text\/plain/ is
                # "regex text plain"
                literal = _REGEX.match(rest).group()
                said = " ".join(["regex", *re.findall(r"[A-Za-z]{2,}", literal[1:literal.rindex("/")])][:6])
                skip = m.start() + len(literal)
            elif jsx and tok == "/" and line[m.end():m.end() + 1] == ">":
                said, skip, tags = "", m.end() + 1, max(tags - 1, 0)  # /> closes an element, even on its own line
            elif jsx and tags and tok == ">":
                said, tags = "", tags - 1
            elif ts and tok in (">", ">>") and (generics or not previous or (
                    line[m.start() - 1:m.start()] not in (" ", "") and line[m.end():m.end() + 1] != " ")):
                said, generics = "", max(generics - len(tok), 0)  # or a type argument list closing on its own line
            elif ts and tok == "!" and after_value and line[m.end():m.end() + 1] in ("", " ", ".", ";", ",", ")", "]"):
                said = "non-null"  # the handbook's non-null assertion, user!.name
            elif ts and tok == "[]" and after_value:
                said = "array"  # string[] is "string array"
            elif ts and tok == ":" and not ternaries and line[:m.start()].rstrip().endswith(")") and depth == 0:
                said = "returns"  # the return type after the parameters: (id: string): User
            elif tok == ":" and python and lambdas and depth == lambdas[-1]:
                lambdas.pop()
                said = "returns"  # lambda x: x * 2 is "lambda x returns x times 2"
            elif tok == "?" and said == "question mark" and not line[m.end():].strip().startswith((":", ")")):
                said, ternaries = "then", ternaries + 1  # the ternary operator: a ? b : c
            elif tok == ":" and (ternaries or not previous):
                said, ternaries = "else", max(ternaries - 1, 0)  # or a ternary's else on a line of its own
            elif tok == ":" and python and re.match(r"\s*(#.*)?$", line[m.end():]):
                said = ""  # the colon that opens a block is not said, as a person reading it out doesn't
            elif tok == ":" and python and depth == 0 and not block_said and _PY_BLOCK.match(line) and \
                    _balanced(line[:m.start()]):
                said, block_said = ",", True  # if x: return 1, with its block on the same line, is "if x, return 1"
            elif tok in ("|", "&") and previous in (("name", "string", "number") if ts else ("name",)) \
                    and re.match(r"\s*[?\\A-Za-z'\"\d]" if ts else r"\s*[?\\A-Za-z]", line[m.end():]) \
                    and (lang is GENERIC or lang.name in ("php", "typescript")):
                said = "or" if tok == "|" else "and"  # a union type, Stringable|string, or an intersection
            words.append(said)
            if tok in (")", "]"):
                kind = "close"
        else:
            words.append(tok)
        previous = kind
    s = " ".join(w for w in words if w)
    s = re.sub(r"\s+([,.])", r"\1", s)
    s = re.sub(r"[,.](\s*[,.])+", lambda m: m.group()[-1], s)
    return s.strip(" ,.")
