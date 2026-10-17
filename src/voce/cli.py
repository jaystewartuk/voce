"""The voce command."""

from __future__ import annotations

import argparse
import concurrent.futures
import curses
import locale
import os
import shutil
import signal
import sys
from pathlib import Path

from voce import __version__
from voce.claude import TranscriptError, last_reply, latest_transcript
from voce.clips import ClipError, read_clipboard, read_stdin, save_clip
from voce.document import load, minutes, quiz_pairs, word_count
from voce.export import ExportError, export_mp3
from voce.player import make_player
from voce.playlist import Entry, PlaylistError, find_playlist, part_matches, read_playlist, update_minutes
from voce.state import State
from voce.voices import DEFAULT_GOOGLE_VOICE, FREE_CHARS, Google, Voice, next_google_voice

USAGE = """\
examples:
  voce notes.md            read a Markdown file, from where you left off
  voce -r                  read Claude Code's latest reply in this folder (run it in another terminal)
  voce -c                  read what's on the clipboard
  pbpaste | voce -         read standard input
  voce a.md b.md --export walk.mp3   one MP3 for a walk, with the same voice and pauses
  voce                     carry on where you left off: your playlist, or the last thing you read
  voce --playlist DIR      use DIR/README.md's "Listen in this order" list from now on
  voce --menu              choose a file from the playlist

keys:
  space pause · ←/→ sentence · ↑/↓ paragraph · [ ] section · +/- speed
  n/p next or previous file · v voice · m menu · r restart · q quit (your place is saved)
  click a sentence to jump to it · the wheel scrolls

voices:
  The Mac's own voice works out of the box. For Google's Chirp 3 HD voices, set VOCE_GOOGLE_API_KEY, or sign
  in with gcloud and pass --google-project once. Every sentence is fetched once and kept.

https://github.com/jaystewartuk/voce
"""


def speed(value: str) -> float:
    try:
        x = float(value)
    except ValueError:
        x = float("nan")
    if not 0.5 <= x <= 3.0:  # also false for NaN
        raise argparse.ArgumentTypeError(f"{value!r} isn't a speed from 0.5 to 3")
    return x


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="voce", description="Read Markdown aloud in your terminal, highlighting each sentence and word.",
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=USAGE)
    ap.add_argument("files", nargs="*", metavar="FILE", help="Markdown files to read, or - for standard input")
    ap.add_argument("-r", "--reply", action="store_true",
                    help="read Claude Code's latest reply in this folder (the text /copy would take)")
    ap.add_argument("-c", "--clip", action="store_true", help="read what is on the clipboard")
    ap.add_argument("--start", action="store_true", help="start the file from the top")
    ap.add_argument("--one", action="store_true", help="stop at the end of the file instead of carrying on")
    ap.add_argument("--speed", type=speed, metavar="X", help="playback speed from 0.5 to 3, for example 1.2")

    playlist = ap.add_argument_group("playlists")
    playlist.add_argument("--playlist", metavar="DIR", help="use this folder's README.md playlist from now on")
    playlist.add_argument("--menu", action="store_true", help="choose a file from the playlist first")
    playlist.add_argument("--list", action="store_true", help="print the playlist with your progress")
    playlist.add_argument("--quiz", nargs="?", const="", metavar="PART",
                          help="quizzes only: all of them, one part (number or name) or a file")
    playlist.add_argument("--minutes", action="store_true", help="update the minutes in the playlist README")

    voice = ap.add_argument_group("voices")
    voice.add_argument("--voice", metavar="NAME",
                       help=f"a Google voice such as {DEFAULT_GOOGLE_VOICE}, or a Mac voice name with --mac")
    voice.add_argument("--mac", action="store_true", help="use the Mac's voice even when Google is set up")
    voice.add_argument("--google-project", metavar="ID", help="the Google Cloud project to bill (saved)")
    voice.add_argument("--prepare", nargs="*", metavar="PART",
                       help="fetch the voice ahead of time: for the files given, or the playlist (or these parts)")

    tools = ap.add_argument_group("other")
    tools.add_argument("--export", metavar="OUT.mp3",
                       help="write the files (or reply, clipboard or playlist) as one MP3 instead of playing")
    tools.add_argument("--check", nargs="*", metavar="FILE",
                       help="report how files will read, without audio (default: the playlist)")
    tools.add_argument("--afplay", action="store_true", help="play with afplay instead of the built-in player")
    tools.add_argument("--mute", action="store_true", help=argparse.SUPPRESS)
    tools.add_argument("--version", action="version", version=f"voce {__version__}")
    return ap


