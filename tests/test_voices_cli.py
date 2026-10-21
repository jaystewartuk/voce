import pytest

from voce import cli, voices
from voce.state import State
from voce.voices import Azure, ElevenLabs, Google, Kokoro, Mac, OpenAI, Voice


def test_next_google_voice_keeps_the_language():
    assert Google("en-GB-Chirp3-HD-Charon").next_name() == "en-GB-Chirp3-HD-Leda"
    assert Google("en-GB-Chirp3-HD-Despina").next_name() == "en-GB-Chirp3-HD-Charon"
    assert Google("something-else").next_name() == "en-US-Chirp3-HD-Charon"


def test_every_engine_cycles_its_voices_and_names_them_shortly():
    assert Kokoro().name == "af_heart" and Kokoro().label == "Kokoro Heart"
    assert Kokoro("bm_george").next_name() == "bm_fable" and Kokoro("af_nicole").next_name() == "af_heart"
    assert Azure().label == "Azure Ava" and Azure("en-GB-RyanNeural").label == "Azure Ryan"
    assert ElevenLabs().label == "ElevenLabs George" and ElevenLabs("JBFqnCBsd6RMkjVDRZzb").label == "ElevenLabs JBFqnC"
    assert OpenAI().label == "OpenAI Ash" and OpenAI("verse").next_name() == "ash"
    assert Mac().label == "Mac voice" and Mac("Daniel").label == "Mac Daniel"


def test_a_voice_name_tells_its_engine(tmp_path):
    state = State(tmp_path / "s.json")
    assert voices.engine_for("en-US-Chirp3-HD-Charon", state) == "google"
    assert voices.engine_for("en-GB-Neural2-A", state) == "google"
    assert voices.engine_for("en-GB-RyanNeural", state) == "azure"
    assert voices.engine_for("af_heart", state) == "kokoro"
    assert voices.engine_for("coral", state) == "openai"
    assert voices.engine_for("JBFqnCBsd6RMkjVDRZzb", state) == "elevenlabs"
    assert voices.engine_for("Daniel", state) == "mac"  # a plain word is a Mac voice unless ElevenLabs is in use


def test_cache_keys_depend_on_engine_voice_and_text(tmp_path):
    state = State(tmp_path / "s.json")
    google = Voice(Google("en-GB-Chirp3-HD-Orus", api_key="k"), state, cache=tmp_path)
    mac = Voice(Mac(), state, cache=tmp_path)
    kokoro = Voice(Kokoro(), state, cache=tmp_path)
    assert google.path("hi") != google.path("ho")
    assert (google.path("hi").suffix, mac.path("hi").suffix, kokoro.path("hi").suffix) == (".mp3", ".aiff", ".wav")
    assert len({google.key("hi"), mac.key("hi"), kokoro.key("hi")}) == 3
    assert google.label == "Google Orus" and mac.label == "Mac voice"


def test_usage_is_counted_per_engine_and_old_counts_are_googles(tmp_path):
    (tmp_path / "state.json").write_text('{"usage": {"2000-01": 5}}')
    state = State(tmp_path)
    assert state.usage["2000-01"] == {"google": 5}
    state.count("azure", 3)
    state.count("azure", 4)
    assert state.month_chars("azure") == 7 and state.month_chars("google") == 0
    azure = Voice(Azure("en-GB-RyanNeural", key="k", region="uksouth"), state, cache=tmp_path)
    assert azure.usage() == "Azure characters this month: 7 of 500,000 free"
    assert azure.over_free(500_000) and not azure.over_free(10)
    openai = Voice(OpenAI(key="k"), state, cache=tmp_path)
    assert openai.usage() == "OpenAI characters this month: 0" and not openai.over_free(10 ** 9)
    assert Voice(Kokoro(), state, cache=tmp_path).usage() == ""


