"""A pull request written as Markdown, the way a reviewer would walk through it out loud.

The title, then one paragraph that says what it is: who opened it, its state, the branches, how big it is, its
labels, reviewers and checks. Then the description, the commits, each changed file with its diff, and the
conversation with inline comments shown against the lines they are about. The diff fences say the file's
language (```diff python), so the added lines are highlighted and read in that language's words.

The file is written to ~/.local/state/voce/pulls/, one per pull request, and only when it has changed, so your
place in it is kept across fetches and a reader already open on it reloads.
"""

from __future__ import annotations

import datetime
import re
from pathlib import Path

from voce import highlight, paths
from voce.sources.github import ChangedFile, Check, Client, Comment, PullRequest, Review, fetch_pull_request, parse_ref

HUNK_TAIL = 4  # lines of GitHub's diff hunk shown above an inline comment: the line itself and a little before


def when(iso: str) -> str:
    """An API timestamp as a date people say: 17 October 2026."""
    try:
        dt = datetime.datetime.strptime(iso[:10], "%Y-%m-%d")
    except ValueError:
        return ""
    return f"{dt.day} {dt:%B %Y}"


def fence_for(text: str) -> str:
    """A backtick fence longer than any run of backticks in the text, so a diff of Markdown can't close it."""
    longest = max((len(m) for m in re.findall(r"`+", text)), default=0)
    return "`" * max(4, longest + 1)


def demote(body: str) -> str:
    """Headings in a description one level down, so they sit under the document's own sections."""
    out, fence = [], ""
    for line in body.replace("\r\n", "\n").split("\n"):
        m = re.match(r"^\s*(`{3,}|~{3,})", line)
        if m:
            if not fence:
                fence = m.group(1)
            elif line.strip().startswith(fence[0] * len(fence)):
                fence = ""
        elif not fence:
            line = re.sub(r"^(\s{0,3})(#{1,5})(\s)", r"\1#\2\3", line)
        out.append(line)
    return "\n".join(out).strip()


def people(logins: list[str]) -> str:
    names = [lg for lg in logins if lg]
    if len(names) <= 1:
        return "".join(names)
    return ", ".join(names[:-1]) + " and " + names[-1]


def plural(n: int, word: str) -> str:
    return f"{n} {word}{'s' * (n != 1)}"


# ---------------------------------------------------------------- the summary

def state_sentence(pr: PullRequest) -> str:
    if pr.merged:
        by = f" by {pr.merged_by}" if pr.merged_by else ""
        return f"Merged{by} on {when(pr.merged_at)}."
    if pr.state == "closed":
        return f"Closed without merging on {when(pr.closed_at)}."
    return "It is a draft." if pr.draft else "It is open."


def checks_sentence(checks: list[Check]) -> str:
    done = [c for c in checks if c.status == "completed"]
    running = len(checks) - len(done)
    passed = sum(1 for c in done if c.conclusion == "success")
    failed = [c.name for c in done if c.conclusion in ("failure", "timed_out", "cancelled", "action_required")]
    if not checks or not (passed or failed or running):
        return ""
    parts = []
    if passed:
        parts.append(f"{passed} passed")
    if failed:
        named = ", ".join(failed[:3]) + (" and more" if len(failed) > 3 else "")
        parts.append(f"{len(failed)} failed: {named}")
    if running:
        parts.append(f"{running} still running")
    return "Checks: " + ", ".join(parts) + "."


def summary(pr: PullRequest) -> str:
    ref = pr.ref
    opened = f" on {when(pr.created_at)}" if pr.created_at else ""
    sentences = [f"Pull request {ref.number} in `{ref.full_name}`, opened by {pr.author}{opened}.",
                 state_sentence(pr)]
    fork = f" from `{pr.head_repo}`" if pr.head_repo and pr.head_repo != ref.full_name else ""
    sentences.append(f"It merges `{pr.head}`{fork} into `{pr.base}`.")
    sentences.append(f"{plural(len(pr.commits) or 1, 'commit')}, {plural(pr.changed_files, 'file')} changed "
                     f"(+{pr.additions} −{pr.deletions}).")
    if pr.labels:
        sentences.append(f"Labels: {', '.join(pr.labels)}.")
    if pr.reviewers:
        sentences.append(f"Reviewers: {people(pr.reviewers)}.")
    checks = checks_sentence(pr.checks)
    if checks:
        sentences.append(checks)
    return " ".join(sentences)


# ---------------------------------------------------------------- the changes

def file_heading(f: ChangedFile) -> str:
    stat = f" (+{f.additions} −{f.deletions})" if f.additions and f.deletions else \
        f" (+{f.additions})" if f.additions else f" (−{f.deletions})" if f.deletions else ""
    if f.status == "added":
        return f"### `{f.path}` new file{stat}"
    if f.status == "removed":
        return f"### `{f.path}` deleted{stat}"
    if f.status in ("renamed", "copied") and f.previous_path:
        what = "renamed" if f.status == "renamed" else "copied"
        return f"### `{f.path}` {what} from `{f.previous_path}`{stat}"
    return f"### `{f.path}`{stat}"


