<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/jaystewartuk/voce/main/docs/assets/wordmark-dark.svg">
    <img src="https://raw.githubusercontent.com/jaystewartuk/voce/main/docs/assets/wordmark-light.svg" alt="voce" width="300">
  </picture>
</p>

<p align="center">
  <strong>Read Markdown aloud in your terminal.</strong><br>
  Each sentence lights up as it is read, and each word as it is spoken.<br>
  Code is read the way a pairing partner says it.
</p>

<p align="center">
  <a href="https://github.com/jaystewartuk/voce/actions/workflows/ci.yml"><img src="https://github.com/jaystewartuk/voce/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://pypi.org/project/voce/"><img src="https://img.shields.io/pypi/v/voce?color=2f6feb" alt="PyPI"></a>
  <img src="https://img.shields.io/badge/python-3.9%2B-2f6feb" alt="Python 3.9+">
  <img src="https://img.shields.io/badge/platform-macOS%20%7C%20Linux-2f6feb" alt="macOS and Linux">
  <a href="https://github.com/jaystewartuk/voce/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-2f6feb" alt="MIT licence"></a>
</p>

<p align="center">
  <a href="https://jaystewartuk.github.io/voce/">Website</a> ·
  <a href="#install">Install</a> ·
  <a href="#use-it-with-claude-code">Claude Code</a> ·
  <a href="#voices">Voices</a> ·
  <a href="https://github.com/jaystewartuk/voce/blob/main/docs/playlists.md">Playlists</a>
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/jaystewartuk/voce/main/docs/assets/demo.gif" alt="voce reading a Claude Code reply: the sentence being read is on a pale blue band, the word being spoken on a dark blue one, code is syntax highlighted and the table is lined up" width="860">
</p>

voce (Italian for "voice", said *VOH-chay*) reads Markdown to you in the terminal. It shows the page as it should
look, with headings, bold, links, highlighted code and lined-up tables, and reads it the way a person would: the
prose as prose, and the code the way a pairing partner says it out loud. You can look away, follow along, or
jump around with the keyboard or the mouse.

Coding agents write a lot worth knowing: explanations of a codebase, walkthroughs of a pull request, lessons on
a language or a framework. voce lets you listen to it instead of reading it, away from the screen if you like.
Ask Claude Code, Codex or any agent to write you something, and press play. It reads any Markdown.

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
- **Sounds good, costs nothing.** Kokoro, a small open voice, runs on your computer out of the box: no account, no key,
  nothing sent anywhere. Every sentence is made once and cached, so listening again is instant.
- **Goes with you.** `--export` turns files into one MP3 with the same voice and pauses, for a walk or a drive.

## Install

You need macOS or Linux, and Python 3.10 to 3.14 for the voice that works out of the box.

```bash
uv tool install voce
# or
pipx install voce
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

On **Linux**, voce plays audio with mpv or ffplay if one is installed, else with `pw-play`, `paplay` or `aplay`,
which play at one speed only. For the clipboard it uses `wl-clipboard` on Wayland, or `xclip` or `xsel` on X11:

```bash
sudo apt install mpv wl-clipboard      # or: sudo dnf install mpv wl-clipboard
```

On **Windows**, run it in [WSL](https://learn.microsoft.com/windows/wsl/install), where it is Linux.

## Use it

```bash
voce notes.md              # read a file, from where you left off
voce a.md b.md             # read several files in a row
voce -r                    # read Claude Code's latest reply in this folder
voce -c                    # read what is on the clipboard
cat notes.md | voce -      # read standard input
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
| <kbd>v</kbd> | next voice |
| <kbd>V</kbd> | next voice engine, of those set up |
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
| `usort($rows, fn ($a, $b) => $a['nights'] <=> $b['nights']);` | U sort rows, arrow function a, b returns a nights spaceship b nights |
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
"null coalescing assignment" and "spaceship" come out of your mouth as easily as "equals", which is exactly what you want when
you pair or review code with someone.

