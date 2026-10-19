import json

import pytest

from voce.document import load
from voce.playlist import PlaylistError, find_playlist, parse_playlist, part_matches, read_playlist, update_minutes
from voce.sources.clips import ClipError, save_clip
from voce.state import State


def make_course(tmp_path):
    (tmp_path / "a.md").write_text("# A\n\nOne. Two.\n")
    (tmp_path / "b.md").write_text("# B\n\nThree.\n")
    readme = tmp_path / "README.md"
    readme.write_text("# Course\n\n## Listen in this order\n\n### Part 3. Later\n\n1. [A](a.md) · 9 min\n\n"
                      "### Part 1. First\n\n2. [B](b.md) · 9 min\n3. [Missing](nope.md)\n\n## Other\n\n"
                      "1. [Not this](a.md)\n")
    return readme


def test_reads_entries_with_parts_and_skips_missing_files(tmp_path):
    entries = read_playlist(make_course(tmp_path))
    assert [(e.title, e.part) for e in entries] == [("A", "Part 3. Later"), ("B", "Part 1. First")]


def test_parse_playlist_is_the_text_alone_with_links_as_written(tmp_path):
    items = parse_playlist(make_course(tmp_path).read_text())
    assert items == [{"path": "a.md", "title": "A", "part": "Part 3. Later", "minutes": 9},
                     {"path": "b.md", "title": "B", "part": "Part 1. First", "minutes": 9},
                     {"path": "nope.md", "title": "Missing", "part": "Part 1. First", "minutes": 0}]
    assert parse_playlist("# No playlist here\n\n1. [A](a.md)\n") == []


def test_find_playlist_by_folder_and_errors(tmp_path):
    readme = make_course(tmp_path)
    assert find_playlist(tmp_path) == readme
    (tmp_path / "plain").mkdir()
    (tmp_path / "plain" / "README.md").write_text("# Nothing here\n")
    with pytest.raises(PlaylistError):
        find_playlist(tmp_path / "plain")


def test_parts_match_by_number_in_the_heading_not_position():
    assert part_matches("Part 3. Later", "3")
    assert not part_matches("Part 3. Later", "1")
    assert part_matches("2. Basics", "2")
    assert part_matches("Part 3. Later", "later")


def test_update_minutes(tmp_path):
    readme = make_course(tmp_path)
    update_minutes(readme)
    assert "[A](a.md) · 1 min" in readme.read_text()


def test_state_resumes_by_text_when_the_file_changes(tmp_path):
    path = tmp_path / "a.md"
    path.write_text("One. Two. Three.\n")
    doc = load(path)
    state = State(tmp_path / "state")
    state.place(doc.path, doc.units, 2)
    state.save(force=True)
    path.write_text("New first. One. Two. Three.\n")
    again = State(tmp_path / "state")
    assert again.progress(doc.path) == "66%"
    assert again.resume(doc.path, load(path).units) == 3
    again.done(doc.path)
    assert again.resume(doc.path, load(path).units) == 0 and again.progress(doc.path) == "done"
    again.save(force=True)
    assert len(list((tmp_path / "state" / "places").glob("*.json"))) == 1  # the old hash's place moved, not copied


def test_places_are_keyed_by_text_so_a_copy_elsewhere_resumes(tmp_path):
    a, b = tmp_path / "here" / "a.md", tmp_path / "there" / "renamed.md"
    a.parent.mkdir(), b.parent.mkdir()
    a.write_text("One. Two. Three.\n")
    b.write_text(a.read_text())
    state = State(tmp_path / "state")
    state.place(a, load(a).units, 1)
    state.save(force=True)
    again = State(tmp_path / "state")
    assert again.resume(b, load(b).units) == 1 and again.progress(b) == "33%"
    place = json.loads(next((tmp_path / "state" / "places").glob("*.json")).read_text())
    assert place["pos"] == 1 and set(place) >= {"at", "total", "updated", "paths"}


def test_old_state_json_is_migrated_to_places(tmp_path):
    path = tmp_path / "a.md"
    path.write_text("One. Two. Three.\n")
    old = {"files": {str(path): {"pos": 2, "at": "Three.", "total": 3}, "/gone.md": {"pos": 1}},
           "usage": {"2000-01": 5}, "speed": 1.4, "last": str(path)}
    (tmp_path / "state.json").write_text(json.dumps(old))
    state = State(tmp_path)
    assert state.get("speed") == 1.4 and state.get("last") == str(path)
    assert state.resume(path, load(path).units) == 2 and state.usage == {"2000-01": {"google": 5}}
    assert not (tmp_path / "state.json").exists() and (tmp_path / "state-v1.json").exists()
    assert (tmp_path / "settings.json").exists() and len(list((tmp_path / "places").glob("*.json"))) == 1
    assert State(tmp_path).resume(path, load(path).units) == 2  # and loading again finds the same


def test_only_what_changed_is_written(tmp_path):
    a, b = tmp_path / "a.md", tmp_path / "b.md"
    a.write_text("One. Two.\n"), b.write_text("Three. Four.\n")
    state = State(tmp_path / "state")
    state.place(a, load(a).units, 1), state.place(b, load(b).units, 1)
    state.save(force=True)
    places = tmp_path / "state" / "places"
    before = {f.name: f.stat().st_mtime_ns for f in places.glob("*.json")}
    assert len(before) == 2
    state.done(b)
    state.save(force=True)
    after = {f.name: f.stat().st_mtime_ns for f in places.glob("*.json")}
    assert sum(before[n] != after[n] for n in before) == 1


def test_usage_counts_by_month(tmp_path):
    state = State(tmp_path / "s.json")
    state.count("google", 100)
    state.count("google", 50)
    assert state.month_chars("google") == 150 and state.month_chars("azure") == 0


def test_clips_are_reused_for_the_same_text(tmp_path):
    first = save_clip("Hello.\r\n", "clipboard", tmp_path)
    assert first.read_text() == "Hello.\n"
    assert save_clip("Hello.", "clipboard", tmp_path) == first
    with pytest.raises(ClipError):
        save_clip("  \n", "clipboard", tmp_path)
