#!/usr/bin/env python3
"""Read a whole code base the way voce would and report what came out odd, so the speech rules can be fixed.

A corpus is a repository and the language its files are in, named in corpora.txt:

    laravel  https://github.com/laravel/framework.git  php  src

    .venv/bin/python docs/hearing/corpus.py laravel          # fetch it if need be, read it, write the reports
    .venv/bin/python docs/hearing/corpus.py ~/code/app --lang php
    .venv/bin/python docs/hearing/corpus.py laravel --grep 'static fn'   # just the lines that match, to the terminal

Every line goes through spoken_line and speakable, the same path as a fenced code block, and the reports go to
docs/hearing/.corpus/<name>/:

    transcript.txt  every line next to how it is read, grep this when a word in the other reports looks wrong
    unknown.tsv     spoken words that are not in the dictionary, most frequent first: abbreviations said raw,
                    names that should be split or spelt, symbols that fell through
    names.tsv       every name in the code and what it is said as, most frequent first
    strings.tsv     every string literal and what it is said as
    operators.tsv   every operator with the word before it and the word after, and what it is said as
    sample.txt      a few hundred lines at random, to read as a listener would hear them

Adding a framework is a line in corpora.txt. Adding a language is a file in speech/words/; its files are
found by extension through the same table of language aliases.
"""

from __future__ import annotations

import argparse
import random
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

from voce.speech import speakable, spoken_line
from voce.speech.code import _tokens  # the same tokeniser the reader uses, so the operator report matches it
from voce.speech.words import GENERIC, language

HERE = Path(__file__).resolve().parent
CORPORA = HERE / "corpora.txt"
CACHE = HERE / ".corpus"
DICTIONARY = Path("/usr/share/dict/words")


def read_corpora(path: Path = CORPORA) -> dict[str, tuple[str, str, str]]:
    """name -> (url, language, subdir) from corpora.txt."""
    out = {}
    for line in path.read_text().splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        name, url, lang, *rest = line.split()
        out[name] = (url, lang, rest[0] if rest else "")
    return out


def fetch(name: str, url: str) -> Path:
    repo = CACHE / name / "repo"
    if not (repo / ".git").exists():
        print(f"fetching {url} into {repo}", file=sys.stderr)
        repo.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "--depth", "1", "--quiet", url, str(repo)], check=True)
    return repo


def source_files(root: Path, lang: str) -> list[Path]:
    """The files under root whose extension is an alias of the language, or every known language's if none."""
    want = language(lang) if lang else None
    files = []
    for p in sorted(root.rglob("*")):
        parts = p.relative_to(root).parts
        if not p.is_file() or any(part.startswith(".") or part in ("vendor", "node_modules") for part in parts):
            continue
        if p.name.endswith(".blade.php"):
            continue  # a Blade view is mostly HTML, which has no rules yet
        found = language(p.suffix.lstrip("."))
        if found is GENERIC or (want and found is not want):
            continue
        files.append(p)
    return files


def words_in(spoken: str) -> list[str]:
    return [w.strip("'") for w in re.findall(r"[A-Za-z']+", spoken)]


