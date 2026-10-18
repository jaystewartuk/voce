"""The words a developer uses for code, as data: what is common to every language, then each language's own.

Adding a language is a new Language here and a line in LANGUAGES. Nothing else needs to know. The names are
each manual's own where it has one (the PHP manual's "identical", MDN's "strict equality"), so a listener learns
to say them.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Language:
    name: str
    words: dict = field(default_factory=dict)       # names said in full or by letter, on top of COMMON_WORDS
    operators: dict = field(default_factory=dict)   # operators by this language's names, on top of LINE_OPERATORS
    comments: tuple = ()                            # how a comment starts
    dunder: bool = False                            # __init__ is "dunder init"
    prose: bool = False                             # a prose format: a line is read as text, not as code


# ---------------------------------------------------------------- common to every language

# Names said in full or by their letters. Anything not here is said as its words: checkIn is "check In".
COMMON_WORDS = {
    "str": "string", "json": "JSON", "html": "HTML", "url": "URL", "id": "I D", "db": "D B", "sql": "S Q L",
    "php": "P H P", "cli": "C L I", "api": "A P I", "uuid": "U U I D", "len": "length", "pos": "position",
    "num": "number", "src": "source", "tmp": "temp", "cfg": "config", "ctx": "context", "req": "request",
    "res": "response", "err": "error", "msg": "message", "idx": "index", "val": "value", "obj": "object",
    "cb": "callback", "fmt": "format", "prev": "previous", "sprintf": "S print F", "printf": "print F",
    "env": "env", "md": "M D", "ci": "C I", "ui": "U I", "io": "I O", "os": "O S", "pr": "P R",
}

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

# An operator in a line of code, by the PHP manual's name. Brackets are silent, a semicolon is a pause.
LINE_OPERATORS = {
    "<=>": "spaceship", "===": "is identical to", "!==": "is not identical to", "??=": "null coalescing assignment",
    "**=": "exponentiation equals", "<<<": "heredoc", "?->": "nullsafe arrow", "->": "arrow", "=>": "double arrow",
    "::": "double colon", "==": "is equal to", "!=": "is not equal to", ">=": "is greater than or equal to",
    "<=": "is less than or equal to", "?.": "optional chaining", ":=": "walrus", "//": "floor divided by",
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

# File extensions, as said after "dot": cli.py is "C L I dot P Y". Anything not here is said as a word.
FILE_EXTENSIONS = {
    "py": "P Y", "md": "M D", "js": "J S", "ts": "T S", "tsx": "T S X", "jsx": "J S X", "mjs": "M J S",
    "cjs": "C J S", "php": "P H P", "rb": "R B", "rs": "R S", "sh": "S H", "css": "C S S", "scss": "S C S S",
    "html": "HTML", "htm": "HTML", "sql": "S Q L", "yml": "yaml", "json": "JSON", "jsonl": "JSON L", "txt": "text",
    "cfg": "config", "ini": "I N I", "c": "C", "h": "H", "cpp": "C plus plus", "hpp": "H plus plus",
    "cs": "C sharp", "kt": "K T", "xml": "X M L", "svg": "S V G", "png": "P N G", "jpg": "J P G",
    "jpeg": "J P G", "csv": "C S V", "pdf": "P D F", "mp3": "M P 3", "env": "env", "tape": "tape",
}


# ---------------------------------------------------------------- each language

PHP = Language("php", comments=("//", "#", "/*"), words={
    "Str": "string", "Arr": "array", "mb": "M B", "strlen": "string length", "strpos": "string position",
    "substr": "sub string", "strtoupper": "string to upper", "strtolower": "string to lower",
    "ucfirst": "U C first", "strcmp": "string compare", "strtotime": "string to time", "strval": "string value",
    "intval": "int value", "intdiv": "int div", "usort": "U sort", "uasort": "U A sort", "uksort": "U K sort",
    "ksort": "K sort", "krsort": "K R sort", "asort": "A sort", "arsort": "A R sort", "rsort": "R sort",
    "isset": "is set", "foreach": "for each", "elseif": "else if", "fn": "F N", "stdClass": "standard class",
})

PYTHON = Language("python", comments=("#",), dunder=True, words={
    "elif": "else if", "kwargs": "keyword args", "cls": "class", "isinstance": "is instance",
    "re": "R E", "np": "numpy", "pd": "pandas", "dt": "date time", "func": "function",
    "iter": "iterator", "attr": "attribute", "getattr": "get attribute", "setattr": "set attribute",
}, operators={
    "->": "returns", "**": "to the power of", "//": "floor divided by", ":=": "walrus", "@": "at",
})

JAVASCRIPT = Language("javascript", comments=("//", "/*"), words={
    "el": "element", "evt": "event", "btn": "button", "arr": "array", "fn": "function", "init": "init",
    "DOM": "DOM", "params": "params", "args": "args", "props": "props", "ref": "ref", "ctx": "context",
}, operators={
    "===": "is strictly equal to", "!==": "is not strictly equal to", "=>": "arrow", "?.": "optional chaining",
    "??": "nullish coalescing", "??=": "nullish assignment", "...": "spread", "**": "to the power of",
})

SHELL = Language("shell", comments=("#",), words={
    "cd": "C D", "ls": "L S", "rm": "R M", "mv": "move", "cp": "copy", "mkdir": "make dir", "chmod": "C H mod",
    "sudo": "sudo", "grep": "grep", "sed": "sed", "awk": "awk", "ssh": "S S H", "pwd": "P W D",
}, operators={"|": "pipe", "&&": "and then", "||": "or else", ">": "to", ">>": "appended to", "<": "from"})

SQL = Language("sql", comments=("--", "/*"), words={"id": "I D", "db": "D B", "desc": "descending",
                                                     "asc": "ascending"},
               operators={"<>": "is not equal to", "=": "equals", "!=": "is not equal to"})

PROSE = Language("text", prose=True)

GENERIC = Language("code", comments=("//", "#", "/*"), words=PHP.words)  # the rules were written for PHP first

LANGUAGES: dict[str, Language] = {
    "php": PHP, "blade": PHP,
    "python": PYTHON, "py": PYTHON, "python3": PYTHON,
    "javascript": JAVASCRIPT, "js": JAVASCRIPT, "typescript": JAVASCRIPT, "ts": JAVASCRIPT, "jsx": JAVASCRIPT,
    "tsx": JAVASCRIPT, "mjs": JAVASCRIPT, "cjs": JAVASCRIPT, "vue": JAVASCRIPT, "svelte": JAVASCRIPT,
    "bash": SHELL, "sh": SHELL, "shell": SHELL, "zsh": SHELL, "console": SHELL, "terminal": SHELL,
    "sql": SQL, "mysql": SQL, "postgresql": SQL, "postgres": SQL, "sqlite": SQL, "plpgsql": SQL,
    "markdown": PROSE, "md": PROSE, "text": PROSE, "txt": PROSE, "plain": PROSE, "rst": PROSE,
    "restructuredtext": PROSE, "asciidoc": PROSE, "adoc": PROSE,
}


def language(alias: str) -> Language:
    """The language for a fence label or Pygments alias, or the generic rules for one that isn't known."""
    return LANGUAGES.get(alias.strip().lower().split()[-1] if alias.strip() else "", GENERIC)
