"""The voce command: the arguments, then which of the sources to read and which command to run with it.

    parser()   the arguments
    main()     the command: sources (sources/), then one of the printing commands (commands.py) or the reader
               (ui/session.py)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from voce import __version__, commands, sources, sync, voices
from voce.document import load
from voce.export import ExportError
from voce.player import find_players, make_player
from voce.playlist import Entry, PlaylistError, find_playlist, part_matches, read_playlist
from voce.state import State
from voce.voices import ENGINES, Voice

USAGE = """\
examples:
  voce notes.md            read a Markdown file, from where you left off
  voce -r                  read Claude Code's latest reply in this folder (run it in another terminal)
  voce -c                  read what's on the clipboard
  cat notes.md | voce -    read standard input
  voce a.md b.md --export walk.mp3   one MP3 for a walk, with the same voice and pauses
  voce                     carry on where you left off: your playlist, or the last thing you read
  voce --playlist DIR      use DIR/README.md's "Listen in this order" list from now on
  voce --menu              choose a file from the playlist
  voce --sync you/voce     keep your places and documents in a private GitHub repository, for other devices

keys:
  space pause · ←/→ sentence · ↑/↓ paragraph · [ ] section or file · +/- speed
  n/p next or previous file · v voice · V engine · m menu · r restart · q quit (your place is saved)
  click a sentence or a line of code to jump to it · drag to copy · the wheel scrolls

voices:
  Kokoro, a small open voice, runs on your computer, works out of the box and costs nothing. On a Mac, the
  Mac's own voices are there too. Nothing you read is sent anywhere. Every sentence is made once and kept.

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
    ap.add_argument("--skip-code", action="store_true", help="show code blocks and diffs without reading them")
    ap.add_argument("--speed", type=speed, metavar="X", help="playback speed from 0.5 to 3, for example 1.2")

    playlist = ap.add_argument_group("playlists")
    playlist.add_argument("--playlist", metavar="DIR", help="use this folder's README.md playlist from now on")
    playlist.add_argument("--menu", action="store_true", help="choose a file from the playlist first")
    playlist.add_argument("--list", action="store_true", help="print the playlist with your progress")
    playlist.add_argument("--quiz", nargs="?", const="", metavar="PART",
                          help="quizzes only: all of them, one part (number or name) or a file")
    playlist.add_argument("--minutes", action="store_true", help="update the minutes in the playlist README")

    voice = ap.add_argument_group("voices")
    voice.add_argument("--engine", choices=list(ENGINES), metavar="ENGINE",
                       help="which voices to use: kokoro or mac (saved)")
    voice.add_argument("--voice", metavar="NAME",
                       help="a voice, such as af_heart, bm_george or Daniel; the engine follows from the name (saved)")
    voice.add_argument("--mac", action="store_true", help="the same as --engine mac")
    voice.add_argument("--voices", action="store_true", help="show the engines, which are set up, and their voices")
    voice.add_argument("--prepare", nargs="*", metavar="PART",
                       help="fetch the voice ahead of time: for the files given, or the playlist (or these parts)")

    tools = ap.add_argument_group("other")
    tools.add_argument("--export", metavar="OUT.mp3",
                       help="write the files (or reply, clipboard or playlist) as one MP3 instead of playing")
    tools.add_argument("--check", nargs="*", metavar="FILE",
                       help="report how files will read, without audio (default: the playlist)")
    tools.add_argument("--sync", nargs="?", const="", metavar="REPO",
                       help="push your places and prepared documents to a git repository and pull the other "
                            "devices'; give OWNER/REPO or a git URL the first time")
    tools.add_argument("--plain-player", "--afplay", dest="plain", action="store_true",
                       help="play one sentence at a time with afplay, mpv or ffplay, not the built-in player")
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
    from voce.document import quiz_pairs

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


def pick_voice(args, state: State) -> Voice:
    """The engine asked for, or the one a voice name belongs to, or the one used last time, or the best set up."""
    kind = args.engine or ("mac" if args.mac else "")
    if not kind and args.voice:
        kind = voices.engine_for(args.voice, state)
    if not kind:
        kind = voices.default_engine(state)
    if not ENGINES[kind].configured(state):
        sys.exit(f"{ENGINES[kind].title} isn't set up. {ENGINES[kind].setup}")
    voice = voices.make(kind, args.voice or "", state)
    if args.engine or args.voice or args.mac:
        voices.remember(state, voice)
        state.save(force=True)
    return voice


