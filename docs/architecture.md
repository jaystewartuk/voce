# How voce works

voce is a small Python package with one runtime dependency, Pygments. Audio is played by a Swift program that
voce compiles on first use.

```
src/voce/
  cli.py            the voce command: arguments, sources, then a printing command or the reader
  commands.py       the printing commands: --check, --list, --minutes, --prepare, --export
  sources/          where text comes from, besides files: each one ends as a Markdown file
    claude.py         Claude Code's latest reply from its session transcript
    clips.py          clipboard and standard input, kept as files
    github.py         a pull request from GitHub's REST API, as plain data
    pullrequest.py    that pull request written as Markdown
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
  voices.py         Google and Mac voices, the audio cache, fetching ahead
  player.py         the native player (player.swift) and the afplay fallback
  export.py         one MP3 from many sentences, with ffmpeg
  state.py          your place, settings and usage, in one JSON file
  paths.py          where state, clips, pull requests and the cache live
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
clipboard and standard input are saved under `~/.local/state/voce/clips/`. A pull request is fetched from GitHub
and written under `~/.local/state/voce/pulls/`, one file per request, rewritten only when its text changes.

That is what makes the rest simple: the reader, `--check`, `--export`, `--prepare`, your saved place and the
reload-on-change all work the same way whatever the text came from. `sources.resolve` is the one place that
turns the command line's `-r`, `-c`, `-` and `--pr` into a file, and every source raises one `SourceError` with a
message written for the person at the keyboard.

To add a source, write a module in `sources/` that ends in a Markdown file and add a line to `sources.resolve`.
The pull request source is the model: `github.py` knows the API and returns plain dataclasses; `pullrequest.py`
knows what a reviewer wants to hear and writes the Markdown; neither knows about voices or screens.

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

`~/.local/state/voce/state.json` holds, for each file, the index of the unit you reached and the first 80
characters of what it says. When a file changes, voce finds your place again by that text. The same file holds
your speed, voice, playlist, Google project and a count of characters sent to Google each month.

## Testing

Everything below the screen is plain functions over plain data, and the tests use them directly: Markdown in,
blocks out; a line of code in, words out; a dict of API answers in, Markdown out. The reader runs in tests
against a fake terminal, player and voice (`tests/test_reader.py`), and GitHub is stood in for by a function that
answers URLs from a dict (`tests/test_github.py`). No test touches the network, your state or your cache.
