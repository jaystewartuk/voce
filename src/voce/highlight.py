"""Syntax highlighting for fenced code, as role spans the terminal theme knows how to colour.

Pygments does the tokenising. Each token type is reduced to one of a dozen roles (keyword, string, comment and so
on), so the theme stays small and works the same for every language. Without Pygments, code is shown plain.

A diff is highlighted as a reviewer reads it: added lines in the syntax colours of the file's language, with a
green marker, removed lines in red, and the unchanged lines around them dimmed. The fence says the language of
the file after the word diff: ```diff python.
"""

from __future__ import annotations

import bisect
from functools import cache

try:
    from pygments.lexers import get_lexer_by_name, get_lexer_for_filename, guess_lexer
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
DIFF_LABELS = ("diff", "patch", "udiff")
_FILE_HEADERS = ("diff ", "index ", "--- ", "+++ ", "new file", "deleted file", "similarity", "rename ", "old mode",
                 "new mode", "Binary")


def available() -> bool:
    return Token is not None


def is_diff(lang: str) -> bool:
    """Whether a fence label names a diff: "diff", or "diff python" for a diff of Python."""
    return lang.split()[:1] in ([label] for label in DIFF_LABELS)


def language_for(filename: str) -> str:
    """The fence label for a file, from its name: "python" for cli.py, "" when Pygments doesn't know it."""
    if not available():
        return ""
    try:
        lexer = get_lexer_for_filename(filename)
    except ClassNotFound:
        return ""
    return lexer.aliases[0] if lexer.aliases else ""


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


def _spans(code: str, lexer) -> list[Span]:
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


def code_spans(code: str, lang: str = "") -> list[Span]:
    """(start, end, roles) for each highlighted run of code, in character offsets into code."""
    if not available() or not code:
        return []
    if is_diff(lang):
        words = lang.split()
        return diff_spans(code, words[1] if len(words) > 1 else "")
    lexer = _lexer(code, lang)
    return _spans(code, lexer) if lexer is not None else []


# ---------------------------------------------------------------- diffs

def diff_lines(code: str) -> list[tuple[int, str, str]]:
    """Each line of a unified diff as (offset, kind, text): kind is "+", "-", " " (context), "@" (a hunk header)
    or "#" (a file header such as --- a/x or diff --git, before the first hunk, and "\\ No newline" notes)."""
    out, offset, in_hunk = [], 0, False
    for line in code.split("\n"):
        if line.startswith("@@"):
            kind, in_hunk = "@", True
        elif line.startswith("\\") or (not in_hunk and line.startswith(_FILE_HEADERS)):
            kind = "#"  # "\ No newline at end of file", or the header lines before the first hunk
        elif line[:1] in ("+", "-"):
            kind = line[0]
        else:
            kind = " "
        out.append((offset, kind, line))
        offset += len(line) + 1
    return out


def diff_spans(code: str, lang: str = "") -> list[Span]:
    """Spans for a diff: markers and removed lines by role, context dimmed, added lines in the language's syntax.

    The added and context lines of each hunk are lexed together as the file reads after the change, so a string
    or comment that runs over several lines keeps its colour; only the spans on added lines are kept.
    """
    lexer = _lexer("", lang) if lang else None
    spans: list[Span] = []
    hunk: list[tuple[int, str, str]] = []

    def flush() -> None:
        if lexer is None or not hunk:
            hunk.clear()
            return
        bodies = [text[1:] for _, _, text in hunk]
        starts = [0]
        for body in bodies[:-1]:
            starts.append(starts[-1] + len(body) + 1)
        joined = "\n".join(bodies)
        for a, z, roles in _spans(joined, lexer):
            k = bisect.bisect_right(starts, a) - 1
            while a < z and k < len(hunk):
                line_end = starts[k] + len(bodies[k])
                piece_end = min(z, line_end)
                if piece_end > a and hunk[k][1] == "+" and joined[a:piece_end].strip():
                    at = hunk[k][0] + 1 + (a - starts[k])
                    spans.append((at, at + (piece_end - a), roles))
                a, k = line_end + 1, k + 1
        hunk.clear()

    for offset, kind, text in diff_lines(code):
        if not text:
            continue
        if kind == "@":
            flush()
            spans.append((offset, offset + len(text), frozenset(("prompt",))))
        elif kind == "#":
            spans.append((offset, offset + len(text), frozenset(("prompt",))))
        elif kind == "+":
            spans.append((offset, offset + 1, frozenset(("inserted",))))
            hunk.append((offset, kind, text))
        elif kind == "-":
            spans.append((offset, offset + len(text), frozenset(("deleted",))))
        else:
            spans.append((offset, offset + len(text), frozenset(("context",))))
            hunk.append((offset, kind, text))
    flush()
    return sorted(spans)
