"""Playlists: a README whose "Listen in this order" section lists Markdown files, grouped into parts.

    ## Listen in this order

    ### Part 1. The basics
    1. [Getting started](basics/start.md) · 12 min
    2. [Core ideas](basics/ideas.md) · 9 min

Any numbered list of links to .md files works; the "· N min" is optional and `voce --minutes` keeps it current.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from voce.document import load, minutes, word_count
from voce.markdown import plain

SECTION = re.compile(r"^## (?:Listen in this order|Listening order|Playlist)\b.*?$(.*?)(?=^## |\Z)", re.M | re.S)
_ITEM = re.compile(r"^\s*\d+\.\s+\[([^\]]+)\]\(([^)#\s]+\.md)(?:#[^)]*)?\)")


@dataclass
class Entry:
    path: Path
    title: str
    part: str = ""


class PlaylistError(Exception):
    pass


def find_playlist(where: Path | str) -> Path:
    """The README holding a playlist, given its folder or the file itself."""
    p = Path(where).expanduser().resolve()
    if p.is_dir():
        p = p / "README.md"
    if not p.exists():
        raise PlaylistError(f"No such file: {p}")
    if not SECTION.search(p.read_text(encoding="utf-8")):
        raise PlaylistError(f'{p} has no "## Listen in this order" section.')
    return p


def read_playlist(readme: Path | None) -> list[Entry]:
    """The files in the README's playlist that exist, with the part (### heading) each sits under."""
    if readme is None or not readme.exists():
        return []
    m = SECTION.search(readme.read_text(encoding="utf-8"))
    if not m:
        return []
    entries, part = [], ""
    for line in m.group(1).splitlines():
        heading = re.match(r"^###\s+(.*)", line)
        if heading:
            part = plain(heading.group(1))
            continue
        item = _ITEM.match(line)
        if item:
            path = (readme.parent / item.group(2)).resolve()
            if path.exists():
                entries.append(Entry(path, plain(item.group(1)), part))
    return entries


def part_matches(part: str, wanted: str) -> bool:
    """Whether a part heading is the one asked for: by its number ("2" for "Part 2. ...") or by a word in it."""
    number = re.match(r"^\s*(?:part\s+)?(\d+)\b", part, re.I)
    if wanted.isdigit():
        return bool(number) and int(number.group(1)) == int(wanted)
    return wanted.lower() in part.lower()


def update_minutes(readme: Path) -> int:
    """Rewrite the "· N min" after each file in the playlist from the files as they are now. Returns total words."""
    text = readme.read_text(encoding="utf-8")

    def fix(m: re.Match) -> str:
        path = (readme.parent / m.group(2)).resolve()
        if not path.exists():
            return m.group(0)
        return f"{m.group(1)} · {max(1, round(minutes(word_count(load(path)))))} min"

    pattern = r"^(\s*\d+\.\s+\[[^\]]+\]\(([^)#\s]+\.md)(?:#[^)]*)?\))\s*·\s*\d+\s*min"
    readme.write_text(re.sub(pattern, fix, text, flags=re.M), encoding="utf-8")
    return sum(word_count(load(e.path)) for e in read_playlist(readme))
