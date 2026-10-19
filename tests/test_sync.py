import json
import shutil
import subprocess

import pytest

from voce import prepared, sync
from voce.document import load
from voce.playlist import Entry
from voce.state import State

needs_git = pytest.mark.skipif(not shutil.which("git"), reason="needs git")


def test_prepared_copy_holds_blocks_and_units_as_plain_json(tmp_path):
    path = tmp_path / "a.md"
    path.write_text("# Title\n\nSome **bold** and `code()`.\n\n```python\nx = 1\n```\n")
    state = State(tmp_path / "state")
    out = prepared.save(load(path), state)
    d = json.loads(out.read_text())
    assert out.parent.name == "prepared" and out.stem == state.key(path) and d["voce"] == prepared.FORMAT
    assert d["title"] == "Title" and d["file"] == "a.md" and d["words"] > 0
    assert [b["kind"] for b in d["blocks"]] == ["h1", "p", "code"]
    assert ["bold"] in [s[2] for s in d["blocks"][1]["spans"]]  # a frozenset became a list
    assert d["units"][0] == {"block": 0, "start": 0, "end": 5, "say": "Title", "pause": 0.8, "wait": False}
    before = out.stat().st_mtime_ns
    prepared.save(load(path), state)
    assert out.stat().st_mtime_ns == before  # the same text is not written twice


def test_prepared_copy_is_made_again_when_the_reading_code_changed(tmp_path, monkeypatch):
    path = tmp_path / "a.md"
    path.write_text("# A\n\nOne sentence.\n")
    state = State(tmp_path / "state")
    out = prepared.save(load(path), state)
    out.write_text(out.read_text().replace("One sentence.", "Old words."))
    prepared.save(load(path), state)
    assert "Old words." in out.read_text(), "the same reading code leaves a prepared file alone"
    monkeypatch.setattr(prepared, "MADE_BY", "something-else")
    prepared.save(load(path), state)
    d = json.loads(out.read_text())
    assert "Old words." not in out.read_text() and d["made"] == "something-else"


def test_index_lists_the_playlist_in_order_then_the_rest(tmp_path):
    for name in "abc":
        (tmp_path / f"{name}.md").write_text(f"# {name.upper()}\n\nOne.\n")
    state = State(tmp_path / "state")
    for name in "abc":
        prepared.save(load(tmp_path / f"{name}.md"), state)
    (tmp_path / "state" / "prepared" / ("x" * 64 + " (conflicted copy).json")).write_text("{}")
    entries = [Entry(tmp_path / "c.md", "C", "Part 1"), Entry(tmp_path / "a.md", "A", "Part 2")]
    d = json.loads(prepared.index(state, entries).read_text())
    assert [(r["title"], r["part"]) for r in d["documents"]] == [("C", "Part 1"), ("A", "Part 2"), ("B", "")]
    assert all(set(r) == {"hash", "title", "file", "part", "words", "minutes"} for r in d["documents"])


def test_remote_url_knows_a_github_repo_from_a_url():
    assert sync.remote_url("jay/voce") == "https://github.com/jay/voce.git"
    assert sync.remote_url("git@github.com:jay/voce.git") == "git@github.com:jay/voce.git"
    assert sync.remote_url("/tmp/x.git") == "/tmp/x.git" and sync.remote_url("https://h/a/b.git") == "https://h/a/b.git"


def bare(tmp_path):
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)
    return str(remote)


def device(tmp_path, name, remote):
    state = State(tmp_path / name)
    sync.setup(state.root, remote, lambda s: None)
    return state


@needs_git
def test_two_devices_share_places_and_the_newer_place_wins(tmp_path):
    doc_path = tmp_path / "a.md"
    doc_path.write_text("One. Two. Three. Four.\n")
    doc = load(doc_path)
    remote = bare(tmp_path)

    a = device(tmp_path, "a", remote)
    a.place(doc_path, doc.units, 2)
    prepared.save(doc, a)
    a.save(force=True)
    sync.run(a.root, lambda s: None)
    assert (a.root / ".gitignore").exists()

    b = device(tmp_path, "b", remote)
    sync.run(b.root, lambda s: None)
    b = State(b.root)
    assert b.resume(doc_path, doc.units) == 2
    assert (b.root / "prepared" / f"{b.key(doc_path)}.json").exists()

    a.place(doc_path, doc.units, 1)
    a.places[a.key(doc_path)]["updated"] = "2020-01-01T00:00:00Z"
    a.save(force=True)
    sync.run(a.root, lambda s: None)
    b.place(doc_path, doc.units, 3)
    b.places[b.key(doc_path)]["updated"] = "2030-01-01T00:00:00Z"
    b.save(force=True)
    sync.run(b.root, lambda s: None)  # conflicts with a's push and keeps the newer place
    assert State(b.root).resume(doc_path, doc.units) == 3
    sync.run(a.root, lambda s: None)
    assert State(a.root).resume(doc_path, doc.units) == 3
    assert "rebase" not in sync.git(a.root, "status")


@needs_git
def test_usage_stays_on_the_device(tmp_path):
    remote = bare(tmp_path)
    a = device(tmp_path, "a", remote)
    a.count("google", 5)
    a.set("speed", 1.5)
    a.save(force=True)
    sync.run(a.root, lambda s: None)
    assert "usage.json" not in sync.git(a.root, "ls-files") and "settings.json" in sync.git(a.root, "ls-files")
