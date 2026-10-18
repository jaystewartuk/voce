<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/assets/wordmark-dark.svg">
    <img src="docs/assets/wordmark-light.svg" alt="voce" width="300">
  </picture>
</p>

<p align="center">
  <strong>Read Markdown aloud in your terminal.</strong><br>
  Each sentence lights up as it is read, and each word as it is spoken.<br>
  Code is read the way a pairing partner says it.
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
look, with headings, bold, links, highlighted code and lined-up tables, and reads it the way a person would: the
prose as prose, and the code the way a pairing partner says it out loud. You can look away, follow along, or
jump around with the keyboard or the mouse.

It was built to listen to long Claude Code replies and study notes, but it reads any Markdown.

- **Reads code like a pairing partner.** `'1' === 1` is heard as "the string 1 is identical to 1", and
  `$totals[$channel] ??= 0;` as "totals channel null coalescing assignment zero". Operators get their manual's
  real names, in each language's own words, so you learn to say them. See [Code, read aloud](#code-read-aloud).
- **Reads what a person would read.** Markup is never spoken. Tables are read row by row, and links by their
  text. Things meant for the eye stay on the screen.
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
| <kbd>c</kbd> <kbd>C</kbd> | copy the sentence, or the whole paragraph |
| <kbd>q</kbd> | quit, keeping your place |

A click on a sentence or a line of code jumps to it. Drag across any text to copy it, without moving the voice:
it is on the clipboard when you let go. With `--skip-code`, a click on a code block copies it. To select text
with the terminal's own mouse instead, hold <kbd>shift</kbd> while you drag.

The mouse wheel scrolls, and the page follows the voice again at the next
sentence. Vim users can use <kbd>h</kbd> <kbd>j</kbd> <kbd>k</kbd> <kbd>l</kbd>.

## Code, read aloud

Every reader that speaks code gets it wrong in one of two ways. Screen readers read the symbols one by one:
"dollar, totals, left bracket, dollar, channel...". Text-to-speech apps read code as if it were prose, and `Str::slug`
comes out as "stress log". Neither says what a colleague sitting next to you would say.

voce reads code the way a pairing partner says it out loud, one line at a time, and the line sits on the band
as it is read, with the word being spoken marked, just like a sentence of prose.

| On the line | What you hear |
| --- | --- |
| `$totals[$channel] ??= 0;` | totals channel null coalescing assignment zero |
| `usort($rows, fn ($a, $b) => $a['nights'] <=> $b['nights']);` | U sort rows, F N a, b double arrow a nights spaceship b nights |
| `foreach ($rows as &$row) {` | for each rows as by reference row |
| `'1' === 1;   // false: a string is not an integer` | the string 1 is identical to 1, false: a string is not an integer |
| `if (strpos($s, 'Hi') !== false) { ... }` | if string position s, Hi is not identical to false and so on |
| `(int) (19.99 * 100);   // 1998, a cent short` | cast to int 19.99 times 100, 1998, a cent short |
| `Str::slug('Sea View');` | string double colon slug Sea View |

The rules are the ones a person uses without thinking. Names are said as words: `array_values` is "array
values", `strlen` is "string length", `mb_strlen` is "M B string length", `usort` is "U sort", `isset` is "is
set", `checkIn` is "check In". A variable's dollar sign is silent, and so are brackets and semicolons. Operators
get their real names: `->` is "arrow", `=>` is "double arrow", `::` is "double colon", `===` is "is identical to"
and `==` is "is equal to", the PHP manual's own names rather than the "triple equals" nickname, `??` is "null coalescing", `?:` is "short ternary", `<=>` is "spaceship", `?string` is
"nullable string", `(int)` is "cast to int", `++` is "increment", `&` on a parameter is "by reference", and `...` is
"unpack" in a call and "variadic" in a signature. The names are the PHP manual's own. A string
is read by its contents, so `''` is "the empty string" and `','` is "a comma". A trailing comment is read as
prose. Inline code in a sentence is read the same way.

Because the names are the real ones, you learn them as you listen. After a few sessions, "identical",
"null coalescing assignment" and "spaceship" come out of your mouth as easily as "equals", which is exactly what you want in a
pair-programming interview or a code review.

The rules were written for PHP and Laravel first, checked by ear against the real voice with
[docs/hearing/check.py](docs/hearing/check.py). Each language then has its own words on top of what is common
to all of them, in [`speech/words.py`](src/voce/speech/words.py): a Python line says "returns" for `->`, "floor
divided by" for `//` and "dunder init" for `__init__`; a JavaScript line says "is strictly equal to" for `===`
and "optional chaining" for `?.`, which are MDN's names; shell says "pipe" and "and then"; SQL says "is not
equal to" for `<>`. A fenced block is read in the language on its fence, a diff in the language of its file,
and inline code in a sentence in the language most of the document's code is in. Prose inside code, such as a
doc comment or a heredoc, is read as prose. Adding a language is a few lines of data, and welcome.

If you would rather hear only the prose, `--skip-code` shows code without reading it.

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

Code, in fenced blocks and in sentences, is read the way a pairing partner says it: see [Code, read
aloud](#code-read-aloud). A fenced `diff` block is highlighted with added lines in the file's syntax and removed
lines in red, and read hunk by hunk: "Line 40", then the changed lines, with "Added" and "Removed" said once at
the start of each run and the unchanged context shown but not read. Write the file's language after the word
diff, as in ```` ```diff python ````, to have the added lines highlighted and read in that language.

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
