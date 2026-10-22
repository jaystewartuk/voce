import pytest

from voce import cli, voices
from voce.state import State
from voce.voices import Kokoro, Mac, Voice


def test_every_engine_cycles_its_voices_and_names_them_shortly():
    assert Kokoro().name == "af_heart" and Kokoro().label == "Kokoro Heart"
    assert Kokoro("bm_george").next_name() == "bm_fable" and Kokoro("af_nicole").next_name() == "af_heart"
    assert Mac().label == "Mac voice" and Mac("Daniel").label == "Mac Daniel"


def test_a_voice_name_tells_its_engine(tmp_path):
    state = State(tmp_path / "s.json")
    assert voices.engine_for("af_heart", state) == "kokoro"
    assert voices.engine_for("bm_george", state) == "kokoro"
    assert voices.engine_for("Daniel", state) == "mac"
    assert voices.engine_for("en-US-Chirp3-HD-Charon", state) == "mac"  # Google's names are gone with Google


def test_cache_keys_depend_on_engine_voice_and_text(tmp_path):
    state = State(tmp_path / "s.json")
    mac = Voice(Mac(), state, cache=tmp_path)
    kokoro = Voice(Kokoro(), state, cache=tmp_path)
    assert kokoro.path("hi") != kokoro.path("ho")
    assert (mac.path("hi").suffix, kokoro.path("hi").suffix) == (".aiff", ".wav")
    assert mac.key("hi") != kokoro.key("hi")
    assert Voice(Kokoro("bm_george"), state, cache=tmp_path).key("hi") != kokoro.key("hi")


def test_the_default_engine_is_kokoro_then_the_mac(tmp_path, monkeypatch):
    state = State(tmp_path / "s.json")
    monkeypatch.setattr(Kokoro, "configured", classmethod(lambda cls, state: False))
    monkeypatch.setattr(Mac, "configured", classmethod(lambda cls, state: False))
    assert voices.default_engine(state) == "kokoro"  # off a Mac: asked for, so its setup message is shown
    monkeypatch.setattr(Mac, "configured", classmethod(lambda cls, state: True))
    assert voices.default_engine(state) == "mac"
    monkeypatch.setattr(Kokoro, "configured", classmethod(lambda cls, state: True))
    assert voices.default_engine(state) == "kokoro"
    state.set("engine", "mac")
    assert voices.default_engine(state) == "mac"  # the engine chosen last time wins
    assert voices.available(state) == ["kokoro", "mac"]


def test_a_saved_cloud_engine_falls_back_to_kokoro(tmp_path, monkeypatch):
    state = State(tmp_path / "s.json")
    state.set("engine", "google")  # chosen when voce still had Google
    state.set("voices", {"google": "en-GB-Chirp3-HD-Leda", "kokoro": "bm_george"})
    monkeypatch.setattr(Kokoro, "configured", classmethod(lambda cls, state: True))
    assert voices.default_engine(state) == "kokoro"
    voice = cli.pick_voice(cli.parser().parse_args([]), state)
    assert voice.kind == "kokoro" and voice.name == "bm_george"


def test_without_kokoro_the_mac_voice_says_why(tmp_path, monkeypatch):
    state = State(tmp_path / "s.json")
    monkeypatch.setattr(Kokoro, "configured", classmethod(lambda cls, state: False))
    monkeypatch.setattr(Mac, "configured", classmethod(lambda cls, state: True))
    voice = cli.pick_voice(cli.parser().parse_args([]), state)
    assert voice.kind == "mac" and "Python 3.10" in voice.warning and "uv tool install" in voice.warning
    assert cli.pick_voice(cli.parser().parse_args(["--mac"]), state).warning == ""  # asked for: nothing to say


def test_the_saved_voice_of_each_engine_comes_back(tmp_path):
    state = State(tmp_path / "s.json")
    voices.remember(state, Voice(Kokoro("bm_george"), state))
    assert state.get("engine") == "kokoro" and voices.saved_name(state, "kokoro") == "bm_george"
    assert voices.make("kokoro", "", state).name == "bm_george"
    assert voices.saved_name(state, "mac") == ""


def test_a_failed_engine_falls_back_and_says_so(tmp_path, monkeypatch):
    state = State(tmp_path / "s.json")
    voice = Voice(Kokoro(), state, cache=tmp_path)
    monkeypatch.setattr(voices, "backup_for", lambda engine, state: Mac())

    def down(text, out):
        raise RuntimeError("model missing")

    def said(self, text, out):
        out.write_bytes(b"aiff")

    monkeypatch.setattr(voice.engine, "synthesize", down)
    monkeypatch.setattr(Mac, "synthesize", said)
    path = voice.fetch("hello")
    assert path.suffix == ".aiff" and path.read_bytes() == b"aiff"
    assert voice.warning.startswith("Kokoro voice failed (model missing); using the Mac voice")


def test_check_command(tmp_path, capsys, monkeypatch):
    # how a file reads needs no voice: on Python 3.9 there is none to set up
    monkeypatch.setattr(Kokoro, "configured", classmethod(lambda cls, state: False))
    monkeypatch.setattr(Mac, "configured", classmethod(lambda cls, state: False))
    path = tmp_path / "a.md"
    path.write_text("# A\n\nOne sentence. Another.\n\n```\nx\n```\n")
    cli.main(["--check", str(path)])
    out = capsys.readouterr().out
    assert "4 sentences" in out and "1 code block, read line by line" in out


def test_voices_command_lists_every_engine(capsys):
    cli.main(["--voices"])
    out = capsys.readouterr().out
    assert "Kokoro" in out and "Mac" in out
    assert "Google" not in out


def test_help_and_version(capsys):
    with pytest.raises(SystemExit):
        cli.main(["--version"])
    assert "voce " in capsys.readouterr().out


def test_kokoro_fetches_the_small_model_but_keeps_using_a_full_one_already_there(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    folder = tmp_path / "voce" / "kokoro"
    assert [p.name for p in Kokoro.files()] == ["kokoro-v1.0.int8.onnx", "voices-v1.0.bin"]
    folder.mkdir(parents=True)
    (folder / "kokoro-v1.0.onnx").write_bytes(b"")
    assert [p.name for p in Kokoro.files()] == ["kokoro-v1.0.onnx", "voices-v1.0.bin"]


def test_kokoro_downloads_the_missing_files_on_one_line_of_progress(tmp_path, monkeypatch, capsys):
    import io

    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    seen = []

    class Response(io.BytesIO):
        def __enter__(self): return self
        def __exit__(self, *_): pass

    def urlopen(url, timeout):
        seen.append(Kokoro().downloading())
        return Response(b"x" * 3_000_000)

    monkeypatch.setattr(voices.urllib.request, "urlopen", urlopen)
    said = []
    Kokoro().prepare(said.append)
    assert len(said) == 1 and "Downloading the Kokoro voice (120 MB), once" in said[0]
    assert [s.split(": ")[1] for s in seen] == ["0 of 120 MB", "3 of 120 MB"]
    assert capsys.readouterr().out.endswith("\r  6 of 120 MB\n")
    assert Kokoro().ready() and Kokoro().downloading() == ""
    Kokoro().prepare(said.append)  # nothing missing: nothing said
    assert len(said) == 1
