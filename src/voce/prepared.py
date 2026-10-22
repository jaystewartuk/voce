"""A document as another device plays it: the blocks to show and the units to say, as one JSON file.

The Mac does the work of reading Markdown and turning code into words (document.py, speech/); a phone or a browser
then needs only this file and a voice. Each document is kept under `prepared/<hash>.json` in the state directory,
named by the same hash as its place (state.py), and `prepared/index.json` lists them in playlist order.

A prepared file also says which reading code made it: a hash of the modules that decide what is shown and said.
When those change, every document is prepared again the next time it is opened or synced, so a better way of
saying something reaches the other devices without anyone having to remember.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from voce.document import Doc, minutes, word_count
from voce.playlist import Entry
from voce.state import State

FORMAT = 1  # bump when the shape of these files changes


def _reading_code() -> str:
    """A short hash of the source that turns Markdown into blocks and code into words."""
    here = Path(__file__).parent
    files = sorted([here / "document.py", here / "highlight.py",
                    *here.glob("markdown/*.py"), *here.glob("speech/**/*.py")])
    h = hashlib.sha256()
    for f in files:
        h.update(f.relative_to(here).as_posix().encode())
        h.update(f.read_bytes())
    return h.hexdigest()[:12]


MADE_BY = _reading_code()


def _plain(value: Any) -> Any:
    """Dataclass fields as JSON can hold them: a span's frozenset of roles becomes a sorted list."""
    if isinstance(value, (set, frozenset)):
        return sorted(value)
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    if isinstance(value, dict):
        return {k: _plain(v) for k, v in value.items()}
    return value


def as_json(doc: Doc, key: str) -> dict[str, Any]:
    words = word_count(doc)
    return {
        "voce": FORMAT,
        "made": MADE_BY,
        "hash": key,
        "title": doc.title,
        "file": doc.path.name,
        "language": doc.language,
        "words": words,
        "minutes": round(minutes(words), 1),
        "blocks": [_plain(asdict(b)) for b in doc.blocks],
        "units": [asdict(u) for u in doc.units],
    }


def save(doc: Doc, state: State) -> Path:
    """Write the document's prepared file, unless the one there was made for this text by this reading code."""
    key = state.key(doc.path)
    out = state.root / "prepared" / f"{key}.json"
    if not _current(out):
        out.parent.mkdir(parents=True, exist_ok=True)
        tmp = out.with_suffix(".tmp")
        tmp.write_text(json.dumps(as_json(doc, key), ensure_ascii=False))
        tmp.replace(out)
    return out


def _current(path: Path) -> bool:
    try:
        return json.loads(path.read_text()).get("made") == MADE_BY
    except (OSError, ValueError, AttributeError):
        return False


def index(state: State, entries: list[Entry]) -> Path:
    """prepared/index.json: every prepared document, the playlist's first and in its order, the rest by title.
    A copy of a playlist file made from an older text of it is removed: the file was edited, and this is its past."""
    folder = state.root / "prepared"
    folder.mkdir(parents=True, exist_ok=True)
    order = {state.key(e.path): (i, e.part) for i, e in enumerate(entries)}
    names = {e.path.name for e in entries}
    rows = []
    for f in folder.glob("*.json"):
        if f.name == "index.json" or len(f.stem) != 64:
            continue
        try:
            d = json.loads(f.read_text())
        except (OSError, ValueError):
            continue
        if f.stem not in order and d.get("file") in names:
            f.unlink(missing_ok=True)
            continue
        i, part = order.get(f.stem, (len(order), ""))
        rows.append({"hash": f.stem, "title": d.get("title", f.stem), "file": d.get("file", ""), "part": part,
                     "words": d.get("words", 0), "minutes": d.get("minutes", 0), "_order": i})
    rows.sort(key=lambda r: (r.pop("_order"), r["title"].lower()))
    out = folder / "index.json"
    tmp = out.with_suffix(".tmp")
    tmp.write_text(json.dumps({"voce": FORMAT, "documents": rows}, ensure_ascii=False, indent=1))
    tmp.replace(out)
    return out
