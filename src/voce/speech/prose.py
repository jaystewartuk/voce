"""Small rewrites so a voice reads prose naturally: symbols as words, abbreviations in full, codes spelled out.

Audio is cached by the exact text sent to the voice, so a change here makes every sentence it touches fetch again.
Make such changes on purpose, and check them by ear with docs/hearing/check.py.
"""

from __future__ import annotations

import re

_SYMBOLS = {"→": " to ", "←": " from ", "≈": " about ", "×": " times ", "−": " minus ", "&": " and ",
            "▸": "", "│": ", ", "·": ", ", "☐": "", "☑": ""}
# A diff's count of lines, as pull requests show it: "(+12 −3)" is "12 added, 3 removed".
_DIFF_STAT = re.compile(r"\(\s*(?:\+(\d+))?\s*(?:−(\d+))?\s*\)")
# Currency codes that mean something else in technical writing. A voice can read "PHP 8" as "eight Philippine
# pesos", so before a version-like number (one or two digits, maybe dotted) these are spelled out: "P H P 8".
# Sums of money keep their code: "PHP 500", "PHP 1,500". Checked by ear with docs/hearing/check.py.
_VERSIONED_CODES = re.compile(r"\b(PHP|BSD|CRC|CVE)(?=\s+\d{1,2}(?:\.\d+)*(?!\d|,\d))")
# An operator's name that is one word to a programmer but two to the voice, which can leave a gap in it: "plus ‖
# equals". Joined, the voice says it in one breath, as "plus-equals", the way a person does. Checked by ear. Not
# "dot equals", which is as often Java's a.equals(b).
_ONE_WORD = re.compile(r"\b(plus|minus|times|divided|shift|or|and|remainder|modulo|clear|exponentiation|R|OR|at"
                       r"|case) equals\b|\b(null|nullish|nil) coalescing\b|\b(read) only\b")
# Words Kokoro says wrongly as written: "modulo" as "muh-JOO-low", "init" as "in it", "enum" as "in-UM", "iterable"
# as "EYE-terable", "Redis" as "ri-diz". Respelled, both voices say them right. Checked by ear.
# The letter A, which both voices say as the article "uh": "A P I" as "uh P I", the variable in "for A in items" as
# "fer-uh". "eh" is the letter to both. The article stays: "A good day", and "A Value" in a title.
_LETTER_A = re.compile(r"(?<![\w'’-])A(?![\w'’-])")
_A_FOLLOWS = re.compile(r"\s+([A-Za-z]+)")
_AFTER_A = {"plus", "minus", "times", "divided", "equals", "dot", "is", "in", "to", "and", "or", "not", "less",
            "greater", "modulo", "arrow", "returns", "of", "spaceship"}


def _letter_a(m: re.Match) -> str:
    before, after = m.string[:m.start()].rstrip(), _A_FOLLOWS.match(m.string, m.end())
    word = after.group(1) if after else ""
    if re.fullmatch(r"[A-Z][a-z]+", word):
        return "A"  # A Value, A Tour of Go: an article in a title
    if (not before or before[-1] in ".!?:;\"“(") and word.islower() and word not in _AFTER_A:
        return "A"  # A good day: an article starting a sentence
    return "eh"


_RESPELLED = {"modulo": "moduloh", "init": "innit", "turbofish": "turbo fish", "enum": "eenum", "enums": "eenums",
              "iterable": "itterable", "iterables": "itterables", "redis": "reddis"}


def _diff_stat(m: re.Match) -> str:
    added, removed = m.group(1), m.group(2)
    if not added and not removed:
        return m.group(0)
    parts = [f"{added} added" if added else "", f"{removed} removed" if removed else ""]
    return ", " + ", ".join(p for p in parts if p)


def speakable(s: str) -> str:
    """Small fixes so the voice reads the text naturally."""
    s = _DIFF_STAT.sub(_diff_stat, s)
    for symbol, words in _SYMBOLS.items():
        s = s.replace(symbol, words)
    s = re.sub(r"\be\.g\.,?", "for example,", s)
    s = re.sub(r"\bi\.e\.,?", "that is,", s)
    s = re.sub(r"\betc\.", "and so on.", s)
    s = re.sub(r"(?<=\s)vs\.?(?=\s)", "versus", s)
    s = _VERSIONED_CODES.sub(lambda m: " ".join(m.group(1)), s)
    s = re.sub(r"#(\d+)", r"\1", s)
    s = re.sub(r"~(?=\d)", "about ", s)
    s = _ONE_WORD.sub(lambda m: m.group().replace(" ", "-"), s)
    s = re.sub(r"\b(" + "|".join(_RESPELLED) + r")\b", lambda m: _RESPELLED[m.group().lower()], s, flags=re.I)
    s = _LETTER_A.sub(_letter_a, s)
    s = re.sub(r"\s+([,.;:!?])", r"\1", s)
    s = re.sub(r",(\s*,)+", ",", s)
    return re.sub(r"\s+", " ", s).strip()
