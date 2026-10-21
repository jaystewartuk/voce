# How voce works

voce is a small Python package with one runtime dependency, Pygments, plus Kokoro for the local voice. On macOS
audio is played by a Swift program that voce compiles on first use; on Linux, by mpv, ffplay or the system's own
player.

```
src/voce/
  cli.py            the voce command: arguments, sources, then a printing command or the reader
  commands.py       the printing commands: --check, --list, --minutes, --prepare, --export
  sources/          where text comes from, besides files: each one ends as a Markdown file
    claude.py         Claude Code's latest reply from its session transcript
    clips.py          clipboard and standard input, kept as files
  markdown/         Markdown into Blocks: plain text plus styled spans
    inline.py         bold, italic, code, links and strikethrough as spans
    blocks.py         headings, paragraphs, lists, quotes, fences and the rest
    tables.py         rows padded into aligned columns
  speech/           what the voice is given to say
    sentences.py      cutting prose into sentences
    prose.py          small rewrites so prose reads naturally (symbols, abbreviations, "(+12 −3)")
    code.py           code read the way a pairing partner says it, in a language's own words
    words.py          the word tables: common ones, then a Language for PHP, Python, JavaScript, shell, SQL
  highlight.py      Pygments tokens reduced to a dozen roles; diffs highlighted as a reviewer reads them
  document.py       a file as Blocks to show and Units to say: sentences, code lines, diff hunks, quiz pairing
  playlist.py       "Listen in this order" READMEs
  voices.py         the six voice engines (Kokoro, Mac, Google, Azure, ElevenLabs, OpenAI), the cache, fetching ahead
  player.py         the native player (player.swift), and one process per sentence: afplay, mpv, ffplay...
  export.py         one MP3 from many sentences, with ffmpeg
  state.py          your place in each document, settings and usage, as small JSON files
  prepared.py       a document as another device plays it: blocks and units as one JSON file, and the index
  sync.py           the state directory as a git repository: commit, pull with the newer place winning, push
  paths.py          where state, clips and the cache live
  ui/               the screen
    theme.py          colours and attributes
    terminal.py       keys and the mouse
    layout.py         blocks as screen lines; the word highlight's timing
    view.py           where things are: layout, scrolling, the anchor row, the mouse's cell, the selection
    reader.py         what happens in time: the state machine, keys, the mouse's meaning, the bars
    menu.py           the playlist menu
    session.py        running the reader inside curses
```

## Everything is a Markdown file

Whatever voce reads, it reads from a Markdown file. A file on disk is read as it is. A Claude Code reply, the
clipboard and standard input are saved under `~/.local/state/voce/clips/`.

That is what makes the rest simple: the reader, `--check`, `--export`, `--prepare`, your saved place and the
reload-on-change all work the same way whatever the text came from. `sources.resolve` is the one place that
turns the command line's `-r`, `-c` and `-` into a file, and every source raises one `SourceError` with a message
written for the person at the keyboard.

To add a source, write a module in `sources/` that ends in a Markdown file and add a line to `sources.resolve`.
Keep what knows the outside world (an API, a transcript format) apart from what writes the Markdown; neither
needs to know about voices or screens.

## From Markdown to what you see and hear

`markdown.parse` turns a document into a list of `Block`s. Each block has a `kind` (heading, paragraph, list item,
code, table row and so on) and a `text`, which is the plain text with all markup removed. Inline styles are kept
separately as `spans`: `(start, end, roles)` over that text, where roles are things like `bold`, `code` or
`link`. For code blocks the spans come from Pygments and carry syntax roles instead.

Keeping one plain text per block is the central idea. The voice reads it, the sentence splitter cuts it, the
word highlight indexes into it, and the screen draws it with the spans laid over. Nothing has to map between a
marked-up version and a spoken version.

