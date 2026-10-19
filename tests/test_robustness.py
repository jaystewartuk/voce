"""Inputs found by review and fuzzing that once crashed or lost text."""

import json
import time

import pytest

from voce import cli
from voce.markdown import parse, plain
from voce.sources.claude import last_reply
from voce.state import State
from voce.voices import Google, Mac, Refused, Voice


def texts(md):
    return [(b.kind, b.text, b.spoken) for b in parse(md)]


def test_control_characters_are_dropped():
    assert plain("a\x00b&#0;c\x1bd") == "ab&#0;cd"
    assert parse("```\nx\x00y\n```")[0].text == "xy"


def test_out_of_range_entities_stay_as_text():
    assert plain("a &#99999999; b &#xD800; c &#65;") == "a &#99999999; b &#xD800; c A"


def test_text_inside_block_html_is_kept():
    assert texts("<p>Real text.</p>") == [("p", "Real text.", True)]
    assert texts('<p align="center"><img src="x.png"></p>') == []


def test_text_after_a_comment_on_the_same_line_is_kept():
    assert texts("<!-- note --> Visible.") == [("p", "Visible.", True)]
    assert texts("<!-- a\nb --> After.\n\nMore.") == [("p", "After.", True), ("p", "More.", True)]


def test_byte_order_mark_is_ignored():
    assert texts("﻿# Title") == [("h1", "Title", True)]


def test_unclosed_details_does_not_silence_the_rest():
    assert texts("<details>\n\nInside.\n\nAfter.") == [("p", "Inside.", True), ("p", "After.", True)]


def test_generics_are_not_html():
    assert plain("A List<String> and Map<K, V> but not <b>bold</b>") == "A List<String> and Map<K, V> but not bold"


def test_stray_asterisks_parse_quickly():
    start = time.monotonic()
    parse("*a " * 20000)
    assert time.monotonic() - start < 2


def test_transcripts_with_odd_lines(tmp_path):
    path = tmp_path / "t.jsonl"
    lines = ["[1, 2]", '"text"', json.dumps({"type": "user", "message": "a string"}),
             json.dumps({"type": "user", "message": {"content": "q"}}),
             json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": "A."}]}})]
    path.write_text("\n".join(lines))
    assert last_reply(path) == "A."


def test_google_rests_after_outages_but_not_after_a_refused_sentence(tmp_path, monkeypatch):
    state = State(tmp_path / "s.json")
    voice = Voice(Google("en-US-Chirp3-HD-Kore", api_key="k"), state, cache=tmp_path)
    calls = []
    monkeypatch.setattr(voice, "_fallback", lambda text, warning="": tmp_path / "mac.aiff")

    def refused(text, out):
        calls.append(text)
        raise Refused("refused")

    monkeypatch.setattr(voice.engine, "synthesize", refused)
    for n in range(5):
        voice.fetch(f"r{n}")
    assert len(calls) == 5 and voice.resting_until == 0

    def down(text, out):
        calls.append(text)
        raise RuntimeError("503")

    monkeypatch.setattr(voice.engine, "synthesize", down)
    for n in range(5):
        voice.fetch(f"d{n}")
    assert len(calls) == 8 and voice.resting_until > time.monotonic()
    voice.resting_until = 0  # the rest is over: Google is tried again
    voice.fetch("again")
    assert calls[-1] == "again"


def test_mac_voice_never_runs_embedded_commands(tmp_path, monkeypatch):
    seen = {}
    monkeypatch.setattr("subprocess.run", lambda args, **kw: seen.update(args=args, input=kw.get("input")))
    Mac().synthesize("[[slnc 6000]] hi", tmp_path / "o")
    assert "[[" not in seen["input"] and "slnc" not in " ".join(seen["args"])


@pytest.mark.parametrize("value", ["-1", "nan", "0", "9", "fast"])
def test_speed_must_be_sensible(value, capsys):
    with pytest.raises(SystemExit):
        cli.main(["--speed", value, "--check", "README.md"])
    assert "speed from 0.5 to 3" in capsys.readouterr().err


def test_check_reports_unreadable_files(tmp_path, capsys):
    bad = tmp_path / "bad.md"
    bad.write_bytes(b"\xff\xfe\x00bad")
    cli.main(["--check", str(bad)])
    assert "couldn't read it" in capsys.readouterr().out
