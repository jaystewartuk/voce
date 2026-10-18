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
from voce.ui.terminal import DRAG, PRESS, RELEASE, WHEEL_DOWN, decode_sgr_mouse


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
    bar = dim = heading = selected = progress = 0
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


def click(r, x, y):
    r.mouse((PRESS, x, y))
    r.mouse((RELEASE, x, y))


def play_through(r, ticks=200):
    for _ in range(ticks):
        r.tick()
        if r.mode == "playing":
            r.player.done = True
        r.gap_until = 0
        r.draw()


def test_an_empty_file_in_a_playlist_stops_cleanly(tmp_path):
    r = reader(tmp_path, {"a.md": "One.", "b.md": "[Next](c.md)", "c.md": "Three."})
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
    click(r, 5, 23)  # the status bar
    assert r.pos == 0
    click(r, 70, 1)  # far right of the first line, past its end
    assert r.units[r.pos].say == "Second."


def test_a_stuck_player_is_skipped(tmp_path):
    r = reader(tmp_path, {"a.md": "One. Two."})
    r.tick()
    assert r.mode == "playing"
    r.deadline = time.monotonic() - 1
    r.tick()
    assert r.mode == "gap" and "stopped responding" in r.message


def test_pausing_in_the_gap_after_a_sentence_carries_on_to_the_next(tmp_path):
    r = reader(tmp_path, {"a.md": "One. Two. Three."})
    r.tick()
    r.player.done = True
    r.tick()
    assert r.mode == "gap" and r.pos == 0
    r.toggle()  # space while the last word is still in the ear: the sentence has already been read
    assert r.mode == "paused"
    r.toggle()
    assert r.pos == 1 and r.mode == "loading"
    r.tick()
    assert r.player.played[-1].name == "Two."
    r.player.can_pause = False  # with afplay a pause mid-sentence stops it, and carrying on replays that sentence
    r.toggle()
    assert r.mode == "paused"
    r.toggle()
    r.tick()
    assert r.pos == 1 and r.player.played[-2:] == [Path("/audio/Two."), Path("/audio/Two.")]


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


def test_copy_keys_and_a_click_on_code(tmp_path, monkeypatch):
    copied = []
    monkeypatch.setattr("voce.ui.reader.write_clipboard", copied.append)
    r = reader(tmp_path, {"a.md": "First one. Second one.\n\n```php\n$x = 1;\n$y = 2;\n```\n\nAfter."})
    r.key(ord("c"))
    assert copied == ["First one."] and r.message == "Copied the sentence"
    r.key(ord("C"))
    assert copied[-1] == "First one. Second one." and r.message == "Copied the paragraph"
    r.draw()
    code = next(n for n, ln in enumerate(r.view.lines) if ln.block >= 0 and r.doc.blocks[ln.block].kind == "code")
    click(r, 10, code + 3)  # the second line of code, under the language header
    assert r.doc.blocks[r.units[r.pos].block].text[r.units[r.pos].start:r.units[r.pos].end] == "$y = 2;"
    click(r, 10, code + 1)  # the language header counts as the first line
    assert r.units[r.pos].start == 0 and r.doc.blocks[r.units[r.pos].block].kind == "code"
    r.key(ord("C"))
    assert copied[-1] == "$x = 1;\n$y = 2;" and r.message == "Copied the paragraph"
    assert len(copied) == 3  # the clicks on code read it; they do not copy


def test_a_click_on_unread_code_copies_it(tmp_path, monkeypatch):
    copied = []
    monkeypatch.setattr("voce.ui.reader.write_clipboard", copied.append)
    r = reader(tmp_path, {"a.md": "First one.\n\n```php\n$x = 1;\n$y = 2;\n```\n\nAfter."}, skip_code=True)
    r.draw()
    code = next(n for n, ln in enumerate(r.view.lines) if ln.block >= 0 and r.doc.blocks[ln.block].kind == "code")
    click(r, 10, code + 2)
    assert copied == ["$x = 1;\n$y = 2;\n"] and r.message == "Copied the code, 2 lines"
    assert r.pos == 0


def test_the_sentence_being_read_glides_to_the_anchor_row(tmp_path):
    md = "\n\n".join(f"Sentence number {i} is here." for i in range(60))
    r = reader(tmp_path, {"a.md": md})
    anchor = r.view.anchor()
    r.draw()
    assert r.view.top == 0  # the first sentence stays at the top: nothing above it to show
    r.go(30)
    r.draw()
    first = r.view.where[r.units[30].block]
    assert r.view.top == first - anchor  # a jump to somewhere off screen snaps there at once
    r.go(32)  # two blank-separated sentences on: four lines further down
    tops = []
    for _ in range(6):
        r.draw()
        tops.append(r.view.top)
    goal = r.view.where[r.units[32].block] - anchor
    assert tops[0] < goal and tops[-1] == goal  # a nearby move glides a line or so a frame
    assert all(b - a in (0, 1, 2) for a, b in zip(tops, tops[1:]))
    r.go(len(r.units) - 1)
    r.draw()
    # the last line rises to the anchor rather than stopping
    assert r.view.top == r.view.where[r.units[-1].block] - anchor


