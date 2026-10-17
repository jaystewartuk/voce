#!/usr/bin/env python3
"""Check by ear what the voice makes of tricky phrases: fetch each one, transcribe it, compare.

Google reads "PHP 8" as "eight Philippine pesos". speech.speakable rewrites text like that before it reaches
the voice, and this script is how those rewrites are checked and new ones are found. It runs the real voice,
so it needs Google set up (or --mac), ffmpeg, and whisper.cpp with a model:

    brew install whisper-cpp ffmpeg
    curl -LO https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin
    .venv/bin/python docs/hearing/check.py --model ggml-base.en.bin

Each line of phrases.txt is "what is written => what should be heard", with | between acceptable hearings. A
phrase is heard right when the transcript, lowercased and stripped of spaces and punctuation, contains one of
them treated the same way. Pass --raw to hear the text as written, without speakable: that shows what the
voice gets wrong on its own. Audio goes through the normal cache, so a phrase already heard is free to check
again, and the characters sent to Google count towards the month like any other.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from voce.speech import speakable
from voce.state import State
from voce.voices import DEFAULT_GOOGLE_VOICE, Google, Voice

HERE = Path(__file__).resolve().parent


def read_phrases(path: Path) -> list[tuple[str, list[str]]]:
    out = []
    for line in path.read_text().splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        written, _, heard = line.partition("=>")
        out.append((written.strip(), [h.strip() for h in heard.split("|") if h.strip()]))
    return out


_NUMBERS = {"zero": "0", "one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6",
            "seven": "7", "eight": "8", "nine": "9", "ten": "10"}


def letters(s: str) -> str:
    """Just the letters and digits, so "P.H.P. Eight" and "PHP 8" compare equal."""
    s = re.sub(r"\b(" + "|".join(_NUMBERS) + r")\b", lambda m: _NUMBERS[m.group(1)], s.lower())
    return re.sub(r"[^a-z0-9]", "", s)


def transcribe(audio: Path, model: Path, tmp: Path) -> str:
    wav = tmp / (audio.stem + ".wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(audio), "-ar", "16000", "-ac", "1", str(wav)],
                   check=True)
    out = subprocess.run(["whisper-cli", "-m", str(model), "-f", str(wav), "-nt", "-np"],
                         capture_output=True, text=True, check=True).stdout
    return " ".join(out.split())


def main() -> int:
    ap = argparse.ArgumentParser(description="Transcribe what the voice says for each phrase and compare.")
    ap.add_argument("phrases", nargs="?", type=Path, default=HERE / "phrases.txt")
    ap.add_argument("--model", type=Path, default=os.environ.get("WHISPER_MODEL", "ggml-base.en.bin"),
                    help="a whisper.cpp model file (or set WHISPER_MODEL)")
    ap.add_argument("--voice", default="", help="voice name, as for voce --voice")
    ap.add_argument("--mac", action="store_true", help="use the Mac's voice instead of Google")
    ap.add_argument("--raw", action="store_true", help="send the text as written, without speakable")
    args = ap.parse_args()

    for tool in ("ffmpeg", "whisper-cli"):
        if not shutil.which(tool):
            sys.exit(f"{tool} is not installed: brew install whisper-cpp ffmpeg")
    if not args.model.exists():
        sys.exit(f"No whisper model at {args.model}: see the top of {__file__}")

    state = State()
    google = None if args.mac else Google.from_environment(state.get("google_project", ""))
    if google is None and not args.mac:
        sys.exit("Google is not set up (VOCE_GOOGLE_API_KEY or gcloud): pass --mac to check the Mac voice")
    voice = Voice(args.voice or (state.get("voice") or DEFAULT_GOOGLE_VOICE if google else ""), state,
                  mac=args.mac, google=google)
    print(f"Voice: {voice.label}{'  (raw text)' if args.raw else ''}")

    phrases = read_phrases(args.phrases)
    texts = [written if args.raw else speakable(written) for written, _ in phrases]
    for text in texts:
        voice.want(text)
    failed = 0
    with tempfile.TemporaryDirectory() as tmp:
        for (written, heard), text in zip(phrases, texts):
            path, _ = voice.get(text)
            transcript = transcribe(path, args.model, Path(tmp))
            ok = any(letters(h) in letters(transcript) for h in heard)
            failed += not ok
            sent = "" if text == written else f"\n       sent:  {text}"
            print(f"{'ok  ' if ok else 'FAIL'} {written}{sent}\n       heard: {transcript}")
    if voice.warning:
        print(f"\n{voice.warning}")
    voice.close()
    state.save(force=True)
    print(f"\n{len(phrases) - failed} of {len(phrases)} heard right.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