def diff_block(patch: str, filename: str) -> str:
    fence = fence_for(patch)
    lang = highlight.language_for(filename)
    return f"{fence}diff{' ' + lang if lang else ''}\n{patch.rstrip()}\n{fence}"


def changes(pr: PullRequest) -> list[str]:
    out = ["## Changes"]
    if not pr.files:
        out.append("No files changed.")
    for f in pr.files:
        out.append(file_heading(f))
        if f.patch:
            out.append(diff_block(f.patch, f.path))
        elif f.status in ("renamed", "copied") and not (f.additions or f.deletions):
            out.append("Moved without changes.")
        else:
            out.append("GitHub shows no diff for this file: it is binary, or the change is too large.")
    return out


# ---------------------------------------------------------------- the conversation

REVIEW_WORDS = {"APPROVED": "approved", "CHANGES_REQUESTED": "requested changes", "COMMENTED": "commented",
                "DISMISSED": "had a review dismissed"}


def comment_heading(c: Comment, level: str = "###") -> str:
    if c.reply_to:
        return f"{level} {c.author} replied"
    if c.path:
        where = f" line {c.line}" if c.line else ""
        old = " (on an older version)" if c.outdated else ""
        return f"{level} {c.author} on `{c.path}`{where}{old}"
    return f"{level} {c.author} commented"


def hunk_tail(hunk: str, filename: str) -> str:
    """The last few lines of the diff GitHub shows with an inline comment, as a diff block."""
    lines = [ln for ln in hunk.replace("\r\n", "\n").split("\n") if not ln.startswith("@@")]
    tail = "\n".join(lines[-HUNK_TAIL:]).rstrip()
    return diff_block(tail, filename) if tail.strip() else ""


def conversation(pr: PullRequest) -> list[str]:
    """Reviews, comments and inline threads in the order they happened; replies under what they answer."""
    events: list[tuple[str, int, object]] = []
    for r in pr.reviews:
        if r.state in REVIEW_WORDS and (r.body.strip() or r.state != "COMMENTED"):
            events.append((r.at, 0, r))
    roots = [c for c in pr.comments if not c.reply_to]
    replies: dict[int, list[Comment]] = {}
    for c in pr.comments:
        if c.reply_to:
            replies.setdefault(c.reply_to, []).append(c)
    for c in roots:
        events.append((c.at, 1, c))
    if not events:
        return []
    out = ["## Conversation"]
    for _, _, event in sorted(events, key=lambda e: (e[0], e[1])):
        if isinstance(event, Review):
            out.append(f"### {event.author} {REVIEW_WORDS[event.state]}")
            if event.body.strip():
                out.append(demote(event.body))
            continue
        c: Comment = event  # type: ignore[assignment]
        out.append(comment_heading(c))
        if c.path and c.hunk:
            block = hunk_tail(c.hunk, c.path)
            if block:
                out.append(block)
        if c.body.strip():
            out.append(demote(c.body))
        for reply in sorted(replies.get(c.id, []), key=lambda r: r.at):
            out.append(comment_heading(reply, "####"))
            if reply.body.strip():
                out.append(demote(reply.body))
    return out


# ---------------------------------------------------------------- the whole document

def to_markdown(pr: PullRequest) -> str:
    parts = [f"# {pr.title.strip() or f'Pull request {pr.ref.number}'}", summary(pr), "## Description",
             demote(pr.body) if pr.body.strip() else "No description."]
    if len(pr.commits) > 1:
        parts.append("## Commits")
        parts.append("\n".join(f"- {c.subject}" + (f" (by {c.author})" if c.author != pr.author and c.author else "")
                               for c in pr.commits))
    parts += changes(pr)
    parts += conversation(pr)
    return "\n\n".join(p for p in parts if p) + "\n"


def save(pr: PullRequest, folder: Path | None = None) -> Path:
    """Write the pull request as Markdown to its own file, touching the file only when the text has changed."""
    folder = folder or paths.pulls_dir()
    folder.mkdir(parents=True, exist_ok=True)
    ref = pr.ref
    host = "" if ref.host == "github.com" else ref.host.replace(".", "-") + "-"
    path = folder / f"{host}{ref.owner}-{ref.repo}-{ref.number}.md"
    text = to_markdown(pr)
    if not path.exists() or path.read_text(encoding="utf-8") != text:
        path.write_text(text, encoding="utf-8")
    return path


def read_pull_request(text: str, cwd: Path | None = None, client: Client | None = None,
                      folder: Path | None = None) -> Path:
    """From how the user wrote the pull request to the Markdown file to read."""
    ref = parse_ref(text, cwd)
    return save(fetch_pull_request(ref, client), folder)
