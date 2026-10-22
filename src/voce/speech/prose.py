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
    s = re.sub(r"\s+([,.;:!?])", r"\1", s)
    s = re.sub(r",(\s*,)+", ",", s)
    return re.sub(r"\s+", " ", s).strip()
