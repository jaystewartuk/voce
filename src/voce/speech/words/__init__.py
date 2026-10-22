"""The words a developer uses for code, as data: what is common to every language, then each language's own.

Each language is a file here, named for it, with a manual it takes its operator names from (the PHP manual's
"identical", MDN's "strict equality"), so a listener learns to say them. Adding a language is a new file and a
line in ALL. Nothing else needs to know.
"""

from __future__ import annotations

from voce.speech.words.common import (
    CAST_TYPES,
    CODE_OPERATORS,
    COMMON_WORDS,
    FILE_EXTENSIONS,
    LINE_OPERATORS,
    STRING_PREFIXES,
    STRING_WORDS,
    Language,
)
from voce.speech.words.csharp import CSHARP
from voce.speech.words.go import GO
from voce.speech.words.java import JAVA
from voce.speech.words.javascript import JAVASCRIPT
from voce.speech.words.kotlin import KOTLIN
from voce.speech.words.php import PHP
from voce.speech.words.python import PYTHON
from voce.speech.words.ruby import RUBY
from voce.speech.words.rust import RUST
from voce.speech.words.shell import SHELL
from voce.speech.words.sql import SQL
from voce.speech.words.swift import SWIFT
from voce.speech.words.typescript import TYPESCRIPT

PROSE = Language("text", prose=True, aliases=("markdown", "md", "text", "txt", "plain", "rst", "restructuredtext",
                                               "asciidoc", "adoc"))

GENERIC = Language("code", comments=("//", "#", "/*"), words=PHP.words)  # the rules were written for PHP first

ALL = (PHP, PYTHON, JAVASCRIPT, TYPESCRIPT, SHELL, SQL, GO, RUST, RUBY, JAVA, CSHARP, SWIFT, KOTLIN, PROSE)

LANGUAGES: dict[str, Language] = {alias: lang for lang in ALL for alias in lang.aliases}


def language(alias: str) -> Language:
    """The language for a fence label or Pygments alias, or the generic rules for one that isn't known."""
    return LANGUAGES.get(alias.strip().lower().split()[-1] if alias.strip() else "", GENERIC)


__all__ = ["ALL", "CAST_TYPES", "CODE_OPERATORS", "COMMON_WORDS", "CSHARP", "FILE_EXTENSIONS", "GENERIC", "GO",
           "JAVA", "JAVASCRIPT", "KOTLIN", "LANGUAGES", "LINE_OPERATORS", "PHP", "PROSE", "PYTHON", "RUBY", "RUST",
           "SHELL", "SQL", "STRING_PREFIXES", "STRING_WORDS", "SWIFT", "TYPESCRIPT", "Language", "language"]