`document.build_units` then cuts spoken blocks into `Unit`s, usually one per sentence, each with a character range
in its block, the exact text to send to the voice, and the pause to leave after it. Headings and table rows are
one unit each. Code is one unit per line. Quiz answers are moved to sit straight after their questions.

## Code and diffs

`speech/code.py` reads a line of code the way a pairing partner says it: names as words, a variable's dollar sign
and the brackets silent, operators by name, strings by their contents, a trailing comment as prose. The words
are data in `speech/words.py`: `COMMON_WORDS` and `LINE_OPERATORS` for every language, then a `Language` for
each language with its own words, operator names and comment markers. `language(alias)` looks one up by its
fence label or Pygments alias; anything unknown gets the generic rules, which are PHP's. A fenced block is read
in the language on its fence, and a document's inline code in the language most of its code is in
(`Doc.language`). A line with four or more words, a sentence's punctuation and nothing that only code has is
read as prose.

A fenced `diff` block carries the file's language after the word diff: ```` ```diff python ````. `highlight.diff_spans`
colours it as a reviewer reads it: the `+` marker green, removed lines red, context dimmed, and the added lines
lexed in the file's language (the added and context lines of a hunk are lexed together, so a string that runs
over several lines keeps its colour). `document.diff_units` reads it: each hunk's header as "Line 40", then the
changed lines, "Added" or "Removed" said once at the start of each run, context lines not said at all.

## Playing

The reader is a small state machine driven by a 40 ms tick:

```
loading ──audio ready──▶ playing ──finished──▶ gap ──pause over──▶ loading (next unit)
                            │
                       space│ (held)        quiz question finished ──▶ waiting ──space──▶ answer
```

`Voice.want(text)` returns a future for a unit's audio file and its duration. The reader asks for the current unit
and the eight after it, so by the time one sentence ends the next is usually on disk. Files are cached under a
hash of the voice name and the text.

The native player reads commands such as `play ID PATH`, `pause` and `rate 1.2` on standard input. It plays
through AVAudioEngine with a time-pitch unit, so speed changes keep the pitch, and it reports `pos ID SECONDS`
every 50 ms. The word highlight comes from that position. Each word in the sentence is weighted by its length and
any punctuation after it, and the highlight moves through the weights in proportion to the time played.

## Drawing

`ui.layout` turns blocks into screen lines at the current width. Each line is a character range of one block plus
a prefix (a bullet, a quote bar or the code gutter). Prose wraps at spaces. Code keeps its spacing and wraps long
lines under the gutter.

`ui.view.View` owns where things are on the screen: the layout at the current width, how far the text has
scrolled, the anchor row the sentence being read is kept on (two fifths of the way down, with the text gliding up
to meet it), which cell the mouse is over, and the drag selection. To draw a line it cuts the line at every span
edge, the sentence edges, the word edges and the selection edges, and asks the theme for each piece's attribute.
`ui.reader.Reader` owns what happens in time, and asks the view for everything spatial. The theme is one table
of xterm-256 colours with 8-colour fallbacks.

## State

The state directory (`~/.local/state/voce/`, or `VOCE_STATE`) is laid out so a folder sync carries it between
machines without conflicts:

```
settings.json        speed, engine, the voice chosen on each engine, playlist, Google project
usage.json           the characters sent to each cloud engine each month
places/<hash>.json   one file per document: the index of the unit you reached, the first 80 characters of what
                     it says, when it was written, and the document's path on each machine that read it
```

A place is keyed by the SHA-256 of the document's bytes, so the same text resumes on any machine however it got
there. When a file changes, its hash changes too: the place last saved under that path on this machine moves to
the new hash, and voce finds your sentence again by its text. Only the files that changed are written on a save,
each atomically; a sync tool's "conflicted copy" is ignored, and when two machines write the same place, the one
written last is what the sync leaves. An older `state.json` is split into these files once and kept as
`state-v1.json`.

## Other devices

