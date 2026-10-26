# Changelog

All notable changes to voce are listed here. The format follows [Keep a Changelog](https://keepachangelog.com),
and versions follow [Semantic Versioning](https://semver.org).

## [Unreleased]

### Fixed

- **The web app says what the voice is doing after its download.** At 100% it said nothing more for several
  seconds while Kokoro started and made the first sentence. It now says "Starting the voice on this device",
  then "Making the first sentence", and says where you are again as soon as the voice speaks.

- **Kokoro plays in the web app on iPhone and iPad.** iOS lets a page play sound only if it starts during a tap,
  and the first sentence came seconds later, once the model had loaded. The tap on play now starts a moment of
  silence, which lets the voice play after. iOS also gets the smaller model (92 MB, on the CPU) instead of the
  full one for WebGPU, which is more than a phone gives a web page.

### Added

- **TypeScript's mapped types**: `{ [K in keyof T]: T[K] }` is "for each K in key of T colon T K", not "array
  of K in key of T".

## [0.4.0] - 2026-10-25

### Added

- **Eight more languages, each in its manual's words:** TypeScript (split out of JavaScript), Go, Rust, Ruby,
  Java, C#, Swift and Kotlin. `List<String>` is "List of String", Rust's `println!` and lifetimes read cleanly,
  and Ruby's `empty?` and `save!` keep their marks. PHP, Python, JavaScript, shell and SQL know many more words
  and operators: `SELECT *` is "star", `0xFF` is "hex FF", and `${name}` and `#{name}` in a string are read as
  code.
- **The website shows all thirteen languages**, with a tab for each: four lines of code, what you hear, and the
  manual the names come from. Nothing on it is typed by hand: `docs/hearing/site_examples.py` writes it from
  voce, and a test fails if the page and voce disagree.
- **JSX and TSX.** An element is read by its name: `<div>` is "div", `</div>` is "end div", `<App />` is "App" and
  `<>` is "fragment". Before, `</div>` was "less than divided by div greater than".
- **More of TypeScript, by the Handbook.** `T[]` is "T array", `user!` is "user, non-null assertion",
  `name!: string` is "name definitely string", and a function's return type is "returns": `function
  greet(name: string): string` is "function greet name colon string returns string". `first<T>(...)` and
  `toEqualTypeOf<number>()` are type arguments too, also when the list runs over several lines.
- **Regular expressions** in JavaScript and TypeScript are read as "regular expression" and the words in them,
  not symbol by symbol.
- `docs/hearing/corpora.txt` reads Hono, a TypeScript web framework, alongside laravel/framework.

### Changed

- **Code in the new and deepened languages is fetched from the voice again, once**, since what is said for it
  changed. `%` is now "remainder" in JavaScript, Java, Go, Swift, C#, Rust and Kotlin, each manual's word.

### Fixed

- **`return []` is "return empty array"**, and `return [$a, $b]` "return array of a, b", in every language.
  Before, a keyword before a bracket was taken for a value, so it was "return square brackets".
- **Python's lambda.** `lambda x: x * 2` is "lambda x returns x times 2", not "lambda x colon". The colon that
  opens a block is found after a slice too (`if xs[1:2]: pass`), and an f-string's symbols between its fields are
  said: `f'**{n}'` is "f string double star n".
- **A path that starts with a slash** is "slash stubs slash job dot stub", not "slash slash stubs".
- **A doc comment's example code**, such as `* const app = new Hono()`, is read as code in JavaScript and
  TypeScript. A comment such as `// Re-assign` or `# 0-9` is no longer read as a sum.

## [0.3.0] - 2026-10-22

### Added

- **Hear it before you install it.** The website's demo plays Kokoro itself, recorded from voce, reading a part
  of Karpathy's micrograd, with each word lit as it is spoken. The README links to it, and to the MP3.
- **voce says why it is using the Mac's voice.** When Kokoro can't run, as with macOS's own Python 3.9, the
  reader says so the first time it speaks, and how to reinstall with a Python that has it.
- **The web app reads web pages.** Paste an address, or share a page to voce from another app on Android, and it
  reads the article aloud without the menus and footers. You can open `.html` files too.
- **The web app works without signing in.** Open a web page or a file and listen. What you open, and your place in
  it, stays in your browser. Signing in with GitHub is still there for your voce library.
- **What goes where.** A new page on the website lists everything voce keeps and sends, and to whom.
- **Time left.** The web app's player shows the time left at your speed and the heading you are under, such as
  "8 min left · Setup", instead of a sentence count. Tap or drag the progress bar to go anywhere in the document.
- **Back to the voice.** Scroll away while it reads and the page stops following the voice. A button takes you back.

### Removed

- **The cloud voices: Google, Azure, ElevenLabs and OpenAI.** voce is now free for good and fully local: its
  voices run on your computer, and what you read is never sent anywhere. If you had chosen a cloud voice, voce
  uses Kokoro instead, with the Kokoro voice you used last. `--google-project` and the monthly character counts
  are gone with them.

### Changed

- **A smaller Kokoro download: 120 MB, down from 350 MB.** voce now fetches the int8 build of the same model, which
  sounds the same. If you already have the full model, voce keeps using it and downloads nothing.
- **You can see the voice download.** The reader's status bar shows how far it has got, such as "45 of 120 MB",
  and the command line shows one line of progress for it rather than one per file.

### Fixed

- **Python reads more like a person says it.** A docstring is read as its words, not "the empty string". The
  colon that opens a block is silent (`if x: return 1` is "if x, return 1"), `[]` is "empty list", `{}` is
  "empty dict" and `()` is "empty tuple". An f-string's fields are read as code: `{self.data}` is "self dot data".
  A comment that is only an expression, such as `# other + self`, is read as one. `a ** n` in a sentence is "a to
  the power of n". Lines of Python like these will be fetched from the voice again, once.
- **A swipe on the web app's player no longer scrolls the page behind it.**
- **A sharp picture in Android's media controls.** The web app now has 192 and 512 pixel icons, and gives them to
  the lock screen and notification player.
- **The web app keeps your place.** It could say "Couldn't save your place after three tries" when you paused or
  switched tabs soon after it had saved. It now saves one at a time, and checks GitHub's own copy when a save is
  turned away.
- **Kokoro on Python 3.14.** Installing voce with Python 3.14, Homebrew's default, now includes Kokoro. Before,
  it was left out and voce said to reinstall with a newer Python.

## [0.2.0] - 2026-10-21

### Added

- **Linux.** voce runs on Linux as well as macOS. It plays audio with mpv or ffplay, or with `pw-play`,
  `paplay` or `aplay` at one speed, and uses `wl-clipboard`, `xclip` or `xsel` for the clipboard. Kokoro is the
  voice there too. On Windows it runs in WSL. `--plain-player` is the new name for `--afplay`, which still works.
- **On PyPI.** `pipx install voce` or `uv tool install voce`.
- **Built to be extended with a coding agent.** `AGENTS.md` (and `CLAUDE.md`, which points to it) tells Claude
  Code, Codex or Cursor how voce is laid out, how to test it and what to keep stable.
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
  library on a phone or in any browser, played by the device's own voice or by Kokoro running in the page, with
  your place written back. Sign in with GitHub and choose the repository; the voce GitHub App reaches only that
  one, and a stateless relay (`relay/`) does the code-for-token swap a page can't. Static files on GitHub Pages
  otherwise. A fine-grained token can be pasted instead.
- **The web app reads for itself.** voce's reading code runs in the browser (Pyodide), so the app can take a
  playlist README straight from any repository voce can reach, or a Markdown file from the device, and read it
  with nothing prepared on a Mac first. Prepared copies carry a stamp of the reading code and are made again
  when it changes, so a better way of saying something reaches every device.
- `c` copies the sentence being read and `C` its paragraph; a click on a code block copies the code. Shift-drag
  still selects text the terminal's own way.
- Inline code is read the same way: `array_values` in a sentence is "array values", and `===` on its own is
  "identical". Before, the voice got the raw text, so study notes had to spell names out in prose.
- `docs/hearing/check.py` fetches tricky phrases from the real voice, transcribes them with whisper.cpp and
  checks what was heard. It is how rewrites for the voice are verified and new ones found.
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

- **Pausing in the web app holds your place in the sentence.** With the Kokoro voice, playing again within half a
  minute picks up about a second before where you stopped, at the gap before a word, so the cut-off word is heard
  whole. After a longer pause, or with the device's own voice, the sentence starts again as before.
- **The web app's play button is the whole player bar** between the previous and next arrows, so you can pause
  without looking. Tapping the sentence being read plays or pauses too; tapping any other sentence still goes there.
- **The web app marks the word being read** inside the highlighted sentence, from how long Kokoro makes each
  sound (or from the device's own voice, where it reports words). A line of code said differently from how it's
  shown keeps only its line marked. It can be turned off in settings. Kokoro now downloads the timestamped copy of
  the same model, once.
- **State is laid out for syncing.** Your place in each document is its own small file under
  `~/.local/state/voce/places/`, named by a hash of the document's text rather than its path, so the same file
  resumes on any machine however it got there. Settings and the month's character counts have their own files.
  Point `VOCE_STATE` at a synced folder to pick up on another Mac where you left off. An existing `state.json` is
  migrated once and kept as `state-v1.json`.
- The usage file counts characters per engine. Existing counts are kept as Google's.
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

[Unreleased]: https://github.com/jaystewartuk/voce/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/jaystewartuk/voce/releases/tag/v0.4.0
[0.3.0]: https://github.com/jaystewartuk/voce/releases/tag/v0.3.0
[0.2.0]: https://github.com/jaystewartuk/voce/releases/tag/v0.2.0
[0.1.0]: https://github.com/jaystewartuk/voce/releases/tag/v0.1.0
