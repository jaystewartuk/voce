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
- **Add a test** for any change to parsing, sentence splitting, layout or the transcript reader.
- **Write for people.** Messages, help text and docs use plain words and short sentences.

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
