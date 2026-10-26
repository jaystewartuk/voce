"""Exporting to a single MP3, to listen away from the computer, with the same voice and pauses as the reader."""

from __future__ import annotations

import concurrent.futures
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Iterable
from pathlib import Path
from typing import Callable

from voce.document import Doc, Unit
from voce.voices import Voice

SAMPLE_RATE = 24000   # most of the voices come at 24 kHz mono; anything else is converted to match
QUIZ_THINKING = 1.5   # extra silence after a quiz question, to answer before the answer comes


class ExportError(Exception):
    pass


def spoken(docs: Iterable[Doc]) -> list[Unit]:
    """Everything said, in order: each file's title, then its sentences. A file that opens with its title as a
    heading has it said once."""
    units: list[Unit] = []
    for doc in docs:
        title = doc.title.rstrip(".")
        if not (doc.units and doc.units[0].say.rstrip(".") == title):
            units.append(Unit(-1, 0, 0, title + ".", pause=0.8))
        units += doc.units
    return units


def silence_after(unit: Unit) -> float:
    return round(max(unit.pause, 0.1) + (QUIZ_THINKING if unit.wait else 0.0), 2)


def _ffmpeg(*args: str) -> None:
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", *args], check=True)


def export_mp3(docs: list[Doc], out: Path, voice: Voice, state, say: Callable[[str], None] = print) -> Path:
    """Fetch any missing audio, then stitch it into one MP3 at out. Returns the path written."""
    if not shutil.which("ffmpeg"):
        how = "brew install ffmpeg" if sys.platform == "darwin" else "sudo apt install ffmpeg, or your system's own"
        raise ExportError(f"ffmpeg not found. Install it with {how}.")
    units = spoken(docs)
    todo = [t for t in dict.fromkeys(u.say for u in units) if not voice.path(t).exists()]
    chars = sum(len(t) for t in todo)
    say(f"{len(docs)} file{'s' * (len(docs) != 1)}, {len(units)} sentences, {len(todo)} not yet fetched "
        f"({chars:,} characters).")
    voice.engine.prepare(say)
    audio_of: dict[str, Path] = {}
    warnings: set[str] = set()
    futures = {voice.pool.submit(voice.fetch, t): t for t in todo}
    for done, future in enumerate(concurrent.futures.as_completed(futures), start=1):
        audio_of[futures[future]] = future.result()  # a failure here stops the export with its reason
        if voice.warning:
            warnings.add(voice.warning)
            voice.warning = ""
        if done % 10 == 0 or done == len(todo):
            print(f"\r  {done}/{len(todo)}", end="", flush=True)
            state.save()
    if todo:
        print()
    state.save(force=True)
    for warning in sorted(warnings):
        say(warning)

    work = Path(tempfile.mkdtemp(prefix="voce-export-"))
    try:
        silences: dict[float, Path] = {}
        converted: dict[Path, Path] = {}

        def silence(seconds: float) -> Path:
            if seconds not in silences:
                path = silences[seconds] = work / f"silence-{seconds}.mp3"
                _ffmpeg("-f", "lavfi", "-i", f"anullsrc=r={SAMPLE_RATE}:cl=mono", "-t", str(seconds),
                        "-c:a", "libmp3lame", "-b:a", "32k", str(path))
            return silences[seconds]

        def audio(path: Path) -> Path:
            """Each sentence's WAV or AIFF, converted to an MP3 to join."""
            if path not in converted:
                target = converted[path] = work / f"{len(converted)}.mp3"
                _ffmpeg("-i", str(path), "-ar", str(SAMPLE_RATE), "-ac", "1", "-c:a", "libmp3lame", "-b:a", "48k",
                        str(target))
            return converted[path]

        def quoted(path: Path) -> str:
            return "file '" + str(path).replace("'", "'\\''") + "'"

        lines = []
        for unit in units:
            # Each sentence once: what was just fetched, or what was cached before
            lines.append(quoted(audio(audio_of.get(unit.say) or voice.fetch(unit.say))))
            lines.append(quoted(silence(silence_after(unit))))
        listing = work / "list.txt"
        listing.write_text("\n".join(lines) + "\n", encoding="utf-8")
        out = out.expanduser()
        out.parent.mkdir(parents=True, exist_ok=True)
        title = docs[0].title if len(docs) == 1 else out.stem
        _ffmpeg("-f", "concat", "-safe", "0", "-i", str(listing), "-ar", str(SAMPLE_RATE), "-ac", "1",
                "-c:a", "libmp3lame", "-b:a", "48k", "-metadata", f"title={title}", "-metadata", "artist=voce",
                str(out))
    finally:
        shutil.rmtree(work, ignore_errors=True)
        voice.close()
    seconds = voice.duration(out)
    say(f"Wrote {out} ({out.stat().st_size / 1e6:.1f} MB, {int(seconds // 60)} min {int(seconds % 60)} s).")
    return out
