"""What voce remembers between runs: your place in each file, settings, and the month's voice usage."""

from __future__ import annotations

import datetime
import json
import os
import threading
import time
from pathlib import Path
from typing import Any

from voce import paths


class State:
    """A small JSON file, written atomically and at most every couple of seconds unless forced."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or paths.state_file()
        self.lock = threading.Lock()
        try:
            self.data: dict[str, Any] = json.loads(self.path.read_text())
        except (OSError, ValueError):
            self.data = {}
        if not isinstance(self.data, dict):
            self.data = {}
        for key in ("files", "usage"):
            if not isinstance(self.data.get(key), dict):
                self.data.pop(key, None)
        self.data.setdefault("files", {})
        self.data.setdefault("usage", {})
        self.saved_at = 0.0

    # ---- settings

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.data[key] = value

    # ---- places

    def file(self, path: Path) -> dict[str, Any]:
        return self.data["files"].setdefault(str(path), {})

    def is_done(self, path: Path) -> bool:
        return bool(self.data["files"].get(str(path), {}).get("done"))

    def progress(self, path: Path) -> str:
        """"done", a percentage, or "" for a file not started."""
        f = self.data["files"].get(str(path), {})
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
        self.data["last"] = str(path)

    def resume(self, path: Path, units: list) -> int:
        """Where to start: the saved sentence, found again by its text if the file has changed since."""
        f = self.data["files"].get(str(path), {})
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

    def count(self, chars: int) -> None:
        month = datetime.date.today().strftime("%Y-%m")
        with self.lock:
            self.data["usage"][month] = self.data["usage"].get(month, 0) + chars

    def month_chars(self) -> int:
        return self.data["usage"].get(datetime.date.today().strftime("%Y-%m"), 0)

    # ---- saving

    def save(self, force: bool = False) -> None:
        if not force and time.monotonic() - self.saved_at < 2:
            return
        self.saved_at = time.monotonic()
        with self.lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_name(f"{self.path.name}.{os.getpid()}.tmp")  # two voces never share a temp file
            tmp.write_text(json.dumps(self.data, indent=1))
            tmp.replace(self.path)
