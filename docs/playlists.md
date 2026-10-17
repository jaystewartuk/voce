# Playlists and quizzes

A playlist turns a folder of Markdown into something you can listen through in order, a bit like an audiobook.
voce remembers which files you have finished and where you stopped in the others.

## Making one

Add a `## Listen in this order` section to the folder's README. `## Listening order` and `## Playlist` work too.
Put a numbered list of links to Markdown files under it, grouped into parts with `###` headings:

```markdown
# My course

Anything here is ignored by voce.

## Listen in this order

### Part 1. Before you start
1. [Why this matters](intro/why.md) · 6 min
2. [The vocabulary](intro/words.md) · 11 min

### Part 2. The core
3. [First principles](core/principles.md) · 14 min

## Notes

Lists after the next ## heading are not part of the playlist.
```

The links are relative to the README. Files that don't exist are skipped. The "· N min" after each link is
optional; `voce --minutes` adds the current figure for every line that has one.

## Using one

```bash
voce --playlist ~/notes/course   # make it the current playlist (remembered)
voce                             # the file you were in, or the first one you haven't finished
voce --menu                      # choose a file; r in the menu marks a file as not started
voce --list                      # progress for every file
voce --prepare 2                 # fetch part 2's audio ahead of time, say before a flight
voce --prepare                   # fetch the whole playlist
voce --export course.mp3         # the whole playlist as one MP3
```

Parts are chosen by the number in their heading, so `2` means "Part 2. The core" wherever it sits in the list.
A word from the heading works too, as in `voce --prepare core`.

When a file ends, voce moves on to the next one after a short pause. Use `--one` to stop at the end of each file
instead.

## Quizzes

A file becomes a quiz when it has a numbered list under a `## Quiz` heading and the same number of items under
`## Answers`:

```markdown
## Quiz

1. What does the cache key ignore?
2. Why sort the query parameters?

## Answers

1. The query string.
2. So that the same parameters in a different order share one entry.
```

voce reads each question and waits. Answer out loud, then press space to hear the answer. The answers aren't
read in their own section, so they never give the game away. If the counts don't match, the file is read as it
is, and `voce --check` tells you.

```bash
voce --quiz            # every quiz in the playlist
voce --quiz 2          # just part 2's quizzes
voce --quiz file.md    # one file's quiz
```

## Writing for the ear

`voce --check` reports how a file will read: the number of sentences and words, the minutes, the characters sent
to the voice, the quiz pairing, and any sentences long enough to be hard to follow by ear. A few habits help:

- Keep sentences under about 30 words. Long ones are hard to hold in your head.
- Put code in fenced blocks. It is highlighted and read line by line, the way a person reads code aloud, so keep
  examples short. `--skip-code` shows code without reading it.
- Use a `<details>` block for anything that is for the eye only. It is shown but never read.
- Lines that are only links, such as breadcrumbs at the top or "Next:" at the bottom, are shown and skipped.