`prepared/<hash>.json` is a document after all the work in `document.py` and `speech/` is done: its blocks with
their spans, and its units with the words to say and the pause after each. A phone or a browser needs only this
and a voice, so the pipeline runs in one place and the word tables have one copy. The reader writes one for each
document it opens; `--prepare` and `--sync` write them for the playlist, and `prepared/index.json` lists them in
playlist order with titles and minutes. Each carries a hash of the reading code that made it (`document.py`,
`highlight.py`, `markdown/`, `speech/`), and is written again when that code has changed since, so a better way
of saying something reaches the phone on the next open or `--sync` without anyone remembering to redo it.

`sync.py` makes the state directory a git repository (`voce --sync OWNER/REPO` creates a private one on GitHub
through `gh`, or takes any git URL). Every run pulls first and pushes at the end; `--sync` also prepares the
playlist. A pull is a fetch and a rebase; when both devices saved the same place, the conflicted file is settled
by its `updated` time and the rebase continues. `usage.json` is ignored: the characters billed to a key are that
machine's business. There is no voce server.

## The web app

`site/app/` is the library in a browser: four static files (`index.html`, `app.js`, `py.js`, `sw.js`), a manifest
and, built by the Pages workflow (`.github/web.sh`), a wheel of this package under `py/` with a manifest naming it,
served by GitHub Pages beside the website. Signing in is GitHub's: the page sends the user to authorize the voce
GitHub App and comes back with a code, which `relay/worker.js` (a stateless function on Cloudflare Workers, the
only thing that is not a static file) swaps for a user token, because that swap needs the app's client secret and
GitHub's token endpoint refuses browsers. The token reaches only the repositories the app is installed on; the
page lists them and uses the one chosen, refreshing the token through the relay when it is about to expire. With
no client ID in `app.js` the page falls back to a pasted fine-grained token. `app.js` then talks to GitHub's API:
one request for the `prepared/` tree and one for `places/`, then only the blobs whose sha it hasn't cached (the
Cache API, keyed by sha). A document is rendered from its prepared JSON: each block's text is cut at
every unit edge and every style edge, so a span knows its unit and its roles, and the sentence being read is the
spans of that unit. Code spans carry the same role names as the terminal (`keyword`, `string`, `comment`...).

Two voices. The device's own, through the Web Speech API, is instant. Kokoro runs in the page through kokoro-js
and ONNX Runtime Web, on WebGPU where there is one; it is the same model the Mac uses, fetched from Hugging Face
once and kept by the browser. Clips are generated a few units ahead and played through one audio element, so
the lock screen's controls and background playback work through the Media Session API.

`py.js` is voce's reading code in the page: a module worker that loads Pyodide from its CDN (Python 3.14 in
WebAssembly, about 15 MB, kept by the browser), Pyodide's own pygments, and voce's wheel with `micropip`, then
answers `prepare(text, name)` with the same JSON `prepared.as_json` writes, hash included. It is loaded the first
time a document needs it, not before. A playlist source in settings is a repository and the path of a README in
it: `app.js` reads the README's "## Listen in this order" with the same regexes as `playlist.py`, takes the
folder's tree in one request, fetches each linked file once by its blob sha, hashes it, and lists it with the
place that hash has. Opening one prepares it in the worker and keeps the result in the Cache API under the sha
and the reading code's stamp from `py/manifest.json`, so a document is read once per version of voce. The Mac's
prepared copies and files opened on the device are listed after the playlists, each once by hash.

A place is written with the Contents API on pause, finish, leaving the page and every two minutes while playing.
The write carries the blob's sha; a 409 means another device wrote first, so the page re-reads that place and
keeps whichever `updated` is newer, the same rule as `sync.py`. The service worker caches the app's own files
for offline opening and nothing else.

## Testing

Everything below the screen is plain functions over plain data, and the tests use them directly: Markdown in,
blocks out; a line of code in, words out. The reader runs in tests against a fake terminal, player and voice
(`tests/test_reader.py`). No test touches the network, your state or your cache.
