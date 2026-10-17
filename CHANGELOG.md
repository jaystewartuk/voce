# Changelog

All notable changes to voce are listed here. The format follows [Keep a Changelog](https://keepachangelog.com),
and versions follow [Semantic Versioning](https://semver.org).

## [Unreleased]

### Changed

- Code blocks are read, line by line, the way a pairing partner says code aloud: names as words (`array_values`
  is "array values", `usort` is "U sort"), operators by the PHP manual's names (`===` is "is identical to", `==` is
  "is equal to", `=>` is "double arrow", `??` is "null coalescing", `<=>` is "spaceship", `++` is "increment"), brackets silent,
  strings by their contents, and a trailing comment as prose after a short pause. The line being read sits on the band and the word being
  spoken is marked, as in prose. `--skip-code` keeps the old behaviour, showing code without reading it.

### Fixed

- PHP code blocks are highlighted even when they do not start with an opening `<?php` tag, as snippets in notes
  rarely do.
- "PHP 8" is read as the language version, not as eight Philippine pesos; likewise BSD, CRC and CVE before a
  version-like number. Sums of money such as "PHP 500" are still money.
- The mouse wheel scrolls down as well as up on macOS, whose own ncurses has no fifth button and reports
  wheel-down differently.

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