def test_the_default_engine_prefers_a_cloud_one_then_kokoro_then_the_mac(tmp_path, monkeypatch):
    state = State(tmp_path / "s.json")
    for var in ("VOCE_GOOGLE_API_KEY", "VOCE_AZURE_KEY", "VOCE_AZURE_REGION", "VOCE_ELEVENLABS_API_KEY",
                "ELEVENLABS_API_KEY", "VOCE_OPENAI_API_KEY", "OPENAI_API_KEY"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setattr("shutil.which", lambda name: None)
    monkeypatch.setattr(Kokoro, "configured", classmethod(lambda cls, state: False))
    monkeypatch.setattr(Mac, "configured", classmethod(lambda cls, state: False))
    assert voices.default_engine(state) == "kokoro"  # off a Mac: asked for, so its setup message is shown
    monkeypatch.setattr(Mac, "configured", classmethod(lambda cls, state: True))
    assert voices.default_engine(state) == "mac"
    monkeypatch.setattr(Kokoro, "configured", classmethod(lambda cls, state: True))
    assert voices.default_engine(state) == "kokoro"
    monkeypatch.setenv("VOCE_OPENAI_API_KEY", "k")
    assert voices.default_engine(state) == "openai"
    monkeypatch.setenv("VOCE_AZURE_KEY", "k")
    monkeypatch.setenv("VOCE_AZURE_REGION", "uksouth")
    assert voices.default_engine(state) == "azure"
    state.set("engine", "kokoro")
    assert voices.default_engine(state) == "kokoro"  # the engine chosen last time wins
    assert voices.available(state) == ["kokoro", "mac", "azure", "openai"]


def test_the_saved_voice_of_each_engine_comes_back(tmp_path):
    state = State(tmp_path / "s.json")
    state.set("voice", "en-GB-Chirp3-HD-Leda")  # how voce saved its one Google voice before
    assert voices.saved_name(state, "google") == "en-GB-Chirp3-HD-Leda"
    voice = Voice(Azure("en-GB-RyanNeural", key="k", region="r"), state)
    voices.remember(state, voice)
    assert state.get("engine") == "azure" and voices.saved_name(state, "azure") == "en-GB-RyanNeural"
    assert voices.make("azure", "", state).name == "en-GB-RyanNeural"


def test_google_from_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("VOCE_GOOGLE_API_KEY", "secret")
    google = Google.build("", State(tmp_path / "s.json"))
    assert google.api_key == "secret" and google.name == "en-US-Chirp3-HD-Charon"


def test_a_failed_engine_falls_back_and_says_so(tmp_path, monkeypatch):
    state = State(tmp_path / "s.json")
    voice = Voice(Google("en-US-Chirp3-HD-Kore", api_key="k"), state, cache=tmp_path)
    monkeypatch.setattr(voices, "backup_for", lambda engine, state: Mac())

    def down(text, out):
        raise RuntimeError("503")

    def said(self, text, out):
        out.write_bytes(b"aiff")

    monkeypatch.setattr(voice.engine, "synthesize", down)
    monkeypatch.setattr(Mac, "synthesize", said)
    path = voice.fetch("hello")
    assert path.suffix == ".aiff" and path.read_bytes() == b"aiff"
    assert voice.warning.startswith("Google voice failed (503); using the Mac voice")
    assert state.month_chars("google") == 0


def test_check_command(tmp_path, capsys):
    path = tmp_path / "a.md"
    path.write_text("# A\n\nOne sentence. Another.\n\n```\nx\n```\n")
    cli.main(["--check", str(path)])
    out = capsys.readouterr().out
    assert "4 sentences" in out and "1 code block, read line by line" in out


def test_voices_command_lists_every_engine(capsys):
    cli.main(["--voices"])
    out = capsys.readouterr().out
    for title in ("Kokoro", "Mac", "Google", "Azure", "ElevenLabs", "OpenAI"):
        assert title in out


def test_help_and_version(capsys):
    with pytest.raises(SystemExit):
        cli.main(["--version"])
    assert "voce " in capsys.readouterr().out
