# Changelog

All notable changes to voce are listed here. The format follows [Keep a Changelog](https://keepachangelog.com),
and versions follow [Semantic Versioning](https://semver.org).

## [Unreleased]

### Added

- **Voices that work out of the box.** Kokoro, a small open voice model, runs on the Mac: free, offline, no key.
  The model (350 MB) is downloaded once. It is the voice when no cloud engine is set up; on Python 3.9, where
  Kokoro can't run, the Mac's voices are used as before.
- **Azure, ElevenLabs and OpenAI** beside Google. Each is used as soon as its key is set (`VOCE_AZURE_KEY` and
  `VOCE_AZURE_REGION`, `VOCE_ELEVENLABS_API_KEY`, `VOCE_OPENAI_API_KEY`), with eight voices to cycle through,
  the month's characters counted against each one's free allowance, and a fallback to Kokoro when one fails.
  `--engine` picks one; `--voice` picks a voice and the engine follows from the name; `voce --voices` shows what
  is set up. <kbd>V</kbd> in the reader moves to the next engine, and <kbd>v</kbd> now cycles the Mac's voices too.

- **Pick up on another device.** `voce --sync OWNER/REPO` keeps your places, settings and a prepared copy of each
  document in a private git repository, made on GitHub for you when `gh` is signed in; any git URL works too.
  Every run pulls first and pushes when you stop. A prepared copy (`prepared/<hash>.json`) is the document as voce
  shows and says it, so a phone or a browser needs only it and a voice; the reader writes one for whatever it
  opens, and `--prepare` and `--sync` write them for the playlist, with `prepared/index.json` listing them.
- **A web app**, at [jaystewartuk.github.io/voce/app](https://jaystewartuk.github.io/voce/app/): the same
  library on a phone or in any browser, read from that repository with a token for it alone, played by the
  device's own voice or by Kokoro running in the page, with your place written back. Static files on GitHub
  Pages; no server.

### Changed

- **State is laid out for syncing.** Your place in each document is its own small file under
  `~/.local/state/voce/places/`, named by a hash of the document's text rather than its path, so the same file
  resumes on any machine however it got there. Settings and the month's character counts have their own files.
  Point `VOCE_STATE` at a synced folder to pick up on another Mac where you left off. An existing `state.json` is
  migrated once and kept as `state-v1.json`.
- The usage file counts characters per engine. Existing counts are kept as Google's.

- **Diffs.** A fenced `diff` block in any Markdown is highlighted with added lines in the file's
  syntax, removed lines in red and context dimmed, and read as above. Name the file's language after the word
  diff (```` ```diff python ````) to have the added lines highlighted and read in that language.
- **Languages.** Code is read in each language's own words. PHP is the full set; Python ("returns", "floor
  divided by", "dunder init"), JavaScript and TypeScript (MDN's "is strictly equal to", "optional chaining",
  "spread"), shell and SQL have starters; Markdown and text are read as prose. Inline code in a sentence is
  read in the language most of the document's code is in. A language is a few lines of data in
  `speech/words.py`.
- Paths and file names are said with their slashes and the extension by letter: `src/voce/cli.py` is "source
  slash voce slash C L I dot P Y". A line of prose inside code, such as a doc comment, is read as prose.
- Link reference definitions (`[name]: url`, and the `[//]: # (comment)` idiom) are neither shown nor read.
- **Doc comments.** The lines of a `/** ... */` block are read as a person reads them: `@param  array|string
  $columns  The columns` is "parameter array or string, columns, The columns", `@return` is "returns",
  `array<int, string>` is "array of int, string", `\Closure(TValue): bool` is "Closure taking T Value returning
  bool", `{@inheritdoc}` is "inherit doc", and the opening and closing lines are silent.
- `docs/hearing/corpus.py` reads a whole code base the way voce would and reports the words that came out odd,
  so the rules can be checked against real code. `corpora.txt` names the code bases; laravel/framework is the
  first, and a framework in another language is one more line.
- `fn` is "arrow function", the manual's name, and the `=>` that follows its parameters is "returns": `fn ($x)
  => $x * 2` is "arrow function x returns x times 2". A `=>` inside the body is still "double arrow".
- PHP, after reading laravel/framework: `<?php` is "P H P open tag", `#[AsCommand]` is "attribute As Command",
  `$list[] = $item` is "list append item", `$a ? $b : $c` is "a then b else c", `Stringable|string` in a
  signature is "Stringable or string", `instanceof` is "instance of", `endforeach` is "end for each", and
  some two hundred of the standard library's names are said in full, `rtrim` as "R trim" and `realpath` as
  "real path". A string of one symbol is said by name, `'@'` as "an at sign" and `'>='` as "greater than or
  equal to", and `"{$this->name}"` inside a string is read as code, and a path in a string,
  `'routes/web.php'`, as a path. An abbreviation inside a camel-case name
  is said as it would be on its own: `expectsJson` is "expects JSON", `getId` is "get I D".

### Changed

- The code is arranged for people who want to extend it: `markdown/` (inline, blocks, tables), `speech/`
  (sentences, prose, code, the word tables), `sources/` (Claude's reply, the clipboard), `commands.py`
  for the printing commands, `ui/session.py` for the curses session and `ui/view.py` for where things sit on
  the screen, leaving `ui/reader.py` to what happens in time. Every source raises one `SourceError`.
- The text sent to the voice changes for inline code with a slash, a file name or an operator in it, and for
  text with a middle dot or a diff count such as "(+12 −3)", so those sentences are fetched again once.

- Drag across any text to copy it, without moving the voice. The text holds still while the button is down,
  the selection shows as you drag, and it is on the clipboard when you let go. Whole blocks come out as they
  are in the document, so a drag down a code block copies real lines.

- The title bar fills from the left as the file is read, and the status bar says how far through you are as a
  percentage, in place of the sentence count.

### Changed

- The sentence being read stays on one row, two fifths of the way down, and the text glides up to meet it a
  line or so a frame instead of jumping when it drifted too far. Clicking a sentence or carrying on after a
  pause brings it to the same row, and the end of a file rises to it too, so the eye never has to drop.
- Code blocks are read, line by line, the way a pairing partner says code aloud: names as words (`array_values`
  is "array values", `usort` is "U sort"), operators by the PHP manual's names (`===` is "is identical to", `==` is
  "is equal to", `=>` is "double arrow", `??` is "null coalescing", `<=>` is "spaceship", `++` is "increment"), brackets silent,
  strings by their contents, and a trailing comment as prose after a short pause. The line being read sits on the band and the word being
  spoken is marked, as in prose, and a click on a line of code starts reading there. `--skip-code` keeps the
  old behaviour, showing code without reading it, where a click still copies the block.

### Fixed

- PHP code blocks are highlighted even when they do not start with an opening `<?php` tag, as snippets in notes
  rarely do.
- "PHP 8" is read as the language version, not as eight Philippine pesos; likewise BSD, CRC and CVE before a
  version-like number. Sums of money such as "PHP 500" are still money.
- The mouse wheel scrolls down as well as up on macOS, whose own ncurses has no fifth button and reports
  wheel-down differently.
- Pausing just as a sentence ends, in the short silence after it, no longer plays that sentence again when you
  carry on: the reader moves to the next one.

### Added

- `c` copies the sentence being read and `C` its paragraph; a click on a code block copies the code. Shift-drag
  still selects text the terminal's own way.
- Inline code is read the same way: `array_values` in a sentence is "array values", and `===` on its own is
  "identical". Before, the voice got the raw text, so study notes had to spell names out in prose.
- `docs/hearing/check.py` fetches tricky phrases from the real voice, transcribes them with whisper.cpp and
  checks what was heard. It is how rewrites for the voice are verified and new ones found.

## [0.1.0] - 2026-10-17

The first public release.

### Added

- Reads Markdown aloud in the terminal, highlighting the sentence being read and the word being spoken.
- Shows inline styles (bold, italic, code, links, strikethrough), aligned tables, task lists and syntax-highlighted
  code. Code is shown but not read. Tables are read row by row.
- `voce -r` reads Claude Code's latest reply in the current folder, straight from the session transcript.
- `voce -c` reads the clipboard, and `voce -` reads standard input.
- Several files in one go: `voce a.md b.md`.
- Mac voices out of the box. Google Chirp 3 HD voices with an API key or gcloud, eight to cycle through, any
  language.
- A per-sentence audio cache, so listening again is free and works offline.
- A native Swift player for gapless playback, a true pause and a word highlight that keeps time, with `afplay` as
  a fallback.
- Your place is kept per file and found again by its text after edits. Files reload when they change on disk.
- Playlists from a README's "Listen in this order" section, with a menu, progress, parts and quizzes.
- `--export` writes files, a reply, the clipboard or a playlist as one MP3.
- `--prepare` fetches audio ahead of time, `--check` reports how files will read, and `--minutes` keeps playlist
  durations current.
- A click on a sentence jumps to it. The mouse wheel scrolls.

[0.1.0]: https://github.com/jaystewartuk/voce/releases/tag/v0.1.0
