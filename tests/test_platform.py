import shutil
import subprocess
import wave

import pytest

from voce import player
from voce.player import CommandPlayer
from voce.sources import clips
from voce.voices import audio_seconds, mp3_seconds


def test_a_wav_file_is_timed_from_its_header(tmp_path):
    path = tmp_path / "a.wav"
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(24000)
        w.writeframes(b"\0\0" * 36000)
    assert audio_seconds(path) == pytest.approx(1.5)


def frame(version_bits: int, bitrate_index: int, rate_index: int, length: int) -> bytes:
    header = bytes([0xFF, 0xE0 | version_bits << 3 | 1 << 1 | 1, bitrate_index << 4 | rate_index << 2, 0xC4])
    return header + b"\0" * (length - 4)


def test_an_mp3_is_timed_by_walking_its_frames():
    # MPEG-1 at 128 kb/s and 44.1 kHz: 417-byte frames of 1152 samples each
    data = b"ID3\x04\0\0\0\0\0\x05" + b"tags!" + frame(3, 9, 0, 417) * 100
    assert mp3_seconds(data) == pytest.approx(100 * 1152 / 44100)
    # MPEG-2 at 32 kb/s and 24 kHz, as Google sends: 96-byte frames of 576 samples
    assert mp3_seconds(frame(2, 4, 1, 96) * 50) == pytest.approx(50 * 576 / 24000)
    assert mp3_seconds(b"not audio at all") is None


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="needs ffmpeg")
def test_an_mp3_from_ffmpeg_is_timed_right(tmp_path):
    path = tmp_path / "tone.mp3"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-f", "lavfi", "-i", "sine=duration=2.5:sample_rate=24000",
                    "-c:a", "libmp3lame", "-b:a", "48k", str(path)], check=True)
    assert mp3_seconds(path.read_bytes()) == pytest.approx(2.5, abs=0.1)


def test_the_first_player_that_plays_the_file_is_used(tmp_path):
    p = CommandPlayer(names=["paplay", "ffplay"])
    assert p.command(tmp_path / "a.wav", 1.5)[0] == "paplay"
    assert p.command(tmp_path / "a.mp3", 1.5)[:1] == ["ffplay"]  # paplay plays WAV only
    assert "atempo=1.50" in p.command(tmp_path / "a.mp3", 1.5)
    assert CommandPlayer(names=["aplay"]).command(tmp_path / "a.mp3", 1.0) is None


def test_a_player_with_one_speed_keeps_the_highlight_at_that_speed(tmp_path, monkeypatch):
    started = []
    monkeypatch.setattr(player.subprocess, "Popen", lambda command, **kw: started.append(command) or FakeProc())
    p = CommandPlayer(names=["aplay"])
    p.play(tmp_path / "a.wav", 2.0, 1.5)
    p.set_rate(2.0)
    assert started[0][0] == "aplay" and p.speed == 1.0
    p = CommandPlayer(names=["mpv"])
    p.play(tmp_path / "a.wav", 2.0, 1.5)
    assert "--speed=1.50" in started[1] and p.speed == 1.5


def test_a_file_no_player_takes_is_reported(tmp_path):
    p = CommandPlayer(names=["aplay"])
    p.play(tmp_path / "a.mp3", 2.0, 1.0)
    assert "mpv" in p.error


def test_players_are_looked_for_by_platform(monkeypatch):
    monkeypatch.setattr(player.shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(player.sys, "platform", "linux")
    assert player.find_players() == ["mpv", "ffplay", "pw-play", "paplay", "aplay"]
    monkeypatch.setattr(player.sys, "platform", "darwin")
    assert player.find_players() == ["afplay"]


def test_the_clipboard_tool_follows_the_desktop(monkeypatch):
    have = {"wl-paste", "wl-copy", "xclip"}
    monkeypatch.setattr(clips.shutil, "which", lambda name: name if name in have else None)
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-0")
    assert clips._tool(clips.PASTE)[0] == "wl-paste"
    monkeypatch.delenv("WAYLAND_DISPLAY")
    assert clips._tool(clips.COPY)[0] == "xclip"
    have.clear()
    with pytest.raises(clips.ClipError, match="wl-clipboard"):
        clips._tool(clips.PASTE)


class FakeProc:
    def poll(self):
        return None

    def kill(self):
        pass

    def wait(self, timeout=None):
        return 0
