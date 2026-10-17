"""Splitting text into sentences, and small rewrites so a voice reads it naturally."""

from __future__ import annotations

import re

ABBREVIATIONS = {"e.g", "i.e", "etc", "vs", "mr", "mrs", "ms", "dr", "st", "no", "approx", "inc", "ltd", "co",
                 "fig", "cf", "u.s", "u.k", "a.m", "p.m", "jan", "feb", "mar", "apr", "jun", "jul", "aug",
                 "sep", "sept", "oct", "nov", "dec"}
_BOUNDARY = re.compile(r"([.!?…]+[\"'”’)\]]*)(\s+)(?=[\"'“‘(\[]?[A-Z0-9])")


def sentences(text: str) -> list[tuple[int, int]]:
    """(start, end) of each sentence in text."""
    out, start = [], 0
    for m in _BOUNDARY.finditer(text):
        before = text[start:m.end(1)]
        last = re.search(r"(\S+)$", before)
        token = last.group(1).rstrip(".!?…\"'”’)]").lower() if last else ""
        if token in ABBREVIATIONS or re.fullmatch(r"[a-z]", token):
            continue
        if re.fullmatch(r"\d+", token) and m.group(1) == "." and text[m.end(2):m.end(2) + 1].isdigit():
            continue  # "version 3. 4 changes" is rare; "step 3. 4" is a list written inline
        out.append((start, m.end(1)))
        start = m.end(2)
    if start < len(text):
        out.append((start, len(text)))
    return [(a, b) for a, b in out if text[a:b].strip()]


_SYMBOLS = {"→": " to ", "←": " from ", "≈": " about ", "×": " times ", "−": " minus ", "&": " and ",
            "▸": "", "│": ", ", "☐": "", "☑": ""}
# Currency codes that mean something else in technical writing. Google reads "PHP 8" as "eight Philippine
# pesos", so before a version-like number (one or two digits, maybe dotted) these are spelled out: "P H P 8".
# Sums of money keep their code: "PHP 500", "PHP 1,500". Checked by ear with docs/hearing/check.py.
_VERSIONED_CODES = re.compile(r"\b(PHP|BSD|CRC|CVE)(?=\s+\d{1,2}(?:\.\d+)*(?!\d|,\d))")


def speakable(s: str) -> str:
    """Small fixes so the voice reads the text naturally."""
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