def known(word: str, dictionary: set) -> bool:
    """In the dictionary, allowing for the plural, past tense and -ing that a word list leaves out."""
    w = word.lower()
    if len(word) == 1 or (word.isupper() and len(word) <= 4) or w in dictionary:
        return True
    for end, stem in (("ies", "y"), ("es", ""), ("s", ""), ("ed", ""), ("ed", "e"), ("ing", ""), ("ing", "e"),
                      ("ly", ""), ("er", ""), ("ers", ""), ("ness", "")):
        if w.endswith(end) and w[: -len(end)] + stem in dictionary:
            return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser(description="Read a code base the way voce would and report what came out odd.")
    ap.add_argument("corpus", help="a name from corpora.txt, or a directory")
    ap.add_argument("--lang", default="", help="the language the files are in, if not the corpus's own")
    ap.add_argument("--grep", default="", help="print only the lines matching this regex and how they are read")
    ap.add_argument("--sample", type=int, default=300, help="how many lines sample.txt holds")
    ap.add_argument("--seed", type=int, default=1)
    args = ap.parse_args()

    corpora = read_corpora() if CORPORA.exists() else {}
    if args.corpus in corpora:
        url, lang, subdir = corpora[args.corpus]
        root = fetch(args.corpus, url) / subdir
        name = args.corpus
    else:
        root = Path(args.corpus).expanduser().resolve()
        lang, name = "", root.name
        if not root.is_dir():
            print(f"{args.corpus} is neither a corpus in {CORPORA} nor a directory", file=sys.stderr)
            return 2
    lang = args.lang or lang
    files = source_files(root, lang)
    if not files:
        print(f"no {lang or 'source'} files under {root}", file=sys.stderr)
        return 1

    dictionary = set(DICTIONARY.read_text().lower().split()) if DICTIONARY.exists() else set()
    grep = re.compile(args.grep) if args.grep else None
    tokens = _tokens(language(lang).comments)

    transcript: list[str] = []
    unknown: Counter = Counter()
    unknown_where: dict[str, str] = {}
    names: Counter = Counter()
    name_said: dict[str, str] = {}
    strings: Counter = Counter()
    string_said: dict[str, str] = {}
    ops: Counter = Counter()
    op_said: dict[tuple, str] = {}
    total = 0

    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        rel = path.relative_to(root)
        for n, line in enumerate(text.split("\n"), 1):
            if not line.strip():
                continue
            said = speakable(spoken_line(line, lang))
            total += 1
            if grep:
                if grep.search(line):
                    print(f"{rel}:{n}: {line.strip()}\n    => {said}")
                continue
            transcript.append(f"{rel}:{n}\t{line.strip()}\t{said}")
            for w in words_in(said):
                if w and not known(w, dictionary):
                    unknown[w] += 1
                    unknown_where.setdefault(w, f"{line.strip()}  =>  {said}")
            if re.match(r"\s*(/\*|\*)", line):
                continue  # a doc comment's lines are prose, not operators
            kinds = [(m.lastgroup, m.group()) for m in tokens.finditer(line) if m.lastgroup != "space"]
            for i, (kind, tok) in enumerate(kinds):
                if kind in ("name", "var"):
                    bare = tok.lstrip("$")
                    names[bare] += 1
                    if bare not in name_said:
                        name_said[bare] = speakable(spoken_line(tok, lang))
                elif kind == "string":
                    strings[tok] += 1
                    if tok not in string_said:
                        string_said[tok] = speakable(spoken_line(tok, lang))
                elif kind == "op":
                    before = kinds[i - 1][1] if i else ""
                    after = kinds[i + 1][1] if i + 1 < len(kinds) else ""
                    key = (tok, before, after)
                    ops[key] += 1
                    if key not in op_said:
                        op_said[key] = speakable(spoken_line(f"{before} {tok} {after}".strip(), lang))
                if kind == "comment":
                    break

    if grep:
        return 0
    out = CACHE / name
    out.mkdir(parents=True, exist_ok=True)
    (out / "transcript.txt").write_text("\n".join(transcript) + "\n")
    (out / "unknown.tsv").write_text("".join(
        f"{w}\t{c}\t{unknown_where[w]}\n" for w, c in unknown.most_common()))
    (out / "names.tsv").write_text("".join(
        f"{w}\t{c}\t{name_said[w]}\n" for w, c in names.most_common()))
    (out / "strings.tsv").write_text("".join(
        f"{s}\t{c}\t{string_said[s]}\n" for s, c in strings.most_common()))
    by_op: dict[str, Counter] = defaultdict(Counter)
    for (tok, before, after), c in ops.items():
        by_op[tok][(before, after)] += c
    with (out / "operators.tsv").open("w") as f:
        for tok, contexts in sorted(by_op.items(), key=lambda kv: -sum(kv[1].values())):
            for (before, after), c in contexts.most_common(12):
                f.write(f"{tok}\t{c}\t{before} {tok} {after}\t{op_said[(tok, before, after)]}\n")
    random.seed(args.seed)
    picked = random.sample(transcript, min(args.sample, len(transcript)))
    (out / "sample.txt").write_text("".join(
        f"{where}\n    {line}\n    => {said}\n\n" for where, line, said in (t.split("\t") for t in picked)))
    print(f"{len(files)} files, {total} lines, {len(unknown)} unknown words -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
