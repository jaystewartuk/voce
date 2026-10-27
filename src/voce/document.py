"""A Markdown file as blocks to show and units to say: sentences, headings, table rows, code lines, quiz answers.

A Unit is one thing the voice says, with the character range of the block it sits in, so the screen can put the
band under it. Prose is cut into sentences, headings and table rows are one unit each, and code is read a line at
a time the way a pairing partner says it (speech/code.py). A diff is read as a reviewer reads it: the changed
lines, each hunk introduced by its line number, and the unchanged lines around them shown but not said.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from voce import highlight
from voce.markdown import Block, parse, plain
from voce.speech import Language, language, sentences, speakable, spoken_code, spoken_line
from voce.speech.http import http_lines, spoken_symbols

WORDS_PER_MINUTE = 150  # speaking speed at 1x, for time estimates


@dataclass
class Unit:
    """One thing the voice says: usually a sentence."""

    block: int           # index into the document's blocks, or -1 for something said but not shown
    start: int           # character range within the block's text
    end: int
    say: str             # the text sent to the voice
    pause: float = 0.12  # silence after it, in seconds at 1x
    wait: bool = False   # quiz: wait for the listener after this one


@dataclass
class Doc:
    path: Path
    title: str
    blocks: list[Block]
    units: list[Unit] = field(default_factory=list)
    language: str = ""   # the language most of the code is in, used for inline code in the prose


PAUSE_AFTER = {"h1": 0.8, "h2": 0.7, "h3": 0.55, "h4": 0.45, "h5": 0.4, "h6": 0.4,
               "p": 0.4, "li": 0.3, "quote": 0.4, "row": 0.3, "code": 0.5}
LINE_PAUSE = 0.25        # between lines of code
BLANK_LINE_PAUSE = 0.45  # a blank line in code is heard as a longer pause
HUNK_PAUSE = 0.35        # after "Line 40." before the changes there


def spoken_text(block: Block, a: int, z: int, lang: Language) -> str:
    """block.text[a:z], with each run of inline code said the way a person reads code aloud."""
    out, pos = [], a
    for start, end, roles in block.spans:
        if "code" not in roles or end <= a or start >= z:
            continue
        start, end = max(start, a), min(end, z)
        out += [block.text[pos:start], " ", spoken_code(block.text[start:end], lang), " "]
        pos = end
    out.append(block.text[pos:z])
    return "".join(out)


# Fence labels for pictures drawn in text: shown, never read. The prose around a diagram says what it shows.
DIAGRAMS = ("diagram", "mermaid", "ascii", "svgbob", "graphviz", "dot", "plantuml")
# Fence labels for an attacker's input, read with every symbol said: a quote is "quote", < is "less than".
PAYLOADS = ("payload", "attack")


def fence_kind(lang: str) -> str:
    """What a fence's label asks of the reader: "http", "payload", "diagram", or "" for ordinary code."""
    word = lang.strip().lower().split()[0] if lang.strip() else ""
    if word in ("http", "https"):
        return "http"
    if word in PAYLOADS:
        return "payload"
    return "diagram" if word in DIAGRAMS else ""


def code_units(b: int, code: str, lang: str = "") -> list[Unit]:
    """A code block read line by line, each line the way a person reads it aloud. Blank lines are a pause.

    An HTTP message is read as a person reads one out (see speech/http.py), and a payload with every symbol said.
    """
    kind = fence_kind(lang)
    said = http_lines(code) if kind == "http" else None
    units, offset = [], 0
    for k, line in enumerate(code.split("\n")):
        if said is not None:
            say = speakable(said[k])
        elif kind == "payload":
            say = speakable(spoken_symbols(line))
        else:
            say = speakable(spoken_line(line, lang))
        if re.search(r"\w", say):
            units.append(Unit(b, offset, offset + len(line), say, pause=LINE_PAUSE))
        elif units and not line.strip():
            units[-1].pause = BLANK_LINE_PAUSE
        offset += len(line) + 1
    return units


_HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,\d+)? @@\s*(.*)$")


def _prose_line(text: str) -> str:
    """A line of a prose file (Markdown, text) in a diff, read as its words."""
    return plain(re.sub(r"^\s*(?:#{1,6}\s+|[-*+]\s+|\d+[.)]\s+|>\s*)", "", text))


def diff_units(b: int, code: str, lang: str) -> list[Unit]:
    """A diff read as a reviewer reads it: each hunk's line number, then the changed lines.

    The first line of a run of additions is introduced with "Added" and of removals with "Removed"; the rest of
    the run is just read. Context lines are shown but not said: the eye has them, and the ear wants the change.
    A diff with no changed lines at all is read as plain code.
    """
    words = lang.split()
    file_lang = language(words[1]) if len(words) > 1 else language("")
    units: list[Unit] = []
    run = ""
    for offset, kind, text in highlight.diff_lines(code):
        end = offset + len(text)
        if kind == "@":
            m = _HUNK.match(text)
            if m and m.group(1) != "0":  # a new file's one hunk starts at line 0: nothing to say
                say = f"Line {m.group(3)}."
                units.append(Unit(b, offset, end, say, pause=HUNK_PAUSE))
            run = ""
        elif kind in ("+", "-"):
            body = text[1:]
            said = _prose_line(body) if file_lang.prose else spoken_line(body, file_lang)
            say = speakable(said)
            if not re.search(r"\w", say):
                if units and not body.strip():
                    units[-1].pause = BLANK_LINE_PAUSE
                continue
            if kind != run:
                say = ("Added, " if kind == "+" else "Removed, ") + say
                run = kind
            units.append(Unit(b, offset, end, say, pause=LINE_PAUSE))
        elif kind == " ":
            run = ""
    if not any(kind in ("+", "-") for _, kind, _ in highlight.diff_lines(code)):
        return code_units(b, code, lang)
    return units


