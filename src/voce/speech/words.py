"""The words a developer uses for code: operators by name, abbreviations in full, letters where letters are said.

These tables are data. Adding a language's abbreviation is a one-line change here, and nothing else needs to know.
The names are the PHP manual's own where PHP has one, so a listener learns to say "identical" and "spaceship".
"""

from __future__ import annotations

# A bit of inline code that is only an operator, said on its own: `===` is "identical".
CODE_OPERATORS = {
    "===": "identical", "!==": "not identical", "==": "equal", "!=": "not equal",
    ">=": "greater than or equal to", "<=": "less than or equal to", "<=>": "spaceship",
    "??=": "null coalescing assignment", "??": "null coalescing", "?:": "short ternary", "?->": "nullsafe arrow",
    "->": "arrow", "=>": "double arrow",
    "::": "double colon", "...": "ellipsis", "&": "ampersand", "&&": "and", "||": "or", "!": "not",
    "[]": "empty square brackets", "()": "empty brackets", "{}": "empty braces", "=": "equals", "+": "plus",
    "-": "minus", "*": "times", "/": "divided by", "%": "modulo", ".": "dot", ".=": "dot equals",
    "+=": "plus equals", "++": "increment", "--": "decrement", "$": "dollar", "_": "underscore",
    "#": "hash", "@": "at", "|": "pipe", "<": "less than", ">": "greater than", "?": "question mark",
    ":": "colon", ";": "semicolon", "\\": "backslash",
}

# Names said in full or by their letters. Anything not here is said as its words: checkIn is "check In".
CODE_WORDS = {
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

# File extensions, as said after "dot": cli.py is "C L I dot P Y". Anything not here is said as a word.
FILE_EXTENSIONS = {
    "py": "P Y", "md": "M D", "js": "J S", "ts": "T S", "tsx": "T S X", "jsx": "J S X", "mjs": "M J S",
    "cjs": "C J S", "php": "P H P", "rb": "R B", "rs": "R S", "sh": "S H", "css": "C S S", "scss": "S C S S",
    "html": "HTML", "htm": "HTML", "sql": "S Q L", "yml": "yaml", "json": "JSON", "jsonl": "JSON L", "txt": "text",
    "cfg": "config", "ini": "I N I", "c": "C", "h": "H", "cpp": "C plus plus", "hpp": "H plus plus",
    "cs": "C sharp", "kt": "K T", "xml": "X M L", "svg": "S V G", "png": "P N G", "jpg": "J P G",
    "jpeg": "J P G", "csv": "C S V", "pdf": "P D F", "mp3": "M P 3", "env": "env", "tape": "tape",
}

# An operator in a line of code, by the PHP manual's name. Brackets are silent, a semicolon is a pause.
LINE_OPERATORS = {
    "<=>": "spaceship", "===": "is identical to", "!==": "is not identical to", "??=": "null coalescing assignment",
    "**=": "exponentiation equals", "<<<": "heredoc", "?->": "nullsafe arrow", "->": "arrow", "=>": "double arrow",
    "::": "double colon", "==": "is equal to", "!=": "is not equal to", ">=": "is greater than or equal to",
    "<=": "is less than or equal to",
    "??": "null coalescing", "?:": "short ternary", "&&": "and", "||": "or", "++": "increment",
    "--": "decrement", "+=": "plus equals", "-=": "minus equals", "*=": "times equals",
    "/=": "divided equals", ".=": "dot equals", "**": "to the power of", "=": "equals", "+": "plus", "-": "minus",
    "*": "times", "/": "divided by", "%": "modulo", ".": "dot", "<": "less than", ">": "greater than",
    "!": "not", ":": "colon", "|": "pipe", "@": "at", "&": "ampersand", "^": "caret", "~": "tilde", "\\": "",
    "(": "", ")": "", "{": "", "}": "", "]": "", ";": ",", ",": ",",
}

# Strings with no letters in them, by what they hold: '' is "the empty string".
STRING_WORDS = {"": "the empty string", ",": "a comma", " ": "a space", "\\n": "a new line", ".": "a dot",
                "-": "a dash", "/": "a slash", ", ": "a comma and a space", "&": "an ampersand", "|": "a pipe",
                ":": "a colon", ";": "a semicolon", "=": "an equals sign", "?": "a question mark"}

# Python's string prefixes: f"..." is "f string ...".
STRING_PREFIXES = {"f": "f string", "b": "byte string", "r": "raw string", "rb": "raw byte string",
                   "fr": "raw f string", "rf": "raw f string"}

# PHP's casts: (int) is "cast to int".
CAST_TYPES = ("int", "integer", "float", "double", "string", "bool", "boolean", "array", "object")