# ---------------------------------------------------------------- choosing what to play

def playlist_path(args, state: State) -> Path | None:
    if args.playlist:
        path = find_playlist(args.playlist)
        state.set("playlist", str(path))
        state.save(force=True)
        print(f"Playlist: {path}")
        return path
    saved = state.get("playlist")
    return Path(saved) if saved and Path(saved).exists() else None


def choose(args, state: State, entries: list[Entry]) -> tuple[list[Entry], int]:
    """The files to play and where to start: the file given, or the first unfinished file in the playlist."""
    if args.files:
        paths = existing(args.files)
        if len(paths) == 1:
            for i, e in enumerate(entries):
                if e.path == paths[0]:
                    return entries, i
        return [Entry(p, load(p).title) for p in paths], 0
    last = state.get("last")
    if not entries:
        if last and Path(last).exists():
            return [Entry(Path(last), load(last).title)], 0
        sys.exit("Nothing to read yet. Give a Markdown file, use -r for Claude Code's latest reply or -c for the "
                 "clipboard, or set a playlist with --playlist DIR. See voce --help.")
    for i, e in enumerate(entries):
        if str(e.path) == last and not state.is_done(e.path):
            return entries, i
    for i, e in enumerate(entries):
        if not state.is_done(e.path):
            return entries, i
    return entries, 0


def existing(files: list[str]) -> list[Path]:
    paths = [Path(f).expanduser().resolve() for f in files]
    missing = [f for f, p in zip(files, paths) if not p.is_file()]
    if missing:
        sys.exit(f"No such file: {', '.join(missing)}")
    return paths


def quizzes(which: str, entries: list[Entry]) -> list[Entry]:
    files = [e for e in entries if quiz_pairs(load(e.path).blocks)]
    if which and Path(which).exists():
        path = Path(which).resolve()
        files = [e for e in files if e.path == path] or [Entry(path, load(path).title)]
    elif which:
        files = [e for e in files if part_matches(e.part, which)]
    if not files:
        sys.exit("No quizzes found. A quiz is a numbered list under a \"## Quiz\" heading, with the same number "
                 "of answers under \"## Answers\".")
    return files


# ---------------------------------------------------------------- commands that don't play

def relative(path: Path) -> str:
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path).replace(str(Path.home()), "~", 1)


def check(paths: list[Path]) -> None:
    """How each file will read: sentences, words, minutes, characters for the voice, quiz pairing, oddities."""
    total_words = total_chars = 0
    for path in paths:
        try:
            doc = load(path)
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
            notes.append(f"{code} code block{'s' * (code != 1)} shown, not read")
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


def prepare(paths: list[Path], voice: Voice, state: State) -> None:
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


# ---------------------------------------------------------------- main

