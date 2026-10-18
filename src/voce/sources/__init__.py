"""Where the text to read comes from, besides Markdown files on disk.

Each source turns something else into a Markdown file in voce's state folder, so the reader, --check, --export
and your saved place all work the same way whatever the text came from:

    claude.py        Claude Code's latest reply, from its session transcript
    clips.py         the clipboard and standard input
    github.py        a pull request on GitHub, fetched through the API
    pullrequest.py   that pull request written as Markdown, with its diff

Every source raises a SourceError, with a message for the user, when it has nothing to give.
"""

from __future__ import annotations


class SourceError(Exception):
    """A source could not be read; the message is written for the person at the keyboard."""
