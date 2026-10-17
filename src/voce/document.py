"""A Markdown file as blocks to show and units to say: sentences, headings, table rows and quiz answers."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from voce.markdown import Block, parse
from voce.speech import sentences, speakable, spoken_code, spoken_line

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


PAUSE_AFTER = {"h1": 0.8, "h2": 0.7, "h3": 0.55, "h4": 0.45, "h5": 0.4, "h6": 0.4,
               "p": 0.4, "li": 0.3, "quote": 0.4, "row": 0.3, "code": 0.5}


def spoken_text(block: Block, a: int, z: int) -> str:
    """block.text[a:z], with each run of inline code said the way a person reads code aloud."""
    out, pos = [], a
    for start, end, roles in block.spans:
        if "code" not in roles or end <= a or start >= z:
            continue
        start, end = max(start, a), min(end, z)
        out += [block.text[pos:start], " ", spoken_code(block.text[start:end]), " "]
        pos = end
    out.append(block.text[pos:z])
    return "".join(out)


def code_units(b: int, code: str) -> list[Unit]:
    """A code block read line by line, each line the way a person reads it aloud. Blank lines are a pause."""
    units, offset = [], 0
    for line in code.split("\n"):
        say = speakable(spoken_line(line))
        if re.search(r"\w", say):
            units.append(Unit(b, offset, offset + len(line), say, pause=0.25))
        elif units and not line.strip():
            units[-1].pause = 0.45
        offset += len(line) + 1
    return units


def block_units(blocks: list[Block], b: int, skip_code: bool = False) -> list[Unit]:
    block = blocks[b]
    if not block.spoken or (skip_code and block.kind == "code"):
        return []
    whole = block.kind.startswith("h") or block.kind == "row"
    if block.kind == "code":
        units = code_units(b, block.text)
        if units:
            units[-1].pause = PAUSE_AFTER["code"]
        return units
    spans = [(0, len(block.text))] if whole else sentences(block.text)
    units = []
    for k, (a, z) in enumerate(spans):
        say = speakable(block.say if block.say and whole else spoken_text(block, a, z))
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


def build_units(doc: Doc, quiz_only: bool = False, skip_code: bool = False) -> list[Unit]:
    """What the voice says, in order. Quiz answers are read straight after their question, after a wait."""
    blocks = doc.blocks
    pairs = quiz_pairs(blocks)
    answer_of = dict(pairs)
    in_answers = {b for b, x in enumerate(blocks) if x.section == "answers"} if pairs else set()
    units: list[Unit] = []
    for b, block in enumerate(blocks):
        if quiz_only and (block.section != "quiz" or block.kind.startswith("h")):
            continue
        if b in in_answers:
            continue
        units += block_units(blocks, b, skip_code)
        if b in answer_of and units:
            units[-1].wait = True
            answer = block_units(blocks, answer_of[b], skip_code)
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
    blocks = parse(path.read_text(encoding="utf-8"))
    doc = Doc(path, title_of(blocks, path), blocks)
    build_units(doc, quiz_only, skip_code)
    return doc


def spoken(md: str) -> str:
    """What the voice says for a piece of Markdown, as one string."""
    doc = Doc(Path("-"), "", parse(md))
    return " ".join(u.say for u in build_units(doc))


def word_count(doc: Doc) -> int:
    return sum(len(u.say.split()) for u in doc.units)


def minutes(words: int, speed: float = 1.0) -> float:
    return words / WORDS_PER_MINUTE / speed
