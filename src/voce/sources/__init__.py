"""Where the text to read comes from, besides Markdown files on disk.

Each source turns something else into a Markdown file in voce's state folder, so the reader, --check, --export
and your saved place all work the same way whatever the text came from:

    claude.py        Claude Code's latest reply, from its session transcript
    clips.py         the clipboard and standard input

Every source raises a SourceError, with a message for the user, when it has nothing to give.
"""

from __future__ import annotations

from pathlib import Path


class SourceError(Exception):
    """A source could not be read; the message is written for the person at the keyboard."""


def resolve(args) -> Path | None:
    """The Markdown file for the one-off source the command line asks for, or None when it names files or nothing.

    ``args`` is the parsed command line: ``reply`` (-r), ``clip`` (-c) and ``files == ["-"]``.
    """
    from voce.sources.claude import last_reply, latest_transcript
    from voce.sources.clips import read_clipboard, read_stdin, save_clip

    if args.reply:
        return save_clip(last_reply(latest_transcript()), "reply")
    if args.clip:
        return save_clip(read_clipboard(), "clipboard")
    if args.files == ["-"]:
        return save_clip(read_stdin(), "input")
    return None
