# A voce library

This repository is a library for [voce](https://github.com/jaystewartuk/voce), which reads Markdown aloud. When
asked to add something to listen to, write Markdown files and list them in the playlist in README.md.

## The playlist

`README.md` has a `## Listen in this order` section. voce reads the numbered links under it, in order, grouped by
the `###` headings above them:

```markdown
## Listen in this order

### Part 1. Ownership
1. [What a value owns](rust/ownership.md) · 8 min
2. [Borrowing](rust/borrowing.md) · 9 min
```

- Links are relative paths to `.md` files in this repository, under the README's folder.
- "· N min" is the listening time, at about 150 words a minute. Code takes longer than prose.
- Put each topic in its own folder.

## Writing to be heard

- Write for the ear: short sentences, one idea each, the point first.
- Headings, lists and tables are read in order. Keep tables small; each row is read as one sentence.
- Use real code in fenced blocks with a language (```` ```python ````). voce reads code the way a person says it,
  operators by the names the language's manual gives them. Keep blocks short; explain them in prose around them.
- Don't use pictures or diagrams to carry meaning; nothing is said for them.
- A `## Quiz` with a numbered list, followed by `## Answers` with the same number of answers, becomes a spoken quiz.

## Leave these alone

`places/`, `items/`, `texts/` and `prepared/` are written by voce: your place in each document and what was added
from the web app. `settings.json` is voce's settings on the Mac.
