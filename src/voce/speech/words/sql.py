"""SQL's own words: ``<>`` is "is not equal to", ``desc`` is "descending"."""

from __future__ import annotations

from voce.speech.words.common import Language

SQL = Language("sql", comments=("--", "/*"), words={"id": "I D", "db": "D B", "desc": "descending",
                                                     "asc": "ascending"},
               operators={"<>": "is not equal to", "=": "equals", "!=": "is not equal to"},
               aliases=("sql", "mysql", "postgresql", "postgres", "sqlite", "plpgsql"),
               manual="https://www.postgresql.org/docs/current/functions-comparison.html")
