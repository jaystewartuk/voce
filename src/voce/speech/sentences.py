"""Cutting prose into sentences, the unit the voice reads and the band on the screen follows."""

from __future__ import annotations

import re

ABBREVIATIONS = {"e.g", "i.e", "etc", "vs", "mr", "mrs", "ms", "dr", "st", "no", "approx", "inc", "ltd", "co",
                 "fig", "cf", "u.s", "u.k", "a.m", "p.m", "jan", "feb", "mar", "apr", "jun", "jul", "aug",
                 "sep", "sept", "oct", "nov", "dec"}
# A sentence starts with a capital or a digit, maybe after an opening quote or bracket, or Spanish's opening ¿ and ¡.
_BOUNDARY = re.compile(r"([.!?…]+[\"'”’»)\]]*)(\s+)(?=[\"'“‘«(\[¿¡]?[A-ZÀ-ÖØ-Þ0-9])")


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