The rules were written for PHP and Laravel first, read right through laravel/framework with
[docs/hearing/corpus.py](https://github.com/jaystewartuk/voce/blob/main/docs/hearing/corpus.py) to find what came out odd, and checked by ear against the real
voice with [docs/hearing/check.py](https://github.com/jaystewartuk/voce/blob/main/docs/hearing/check.py). A doc comment is read as a person reads it: `@param
array|string $columns` is "parameter array or string, columns". Each language then has its own words on top of what is common
to all of them, in [`speech/words.py`](https://github.com/jaystewartuk/voce/blob/main/src/voce/speech/words.py): a Python line says "returns" for `->`, "floor
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

**Kokoro** works out of the box. It is a small open voice model that runs on your computer, so it is free, needs no
account and sends nothing anywhere. The first time it speaks, voce downloads the model (120 MB) into its cache.
It needs Python 3.10 to 3.14; on 3.9, voce uses the Mac's own voices instead (on Linux, install a newer Python).

**The Mac's voices** are always there on macOS: `voce --mac`, or `voce --mac --voice Daniel` to pick one. Add
better ones in System Settings, under Accessibility, Spoken Content, System voice, Manage voices.

Press <kbd>v</kbd> to move through an engine's voices and <kbd>V</kbd> to move to the other engine; both are
remembered. Or name a voice and the engine follows: `--voice bm_george` (Kokoro) or `--voice Daniel` (the Mac).
`--engine` picks an engine outright. If Kokoro fails part-way through, voce reads that sentence with the Mac's
voice and tells you why. The full guide is in [docs/voices.md](https://github.com/jaystewartuk/voce/blob/main/docs/voices.md).

## Playlists and quizzes

A playlist is a README with a `## Listen in this order` section that lists Markdown files, grouped into parts:

```markdown
## Listen in this order

### Part 1. The basics
1. [Getting started](https://github.com/jaystewartuk/voce/blob/main/basics/start.md) · 12 min
2. [Core ideas](https://github.com/jaystewartuk/voce/blob/main/basics/ideas.md) · 9 min
```

Run `voce --playlist path/to/folder` once. After that, `voce` works through the files in order, `voce --menu` lets
you choose one, and `voce --list` shows your progress. `voce --prepare 1` fetches the audio for part 1 ahead of
time, and `voce --minutes` updates the "· N min" figures.

A file with a numbered list under `## Quiz` and the same number of answers under `## Answers` becomes a quiz. voce
reads a question, waits while you answer out loud, and reads the answer when you press space. `voce --quiz` runs
just the quizzes. See [docs/playlists.md](https://github.com/jaystewartuk/voce/blob/main/docs/playlists.md).

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

## Pick up on another device

`voce --sync you/voce` keeps your places, settings and a prepared copy of each document in a private git
repository of your own, so a second computer carries on where the first left off. A
[web app](https://jaystewartuk.github.io/voce/app/) reads the same repository on a phone or in any browser, with
a voice that runs in the page. There is no voce service: the repository is yours. See [docs/sync.md](https://github.com/jaystewartuk/voce/blob/main/docs/sync.md).

## Privacy

voce has no telemetry and makes no network calls of its own. What you read never leaves your computer: the only
download is the Kokoro model, once, from GitHub. Everything voce keeps stays on your computer:

| What | Where |
| --- | --- |
| Your place in each document, one small file per document | `~/.local/state/voce/places/` |
| Speed, engine, voices and playlist | `~/.local/state/voce/settings.json` |
| Documents prepared for other devices | `~/.local/state/voce/prepared/` |
| The last 50 clipboard, reply and piped texts | `~/.local/state/voce/clips/` |
| Cached audio and the compiled player | `~/.cache/voce/` |

voce respects `XDG_STATE_HOME` and `XDG_CACHE_HOME`. The cache is safe to delete at any time.

A place is named by a hash of the document's text, not its path, so the same file resumes wherever it is. With
`--sync` the state directory is a git repository; without it, `VOCE_STATE` can point it at a folder that iCloud
Drive, Dropbox or Syncthing carries between computers. Two machines reading different documents never touch the same
file.

## How it works

voce parses Markdown into blocks of plain text, keeping bold, code and the rest as styled spans over that text.
The screen draws the spans, and the voice reads the plain text a sentence at a time. Audio is fetched up to eight
sentences ahead on a small thread pool. On macOS a tiny Swift program plays it over a pipe, gapless, and reports
its position every 50 milliseconds to time the word highlight; on Linux each sentence is handed to mpv or
ffplay. The interface is plain `curses`,
redrawn 25 times a second. [docs/architecture.md](https://github.com/jaystewartuk/voce/blob/main/docs/architecture.md) has the details.

## Contributing

Issues and pull requests are welcome, and so is a coding agent doing the work. The repository is set up for one:
[AGENTS.md](https://github.com/jaystewartuk/voce/blob/main/AGENTS.md) tells Claude Code, Codex or Cursor how voce is laid out, how to test it and what to keep
stable, so you can ask for the feature you want and review what comes back.

The easiest place to start is a new language for [Code, read aloud](#code-read-aloud): Ruby, Go, Rust, Java, C#
and Swift are all read with the common words today, and each needs only a few lines of data in
[`speech/words.py`](https://github.com/jaystewartuk/voce/blob/main/src/voce/speech/words.py). [CONTRIBUTING.md](https://github.com/jaystewartuk/voce/blob/main/CONTRIBUTING.md) has the details.

## Licence

[MIT](https://github.com/jaystewartuk/voce/blob/main/LICENSE)
