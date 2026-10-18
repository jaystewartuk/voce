"""The commands that print instead of playing: --check, --list, --minutes, --prepare and --export."""

from __future__ import annotations

import concurrent.futures
from pathlib import Path

from voce.document import load, minutes, quiz_pairs, word_count
from voce.export import export_mp3
from voce.playlist import Entry, update_minutes
from voce.state import State
from voce.voices import FREE_CHARS, Voice


def relative(path: Path) -> str:
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path).replace(str(Path.home()), "~", 1)


def check(paths: list[Path], skip_code: bool = False) -> None:
    """How each file will read: sentences, words, minutes, characters for the voice, quiz pairing, oddities."""
    total_words = total_chars = 0
    for path in paths:
        try:
            doc = load(path, skip_code=skip_code)
        except (OSError, UnicodeDecodeError) as e:
            print(f"{relative(Path(path))}\n    couldn't read it: {e}")
            continue
        words, chars = word_count(doc), sum(len(u.say) for u in doc.units)
        total_words += words
        total_chars += chars
        pairs = quiz_pairs(doc.blocks)
        notes = []
        code = sum(1 for b in doc.blocks if b.kind == "code")
        if code:
            how = "shown, not read" if skip_code else "read line by line"
            notes.append(f"{code} code block{'s' * (code != 1)}, {how}")
        long = [u for u in doc.units if len(u.say) > 400]
        if long:
            notes.append(f"{len(long)} sentence{'s' * (len(long) != 1)} over 400 characters")
        if any(b.kind == "h2" and b.text.lower() in ("quiz", "answers") for b in doc.blocks) and not pairs:
            notes.append("the quiz and answers don't pair up")
        quiz = f" · quiz of {len(pairs)}" if pairs else ""
        print(f"{relative(doc.path)}\n    {len(doc.units)} sentences · {words:,} words · "
              f"{minutes(words):.0f} min · {chars:,} characters{quiz}"
              + (f"\n    note: {', '.join(notes)}" if notes else ""))
    if len(paths) > 1:
        print(f"\nTotal: {total_words:,} words, about {minutes(total_words) / 60:.1f} hours at 1×, "
              f"{total_chars:,} characters for the voice.")


def print_list(state: State, entries: list[Entry], google: bool) -> None:
    part = None
    for e in entries:
        if e.part != part:
            part = e.part
            print(f"\n{part}" if part else "")
        print(f"  {state.progress(e.path):>5}  {e.title}")
    if google:
        print(f"\nGoogle characters this month: {state.month_chars():,} of {FREE_CHARS:,} free.")


def print_minutes(readme: Path) -> None:
    total = update_minutes(readme)
    print(f"Updated {relative(readme)}: {total:,} words, about {minutes(total) / 60:.1f} hours at 1×.")


def prepare(paths: list[Path], voice: Voice, state: State) -> None:
    """Fetch the voice for these files ahead of time, so reading them never waits on the network."""
    texts = [u.say for p in paths for u in load(p).units]
    todo = [t for t in dict.fromkeys(texts) if not voice.path(t).exists()]
    chars = sum(len(t) for t in todo)
    print(f"{len(paths)} file{'s' * (len(paths) != 1)}, {len(texts)} sentences, {len(todo)} not yet fetched "
          f"({chars:,} characters).")
    if voice.uses_google and chars + state.month_chars() > FREE_CHARS:
        print(f"Warning: that takes this month past the {FREE_CHARS:,} free characters.")
    done = failed = 0
    try:
        for future in concurrent.futures.as_completed([voice.pool.submit(voice.fetch, t) for t in todo]):
            done += 1
            if future.exception() is not None:
                failed += 1
            if done % 10 == 0 or done == len(todo):
                print(f"\r  {done}/{len(todo)}", end="", flush=True)
                state.save()
    except KeyboardInterrupt:
        print("\nStopped; what was fetched is kept.")
    finally:
        voice.close()
        state.save(force=True)
    if failed:
        print(f"\n{failed} sentence{'s' * (failed != 1)} couldn't be fetched; they will be tried again when read.")
    if voice.warning:
        print(f"\n{voice.warning}")
    if voice.uses_google:
        print(f"\nGoogle characters this month: {state.month_chars():,} of {FREE_CHARS:,} free.")


def export(paths: list[Path], out: Path, voice: Voice, state: State, skip_code: bool = False) -> None:
    export_mp3([load(p, skip_code=skip_code) for p in paths], out, voice, state)
