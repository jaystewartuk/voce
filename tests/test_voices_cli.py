import pytest

from voce import cli
from voce.state import State
from voce.voices import Google, Voice, next_google_voice


def test_next_google_voice_keeps_the_language():
    assert next_google_voice("en-GB-Chirp3-HD-Charon") == "en-GB-Chirp3-HD-Leda"
    assert next_google_voice("en-GB-Chirp3-HD-Despina") == "en-GB-Chirp3-HD-Charon"
    assert next_google_voice("something-else") == "en-US-Chirp3-HD-Charon"


def test_cache_keys_depend_on_voice_and_text(tmp_path):
    state = State(tmp_path / "s.json")
    google = Voice("en-GB-Chirp3-HD-Orus", state, google=Google(api_key="k"), cache=tmp_path)
    mac = Voice("", state, mac=True, cache=tmp_path)
    assert google.path("hi") != google.path("ho")
    assert google.path("hi").suffix == ".mp3" and mac.path("hi").suffix == ".aiff"
    assert google.key("hi") != mac.key("hi")
    assert google.label == "Orus" and mac.label == "Mac voice"


def test_google_voice_name_is_ignored_by_the_mac(tmp_path):
    voice = Voice("en-GB-Chirp3-HD-Orus", State(tmp_path / "s.json"), mac=True)
    assert voice.mac and voice.name == ""


def test_google_from_environment(monkeypatch):
    monkeypatch.setenv("VOCE_GOOGLE_API_KEY", "secret")
    assert Google.from_environment() == Google(api_key="secret")


def test_check_command(tmp_path, capsys):
    path = tmp_path / "a.md"
    path.write_text("# A\n\nOne sentence. Another.\n\n```\nx\n```\n")
    cli.main(["--check", str(path)])
    out = capsys.readouterr().out
    assert "4 sentences" in out and "1 code block, read line by line" in out


def test_help_and_version(capsys):
    with pytest.raises(SystemExit):
        cli.main(["--version"])
    assert "voce " in capsys.readouterr().out


def test_a_pull_request_on_the_command_line_needs_no_flag(tmp_path, monkeypatch, capsys):
    seen = []

    def fake(text, cwd=None, client=None, folder=None):
        seen.append(text)
        path = tmp_path / "pr.md"
        path.write_text("# PR\n\nOne sentence.\n")
        return path

    monkeypatch.setattr("voce.sources.pullrequest.read_pull_request", fake)
    cli.main(["--check", "owner/repo#12"])
    assert seen == ["owner/repo#12"] and "2 sentences" in capsys.readouterr().out
    cli.main(["--check", "--pr", "https://github.com/owner/repo/pull/3"])
    assert seen[-1] == "https://github.com/owner/repo/pull/3"
