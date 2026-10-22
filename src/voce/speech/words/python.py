"""Python's own words: ``->`` is "returns", ``//`` is "floor divided by", ``__init__`` is "dunder init"."""

from __future__ import annotations

from voce.speech.words.common import Language

PYTHON = Language("python", comments=("#",), dunder=True, words={
    "elif": "else if", "kwargs": "keyword args", "cls": "class", "isinstance": "is instance",
    "re": "R E", "np": "numpy", "pd": "pandas", "dt": "date time", "func": "function",
    "iter": "iterator", "attr": "attribute", "getattr": "get attribute", "setattr": "set attribute",
}, operators={
    "->": "returns", "**": "to the power of", "//": "floor divided by", ":=": "walrus", "@": "at",
}, aliases=("python", "py", "python3"),
    manual="https://docs.python.org/3/reference/expressions.html")
