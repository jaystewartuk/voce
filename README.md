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
- **Sounds good, costs nothing.** Kokoro, a small open voice, runs on your Mac out of the box: no account, no key,
  nothing sent anywhere. Google's Chirp 3 HD, Azure, ElevenLabs and OpenAI voices are there when you set a key.
  Every sentence is fetched once and cached, so listening again is free and works offline.
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
"null coalescing assignment" and "spaceship" come out of your mouth as easily as "equals", which is exactly what you want in a
pair-programming interview or a code review.

The rules were written for PHP and Laravel first, read right through laravel/framework with
[docs/hearing/corpus.py](docs/hearing/corpus.py) to find what came out odd, and checked by ear against the real
voice with [docs/hearing/check.py](docs/hearing/check.py). A doc comment is read as a person reads it: `@param
array|string $columns` is "parameter array or string, columns". Each language then has its own words on top of what is common
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

**Kokoro** works out of the box. It is a small open voice model that runs on your Mac, so it is free, needs no
account and sends nothing anywhere. The first time it speaks, voce downloads the model (350 MB) into its cache.
It needs Python 3.10 or newer; on 3.9, voce uses the Mac's own voices instead.

**Four cloud engines** are used as soon as their key is set, and `voce --voices` shows which are:

| Engine | Set up with | Free each month, when this was written |
| --- | --- | --- |
| Google Chirp 3 HD | `VOCE_GOOGLE_API_KEY`, or `gcloud auth login` and `voce --google-project ID` once | 1,000,000 characters, about 18 hours |
| Azure | `VOCE_AZURE_KEY` and `VOCE_AZURE_REGION` | 500,000 characters |
| ElevenLabs | `VOCE_ELEVENLABS_API_KEY` | 10,000 characters |
| OpenAI | `VOCE_OPENAI_API_KEY` | nothing, but the cheapest per hour |

Google is the best value and is used first when more than one is set up. Azure never skips a word. ElevenLabs
is the most expressive. OpenAI is told to read every word as written. voce counts the characters it sends to
each, and the playlist menu shows the month's count against the free amount.

**The Mac's voices** are always there: `voce --mac`, or `voce --mac --voice Daniel` to pick one. Add better ones in
System Settings, under Accessibility, Spoken Content, System voice, Manage voices.

Press <kbd>v</kbd> to move through an engine's voices and <kbd>V</kbd> to move to the next engine; both are
remembered. Or name a voice and the engine follows: `--voice bm_george` (Kokoro), `--voice en-GB-Chirp3-HD-Leda`
(Google), `--voice en-GB-RyanNeural` (Azure), `--voice ash` (OpenAI), or `--engine elevenlabs --voice Alice`.
`--engine` picks an engine outright. If an engine fails part-way through, voce reads that sentence with Kokoro
and tells you why. The full guide, with Google's setup steps, is in [docs/voices.md](docs/voices.md).

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

## Pick up on another device

```sh
voce --sync you/voce
```

makes a private repository on GitHub (with `gh`, if it is signed in; or give any git URL), and keeps your
places, settings and a prepared copy of every document in your playlist there. From then on voce pulls when it
starts and pushes when you stop, so a second Mac carries on where the first left off. `voce --sync` on its own
prepares and pushes the playlist again.

A prepared copy (`prepared/<hash>.json`) is the document as voce shows and says it: the blocks, and each
sentence or line of code as words. Another device needs only that and a voice; it does none of the reading work.
Everything you open in the reader gets one. `prepared/index.json` lists them in playlist order.

The repository is yours, on any git host. There is no voce service, and nothing is sent anywhere else.

### On your phone, or any browser

[jaystewartuk.github.io/voce/app](https://jaystewartuk.github.io/voce/app/) is the same library in a web page.
It is static files on GitHub Pages: the page reads your repository through GitHub's API with a fine-grained token
you make for that one repository (contents, read and write), plays each document with a voice in the page, and
writes your place back. Add it to the home screen and it opens like an app.

Two voices: the device's own, instantly, or Kokoro, the open voice model, which the browser downloads once
(about 90 MB, 330 MB with WebGPU) and runs on the device. Nothing is sent anywhere but api.github.com. The token
stays in that browser; disconnecting in settings forgets it.

## Privacy

voce has no telemetry and makes no network calls of its own. With Kokoro or the Mac's voices nothing leaves your
Mac but the one-time download of the Kokoro model from GitHub. With a cloud engine, the text of each sentence goes
to that engine's speech API and nowhere else. Everything else stays on your Mac:

| What | Where |
| --- | --- |
| Your place in each document, one small file per document | `~/.local/state/voce/places/` |
| Speed, engine, voices and playlist | `~/.local/state/voce/settings.json` |
| Documents prepared for other devices | `~/.local/state/voce/prepared/` |
| Characters sent to each engine this month | `~/.local/state/voce/usage.json` |
| The last 50 clipboard, reply and piped texts | `~/.local/state/voce/clips/` |
| Cached audio and the compiled player | `~/.cache/voce/` |

voce respects `XDG_STATE_HOME` and `XDG_CACHE_HOME`. The cache is safe to delete at any time.

A place is named by a hash of the document's text, not its path, so the same file resumes wherever it is. With
`--sync` the state directory is a git repository; without it, `VOCE_STATE` can point it at a folder that iCloud
Drive, Dropbox or Syncthing carries between Macs. Two machines reading different documents never touch the same
file, and the month's character counts stay on the machine that spent them.

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
