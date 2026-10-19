import shutil
import subprocess
import sys

import pytest

from voce.document import Unit, load
from voce.export import QUIZ_THINKING, export_mp3, silence_after, spoken
from voce.state import State
from voce.voices import Mac, Voice


def test_spoken_starts_each_file_with_its_title(tmp_path):
    (tmp_path / "a.md").write_text("# First\n\nOne.\n")
    (tmp_path / "b.md").write_text("# Second.\n\nTwo.\n")
    units = spoken([load(tmp_path / "a.md"), load(tmp_path / "b.md")])
    assert [u.say for u in units] == ["First.", "First", "One.", "Second.", "Second.", "Two."]


def test_silence_follows_the_reader_and_gives_time_to_answer():
    assert silence_after(Unit(0, 0, 0, "x", pause=0.4)) == 0.4
    assert silence_after(Unit(0, 0, 0, "x", pause=0.0)) == 0.1
    assert silence_after(Unit(0, 0, 0, "x", pause=0.3, wait=True)) == round(0.3 + QUIZ_THINKING, 2)


@pytest.mark.skipif(sys.platform != "darwin" or not shutil.which("ffmpeg"), reason="needs macOS say and ffmpeg")
def test_exports_one_mp3_with_the_mac_voice(tmp_path):
    (tmp_path / "a.md").write_text("# Hello\n\nA short test.\n")
    state = State(tmp_path / "s.json")
    out = export_mp3([load(tmp_path / "a.md")], tmp_path / "out" / "a.mp3",
                     Voice(Mac(), state, cache=tmp_path / "cache"), state, say=lambda _: None)
    info = subprocess.run(["afinfo", str(out)], capture_output=True, text=True).stdout
    assert "24000 Hz" in info and out.stat().st_size > 1000