def block_units(blocks: list[Block], b: int, skip_code: bool = False, lang: Language | None = None) -> list[Unit]:
    block = blocks[b]
    if not block.spoken or (skip_code and block.kind == "code"):
        return []
    whole = block.kind.startswith("h") or block.kind == "row"
    if block.kind == "code":
        if fence_kind(block.lang) == "diagram":
            return []  # a diagram is for the eye: the prose around it says what it shows
        units = diff_units(b, block.text, block.lang) if highlight.is_diff(block.lang) \
            else code_units(b, block.text, block.lang)
        if units:
            units[-1].pause = PAUSE_AFTER["code"]
        return units
    spans = [(0, len(block.text))] if whole else sentences(block.text)
    units = []
    for k, (a, z) in enumerate(spans):
        say = speakable(block.say if block.say and whole else spoken_text(block, a, z, lang or language("")))
        if k == 0 and block.kind == "li" and block.ordered:
            say = block.prefix.strip() + " " + say
        if not re.search(r"\w", say):
            continue
        units.append(Unit(b, a, z, say))
    if units:
        units[-1].pause = PAUSE_AFTER.get(block.kind, 0.3)
    return units


def quiz_pairs(blocks: list[Block]) -> list[tuple[int, int]]:
    """Question and answer blocks, paired in order, when the file has a "Quiz" and a matching "Answers" list."""
    questions = [b for b, x in enumerate(blocks) if x.section == "quiz" and x.kind == "li" and x.ordered]
    answers = [b for b, x in enumerate(blocks) if x.section == "answers" and x.kind == "li" and x.ordered]
    if questions and len(questions) == len(answers):
        return list(zip(questions, answers))
    return []


def main_language(blocks: list[Block]) -> str:
    """The language most of the document's code is in, so inline code in the prose is read in its words."""
    counts = Counter(b.lang.split()[-1] for b in blocks if b.kind == "code" and b.lang)
    return counts.most_common(1)[0][0] if counts else ""


def build_units(doc: Doc, quiz_only: bool = False, skip_code: bool = False) -> list[Unit]:
    """What the voice says, in order. Quiz answers are read straight after their question, after a wait."""
    blocks = doc.blocks
    doc.language = main_language(blocks)
    lang = language(doc.language)
    pairs = quiz_pairs(blocks)
    answer_of = dict(pairs)
    in_answers = {b for b, x in enumerate(blocks) if x.section == "answers"} if pairs else set()
    units: list[Unit] = []
    for b, block in enumerate(blocks):
        if quiz_only and (block.section != "quiz" or block.kind.startswith("h")):
            continue
        if b in in_answers:
            continue
        units += block_units(blocks, b, skip_code, lang)
        if b in answer_of and units:
            units[-1].wait = True
            answer = block_units(blocks, answer_of[b], skip_code, lang)
            if answer:
                answer[0].say = "Answer. " + re.sub(r"^\d+\.?\s*", "", answer[0].say)
            units += answer
    if quiz_only and units:
        units.insert(0, Unit(-1, 0, 0, f"Quiz: {doc.title}.", pause=0.6))
    doc.units = units
    return units


def title_of(blocks: list[Block], path: Path) -> str:
    return next((b.text for b in blocks if b.kind == "h1"), None) \
        or next((b.text for b in blocks if b.kind.startswith("h")), None) \
        or next((b.text[:60] for b in blocks if b.spoken and b.kind != "code"), path.stem)


def load(path: Path | str, quiz_only: bool = False, skip_code: bool = False) -> Doc:
    path = Path(path).resolve()
    return from_markdown(path.read_text(encoding="utf-8"), path, quiz_only, skip_code)


def from_markdown(md: str, path: Path = Path("-"), quiz_only: bool = False, skip_code: bool = False) -> Doc:
    """A document from Markdown text, for text that did not come from a file."""
    blocks = parse(md)
    doc = Doc(path, title_of(blocks, path), blocks)
    build_units(doc, quiz_only, skip_code)
    return doc


def spoken(md: str) -> str:
    """What the voice says for a piece of Markdown, as one string."""
    return " ".join(u.say for u in from_markdown(md).units)


def word_count(doc: Doc) -> int:
    return sum(len(u.say.split()) for u in doc.units)


def minutes(words: int, speed: float = 1.0) -> float:
    return words / WORDS_PER_MINUTE / speed
