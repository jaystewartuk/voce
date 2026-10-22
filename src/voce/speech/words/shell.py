"""The shell's own words: ``|`` is "pipe", ``&&`` is "and then"."""

from __future__ import annotations

from voce.speech.words.common import Language

SHELL = Language("shell", comments=("#",), words={
    "cd": "C D", "ls": "L S", "rm": "R M", "mv": "move", "cp": "copy", "mkdir": "make dir", "chmod": "C H mod",
    "sudo": "sudo", "grep": "grep", "sed": "sed", "awk": "awk", "ssh": "S S H", "pwd": "P W D",
}, operators={"|": "pipe", "&&": "and then", "||": "or else", ">": "to", ">>": "appended to", "<": "from"},
    aliases=("bash", "sh", "shell", "zsh", "console", "terminal"),
    manual="https://www.gnu.org/software/bash/manual/bash.html")
