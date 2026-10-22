import wave

import pytest

from voce import player
from voce.player import CommandPlayer
from voce.sources import clips
from voce.voices import audio_seconds


def test_a_wav_file_is_timed_from_its_header(tmp_path):
    path = tmp_path / "a.wav"
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(24000)
        w.writeframes(b"\0\0" * 36000)
    assert audio_seconds(path) == pytest.approx(1.5)


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
