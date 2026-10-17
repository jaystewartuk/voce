"""Syntax highlighting for fenced code, as role spans the terminal theme knows how to colour.

Pygments does the tokenising. Each token type is reduced to one of a dozen roles (keyword, string, comment and so
on), so the theme stays small and works the same for every language. Without Pygments, code is shown plain.
"""

from __future__ import annotations

from functools import cache

try:
    from pygments.lexers import get_lexer_by_name, guess_lexer
    from pygments.token import Token
    from pygments.util import ClassNotFound
except ImportError:  # pragma: no cover - exercised only when Pygments is missing
    Token = None

Span = tuple[int, int, frozenset]

# Most specific first: the first token type that contains the token's type wins.
_ROLES = (
    ("Comment", "comment"),
    ("Literal.String", "string"),
    ("Literal.Number", "number"),
    ("Keyword.Type", "type"),
    ("Keyword", "keyword"),
    ("Name.Function", "function"),
    ("Name.Class", "type"),
    ("Name.Builtin", "builtin"),
    ("Name.Decorator", "decorator"),
    ("Name.Tag", "keyword"),
    ("Name.Attribute", "function"),
    ("Name.Variable", "variable"),
    ("Name.Constant", "number"),
    ("Operator.Word", "keyword"),
    ("Generic.Inserted", "inserted"),
    ("Generic.Deleted", "deleted"),
    ("Generic.Heading", "heading"),
    ("Generic.Subheading", "heading"),
    ("Generic.Prompt", "prompt"),
)

# Common fence labels that Pygments doesn't know by that name.
_ALIASES = {"sh": "bash", "shell": "bash", "zsh": "bash", "console": "console", "terminal": "console",
            "py": "python", "js": "javascript", "ts": "typescript", "yml": "yaml", "md": "markdown",
            "jsonc": "json", "dockerfile": "docker", "env": "bash", "text": "text", "plain": "text"}


def available() -> bool:
    return Token is not None


@cache
def _role(token_type) -> str:
    for name, role in _ROLES:
        parent = Token
        for part in name.split("."):
            parent = getattr(parent, part)
        if token_type in parent:
            return role
    return ""


def _lexer(code: str, lang: str):
    lang = _ALIASES.get(lang.lower(), lang.lower())
    options = {"stripnl": False, "ensurenl": False}
    if lang == "php" and not code.lstrip().startswith("<?"):
        options["startinline"] = True  # a snippet without an opening tag is otherwise shown as plain text
    try:
        if lang:
            return get_lexer_by_name(lang, **options)
        if len(code.strip().splitlines()) < 2:
            return None  # guessing from a single line is mostly wrong
        return guess_lexer(code, stripnl=False, ensurenl=False)
    except ClassNotFound:
        return None


def code_spans(code: str, lang: str = "") -> list[Span]:
    """(start, end, roles) for each highlighted run of code, in character offsets into code."""
    if not available() or not code:
        return []
    lexer = _lexer(code, lang)
    if lexer is None:
        return []
    spans: list[Span] = []
    for start, token_type, value in lexer.get_tokens_unprocessed(code):
        role = _role(token_type)
        if not role or not value.strip():
            continue
        end = start + len(value)
        if spans and spans[-1][1] == start and spans[-1][2] == frozenset((role,)):
            spans[-1] = (spans[-1][0], end, spans[-1][2])
        else:
            spans.append((start, end, frozenset((role,))))
    return spans
