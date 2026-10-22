# Working on voce with a coding agent

This file is for Claude Code, Codex, Cursor and other agents, and for the people driving them. Read it before
changing anything. [docs/architecture.md](docs/architecture.md) explains the design in full, and
[CONTRIBUTING.md](CONTRIBUTING.md) has the human version of the same rules.

## What voce is

A terminal app that reads Markdown aloud, highlighting each sentence and word as it is spoken, and reads code the
way a person says it out loud. Python 3.9+, one runtime dependency (Pygments), plus Kokoro for the local voice.
It runs on macOS and Linux; the UI is plain `curses`.

## Set up, check, test

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/ruff check .          # must pass
.venv/bin/pytest                # must pass; fast, no network, never touches real state
.venv/bin/voce --check README.md   # how a file will read, with no audio: a quick end-to-end check
```

CI runs ruff and pytest on macOS and Linux, on Python 3.9 and 3.13. Write code that runs on 3.9
(`from __future__ import annotations` is used throughout).

## Where things are

- `src/voce/speech/words/`: how code is read, as data. `common.py` for every language, then a file per
  language (`php.py`, `python.py`, ...), each naming the manual its operator names come from. **Most feature requests about how
  something sounds belong here.**
- `src/voce/speech/code.py`: the tokeniser that turns a line of code into words.
- `src/voce/speech/prose.py`, `sentences.py`: prose rewrites and sentence splitting.
- `src/voce/markdown/`: Markdown into blocks of plain text with styled spans.
- `src/voce/document.py`: blocks into units to say (sentences, code lines, table rows, diff hunks).
- `src/voce/voices.py`: the voice engines and the audio cache. `player.py`: playback.
- `src/voce/ui/`: the curses reader. `reader.py` is the state machine, `view.py` the layout and mouse.
- `src/voce/sources/`: where text comes from (Claude Code transcripts, clipboard, stdin).
- `site/`: the website and the web app (static, no build step). `relay/`: the web app's sign-in relay.

## Rules that keep voce working

- **One plain text per block.** Every block has a single `text` that is shown, spoken and highlighted; styles are
  spans over it. New Markdown features must fit that shape.
- **Keep the spoken text stable.** Audio is cached by the exact text sent to the voice. Changing what
  `speech.speakable` produces, or how blocks are split into units, makes every user fetch audio again. Do it only
  when it makes the reading better, and say so in the pull request.
- **Use the manual's own names.** Operators are named as the language's official docs name them (the PHP
  manual's "identical", MDN's "strict equality"), not nicknames.
- **No network in tests.** Stand in for engines, `gh`, `git` remotes and the clipboard. Tests use `tmp_path`
  and never touch `~/.local/state/voce` or `~/.cache/voce`.
- **No new runtime dependencies** without a strong reason. Standard library first.
- **Write for people.** Messages, help and docs use plain words and short sentences. Error messages say what
  to do next.
- **Add a test** for any change to parsing, splitting, code reading, layout, a source or the reader.

## Adding a language

A good first change. Add `src/voce/speech/words/ruby.py` with a `Language`: its comment markers, the words it
says differently, its operator names, its fence names and the manual the names come from. Then add it to `ALL`
in `words/__init__.py`:

```python
RUBY = Language("ruby", comments=("#",), words={"attr_accessor": "attribute accessor"},
                operators={"=>": "hash rocket", "<=>": "spaceship", "&.": "safe navigation"},
                aliases=("ruby", "rb"), manual="https://docs.ruby-lang.org/en/master/syntax/operators_rdoc.html")
```

If the language has an operator the tokeniser doesn't know, add it to the `op` alternation in
`speech/code.py`. Then add cases to `tests/test_speech.py`: a line of code and exactly how it should sound. To
find what reads badly, run real code through it:

```bash
.venv/bin/python -c "from voce.speech.code import spoken_line; from voce.speech.words import language; \
print(spoken_line('puts user&.name', language('ruby')))"
```

`docs/hearing/corpus.py` does the same over a whole repository of real code.

## Pull requests

Keep each one to one change, with a commit message that says what a user notices. Run ruff and pytest
first. Don't commit generated audio, caches or anything under `.venv`.
