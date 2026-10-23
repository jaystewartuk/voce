"""The shell's own words, named as the GNU Bash Reference Manual names them: ``|`` is "pipe" (a pipeline's
commands are "connected via a pipe"), ``<<<`` is "here string", ``-eq`` is "is equal to"."""

from __future__ import annotations

from voce.speech.words.common import Language

# The Bash manual: https://www.gnu.org/software/bash/manual/bash.html. Sections cited below by name.
SHELL = Language("shell", comments=("#",), words={
    "cd": "C D", "ls": "L S", "rm": "R M", "mv": "move", "cp": "copy", "mkdir": "make dir", "chmod": "C H mod",
    "sudo": "sudo", "grep": "grep", "sed": "sed", "awk": "awk", "ssh": "S S H", "pwd": "P W D",
    # Reserved Words that read badly as written: the voice says "fi" as "fie" and "esac" as a made-up word.
    "elif": "else if", "fi": "end if", "esac": "end case",
    # Bash Conditional Expressions: -eq, -ne, -lt, -le, -gt and -ge, by letter while the tokeniser splits them.
    "eq": "E Q", "ne": "N E", "lt": "L T", "le": "L E", "gt": "G T", "ge": "G E",
    # The POSIX utilities and coreutils, said the way people say them.
    "rmdir": "remove dir", "chown": "C H own", "chgrp": "C H group", "ln": "L N", "wc": "W C", "tr": "T R",
    "df": "D F", "du": "D U", "ps": "P S", "xargs": "X args", "nohup": "no hup", "dirname": "dir name",
    "basename": "base name", "mktemp": "make temp", "readlink": "read link", "realpath": "real path",
    "readonly": "read only", "getopts": "get opts", "pushd": "push D", "popd": "pop D", "fg": "F G", "bg": "B G",
    "uname": "U name", "whoami": "who am I", "umask": "U mask", "ulimit": "U limit", "pkill": "P kill",
    "pgrep": "P grep", "egrep": "E grep", "fgrep": "F grep", "wget": "W get", "scp": "S C P", "rsync": "R sync",
    "jq": "J Q", "dpkg": "D P K G", "rpm": "R P M", "npm": "N P M", "npx": "N P X", "nvm": "N V M",
    "systemctl": "system C T L", "journalctl": "journal C T L", "vi": "V I", "md5sum": "M D 5 sum",
    "sh": "S H", "zsh": "Z S H", "bashrc": "bash R C", "zshrc": "Z S H R C", "zle": "Z L E",
    "zstyle": "Z style", "zmodload": "Z mod load", "setopt": "set opt", "compdef": "comp def",
    "compadd": "comp add", "bindkey": "bind key",
    "usr": "user", "sbin": "S bin", "tty": "T T Y", "stdin": "standard in", "stdout": "standard out",
    "stderr": "standard error", "ifs": "I F S", "pid": "P I D", "uid": "U I D", "gid": "G I D",
    # Flags people say by letter: rm -rf, curl -fsSL, tar -xzf.
    "rf": "R F", "fsSL": "F S S L", "xzf": "X Z F", "xvf": "X V F", "czf": "C Z F", "xf": "X F",
}, operators={
    # Pipelines: "connected via a pipe". Lists of Commands: AND and OR lists, said as what they do.
    "|": "pipe", "&&": "and then", "||": "or else",
    # Redirections: Redirecting Output, Appending Redirected Output, Redirecting Input, Here Strings.
    ">": "to", ">>": "appended to", "<": "from", "<<<": "here string",
    # An option's leading hyphen. The manual says "dash" once (exec) and "hyphen" once ($-); people say dash: rm -rf.
    "-": "dash", "--": "dash dash",
    # Paths, not division: /dev/null, https://. A glob's * (Filename Expansion), printf's and ${x%.txt}'s %.
    "/": "slash", "//": "slash slash", "*": "asterisk", "%": "percent",
    # [ is the test builtin and [[ the conditional command: silent, like every bracket.
    "[": "",
    # These need the tokeniser to know them first (see the report); named here so they work once it does.
    "<<": "here document", "<<-": "here document",                      # Here Documents
    "&>": "standard output and standard error to",                       # Redirecting Standard Output and ...
    "&>>": "standard output and standard error appended to",             # Appending Standard Output and ...
    "2>": "standard error to", "2>>": "standard error appended to",
    "2>&1": "standard error to standard output", ">&2": "to standard error",  # Duplicating File Descriptors
    "1>&2": "to standard error",
    ":=": "assign default",                                              # Shell Parameter Expansion: ${x:=word}
    "=~": "matches",                                                     # Conditional Constructs: [[ =~ ]]
    "-eq": "is equal to", "-ne": "is not equal to", "-lt": "is less than",  # Bash Conditional Expressions
    "-le": "is less than or equal to", "-gt": "is greater than", "-ge": "is greater than or equal to",
    "$(": "the output of", "$((": "the result of", "${": "",            # Command Substitution, Arithmetic ...
    "$?": "the exit status", "$#": "the number of arguments",           # Special Parameters
    "$@": "the arguments", "$*": "the arguments", "$$": "the process I D", "$!": "the background process I D",
}, aliases=("bash", "sh", "shell", "zsh", "console", "terminal"),
    manual="https://www.gnu.org/software/bash/manual/bash.html")
