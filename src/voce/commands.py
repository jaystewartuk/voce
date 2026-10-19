"""The commands that print instead of playing: --check, --list, --minutes, --prepare, --export and --sync."""

from __future__ import annotations

import concurrent.futures
from pathlib import Path

from voce import prepared, sync, voices
from voce.document import load, minutes, quiz_pairs, word_count
from voce.export import export_mp3
from voce.playlist import Entry, update_minutes
from voce.state import State
from voce.voices import Voice


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


def print_list(state: State, entries: list[Entry], voice: Voice) -> None:
    part = None
    for e in entries:
        if e.part != part:
            part = e.part
            print(f"\n{part}" if part else "")
        print(f"  {state.progress(e.path):>5}  {e.title}")
    if voice.usage():
        print(f"\n{voice.usage()}.")


def print_minutes(readme: Path) -> None:
    total = update_minutes(readme)
    print(f"Updated {relative(readme)}: {total:,} words, about {minutes(total) / 60:.1f} hours at 1×.")


def prepare(paths: list[Path], voice: Voice, state: State, entries: list[Entry] = ()) -> None:
    """Fetch the voice for these files ahead of time, so reading them never waits on the network, and keep a
    prepared copy of each for other devices."""
    docs = [load(p) for p in paths]
    for doc in docs:
        prepared.save(doc, state)
    prepared.index(state, list(entries))
    texts = [u.say for doc in docs for u in doc.units]
    todo = [t for t in dict.fromkeys(texts) if not voice.path(t).exists()]
    chars = sum(len(t) for t in todo)
    print(f"{len(paths)} file{'s' * (len(paths) != 1)}, {len(texts)} sentences, {len(todo)} not yet fetched "
          f"({chars:,} characters).")
    if voice.over_free(chars):
        print(f"Warning: that takes this month past the {voice.engine.free_chars:,} free characters.")
    voice.engine.prepare(print)
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
    if voice.usage():
        print(f"\n{voice.usage()}.")


def print_voices(state: State) -> None:
    """Each engine: whether it is set up, how to set it up if not, and the voices the v key goes through."""
    using = voices.default_engine(state)
    for kind, engine_class in voices.ENGINES.items():
        engine = engine_class(voices.saved_name(state, kind))
        if engine_class.configured(state):
            how = "in use" if kind == using else "set up"
            if kind == "kokoro" and not engine.ready():
                how += f", downloads {engine.SIZE_MB} MB on first use"
        else:
            how = f"not set up. {engine.setup}"
        print(f"{engine.title:<11}{how}")
        if engine_class.configured(state):
            names = engine.voices if kind != "mac" else engine.voices[:12]
            print(f"           voices: {', '.join(names) if names else 'the system voice'}"
                  + (" and the others say -v ? lists" if kind == "mac" and names else "")
                  + (f"; any {engine.title} voice name works with --voice" if kind not in ("mac", "kokoro") else "")
                  + (", or any of the 54 names in the model" if kind == "kokoro" else ""))
            usage = Voice(engine, state).usage()
            if usage:
                print(f"           {usage}")


def export(paths: list[Path], out: Path, voice: Voice, state: State, skip_code: bool = False) -> None:
    export_mp3([load(p, skip_code=skip_code) for p in paths], out, voice, state)


def sync_up(state: State, entries: list[Entry], repo: str) -> None:
    """Prepare the playlist for other devices, then commit, pull and push the state directory."""
    if repo:
        url = sync.setup(state.root, repo, print)
        state.set("sync", url)
        state.save(force=True)
        print(f"Syncing {relative(state.root)} with {url}.")
    elif not sync.ready(state.root):
        raise sync.SyncError("Not set up yet. Say where to keep your places: voce --sync OWNER/REPO (a private "
                             "repository on GitHub, made for you if gh is signed in) or any git URL.")
    for e in entries:
        try:
            prepared.save(load(e.path), state)
        except (OSError, UnicodeDecodeError):
            pass
    prepared.index(state, entries)
    state.save(force=True)
    sync.run(state.root, print)
    if repo:
        print(f"\nOn your phone, open {sync.WEB_APP} and sign in with GitHub.\n"
              f"When it asks which repository voce may reach, choose this one.")
