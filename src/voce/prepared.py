"""A document as another device plays it: the blocks to show and the units to say, as one JSON file.

The Mac does the work of reading Markdown and turning code into words (document.py, speech/); a phone or a browser
then needs only this file and a voice. Each document is kept under `prepared/<hash>.json` in the state directory,
named by the same hash as its place (state.py), and `prepared/index.json` lists them in playlist order.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from voce.document import Doc, minutes, word_count
from voce.playlist import Entry
from voce.state import State

FORMAT = 1  # bump when the shape of these files changes


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
    """Write the document's prepared file, unless the one there is already for this text."""
    key = state.key(doc.path)
    out = state.root / "prepared" / f"{key}.json"
    if not out.exists():
        out.parent.mkdir(parents=True, exist_ok=True)
        tmp = out.with_suffix(".tmp")
        tmp.write_text(json.dumps(as_json(doc, key), ensure_ascii=False))
        tmp.replace(out)
    return out


def index(state: State, entries: list[Entry]) -> Path:
    """prepared/index.json: every prepared document, the playlist's first and in its order, the rest by title."""
    folder = state.root / "prepared"
    folder.mkdir(parents=True, exist_ok=True)
    order = {state.key(e.path): (i, e.part) for i, e in enumerate(entries)}
    rows = []
    for f in folder.glob("*.json"):
        if f.name == "index.json" or len(f.stem) != 64:
            continue
        try:
            d = json.loads(f.read_text())
        except (OSError, ValueError):
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