def main(argv: list[str] | None = None) -> None:
    args = parser().parse_args(argv)
    state = State()

    if args.google_project:
        state.set("google_project", args.google_project)
        state.save(force=True)
        print(f"Google project: {args.google_project}")

    try:
        readme = playlist_path(args, state)
        if args.reply:
            args.files = [str(save_clip(last_reply(latest_transcript()), "reply"))]
            args.one = True
        elif args.clip:
            args.files = [str(save_clip(read_clipboard(), "clipboard"))]
            args.one = True
        elif args.files == ["-"]:
            args.files = [str(save_clip(read_stdin(), "input"))]
            args.one = True
    except (PlaylistError, ClipError, TranscriptError) as e:
        sys.exit(str(e))
    entries = read_playlist(readme)

    google = None if args.mac else Google.from_environment(state.get("google_project", ""))
    if google:
        voice = Voice(args.voice or state.get("voice") or DEFAULT_GOOGLE_VOICE, state, google=google)
    else:
        voice = Voice(args.voice or "", state, mac=True)

    if args.check is not None:
        targets = [Path(p) for p in args.check] or [e.path for e in entries]
        if not targets:
            sys.exit("Nothing to check: give files, or set a playlist with --playlist DIR.")
        check(targets)
        return
    if args.list:
        if not entries:
            sys.exit("No playlist set. Use --playlist DIR.")
        print_list(state, entries, bool(google))
        return
    if args.minutes:
        if readme is None:
            sys.exit("No playlist set. Use --playlist DIR.")
        total = update_minutes(readme)
        print(f"Updated {relative(readme)}: {total:,} words, about {minutes(total) / 60:.1f} hours at 1×.")
        return
    if args.export:
        paths = existing(args.files) if args.files else [e.path for e in entries]
        if not paths:
            sys.exit("Nothing to export: give files, use -r or -c, or set a playlist with --playlist DIR.")
        try:
            export_mp3([load(p) for p in paths], Path(args.export), voice, state)
        except ExportError as e:
            sys.exit(str(e))
        return
    if args.prepare is not None:
        if args.files:
            paths = existing(args.files)
        else:
            wanted = args.prepare
            paths = [e.path for e in entries if not wanted or any(part_matches(e.part, p) for p in wanted)]
        if not paths:
            sys.exit("Nothing to prepare: give files, use -r or -c, or set a playlist with --playlist DIR.")
        prepare(paths, voice, state)
        return

    if sys.platform != "darwin" and not args.mute:
        sys.exit("voce plays audio with macOS's own tools, so it needs a Mac for now.")
    for tool in ("afinfo", "say"):
        if not shutil.which(tool) and not args.mute:
            sys.exit(f"{tool} not found: voce needs macOS.")

    if args.quiz is not None:
        playlist, start, quiz_only = quizzes(args.quiz, entries), 0, True
    else:
        (playlist, start), quiz_only = choose(args, state, entries), False
    if args.start and not quiz_only:
        state.restart(playlist[start].path)

    from voce.ui.menu import menu
    from voce.ui.reader import Options, Reader
    from voce.ui.terminal import Terminal
    from voce.ui.theme import Theme

    message = "" if google or args.mac else "Using the Mac voice. Google's voices sound better: see voce --help."
    options = Options(one=args.one, quiz_only=quiz_only, speed=args.speed or state.get("speed", 1.0),
                      message=message)

    def next_voice(current: Voice) -> Voice | None:
        if current.mac or google is None:
            return None
        return Voice(next_google_voice(current.name), state, google=google)

    def session(scr) -> None:
        locale.setlocale(locale.LC_ALL, "")
        term, theme = Terminal(scr), Theme()
        term.start()
        theme.start()
        try:
            index = start
            if args.menu and len(playlist) > 1:
                choice = menu(term, theme, state, playlist, start)
                if choice is None:
                    return
                index = choice
            Reader(term, theme, options, state, voice, next_voice, player, playlist, index).run()
        finally:
            term.stop()

    def interrupted(*_) -> None:
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, interrupted)
    os.environ.setdefault("ESCDELAY", "25")
    player = make_player(mute=args.mute, afplay=args.afplay)
    try:
        curses.wrapper(session)
    except KeyboardInterrupt:
        pass
    finally:
        player.close()
        state.save(force=True)
    print("Your place is saved." + (f" Google characters this month: {state.month_chars():,} of "
                                     f"{FREE_CHARS:,} free." if google else ""))


if __name__ == "__main__":
    main()
