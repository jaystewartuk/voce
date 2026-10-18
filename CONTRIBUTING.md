# Contributing to voce

Thank you for helping. Bug reports, ideas and pull requests are all welcome.

## Set up

```bash
git clone https://github.com/jaystewartuk/voce
cd voce
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/voce README.md
```

## Before you open a pull request

```bash
.venv/bin/ruff check .
.venv/bin/pytest
```

Both run in CI on macOS and Linux. The tests never touch your real state or cache, and never call Google.

Some guidelines:

- **Keep the plain-text model.** Every block has one plain `text` that is shown, spoken and highlighted; styles
  are spans over it. New Markdown features should fit that shape. See [docs/architecture.md](docs/architecture.md).
- **Keep the voice's text stable.** Audio is cached by the exact text sent to the voice. A change to
  `speech.speakable` or to how blocks are split makes everyone re-fetch audio, so make such changes on purpose.
- **Add a test** for any change to parsing, sentence splitting, code reading, layout, a source or the reader.
- **Write for people.** Messages, help text and docs use plain words and short sentences.

## Adding a language

How code is read is data in `src/voce/speech/words.py`. A language is a `Language` with the words it says
differently from the common ones, its operator names, and how its comments start:

```python
RUBY = Language("ruby", comments=("#",), words={"attr_accessor": "attribute accessor", "puts": "puts"},
                operators={"=>": "hash rocket", "<=>": "spaceship", "&.": "safe navigation"})
```

Then add its fence labels and Pygments aliases to `LANGUAGES` (`"ruby": RUBY, "rb": RUBY`). Code fences, diffs
of `.rb` files and inline code in documents about Ruby will use it. If the language has an operator the
tokeniser in `speech/code.py` doesn't know, add it to the `op` alternation there. Use the names from the
language's own manual, and add a line to `tests/test_speech.py` with a line of code and how it should sound.

## Adding a source

A source is a module in `src/voce/sources/` that turns something into a Markdown file and raises a `SourceError`
when it can't. `sources.resolve` is the one place the command line is turned into a file; add a flag to
`cli.parser` and a branch there. Keep the code that talks to the outside world apart from the code that writes
the Markdown, and stand the outside world in for in tests so none of them needs the network.

## Re-recording the demo

The GIF in the README and the screenshot are made with [vhs](https://github.com/charmbracelet/vhs):

```bash
brew install vhs
docs/demo/record.sh
```

The script reads `docs/demo/reply.md` through a throwaway Claude Code transcript, with empty state and cache
folders, so nothing from your machine appears in the recording.

## Checking what the voice says

Voices misread some text: Google turns "PHP 8" into "eight Philippine pesos". `speech.speakable` rewrites such
text before it is spoken, and `docs/hearing/check.py` checks those rewrites by ear: it fetches each phrase in
`docs/hearing/phrases.txt` from the real voice, transcribes it with whisper.cpp and compares.

```bash
brew install whisper-cpp ffmpeg
curl -LO https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin
.venv/bin/python docs/hearing/check.py --model ggml-base.en.bin
```

Run it with `--raw` to hear the text as written, which is how to confirm a misreading before adding a rewrite.
It uses your Google voice and counts towards your monthly characters, so it is not part of the test suite.

## The website

The site in `site/` is a single static page with no build step. Open `site/index.html` in a browser to work on it.
It is published to GitHub Pages by `.github/workflows/pages.yml` on every push to `main` that touches `site/`.

## Releasing

1. Update `__version__` in `src/voce/__init__.py` and add a section to `CHANGELOG.md`.
2. Commit, then tag: `git tag v0.2.0 && git push --tags`.
3. Create a GitHub release from the tag with the changelog section as its notes.
