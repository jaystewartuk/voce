import pytest

from voce.document import load
from voce.playlist import PlaylistError, find_playlist, part_matches, read_playlist, update_minutes
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
    state = State(tmp_path / "state.json")
    state.place(doc.path, doc.units, 2)
    state.save(force=True)
    path.write_text("New first. One. Two. Three.\n")
    again = State(tmp_path / "state.json")
    assert again.resume(doc.path, load(path).units) == 3
    assert again.progress(doc.path) == "66%"
    again.done(doc.path)
    assert again.resume(doc.path, load(path).units) == 0 and again.progress(doc.path) == "done"


def test_usage_counts_by_month(tmp_path):
    state = State(tmp_path / "s.json")
    state.count(100)
    state.count(50)
    assert state.month_chars() == 150


def test_clips_are_reused_for_the_same_text(tmp_path):
    first = save_clip("Hello.\r\n", "clipboard", tmp_path)
    assert first.read_text() == "Hello.\n"
    assert save_clip("Hello.", "clipboard", tmp_path) == first
    with pytest.raises(ClipError):
        save_clip("  \n", "clipboard", tmp_path)
