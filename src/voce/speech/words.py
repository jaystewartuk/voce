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
    "pkg": "package", "cmd": "command", "lib": "lib", "repo": "repo", "auth": "auth", "impl": "implementation",
    "ttl": "T T L", "ip": "I P", "pdo": "P D O", "psr": "P S R", "sqs": "S Q S", "cc": "C C", "bcc": "B C C",
    "svg": "S V G", "css": "C S S", "js": "J S", "ioc": "I O C", "dsn": "D S N", "tz": "time zone",
    "args": "args", "func": "function", "dir": "dir", "ob": "O B", "pg": "P G", "ascii": "ascii",
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


# ---------------------------------------------------------------- each language

PHP = Language("php", comments=("//", "#", "/*"), words={
    "Str": "string", "Arr": "array", "mb": "M B", "strlen": "string length", "strpos": "string position",
    "substr": "sub string", "strtoupper": "string to upper", "strtolower": "string to lower",
    "ucfirst": "U C first", "strcmp": "string compare", "strtotime": "string to time", "strval": "string value",
    "intval": "int value", "intdiv": "int div", "usort": "U sort", "uasort": "U A sort", "uksort": "U K sort",
    "ksort": "K sort", "krsort": "K R sort", "asort": "A sort", "arsort": "A R sort", "rsort": "R sort",
    "isset": "is set", "foreach": "for each", "elseif": "else if", "fn": "arrow function", "stdClass": "standard class",
    "instanceof": "instance of", "insteadof": "instead of", "endif": "end if", "endforeach": "end for each",
    "endwhile": "end while", "endfor": "end for", "endswitch": "end switch", "enddeclare": "end declare",
    "rtrim": "R trim", "ltrim": "L trim", "lcfirst": "L C first", "ucwords": "U C words",
    "realpath": "real path", "basename": "base name", "dirname": "dir name", "pathinfo": "path info",
    "passthru": "pass through", "htmlspecialchars": "HTML special chars", "htmlentities": "HTML entities",
    "nl2br": "N L to B R", "vsprintf": "V S print F", "fprintf": "F print F", "strstr": "str str",
    "strrpos": "string R position", "stripos": "string I position", "strripos": "string R I position",
    "substr_count": "sub string count", "str_pad": "string pad", "strrev": "string reverse",
    "strncmp": "string N compare", "strcasecmp": "string case compare", "strncasecmp": "string N case compare",
    "stripslashes": "strip slashes", "addslashes": "add slashes", "mb_substr": "M B sub string",
    "mb_strtoupper": "M B string to upper", "mb_strtolower": "M B string to lower", "mb_strpos": "M B string position",
    "mb_str_split": "M B string split", "ctype_digit": "C type digit", "ctype_alpha": "C type alpha",
    "ctype_alnum": "C type alphanumeric", "ctype_upper": "C type upper", "ctype_lower": "C type lower",
    "ctype_space": "C type space", "ctype_xdigit": "C type hex digit", "ctype_punct": "C type punctuation",
    "floatval": "float value", "boolval": "bool value", "serialize": "serialize", "unserialize": "unserialize",
    "preg_match": "preg match", "preg_replace": "preg replace", "preg_split": "preg split",
    "preg_quote": "preg quote", "preg_match_all": "preg match all", "preg_replace_callback": "preg replace callback",
    "getenv": "get env", "putenv": "put env", "setlocale": "set locale", "mkdir": "make dir", "rmdir": "remove dir",
    "fopen": "F open", "fclose": "F close", "fwrite": "F write", "fread": "F read", "fgets": "F gets",
    "fputs": "F puts", "feof": "F E O F", "fseek": "F seek", "ftell": "F tell", "fflush": "F flush",
    "ftruncate": "F truncate", "fstat": "F stat", "flock": "F lock", "fputcsv": "F put C S V",
    "fgetcsv": "F get C S V", "tmpfile": "temp file", "tempnam": "temp name", "chmod": "C H mod",
    "chown": "C H own", "chgrp": "C H group", "mt_rand": "M T rand", "mt_srand": "M T S rand",
    "gettype": "get type", "settype": "set type", "gmdate": "G M date", "mktime": "make time",
    "gmmktime": "G M make time", "checkdate": "check date", "strftime": "string F time", "microtime": "micro time",
    "hrtime": "H R time", "usleep": "micro sleep", "json_encode": "JSON encode", "json_decode": "JSON decode",
    "iconv": "I conv", "utf8_encode": "U T F 8 encode", "utf8_decode": "U T F 8 decode", "bin2hex": "bin to hex",
    "hex2bin": "hex to bin", "dechex": "dec to hex", "hexdec": "hex to dec", "decbin": "dec to bin",
    "bindec": "bin to dec", "decoct": "dec to oct", "octdec": "oct to dec", "fmod": "F mod",
    "sqrt": "square root", "rand": "rand", "srand": "S rand", "crc32": "C R C 32", "md5": "M D 5",
    "sha1": "S H A 1", "uniqid": "unique I D", "urlencode": "URL encode", "urldecode": "URL decode",
    "rawurlencode": "raw URL encode", "rawurldecode": "raw URL decode", "http_build_query": "HTTP build query",
    "parse_str": "parse string", "parse_url": "parse URL", "getcwd": "get C W D", "chdir": "C H dir",
    "scandir": "scan dir", "opendir": "open dir", "readdir": "read dir", "closedir": "close dir",
    "is_dir": "is dir", "is_writable": "is writable", "is_readable": "is readable", "is_executable": "is executable",
    "filemtime": "file M time", "filectime": "file C time", "fileatime": "file A time", "filesize": "file size",
    "fileperms": "file perms", "filetype": "file type", "readfile": "read file", "readlink": "read link",
    "symlink": "sym link", "unlink": "unlink", "touch": "touch", "ini_get": "I N I get", "ini_set": "I N I set",
    "ob_start": "O B start", "ob_get_clean": "O B get clean", "ob_get_contents": "O B get contents",
    "ob_end_clean": "O B end clean", "ob_get_level": "O B get level", "spl_object_id": "S P L object I D",
    "spl_object_hash": "S P L object hash", "spl_autoload_register": "S P L autoload register",
    "func_get_args": "function get args", "func_num_args": "function number of args",
    "func_get_arg": "function get arg",
    "phpstan": "P H P stan", "phpunit": "P H P unit", "phpdoc": "P H P doc", "psalm": "psalm",
    "memcached": "memcached", "stdin": "standard in", "stdout": "standard out", "stderr": "standard error",
    "wordwrap": "word wrap", "nl_langinfo": "N L lang info", "gc_collect_cycles": "G C collect cycles",
    "php_sapi_name": "P H P sapi name", "php_uname": "P H P U name", "phpversion": "P H P version",
    "pcntl_signal": "P C N T L signal", "posix_kill": "posix kill", "posix_getpid": "posix get P I D",
    "getmypid": "get my P I D", "proc_open": "proc open", "proc_close": "proc close",
    "escapeshellarg": "escape shell arg",
    "escapeshellcmd": "escape shell command", "array_key_first": "array key first", "array_key_last": "array key last",
    "bg": "background", "fg": "foreground", "px": "pixels", "strtr": "string T R", "clearstatcache": "clear stat cache",
    "avg": "average", "apc": "A P C", "apcu": "A P C U", "jwt": "J W T", "gc": "G C", "ul": "U L", "li": "L I",
    "dd": "D D", "endphp": "end P H P", "endforelse": "end for else", "endisset": "end is set", "forelse": "for else",
    "readonly": "read only", "jsonb": "JSON B", "hostname": "host name", "newline": "new line",
    "charlist": "char list", "ulid": "U L I D", "writeln": "write line", "datetime": "date time",
    "studly": "studly", "undot": "un dot", "wheres": "wheres", "havings": "havings",
    # Laravel's -able traits: the voice says "a rayable" for Arrayable
    "Arrayable": "array able", "Jsonable": "JSON able", "Htmlable": "HTML able", "Macroable": "macro able",
    "Queueable": "queue able", "Dumpable": "dump able", "Pausable": "pause able", "Onceable": "once able",
    "Renderable": "render able", "Castable": "cast able", "Attachable": "attach able", "Lockable": "lock able",
    "Broadcastable": "broadcast able", "Dispatchable": "dispatch able", "Prunable": "prune able",
    "Batchable": "batch able", "Notifiable": "notify able", "Routable": "route able", "Tappable": "tap able",
    "Hashable": "hash able", "Encryptable": "encrypt able", "Validatable": "validate able",
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
