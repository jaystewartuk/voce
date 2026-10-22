"""Python's own words, by the Python reference's names: ``->`` is "returns" (its "return annotation"), ``//`` is
"floor divided by", ``:=`` is "assignment expression", ``__init__`` is "dunder init"."""

from __future__ import annotations

from voce.speech.words.common import Language

PYTHON = Language("python", comments=("#",), dunder=True, words={
    "elif": "else if", "kwargs": "keyword args", "cls": "class", "isinstance": "is instance",
    "re": "R E", "np": "numpy", "pd": "pandas", "dt": "date time", "func": "function",
    "iter": "iterator", "attr": "attribute", "getattr": "get attribute", "setattr": "set attribute",
    # keywords and built-in functions run together: https://docs.python.org/3/library/functions.html
    "del": "delete", "nonlocal": "non local", "hasattr": "has attribute", "delattr": "delete attribute",
    "issubclass": "is subclass", "repr": "repper", "chr": "char", "divmod": "div mod", "bytearray": "byte array",
    "frozenset": "frozen set", "memoryview": "memory view", "classmethod": "class method",
    "staticmethod": "static method", "breakpoint": "break point", "aiter": "A iter", "anext": "A next",
    "kwds": "keywords", "kw": "keyword", "argv": "arg V", "stdin": "standard in", "stdout": "standard out",
    "stderr": "standard error",
    # special method names: __getitem__ is "dunder get item", __lt__ is "dunder less than"
    "getitem": "get item", "setitem": "set item", "delitem": "delete item", "getattribute": "get attribute",
    "eq": "equal", "ne": "not equal", "lt": "less than", "le": "less than or equal", "gt": "greater than",
    "ge": "greater than or equal", "aenter": "A enter", "aexit": "A exit", "qualname": "qual name",
    "subclasshook": "subclass hook", "instancecheck": "instance check", "subclasscheck": "subclass check",
    "getstate": "get state", "setstate": "set state", "mro": "M R O", "builtins": "built ins",
    # str, dict and set methods
    "startswith": "starts with", "endswith": "ends with", "lstrip": "L strip", "rstrip": "R strip",
    "rsplit": "R split", "splitlines": "split lines", "rfind": "R find", "rindex": "R index",
    "rpartition": "R partition", "ljust": "L just", "rjust": "R just", "zfill": "Z fill",
    "isdigit": "is digit", "isalpha": "is alpha", "isalnum": "is alnum", "isspace": "is space",
    "isupper": "is upper", "islower": "is lower", "isidentifier": "is identifier", "isdecimal": "is decimal",
    "isnumeric": "is numeric", "casefold": "case fold", "removeprefix": "remove prefix",
    "removesuffix": "remove suffix", "setdefault": "set default", "fromkeys": "from keys", "popitem": "pop item",
    "issubset": "is subset", "issuperset": "is superset", "isdisjoint": "is disjoint",
    # the standard library's modules and names
    "functools": "func tools", "itertools": "iter tools", "importlib": "import lib", "pathlib": "path lib",
    "contextlib": "context lib", "urllib": "URL lib", "ctypes": "C types", "argparse": "arg parse",
    "asyncio": "async I O", "subprocess": "sub process", "dataclass": "data class", "dataclasses": "data classes",
    "unittest": "unit test", "defaultdict": "default dict", "namedtuple": "named tuple", "deepcopy": "deep copy",
    "datetime": "date time", "timedelta": "time delta", "tzinfo": "time zone info", "tzname": "time zone name",
    "isoformat": "I S O format", "fromisoformat": "from I S O format", "strftime": "string format time",
    "strptime": "string parse time", "utcnow": "U T C now", "contextmanager": "context manager",
    "lru": "L R U", "makedirs": "make dirs", "mkdir": "make dir", "rmtree": "R M tree", "listdir": "list dir",
    "isfile": "is file", "isdir": "is dir", "abspath": "abs path", "basename": "base name", "dirname": "dir name",
    "splitext": "split ext", "expanduser": "expand user", "getenv": "get env", "getcwd": "get C W D",
    "urlparse": "URL parse", "urlsplit": "URL split", "urljoin": "URL join", "urlencode": "URL encode",
    "findall": "find all", "finditer": "find iter", "fullmatch": "full match", "hexdigest": "hex digest",
    "fetchone": "fetch one", "fetchall": "fetch all", "fetchmany": "fetch many", "lineno": "line number",
    "iscoroutinefunction": "is coroutine function", "getLogger": "get logger", "monkeypatch": "monkey patch",
    # short names in Python code bases
    "lhs": "L H S", "rhs": "R H S", "pk": "P K", "fk": "F K", "opts": "options", "attrs": "attributes",
    "conn": "connection", "exc": "exception", "expr": "expression", "exprs": "expressions", "ptr": "pointer",
    "addr": "address", "coords": "coordinates", "queryset": "query set", "charset": "char set",
    "autocommit": "auto commit", "gettext": "get text", "ngettext": "N get text", "noqa": "no Q A",
    "qs": "query set", "resp": "response", "rv": "return value", "objs": "objects", "vals": "values",
    "col": "column", "cols": "columns", "perm": "permission", "perms": "permissions", "fp": "F P", "fd": "F D",
    "rtype": "R type", "netloc": "net loc", "uri": "U R I", "idna": "I D N A", "timezone": "time zone",
    "hostname": "host name", "maxsize": "max size", "fileobj": "file object", "tmpdir": "temp dir",
    "excinfo": "exception info", "skipif": "skip if", "autouse": "auto use", "setenv": "set env",
    "urllib3": "URL lib 3", "urlunparse": "URL unparse", "hashlib": "hash lib", "tempfile": "temp file",
    "zipfile": "zip file", "cookiejar": "cookie jar", "cookielib": "cookie lib", "basestring": "base string",
    "iteritems": "iter items", "iterkeys": "iter keys", "itervalues": "iter values", "sendall": "send all",
    "simplefilter": "simple filter", "formset": "form set", "formfield": "form field", "urlconf": "URL conf",
    "argtypes": "arg types", "nodelist": "node list", "autoescape": "auto escape", "changelist": "change list",
    "fieldsets": "field sets", "savepoint": "save point", "codename": "code name", "sqlparse": "S Q L parse",
    "ReLU": "relu", "truediv": "true div", "rtruediv": "R true div", "radd": "R add", "rsub": "R sub",
    "rmul": "R mul",
}, operators={
    # https://docs.python.org/3/reference/expressions.html: "->" is a return annotation, "@" is "the @ (at)
    # operator", ":=" an assignment expression (6.12), "//" floor division, "~" invert, "..." the Ellipsis.
    "->": "returns", "**": "to the power of", "//": "floor divided by", ":=": "assignment expression", "@": "at",
    "~": "invert", "...": "ellipsis", "[]": "empty list", "{}": "empty dict",
    # bitwise and, or and exclusive or, also set intersection and union, and | in a type: str | None.
    # https://docs.python.org/3/library/operator.html names them "Bitwise And, or Intersection" and so on.
    "&": "and", "|": "or", "^": "exclusive or", "<<": "left shift", ">>": "right shift",
    # augmented assignment, https://docs.python.org/3/reference/simple_stmts.html#augmented-assignment-statements
    "//=": "floor divided equals", "%=": "modulo equals", "@=": "at equals", "&=": "and equals",
    "|=": "or equals", "^=": "exclusive or equals", "<<=": "left shift equals", ">>=": "right shift equals",
}, aliases=("python", "py", "python3"),
    manual="https://docs.python.org/3/reference/expressions.html")
