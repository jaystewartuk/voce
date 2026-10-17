"""Claude Code's latest reply, read from its session transcript, so there is no need to /copy it first.

Claude Code keeps each session as JSON lines under ~/.claude/projects/<folder>/<session>.jsonl, where <folder>
is the working directory with every character that isn't a letter or digit turned into "-". The reply is the
same text /copy takes: what Claude wrote after its last tool call in answer to your last prompt. Thinking,
progress notes between tool calls, subagents and slash-command output are left out.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

_NOT_A_PROMPT = ("<command-", "<local-command", "<system-reminder", "<bash-", "<user-memory", "Caveat:")


class TranscriptError(Exception):
    pass


def claude_home() -> Path:
    return Path(os.environ.get("CLAUDE_CONFIG_DIR", "~/.claude")).expanduser()


def project_folder(cwd: Path) -> str:
    return re.sub(r"[^A-Za-z0-9]", "-", str(cwd))


def latest_transcript(cwd: Path | None = None, home: Path | None = None) -> Path:
    """The most recently written session for this folder, or for any folder if this one has none."""
    projects = (home or claude_home()) / "projects"
    here = projects / project_folder((cwd or Path.cwd()).resolve())
    for folder, pattern in ((here, "*.jsonl"), (projects, "*/*.jsonl")):
        sessions = list(folder.glob(pattern)) if folder.is_dir() else []
        if sessions:
            return max(sessions, key=lambda p: p.stat().st_mtime)
    raise TranscriptError(f"No Claude Code sessions found in {projects}.")


def _texts(content) -> list[str]:
    if isinstance(content, str):
        return [content]
    if isinstance(content, list):
        return [c.get("text", "") for c in content if isinstance(c, dict) and c.get("type") == "text"]
    return []


def last_reply(transcript: Path) -> str:
    """The text of the last reply in the transcript, as Markdown."""
    replies: list[list[str]] = [[]]
    with transcript.open(encoding="utf-8") as lines:
        for line in lines:
            try:
                entry = json.loads(line)
            except ValueError:
                continue
            if not isinstance(entry, dict) or entry.get("isSidechain") or entry.get("isMeta"):
                continue
            message = entry.get("message")
            if not isinstance(message, dict):
                continue
            texts = [t for t in _texts(message.get("content")) if t.strip()]
            if entry.get("type") == "user" and texts and not texts[0].lstrip().startswith(_NOT_A_PROMPT):
                replies.append([])
            elif entry.get("type") == "assistant":
                content = message.get("content")
                if isinstance(content, list) and any(c.get("type") == "tool_use" for c in content
                                                     if isinstance(c, dict)):
                    replies[-1] = []  # what came before a tool call was a progress note
                replies[-1] += texts
    reply = next((r for r in reversed(replies) if r), None)
    if not reply:
        raise TranscriptError(f"No reply from Claude in {transcript}.")
    return "\n\n".join(t.strip() for t in reply)