def test_carrying_on_after_a_wheel_scroll_brings_the_text_back(tmp_path):
    md = "\n\n".join(f"Sentence number {i} is here." for i in range(60))
    r = reader(tmp_path, {"a.md": md})
    r.go(10)
    r.draw()
    r.tick()
    r.tick()
    assert r.mode == "playing"
    r.toggle()
    assert r.mode == "held"
    for _ in range(5):
        r.mouse((WHEEL_DOWN, 0, 0))
    assert r.view.scrolled
    r.toggle()
    assert r.mode == "playing" and not r.view.scrolled


def test_a_drag_copies_the_text_it_crosses_without_moving_the_voice(tmp_path, monkeypatch):
    copied = []
    monkeypatch.setattr("voce.ui.reader.write_clipboard", copied.append)
    md = "First one. Second one.\n\nAnother paragraph here.\n\n```php\n$x = 1;\n$y = 2;\n```\n"
    r = reader(tmp_path, {"a.md": md})
    r.go(1)
    r.draw()
    m = r.view.margin
    # within one line: from "Second" to the end of the line, the far cell included
    r.mouse((PRESS, m + 11, 1))
    r.mouse((DRAG, m + 16, 1))
    assert r.view.selection and r.view.selected_on(0) == (11, 17)
    r.mouse((RELEASE, m + 21, 1))
    assert copied == ["Second one."] and r.message == "Copied the selection"
    assert r.pos == 1 and r.view.selection  # the voice stayed where it was; the selection shows until the next sentence
    # across lines, backwards, through a blank line and into the code: blocks come out whole with real line breaks
    code = next(n for n, ln in enumerate(r.view.lines) if ln.block >= 0 and r.doc.blocks[ln.block].kind == "code")
    r.mouse((PRESS, m + 8, code + 3))
    r.mouse((RELEASE, m + 8, 3))
    assert copied[-1] == "paragraph here.\n\n$x = 1;\n$y = 2;" and r.message == "Copied 4 lines"
    assert r.pos == 1
    # a press and release in the same cell is still a click
    click(r, m + 2, 1)
    assert r.pos == 0 and r.view.selection is None
    # the next sentence clears the highlight
    r.mouse((PRESS, m, 1))
    r.mouse((RELEASE, m + 5, 1))
    assert r.view.selection
    r.go(1)
    assert r.view.selection is None


def test_the_text_holds_still_while_the_button_is_down(tmp_path):
    md = "\n\n".join(f"Sentence number {i} is here." for i in range(60))
    r = reader(tmp_path, {"a.md": md})
    r.go(30)
    r.draw()
    top = r.view.top
    r.mouse((PRESS, r.view.margin, 5))
    r.mouse((DRAG, r.view.margin + 4, 6))
    r.go(40)  # the voice moves on under a held button: the view stays and so does the selection
    r.draw()
    assert r.view.top == top and r.view.selection
    r.mouse((RELEASE, r.view.margin + 4, 6))
    r.draw()
    assert r.view.top == top  # still, until the next sentence
    r.go(41)
    r.draw()
    assert r.view.top != top and r.view.selection is None


def test_sgr_mouse_reports_decode_to_press_drag_release_and_wheel():
    assert decode_sgr_mouse("[<0;5;3M") == (PRESS, 4, 2)
    assert decode_sgr_mouse("[<32;6;3M") == (DRAG, 5, 2)
    assert decode_sgr_mouse("[<0;7;3m") == (RELEASE, 6, 2)
    assert decode_sgr_mouse("[<65;1;1M") == (WHEEL_DOWN, 0, 0)
    assert decode_sgr_mouse("[<65;1;1m") is None  # the wheel has no release
    assert decode_sgr_mouse("[<2;1;1M") is None   # the right button is the terminal's


def test_the_title_bar_fills_as_the_file_is_read(tmp_path):
    md = "\n\n".join(f"Sentence number {i} is here." for i in range(10))
    r = reader(tmp_path, {"a.md": md})
    r.draw()
    assert r.progress() == 0.0
    r.go(5)
    r.draw()
    assert r.progress() == 0.5
    play_through(r)
    assert r.mode == "end" and r.progress() == 1.0
