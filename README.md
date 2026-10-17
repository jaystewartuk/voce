<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/assets/wordmark-dark.svg">
    <img src="docs/assets/wordmark-light.svg" alt="voce" width="300">
  </picture>
</p>

<p align="center">
  <strong>Read Markdown aloud in your terminal.</strong><br>
  Each sentence lights up as it is read, and each word as it is spoken.
</p>

<p align="center">
  <a href="https://github.com/jaystewartuk/voce/actions/workflows/ci.yml"><img src="https://github.com/jaystewartuk/voce/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <img src="https://img.shields.io/badge/python-3.9%2B-2f6feb" alt="Python 3.9+">
  <img src="https://img.shields.io/badge/platform-macOS-2f6feb" alt="macOS">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-2f6feb" alt="MIT licence"></a>
</p>

<p align="center">
  <a href="https://jaystewartuk.github.io/voce/">Website</a> ·
  <a href="#install">Install</a> ·
  <a href="#use-it-with-claude-code">Claude Code</a> ·
  <a href="#voices">Voices</a> ·
  <a href="docs/playlists.md">Playlists</a>
</p>

<p align="center">
  <img src="docs/assets/demo.gif" alt="voce reading a Claude Code reply: the sentence being read is on a pale blue band, the word being spoken on a dark blue one, code is syntax highlighted and the table is lined up" width="860">
</p>

voce (Italian for "voice", said *VOH-chay*) reads Markdown to you in the terminal. It shows the page as it should
look, with headings, bold, links, highlighted code and lined-up tables. It reads only the prose, so you can look
away, follow along, or jump around with the keyboard or the mouse.

It was built to listen to long Claude Code replies and study notes, but it reads any Markdown.

- **Reads what a person would read.** Markup is never spoken. Code blocks are shown with syntax highlighting but
  not read. Tables are read row by row, and links by their text.
- **Follows along.** The sentence being read sits on a pale band, and the word being spoken on a darker one. The
  page scrolls to keep your place, and a click on any sentence jumps there.
- **Knows Claude Code.** `voce -r` reads Claude's latest reply in the folder you are in, with no copying.
- **Keeps your place.** Quit at any point and it starts from the same sentence next time, even if the file has
  changed. It also reloads a file when it changes on disk.
- **Sounds good, costs little.** It uses the Mac's own voices out of the box, or Google's Chirp 3 HD voices if you
  set them up. Every sentence is fetched once and cached, so listening again is free and works offline.
- **Goes with you.** `--export` turns files into one MP3 with the same voice and pauses, for a walk or a drive.

## Install

You need macOS and Python 3.9 or newer.

```bash
uv tool install git+https://github.com/jaystewartuk/voce
# or
pipx install git+https://github.com/jaystewartuk/voce
```

Then try it:

```bash
voce README.md
```

Two optional extras make it better:

- **The Xcode command line tools** (`xcode-select --install`) let voce build its small native audio player the
  first time it runs. You get gapless playback, a pause that keeps your place mid-word, and a word highlight that
  stays in time. Without them it falls back to `afplay`.
- **ffmpeg** (`brew install ffmpeg`) is needed for `--export`.

## Use it

```bash
voce notes.md              # read a file, from where you left off
voce a.md b.md             # read several files in a row
voce -r                    # read Claude Code's latest reply in this folder
voce -c                    # read what is on the clipboard
pbpaste | voce -           # read standard input
voce                       # carry on with whatever you were last reading
voce --start notes.md      # start again from the top
voce notes.md --export notes.mp3   # one MP3 to take with you
voce --check notes.md      # how it will read: sentences, minutes, characters
```

### Keys

| Key | Does |
| --- | --- |
| <kbd>space</kbd> | pause or carry on |
| <kbd>←</kbd> <kbd>→</kbd> | previous or next sentence |
| <kbd>↑</kbd> <kbd>↓</kbd> | previous or next paragraph |
| <kbd>[</kbd> <kbd>]</kbd> | previous or next section |
| <kbd>+</kbd> <kbd>-</kbd> | faster or slower, from 0.8× to 2× |
| <kbd>n</kbd> <kbd>p</kbd> | next or previous file |
| <kbd>v</kbd> | next voice (Google voices) |
| <kbd>m</kbd> | the playlist menu |
| <kbd>r</kbd> | hear this sentence again, or the file again at the end |
| <kbd>q</kbd> | quit, keeping your place |

A click on a sentence jumps to it. The mouse wheel scrolls, and the page follows the voice again at the next
sentence. Vim users can use <kbd>h</kbd> <kbd>j</kbd> <kbd>k</kbd> <kbd>l</kbd>.

