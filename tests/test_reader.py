"""The reader's state machine, driven without a screen or sound."""

from __future__ import annotations

import concurrent.futures
import time
from pathlib import Path

import pytest

from voce.document import Unit
from voce.playlist import Entry
from voce.state import State
from voce.ui.reader import Options, Reader, same_place


class FakeScreen:
    def erase(self): pass
    def refresh(self): pass
    def timeout(self, _): pass


class FakeTerm:
    def __init__(self, h=24, w=80):
        self.h, self.w, self.scr, self.drawn = h, w, FakeScreen(), []

    def size(self):
        return self.h, self.w

    def put(self, y, x, text, attr=0):
        self.drawn.append((y, x, text))


class FakeTheme:
    bar = dim = heading = selected = 0
    def base(self, _): return 0
    def prefix(self, _): return 0
    def text(self, *_): return 0


class FakePlayer:
    can_pause = True
    def __init__(self): self.done, self.length, self.error, self.played = False, 1.0, "", []
    def play(self, path, duration, speed):
        self.done, self.length = False, duration
        self.played.append(path)
    def finished(self): return self.done
    def position(self): return 0.0
    def set_rate(self, _): pass
    def pause(self): pass
    def resume(self): pass
    def stop(self): pass


class FakeVoice:
    label, uses_google, warning, mac = "Test", False, "", True
    def want(self, text):
        f = concurrent.futures.Future()
        f.set_result((Path(f"/audio/{text}"), 1.0))
        return f
    def close(self): pass


def reader(tmp_path, files, **options):
    entries = []
    for name, md in files.items():
        path = tmp_path / name
        path.write_text(md)
        entries.append(Entry(path, name))
    r = Reader(FakeTerm(), FakeTheme(), Options(**options), State(tmp_path / "s.json"), FakeVoice(),
               lambda v: None, FakePlayer(), entries, 0)
    r.open(0)
    return r


def play_through(r, ticks=200):
    for _ in range(ticks):
        r.tick()
        if r.mode == "playing":
            r.player.done = True
        r.gap_until = 0
        r.draw()


def test_an_empty_file_in_a_playlist_stops_cleanly(tmp_path):
    r = reader(tmp_path, {"a.md": "One.", "b.md": "```\ncode only\n```", "c.md": "Three."})
    play_through(r)
    assert r.index == 1 and r.mode == "end" and "Nothing to read" in r.message
    r.key(ord(" "))  # space at the end moves on
    assert r.index == 2 and r.units


def test_reload_during_the_gap_keeps_going_forward(tmp_path):
    r = reader(tmp_path, {"a.md": "One. Two. Three."})
    r.tick()
    r.player.done = True
    r.tick()
    assert r.mode == "gap" and r.pos == 0
    r.doc.path.write_text("One. Two. Three. Four.")
    r.mtime, r.next_check = 0, 0
    r.reload_if_changed()
    assert r.mode == "gap" and r.pos == 0
    r.gap_until = 0
    r.tick()
    assert r.pos == 1


def test_same_place_prefers_the_nearest_repeat():
    old = [Unit(0, 0, 0, s) for s in ["Yes.", "No.", "Yes.", "No.", "Yes."]]
    new = [Unit(0, 0, 0, s) for s in ["Intro.", "Yes.", "No.", "Yes.", "No.", "Yes."]]
    assert same_place(old, new, 4) == 5
    assert same_place(old, [Unit(0, 0, 0, "Else.")], 4) == 0


def test_clicks_outside_the_text_are_ignored_and_clamped_to_the_line(tmp_path):
    r = reader(tmp_path, {"a.md": "First sentence here. Second.\n\nNext paragraph."})
    r.draw()
    r.mouse((1, 5, 23))  # the status bar
    assert r.pos == 0
    r.mouse((1, 70, 1))  # far right of the first line, past its end
    assert r.units[r.pos].say == "Second."


def test_a_stuck_player_is_skipped(tmp_path):
    r = reader(tmp_path, {"a.md": "One. Two."})
    r.tick()
    assert r.mode == "playing"
    r.deadline = time.monotonic() - 1
    r.tick()
    assert r.mode == "gap" and "stopped responding" in r.message


def test_restart_really_restarts(tmp_path):
    path = tmp_path / "a.md"
    path.write_text("One. Two. Three.")
    from voce.document import load
    doc = load(path)
    state = State(tmp_path / "s.json")
    state.place(doc.path, doc.units, 2)
    state.done(doc.path)
    state.restart(doc.path)
    assert state.resume(doc.path, doc.units) == 0
    state.place(doc.path, doc.units, 2)
    state.restart(doc.path)
    assert state.resume(doc.path, doc.units) == 0


def test_unreadable_file_is_reported_not_raised(tmp_path):
    r = reader(tmp_path, {"a.md": "One."})
    r.playlist.append(Entry(tmp_path / "gone.md", "gone"))
    r.open(1)
    assert r.mode == "end" and "Couldn't read gone.md" in r.message
    r.draw()


@pytest.mark.parametrize("bad", ["[]", '{"files": [], "usage": 3}'])
def test_odd_state_files_start_fresh(tmp_path, bad):
    (tmp_path / "s.json").write_text(bad)
    state = State(tmp_path / "s.json")
    assert state.data["files"] == {} and state.month_chars() == 0


def test_wheel_down_on_either_ncurses_mouse_version(monkeypatch):
    import curses

    from voce.ui import terminal

    # ncurses mouse version 2 (Linux, Homebrew): button 5 exists and is the only thing that counts
    monkeypatch.setattr(curses, "BUTTON5_PRESSED", 1 << 21, raising=False)
    assert terminal.wheel_down(1 << 21)
    assert not terminal.wheel_down(curses.REPORT_MOUSE_POSITION)
    # ncurses mouse version 1 (macOS's own): no button 5, wheel-down is a bare position report
    monkeypatch.delattr(curses, "BUTTON5_PRESSED", raising=False)
    assert terminal.wheel_down(curses.REPORT_MOUSE_POSITION)
    assert not terminal.wheel_down(curses.BUTTON4_PRESSED)
    assert not terminal.wheel_down(curses.REPORT_MOUSE_POSITION | curses.BUTTON1_PRESSED)
