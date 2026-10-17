# How voce works

voce is a small Python package with one runtime dependency, Pygments. Audio is played by a Swift program that
voce compiles on first use.

```
src/voce/
  cli.py          the voce command: arguments, then one of play, --check, --list, --prepare, --export
  markdown.py     Markdown into Blocks: plain text plus styled spans
  highlight.py    Pygments tokens reduced to a dozen roles (keyword, string, comment ...)
  speech.py       sentence splitting and small rewrites for the voice
  document.py     a file as Blocks to show and Units to say; quiz pairing
  playlist.py     "Listen in this order" READMEs
  voices.py       Google and Mac voices, the audio cache, fetching ahead
  player.py       the native player (player.swift) and the afplay fallback
  export.py       one MP3 from many sentences, with ffmpeg
  claude.py       Claude Code's latest reply from its session transcript
  clips.py        clipboard and standard input, kept as files
  state.py        your place, settings and usage, in one JSON file
  ui/             theme, terminal input, layout, the reader and the menu
```

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
one unit each. Quiz answers are moved to sit straight after their questions.

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
lines under the gutter. To draw a line, the reader cuts it at every span edge, the sentence edges and the word
edges, and asks the theme for each piece's attribute. The theme is one table of xterm-256 colours with 8-colour
fallbacks.

## State

`~/.local/state/voce/state.json` holds, for each file, the index of the unit you reached and the first 80
characters of what it says. When a file changes, voce finds your place again by that text. The same file holds
your speed, voice, playlist, Google project and a count of characters sent to Google each month.
