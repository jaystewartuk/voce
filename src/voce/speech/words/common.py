"""What is common to every language: the Language each one is, and the words, operators and strings they share.

A language's own file adds its words and operator names on top of these.
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
    aliases: tuple = ()                             # fence labels and Pygments aliases that mean this language
    manual: str = ""                                # where its operator names come from


# Names said in full or by their letters. Anything not here is said as its words: checkIn is "check In".
COMMON_WORDS = {
    "str": "string", "json": "JSON", "html": "HTML", "url": "URL", "id": "I D", "db": "D B", "sql": "S Q L",
    "php": "P H P", "cli": "C L I", "api": "A P I", "uuid": "U U I D", "len": "length", "pos": "position",
    "num": "number", "src": "source", "tmp": "temp", "cfg": "config", "ctx": "context", "req": "request",
    "res": "response", "err": "error", "msg": "message", "idx": "index", "val": "value", "obj": "object",
    "cb": "callback", "fmt": "format", "prev": "previous", "sprintf": "S print F", "printf": "print F",
    "env": "env", "md": "M D", "ci": "C I", "ui": "U I", "io": "I O", "os": "O S", "pr": "P R",
    "pkg": "package", "cmd": "command", "lib": "lib", "repo": "repo", "auth": "auth", "impl": "implementation",
    "ttl": "T T L", "ip": "I P", "pdo": "P D O", "psr": "P S R", "sqs": "S Q S", "cc": "C C", "bcc": "B C C",
    "svg": "S V G", "css": "C S S", "js": "J S", "ioc": "I O C", "dsn": "D S N", "tz": "time zone",
    "args": "args", "func": "function", "dir": "dir", "ob": "O B", "pg": "P G", "ascii": "ascii", "nn": "N N",
    "jwt": "J W T", "jsx": "J S X", "tsx": "T S X", "tok": "token", "alg": "algorithm",
    "IPv4": "I P v4", "IPv6": "I P v6", "href": "H ref", "etag": "E tag",
}

# A bit of inline code that is only an operator, said on its own: `===` is "identical".
CODE_OPERATORS = {
    "===": "identical", "!==": "not identical", "==": "equal", "!=": "not equal",
    ">=": "greater than or equal to", "<=": "less than or equal to", "<=>": "spaceship",
    "??=": "null coalescing assignment", "??": "null coalescing", "?:": "short ternary", "?->": "nullsafe arrow",
    "->": "arrow", "=>": "double arrow",
    "::": "double colon", "...": "ellipsis", "&": "ampersand", "&&": "and", "||": "or", "!": "not",
    "[]": "empty square brackets", "()": "empty brackets", "{}": "empty braces", "[": "open square bracket",
    "]": "close square bracket", "(": "open bracket", ")": "close bracket", "{": "open brace", "}": "close brace",
    "=": "equals", "+": "plus",
    "-": "minus", "*": "times", "/": "divided by", "%": "modulo", ".": "dot", ".=": "dot equals",
    "+=": "plus equals", "++": "increment", "**": "double star", "--": "decrement", "$": "dollar", "_": "underscore",
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
    "(": "", ")": "", "{": "", "}": "", "{}": "", "]": "", ";": ",", ",": ",",
}

# Strings with no letters in them, by what they hold: '' is "the empty string".
STRING_WORDS = {"": "the empty string", ",": "a comma", " ": "a space", "\\n": "a new line", ".": "a dot",
                "-": "a dash", "/": "a slash", ", ": "a comma and a space", "&": "an ampersand", "|": "a pipe",
                ":": "a colon", ";": "a semicolon", "=": "an equals sign", "?": "a question mark",
                "*": "an asterisk", "\\\\": "a backslash", "\\": "a backslash", "@": "an at sign",
                "_": "an underscore", "#": "a hash", "%": "a percent sign", "+": "a plus sign", "'": "a single quote",
                '"': "a double quote", "(": "an open bracket", ")": "a close bracket", "[": "an open square bracket",
                "]": "a close square bracket", "{": "an open brace", "}": "a close brace", "\\t": "a tab",
                "\\r\\n": "a carriage return and a new line", "<": "less than", ">": "greater than",
                "<=": "less than or equal to", ">=": "greater than or equal to", "<>": "not equal",
                "!=": "not equal", "==": "equal"}

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
