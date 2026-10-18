"""The voce command: the arguments, then which of the sources to read and which command to run with it.

    parser()   the arguments
    main()     the command: sources (sources/), then one of the printing commands (commands.py) or the reader
               (ui/session.py)
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from voce import __version__, commands, sources
from voce.document import load
from voce.export import ExportError
from voce.player import make_player
from voce.playlist import Entry, PlaylistError, find_playlist, part_matches, read_playlist
from voce.sources.github import looks_like_pull_request
from voce.state import State
from voce.voices import DEFAULT_GOOGLE_VOICE, FREE_CHARS, Google, Voice, next_google_voice

USAGE = """\
examples:
  voce --pr https://github.com/owner/repo/pull/12   review a pull request by ear: its description, each
                                                      file's diff and the conversation, read and highlighted
  voce --pr 12             the same, for pull request 12 of the repository this folder is a clone of
  voce notes.md            read a Markdown file, from where you left off
  voce -r                  read Claude Code's latest reply in this folder (run it in another terminal)
  voce -c                  read what's on the clipboard
  pbpaste | voce -         read standard input
  voce a.md b.md --export walk.mp3   one MP3 for a walk, with the same voice and pauses
  voce                     carry on where you left off: your playlist, or the last thing you read
  voce --playlist DIR      use DIR/README.md's "Listen in this order" list from now on
  voce --menu              choose a file from the playlist

keys:
  space pause · ←/→ sentence · ↑/↓ paragraph · [ ] section or file · +/- speed
  n/p next or previous file · v voice · m menu · r restart · q quit (your place is saved)
  click a sentence or a line of code to jump to it · drag to copy · the wheel scrolls

voices:
  The Mac's own voice works out of the box. For Google's Chirp 3 HD voices, set VOCE_GOOGLE_API_KEY, or sign
  in with gcloud and pass --google-project once. Every sentence is fetched once and kept.

pull requests:
  Private repositories work when gh is signed in (gh auth login) or GITHUB_TOKEN is set. Running the same
  --pr again fetches the latest version and keeps your place in it.

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
        prog="voce", description="Read Markdown and pull requests aloud in your terminal, highlighting each "
                                 "sentence and word.",
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=USAGE)
    ap.add_argument("files", nargs="*", metavar="FILE",
                    help="Markdown files to read, a pull request URL, or - for standard input")
    ap.add_argument("--pr", metavar="PR",
                    help="a GitHub pull request: a URL, owner/repo#12, or 12 for this folder's repository")
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
    voice.add_argument("--voice", metavar="NAME",
                       help=f"a Google voice such as {DEFAULT_GOOGLE_VOICE}, or a Mac voice name with --mac")
    voice.add_argument("--mac", action="store_true", help="use the Mac's voice even when Google is set up")
    voice.add_argument("--google-project", metavar="ID", help="the Google Cloud project to bill (saved)")
    voice.add_argument("--prepare", nargs="*", metavar="PART",
                       help="fetch the voice ahead of time: for the files given, or the playlist (or these parts)")

    tools = ap.add_argument_group("other")
    tools.add_argument("--export", metavar="OUT.mp3",
                       help="write the files (or reply, clipboard, pull request or playlist) as one MP3")
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
        sys.exit("Nothing to read yet. Give a Markdown file, a pull request with --pr, use -r for Claude Code's "
                 "latest reply or -c for the clipboard, or set a playlist with --playlist DIR. See voce --help.")
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


def pick_voice(args, state: State) -> tuple[Voice, Google | None]:
    google = None if args.mac else Google.from_environment(state.get("google_project", ""))
    if google:
        return Voice(args.voice or state.get("voice") or DEFAULT_GOOGLE_VOICE, state, google=google), google
    return Voice(args.voice or "", state, mac=True), None


def needs_mac(args) -> None:
    if args.mute:
        return
    if sys.platform != "darwin":
        sys.exit("voce plays audio with macOS's own tools, so it needs a Mac for now.")
    for tool in ("afinfo", "say"):
        if not shutil.which(tool):
            sys.exit(f"{tool} not found: voce needs macOS.")


# ---------------------------------------------------------------- main

def main(argv: list[str] | None = None) -> None:
    args = parser().parse_args(argv)
    state = State()

    if args.google_project:
        state.set("google_project", args.google_project)
        state.save(force=True)
        print(f"Google project: {args.google_project}")

    for words in (args.files, args.check or []):
        if len(words) == 1 and not args.pr and looks_like_pull_request(words[0]):
            args.pr = words.pop()  # voce https://github.com/o/r/pull/12 needs no --pr
    try:
        readme = playlist_path(args, state)
        source = sources.resolve(args)
    except (PlaylistError, sources.SourceError) as e:
        sys.exit(str(e))
    if source is not None:
        args.files, args.one = [str(source)], True
    entries = read_playlist(readme)
    voice, google = pick_voice(args, state)

    if args.check is not None:
        targets = [Path(p) for p in args.check] or [Path(f) for f in args.files] or [e.path for e in entries]
        if not targets:
            sys.exit("Nothing to check: give files, or set a playlist with --playlist DIR.")
        commands.check(targets, args.skip_code)
        return
    if args.list:
        if not entries:
            sys.exit("No playlist set. Use --playlist DIR.")
        commands.print_list(state, entries, bool(google))
        return
    if args.minutes:
        if readme is None:
            sys.exit("No playlist set. Use --playlist DIR.")
        commands.print_minutes(readme)
        return
    if args.export:
        paths = existing(args.files) if args.files else [e.path for e in entries]
        if not paths:
            sys.exit("Nothing to export: give files, use -r, -c or --pr, or set a playlist with --playlist DIR.")
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
            sys.exit("Nothing to prepare: give files, use -r, -c or --pr, or set a playlist with --playlist DIR.")
        commands.prepare(paths, voice, state)
        return

    needs_mac(args)
    if args.quiz is not None:
        playlist, start, quiz_only = quizzes(args.quiz, entries), 0, True
    else:
        (playlist, start), quiz_only = choose(args, state, entries), False
    if args.start and not quiz_only:
        state.restart(playlist[start].path)

    from voce.ui.reader import Options
    from voce.ui.session import play

    message = "" if google or args.mac else "Using the Mac voice. Google's voices sound better: see voce --help."
    options = Options(one=args.one, quiz_only=quiz_only, skip_code=args.skip_code,
                      speed=args.speed or state.get("speed", 1.0), message=message)

    def next_voice(current: Voice) -> Voice | None:
        if current.mac or google is None:
            return None
        return Voice(next_google_voice(current.name), state, google=google)

    player = make_player(mute=args.mute, afplay=args.afplay)
    play(playlist, start, options, state, voice, next_voice, player, show_menu=args.menu)
    print("Your place is saved." + (f" Google characters this month: {state.month_chars():,} of "
                                     f"{FREE_CHARS:,} free." if google else ""))


if __name__ == "__main__":
    main()
