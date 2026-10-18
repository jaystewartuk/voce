import json
import os

import pytest

from voce.sources.claude import TranscriptError, last_reply, latest_transcript, project_folder


def entry(kind, content, **extra):
    return json.dumps({"type": kind, "message": {"role": kind, "content": content}, **extra})


def transcript(tmp_path, *lines, name="s.jsonl"):
    path = tmp_path / name
    path.write_text("\n".join(lines) + "\n")
    return path


def test_the_final_message_after_the_last_tool_call(tmp_path):
    path = transcript(
        tmp_path,
        entry("user", "first question"),
        entry("assistant", [{"type": "text", "text": "Old answer."}]),
        entry("user", "second question"),
        entry("assistant", [{"type": "thinking", "thinking": "hmm"}]),
        entry("assistant", [{"type": "text", "text": "Let me look."}]),
        entry("assistant", [{"type": "tool_use", "id": "1", "name": "Bash", "input": {}}]),
        entry("user", [{"type": "tool_result", "tool_use_id": "1", "content": "ok"}]),
        entry("assistant", [{"type": "text", "text": "**The answer.**"}]),
        entry("assistant", [{"type": "text", "text": "With a second part."}]),
        "not json",
    )
    assert last_reply(path) == "**The answer.**\n\nWith a second part."


def test_slash_commands_subagents_and_meta_do_not_hide_the_reply(tmp_path):
    path = transcript(
        tmp_path,
        entry("user", "question"),
        entry("assistant", [{"type": "text", "text": "Answer."}]),
        entry("assistant", [{"type": "text", "text": "Subagent chatter."}], isSidechain=True),
        entry("user", "<command-name>/copy</command-name>"),
        entry("user", "<local-command-stdout>Copied</local-command-stdout>"),
        entry("user", "hidden", isMeta=True),
    )
    assert last_reply(path) == "Answer."


def test_a_turn_still_running_falls_back_to_the_previous_reply(tmp_path):
    path = transcript(
        tmp_path,
        entry("user", "one"),
        entry("assistant", [{"type": "text", "text": "Done."}]),
        entry("user", "two"),
        entry("assistant", [{"type": "tool_use", "id": "1", "name": "Read", "input": {}}]),
    )
    assert last_reply(path) == "Done."


def test_no_reply_is_an_error(tmp_path):
    with pytest.raises(TranscriptError):
        last_reply(transcript(tmp_path, entry("user", "hello")))


def test_latest_transcript_prefers_this_folder(tmp_path):
    projects = tmp_path / "home" / "projects"
    cwd = tmp_path / "work dir"
    cwd.mkdir()
    mine = projects / project_folder(cwd.resolve())
    other = projects / "-elsewhere"
    mine.mkdir(parents=True)
    other.mkdir()
    old = transcript(mine, entry("user", "x"), name="old.jsonl")
    new = transcript(other, entry("user", "x"), name="new.jsonl")
    os.utime(old, (1, 1))
    assert latest_transcript(cwd, tmp_path / "home") == old
    old.unlink()
    assert latest_transcript(cwd, tmp_path / "home") == new
    new.unlink()
    with pytest.raises(TranscriptError):
        latest_transcript(cwd, tmp_path / "home")


def test_project_folder_naming():
    assert project_folder("/Users/someone/my.repo") == "-Users-someone-my-repo"
