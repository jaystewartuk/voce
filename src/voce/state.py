"""What voce remembers between runs: your place in each document, settings, and the characters sent to each voice
engine this month.

The state directory is laid out so that a folder sync (iCloud Drive, Dropbox, Syncthing, a git repo) carries it
between machines without conflicts:

    settings.json       speed, voice, engine, playlist and the rest: small, rarely written
    usage.json          characters sent to each engine each month: this machine's bill, not synced in spirit
    places/<hash>.json  one file per document, named by a hash of the document's text

A place is keyed by what the document says, not where it lives, so the same file resumes on any machine however
it got there. Two machines reading different documents touch different files; the same document read on both is
settled by whichever place was written last.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import socket
import threading
import time
from pathlib import Path
from typing import Any

from voce import paths


def _read_json(path: Path, default: Any) -> Any:
    try:
        value = json.loads(path.read_text())
    except (OSError, ValueError):
        return default
    return value if isinstance(value, type(default)) else default


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")  # two voces never share a temp file
    tmp.write_text(json.dumps(value, indent=1))
    tmp.replace(path)


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class State:
    """Small JSON files in one directory, each written atomically and at most every couple of seconds unless forced."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or paths.state_dir()
        self.lock = threading.Lock()
        self.host = socket.gethostname() or "here"
        self.settings: dict[str, Any] = _read_json(self.root / "settings.json", {})
        self.usage: dict[str, Any] = _read_json(self.root / "usage.json", {})
        self.places: dict[str, dict[str, Any]] = {}
        for f in sorted((self.root / "places").glob("*.json")) if (self.root / "places").is_dir() else []:
            record = _read_json(f, {})
            if record and len(f.stem) == 64:  # a sync tool's "conflicted copy" is not a place
                self.places[f.stem] = record
        self.keys: dict[tuple[str, int, int], str] = {}  # (path, mtime, size) -> hash, so a tick doesn't rehash
        self.dirty: set[str] = set()  # "settings", "usage" and the hashes of places changed since the last save
        self.saved_at = 0.0
        self._migrate()

    def _migrate(self) -> None:
        """Before places had their own files, everything was in state.json, keyed by path."""
        old = self.root / "state.json"
        data = _read_json(old, {})
        if not data:
            return
        if not self.settings:
            self.settings = {k: v for k, v in data.items() if k not in ("files", "usage")}
            self.dirty.add("settings")
        if not self.usage and isinstance(data.get("usage"), dict):
            for month, n in data["usage"].items():
                self.usage[month] = {"google": n} if isinstance(n, int) else n  # the first count was Google's alone
            self.dirty.add("usage")
        files = data.get("files") if isinstance(data.get("files"), dict) else {}
        for path, record in files.items():
            if not isinstance(record, dict) or not Path(path).is_file():
                continue  # a file that is gone can't be hashed; the old state.json keeps its entry
            key = self.key(Path(path))
            if key not in self.places:
                self.places[key] = {**record, "updated": _now(), "paths": {self.host: path}}
                self.dirty.add(key)
        self.save(force=True)
        old.replace(old.with_name("state-v1.json"))

    # ---- settings

    def get(self, key: str, default: Any = None) -> Any:
        return self.settings.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.settings[key] = value
        self.dirty.add("settings")

    # ---- places

    def key(self, path: Path) -> str:
        """The hash of what the file says, which names its place and its prepared copy; a file that can't be read
        is known by its name alone."""
        try:
            st = path.stat()
            stamp = (str(path), st.st_mtime_ns, st.st_size)
            if stamp not in self.keys:
                self.keys[stamp] = hashlib.sha256(path.read_bytes()).hexdigest()
            return self.keys[stamp]
        except OSError:
            return hashlib.sha256(f"path:{path}".encode()).hexdigest()

    def record(self, path: Path) -> dict[str, Any]:
        """The saved place for a document, empty if it has none."""
        key = self.key(path)
        if key not in self.places and path.is_file():
            self._adopt(key, path)
        return self.places.get(key, {})

    def _adopt(self, key: str, path: Path) -> None:
        """A file that has changed has a new hash; the place last saved under its path on this machine moves over."""
        here = str(path)
        candidates = [(k, f) for k, f in self.places.items() if f.get("paths", {}).get(self.host) == here]
        if not candidates:
            return
        old_key, old = max(candidates, key=lambda kf: kf[1].get("updated", ""))
        self.places[key] = {**old, "paths": {self.host: here}}
        del self.places[old_key]
        self.dirty.update((key, old_key))

    def file(self, path: Path) -> dict[str, Any]:
        """The place for a document, to be written to; it is saved on the next save."""
        self.record(path)
        key = self.key(path)
        f = self.places.setdefault(key, {})
        f["updated"] = _now()
        f.setdefault("paths", {})[self.host] = str(path)
        self.dirty.add(key)
        return f

    def is_done(self, path: Path) -> bool:
        return bool(self.record(path).get("done"))

    def progress(self, path: Path) -> str:
        """"done", a percentage, or "" for a file not started."""
        f = self.record(path)
        if f.get("done"):
            return "done"
        if f.get("pos"):
            return f"{int(100 * f['pos'] / max(1, f.get('total', 1)))}%"
        return ""

    def place(self, path: Path, units: list, i: int) -> None:
        f = self.file(path)
        f["pos"] = i
        f["at"] = units[i].say[:80] if 0 <= i < len(units) else ""
        f["total"] = len(units)
        self.set("last", str(path))

    def resume(self, path: Path, units: list) -> int:
        """Where to start: the saved sentence, found again by its text if the file has changed since."""
        f = self.record(path)
        if f.get("done") or not units:
            return 0
        pos, at = f.get("pos", 0), f.get("at", "")
        if 0 <= pos < len(units) and units[pos].say[:80] == at:
            return pos
        for i, u in enumerate(units):
            if at and u.say[:80] == at:
                return i
        return max(0, min(pos, len(units) - 1))

    def done(self, path: Path, value: bool = True) -> None:
        f = self.file(path)
        f["done"] = value
        if value:
            f.update(pos=0, at="")

    def restart(self, path: Path) -> None:
        """Back to the top, as if never started."""
        self.file(path).update(done=False, pos=0, at="", total=0)

    # ---- usage

    def count(self, engine: str, chars: int) -> None:
        month = datetime.date.today().strftime("%Y-%m")
        with self.lock:
            this_month = self.usage.setdefault(month, {})
            this_month[engine] = this_month.get(engine, 0) + chars
            self.dirty.add("usage")

    def month_chars(self, engine: str) -> int:
        return self.usage.get(datetime.date.today().strftime("%Y-%m"), {}).get(engine, 0)

    # ---- saving

    def save(self, force: bool = False) -> None:
        if not force and time.monotonic() - self.saved_at < 2:
            return
        self.saved_at = time.monotonic()
        with self.lock:
            dirty, self.dirty = self.dirty, set()
            for key in dirty:
                if key == "settings":
                    _write_json(self.root / "settings.json", self.settings)
                elif key == "usage":
                    _write_json(self.root / "usage.json", self.usage)
                elif key in self.places:
                    _write_json(self.root / "places" / f"{key}.json", self.places[key])
                else:
                    try:
                        (self.root / "places" / f"{key}.json").unlink()
                    except OSError:
                        pass