## Use it with Claude Code

Keep Claude Code in one terminal and open a second one in the same folder. When a reply lands, run:

```bash
voce -r
```

voce finds the session for that folder in `~/.claude/projects`. It reads the same text that `/copy` would take,
which is Claude's final message without the progress notes, tool calls or thinking. If a turn is still running,
it reads the previous reply.

You can also `/copy` the reply and run `voce -c`, which works in any terminal and with any tool.

## Voices

**The Mac's voice** works with no setup. To pick one, run `voce --mac --voice Daniel`. You can add better voices
in System Settings, under Accessibility, Spoken Content, System voice, Manage voices.

**Google's Chirp 3 HD voices** sound far more natural. There are two ways to set them up:

1. **An API key.** Make a key for a Google Cloud project with the Text-to-Speech API turned on, then export it:
   ```bash
   export VOCE_GOOGLE_API_KEY=...
   ```
2. **The gcloud CLI.** Sign in with `gcloud auth login`, then tell voce which project to bill. You only do this
   once:
   ```bash
   voce --google-project my-project-id
   ```
   voce falls back to `gcloud config get-value project` if you skip this.

Press <kbd>v</kbd> to cycle through eight voices, or pick one with `--voice en-GB-Chirp3-HD-Leda`. Any Chirp 3 HD
voice name works, in any language Google offers. When this was written, Google's free tier covered one million
Chirp 3 HD characters a month, which is about 18 hours of listening. The playlist menu shows how much of that
you have used this month. Check [Google's pricing](https://cloud.google.com/text-to-speech/pricing) for current
numbers.

If Google fails part-way through, voce uses the Mac voice for that sentence and tells you why. The full setup
guide is in [docs/google-voices.md](docs/google-voices.md).

## Playlists and quizzes

A playlist is a README with a `## Listen in this order` section that lists Markdown files, grouped into parts:

```markdown
## Listen in this order

### Part 1. The basics
1. [Getting started](basics/start.md) · 12 min
2. [Core ideas](basics/ideas.md) · 9 min
```

Run `voce --playlist path/to/folder` once. After that, `voce` works through the files in order, `voce --menu` lets
you choose one, and `voce --list` shows your progress. `voce --prepare 1` fetches the audio for part 1 ahead of
time, and `voce --minutes` updates the "· N min" figures.

A file with a numbered list under `## Quiz` and the same number of answers under `## Answers` becomes a quiz. voce
reads a question, waits while you answer out loud, and reads the answer when you press space. `voce --quiz` runs
just the quizzes. See [docs/playlists.md](docs/playlists.md).

## What it understands

Headings, paragraphs, bold, italic, struck-through text, inline code, links and images all work. So do nested,
numbered and task lists, block quotes and rules. Fenced code blocks are highlighted for every language
[Pygments](https://pygments.org) knows, and long lines wrap instead of being cut off. Tables line up in columns,
respect column alignment, and are read one row at a time.

It also handles a few things that suit listening. Anything inside `<details>` is shown but not read. Lines that
are only links, such as breadcrumbs or "Next:" links, are shown but not read. Symbols such as →, ≈ and ×, and
abbreviations such as "e.g." and "i.e.", are read as words.

## Privacy

voce has no telemetry and makes no network calls of its own. Text goes to Google only when you use Google's
voices, and only to the Text-to-Speech API. Everything else stays on your Mac:

| What | Where |
| --- | --- |
| Your place in each file, settings and monthly character count | `~/.local/state/voce/state.json` |
| The last 50 clipboard, reply and piped texts | `~/.local/state/voce/clips/` |
| Cached audio and the compiled player | `~/.cache/voce/` |

voce respects `XDG_STATE_HOME` and `XDG_CACHE_HOME`. The cache is safe to delete at any time.

## How it works

voce parses Markdown into blocks of plain text, keeping bold, code and the rest as styled spans over that text.
The screen draws the spans, and the voice reads the plain text a sentence at a time. Audio is fetched up to eight
sentences ahead on a small thread pool and played by a tiny Swift program over a pipe. That program reports its
position every 50 milliseconds, and voce uses it to time the word highlight. The interface is plain `curses`,
redrawn 25 times a second. [docs/architecture.md](docs/architecture.md) has the details.

## Contributing

Issues and pull requests are welcome. [CONTRIBUTING.md](CONTRIBUTING.md) explains how to set up, test and
re-record the demo.

## Licence

[MIT](LICENSE)
