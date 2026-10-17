"""Text from the clipboard or a pipe, kept as a Markdown file so reading it again resumes where it stopped."""

from __future__ import annotations

import datetime
import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

from voce import paths

KEEP = 50  # clips kept; older ones are deleted


class ClipError(Exception):
    pass


def save_clip(text: str, source: str, folder: Path | None = None) -> Path:
    """Save text as a Markdown file named by its content, reusing the file if the same text was read before."""
    text = text.replace("\r\n", "\n").strip("\n")
    if not text.strip():
        raise ClipError(f"Nothing to read: the {source} is empty.")
    folder = folder or paths.clips_dir()
    folder.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
    same = sorted(folder.glob(f"*-{digest}.md"))
    if same:
        return same[-1]
    path = folder / f"{datetime.datetime.now():%Y-%m-%d-%H%M}-{digest}.md"
    path.write_text(text + "\n", encoding="utf-8")
    for old in sorted(folder.glob("*.md"), key=lambda q: q.stat().st_mtime)[:-KEEP]:
        old.unlink(missing_ok=True)
    return path


def read_clipboard() -> str:
    if not shutil.which("pbpaste"):
        raise ClipError("pbpaste not found: reading the clipboard needs macOS.")
    return subprocess.run(["pbpaste"], capture_output=True, text=True).stdout


def read_stdin() -> str:
    """Everything piped in, then the keyboard back on standard input for the reader."""
    text = sys.stdin.read()
    try:
        fd = os.open("/dev/tty", os.O_RDONLY)
        os.dup2(fd, 0)
        os.close(fd)
        sys.stdin = open(0, closefd=False)  # noqa: SIM115 - stays open for the life of the program
    except OSError as e:
        raise ClipError("No terminal to read keys from.") from e
    return text