def needs_player(args) -> None:
    if args.mute or find_players():
        return
    if sys.platform == "darwin":
        sys.exit("afplay not found: voce plays audio with macOS's own tools.")
    sys.exit("No audio player found. Install mpv (or ffmpeg, for ffplay), for example: sudo apt install mpv")


# ---------------------------------------------------------------- syncing

def pull_places(state: State) -> None:
    """Before anything else, the other devices' places, when syncing is set up. Being offline is not an error."""
    if not state.get("sync") or not sync.ready(state.root):
        return
    try:
        if sync.pull(state.root, timeout=15):
            state.__init__(state.root)  # the files changed under us
    except sync.SyncError as e:
        print(f"Couldn't pull your places: {e}")


def push_places(state: State) -> None:
    if not state.get("sync") or not sync.ready(state.root):
        return
    try:
        if sync.commit(state.root):
            sync.pull(state.root, timeout=15)
            sync.push(state.root, timeout=30)
            print("Synced.")
    except sync.SyncError as e:
        print(f"Couldn't sync your places: {e}")


# ---------------------------------------------------------------- main

def main(argv: list[str] | None = None) -> None:
    args = parser().parse_args(argv)
    state = State()

    try:
        readme = playlist_path(args, state)
        source = sources.resolve(args)
    except (PlaylistError, sources.SourceError) as e:
        sys.exit(str(e))
    if source is not None:
        args.files, args.one = [str(source)], True
    entries = read_playlist(readme)
    if args.sync is not None:
        try:
            commands.sync_up(state, entries, args.sync)
        except sync.SyncError as e:
            sys.exit(f"Sync failed: {e}")
        return
    pull_places(state)
    if args.voices:
        commands.print_voices(state)
        return
    voice = pick_voice(args, state)

    if args.check is not None:
        targets = [Path(p) for p in args.check] or [Path(f) for f in args.files] or [e.path for e in entries]
        if not targets:
            sys.exit("Nothing to check: give files, or set a playlist with --playlist DIR.")
        commands.check(targets, args.skip_code)
        return
    if args.list:
        if not entries:
            sys.exit("No playlist set. Use --playlist DIR.")
        commands.print_list(state, entries, voice)
        return
    if args.minutes:
        if readme is None:
            sys.exit("No playlist set. Use --playlist DIR.")
        commands.print_minutes(readme)
        return
    if args.export:
        paths = existing(args.files) if args.files else [e.path for e in entries]
        if not paths:
            sys.exit("Nothing to export: give files, use -r or -c, or set a playlist with --playlist DIR.")
        try:
            commands.export(paths, Path(args.export), voice, state, args.skip_code)
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
        commands.prepare(paths, voice, state, entries)
        push_places(state)
        return

    needs_player(args)
    try:
        voice.engine.prepare(print)
    except RuntimeError as e:
        if not ENGINES["mac"].configured(state):
            sys.exit(str(e))
        print(f"{e}. Using the Mac voice for now.")
        voice = voices.make("mac", "", state)
    if args.quiz is not None:
        playlist, start, quiz_only = quizzes(args.quiz, entries), 0, True
    else:
        (playlist, start), quiz_only = choose(args, state, entries), False
    if args.start and not quiz_only:
        state.restart(playlist[start].path)

    from voce.ui.reader import Options
    from voce.ui.session import play

    message = "" if voice.kind != "mac" or args.mac else \
        "Using the Mac voice; voce --voices shows the better ones."
    options = Options(one=args.one, quiz_only=quiz_only, skip_code=args.skip_code,
                      speed=args.speed or state.get("speed", 1.0), message=message)

    def switch(current: Voice, what: str) -> Voice | None:
        """The next voice of the same engine, or (what == "engine") the same voice family on the next engine."""
        if what == "voice":
            name = current.engine.next_name()
            return None if name == current.name else voices.make(current.kind, name, state)
        kinds = voices.available(state)
        kind = kinds[(kinds.index(current.kind) + 1) % len(kinds)] if current.kind in kinds else kinds[0]
        return None if kind == current.kind else voices.make(kind, "", state)

    player = make_player(mute=args.mute, plain=args.plain)
    play(playlist, start, options, state, voice, switch, player, show_menu=args.menu)
    print("Your place is saved.")
    push_places(state)


if __name__ == "__main__":
    main()
