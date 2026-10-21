"""Voices: six engines that turn a sentence into audio, and the cache that keeps every sentence once it is said.

* Kokoro      a small open model that runs on this computer. Free, offline and the default: there is nothing to
              set up. The model (120 MB) is downloaded once, into the cache.
* Mac         the Mac's own voices, through ``say``. Used when Kokoro can't run, and as the last resort. macOS only.
* Google      Chirp 3 HD. ``VOCE_GOOGLE_API_KEY``, or the ``gcloud`` CLI signed in, with the project to bill from
              ``VOCE_GOOGLE_PROJECT``, ``voce --google-project``, or ``gcloud config get-value project``.
* Azure       Neural voices. ``VOCE_AZURE_KEY`` and ``VOCE_AZURE_REGION`` (or ``AZURE_SPEECH_KEY`` / ``_REGION``).
* ElevenLabs  ``VOCE_ELEVENLABS_API_KEY`` (or ``ELEVENLABS_API_KEY``).
* OpenAI      gpt-4o-mini-tts. ``VOCE_OPENAI_API_KEY`` (or ``OPENAI_API_KEY``).

A cloud engine that is set up is used ahead of Kokoro, unless you chose another with ``--engine`` or the V key;
that choice is remembered. Every sentence is fetched once and kept in the cache, keyed by the engine, the voice
and the exact text, so listening again costs nothing and works offline. When an engine fails, the sentence is
said by Kokoro (or the Mac) instead and the reader is told why.
"""

from __future__ import annotations

import base64
import concurrent.futures
import hashlib
import http.client
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
import wave
from pathlib import Path
from typing import Callable, ClassVar
from urllib.parse import quote
from xml.sax.saxutils import escape

from voce import paths

_GIVE_UP_AFTER = 3      # failures in a row before an engine rests
_REST_SECONDS = 60      # how long the backup voice is used before the engine is tried again
_RETRY = {429, 500, 502, 503, 504}


class Refused(RuntimeError):
    """The engine turned down this one text (HTTP 400): not a reason to stop using it."""


# ---------------------------------------------------------------- engines

class Engine:
    """One way of turning text into audio. Subclasses say how to reach it and which voices it has."""

    kind = ""            # the word used on the command line and in the state file
    title = ""           # the word used in messages
    ext = "mp3"          # what its audio files are
    rate = 24000         # their sample rate
    local = False        # runs on this computer: nothing is sent anywhere and nothing is counted
    free_chars = 0       # the characters a month that cost nothing, for the metered engines
    voices: tuple[str, ...] = ()   # the voices the v key cycles through
    default = ""
    setup = ""           # how to set it up, for messages
    takes_names = False  # whether a plain word such as "Daniel" can be one of its voices

    def __init__(self, name: str = "") -> None:
        self.name = name or self.default

    @classmethod
    def configured(cls, state) -> bool:
        """Whether this engine can be used here: its key is set, or it is installed."""
        return True

    @classmethod
    def build(cls, name: str, state) -> Engine:
        return cls(name)

    @classmethod
    def owns(cls, name: str) -> bool:
        """Whether a voice name is unmistakably one of this engine's."""
        return False

    @property
    def short(self) -> str:
        return self.name

    @property
    def label(self) -> str:
        return f"{self.title} {self.short}".rstrip()

    def next_name(self, step: int = 1) -> str:
        if not self.voices:
            return self.name
        i = self.voices.index(self.name) if self.name in self.voices else -1
        return self.voices[(i + step) % len(self.voices)]

    def ready(self) -> bool:
        """Whether the next sentence can be made at once, without a one-time download."""
        return True

    def prepare(self, say: Callable[[str], None] | None = None) -> None:
        """One-time setup, reporting progress through say."""

    def downloading(self) -> str:
        """While a one-time download runs, how far it has got; otherwise empty."""
        return ""

    def synthesize(self, text: str, out: Path) -> None:
        raise NotImplementedError


class Mac(Engine):
    kind, title, ext, rate, local = "mac", "Mac", "aiff", 22050, True
    takes_names = True
    setup = "The Mac's voices need macOS; there, add better ones in System Settings, Accessibility, Spoken Content."
    _voices: ClassVar[list[str] | None] = None

    @classmethod
    def configured(cls, state) -> bool:
        return sys.platform == "darwin" and shutil.which("say") is not None

    NOVELTY: ClassVar[set[str]] = {"Albert", "Bad News", "Bahh", "Bells", "Boing", "Bubbles", "Cellos", "Wobble",
                                   "Good News", "Jester", "Organ", "Superstar", "Trinoids", "Whisper", "Zarvox",
                                   "Junior", "Ralph", "Kathy", "Fred", "Eddy", "Flo", "Grandma", "Grandpa", "Reed",
                                   "Rocko", "Sandy", "Shelley"}

    @property
    def short(self) -> str:
        return self.name or "voice"

    @property
    def voices(self) -> tuple[str, ...]:  # type: ignore[override]
        """The English voices installed, from say -v ?, found once."""
        if Mac._voices is None:
            try:
                out = subprocess.run(["say", "-v", "?"], capture_output=True, text=True, timeout=10).stdout
            except (OSError, subprocess.SubprocessError):
                out = ""
            Mac._voices = [m.group(1) for m in re.finditer(r"^(\S.*?)\s+en_\w+\s", out, re.M)
                           if m.group(1).split(" (")[0] not in self.NOVELTY]
        return tuple(Mac._voices)

    def synthesize(self, text: str, out: Path) -> None:
        voice = ["-v", self.name] if self.name else []
        text = text.replace("[[", "[ [")  # [[ starts an embedded command for say, such as [[slnc 6000]]
        subprocess.run(["say", *voice, "-o", str(out), "--file-format=AIFF"], input=text, text=True,
                       check=True, capture_output=True)


class Kokoro(Engine):
    kind, title, ext, local = "kokoro", "Kokoro", "wav", True
    voices = ("af_heart", "af_bella", "am_michael", "am_fenrir", "bf_emma", "bm_george", "bm_fable", "af_nicole")
    default = "af_heart"
    setup = "Kokoro needs Python 3.10 to 3.14. Reinstall voce with one: uv tool install --python 3.13 voce"
    RELEASE = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"
    # The int8 model sounds the same as the full one to the ear, at a third of the download.
    FILES: ClassVar[dict[str, str]] = {"kokoro-v1.0.int8.onnx": RELEASE + "kokoro-v1.0.int8.onnx",
                                       "voices-v1.0.bin": RELEASE + "voices-v1.0.bin"}
    FULL = "kokoro-v1.0.onnx"  # what 0.2.0 downloaded: kept and used where it is already there
    SIZE_MB = 120
    LANGS: ClassVar[dict[str, str]] = {"a": "en-us", "b": "en-gb", "e": "es", "f": "fr-fr", "h": "hi", "i": "it",
                                       "j": "ja", "p": "pt-br", "z": "cmn"}
    _model = None
    _lock = threading.Lock()
    _got: int | None = None  # bytes downloaded so far, while a download runs

    @classmethod
    def configured(cls, state) -> bool:
        return sys.version_info >= (3, 10) and importlib.util.find_spec("kokoro_onnx") is not None

    @classmethod
    def owns(cls, name: str) -> bool:
        return re.fullmatch(r"[abefhijpz][fm]_[a-z]+", name) is not None

    @property
    def short(self) -> str:
        return self.name.split("_", 1)[-1].capitalize()

    @staticmethod
    def files() -> list[Path]:
        folder = paths.cache_dir() / "kokoro"
        full = folder / Kokoro.FULL
        return [full if full.exists() and name.endswith(".onnx") else folder / name for name in Kokoro.FILES]

    def ready(self) -> bool:
        return Kokoro._model is not None or all(p.exists() for p in self.files())

    def prepare(self, say: Callable[[str], None] | None = None) -> None:
        """Download the model files that are missing, once, showing one line of progress for them all."""
        missing = [path for path in self.files() if not path.exists()]
        if not missing:
            return
        missing[0].parent.mkdir(parents=True, exist_ok=True)
        if say:
            say(f"Downloading the Kokoro voice ({self.SIZE_MB} MB), once, to {missing[0].parent}")
        Kokoro._got, shown = 0, -1
        try:
            for path in missing:
                tmp = path.with_name(path.name + ".tmp")
                try:
                    with urllib.request.urlopen(self.FILES[path.name], timeout=60) as r, tmp.open("wb") as f:
                        while chunk := r.read(1 << 20):
                            f.write(chunk)
                            Kokoro._got += len(chunk)
                            if say and self.mb() != shown:
                                shown = self.mb()
                                print(f"\r  {shown} of {self.SIZE_MB} MB", end="", flush=True)
                except Exception as e:
                    tmp.unlink(missing_ok=True)
                    raise RuntimeError(f"Couldn't download the Kokoro voice: {str(e)[:80]}") from e
                tmp.replace(path)
            if say:
                print()
        finally:
            Kokoro._got = None

    def mb(self) -> int:
        return min((Kokoro._got or 0) // 1_000_000, self.SIZE_MB)

    def downloading(self) -> str:
        if Kokoro._got is None:
            return ""
        return f"Downloading the Kokoro voice, once: {self.mb()} of {self.SIZE_MB} MB"

    def _load(self):
        with Kokoro._lock:
            if Kokoro._model is None:
                self.prepare()
                import logging

                logging.getLogger("kokoro_onnx").setLevel(logging.ERROR)
                logging.getLogger("phonemizer").setLevel(logging.ERROR)
                import onnxruntime
                from kokoro_onnx import Kokoro as Model

                onnxruntime.set_default_logger_severity(3)
                model, voices = self.files()
                Kokoro._model = Model(str(model), str(voices))
            return Kokoro._model

    def synthesize(self, text: str, out: Path) -> None:
        import numpy as np

        model = self._load()
        with Kokoro._lock:  # the phonemizer underneath isn't safe to share between threads
            samples, rate = model.create(text, voice=self.name, speed=1.0, lang=self.LANGS.get(self.name[:1], "en-us"))
        with wave.open(str(out), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(rate)
            w.writeframes((np.clip(samples, -1, 1) * 32767).astype(np.int16).tobytes())


class Cloud(Engine):
    """An engine behind an HTTPS API: one connection per thread, retries on outages, and a shared lock."""

    host = ""

    def __init__(self, name: str = "") -> None:
        super().__init__(name)
        self.threads = threading.local()
        self.lock = threading.Lock()

    def post(self, url: str, body: str, headers: dict[str, str], host: str = "",
             refresh: Callable[[], dict[str, str]] | None = None) -> tuple[int, bytes]:
        """POST, trying again on a dropped connection or a busy server. refresh remakes the headers after a 401."""
        for attempt in range(4):
            conn = getattr(self.threads, "conn", None)
            if conn is None:
                conn = self.threads.conn = http.client.HTTPSConnection(host or self.host, timeout=60)
            try:
                conn.request("POST", url, body, headers)
                response = conn.getresponse()
                data = response.read()
            except (OSError, http.client.HTTPException):
                self.threads.conn = None
                if attempt == 3:
                    raise
                time.sleep(0.5 * 2 ** attempt)
                continue
            if response.status in _RETRY and attempt < 3:
                time.sleep(0.5 * 2 ** attempt)  # busy or rate-limited: back off and try again
                continue
            if response.status == 401 and refresh is not None and attempt < 3:
                headers = refresh()
                continue
            return response.status, data
        raise RuntimeError(f"{self.title} failed")

    def check(self, status: int, data: bytes) -> None:
        if status in (400, 422):
            raise Refused(f"{self.title} refused this sentence: {_error_message(data)}")
        if status != 200:
            raise RuntimeError(f"{self.title} said {status}: {_error_message(data)}")


class Google(Cloud):
    kind, title, host = "google", "Google", "texttospeech.googleapis.com"
    free_chars = 1_000_000  # Chirp 3 HD characters free each month, at the time of writing
    voices = ("Charon", "Leda", "Orus", "Kore", "Puck", "Aoede", "Fenrir", "Despina")
    default = "en-US-Chirp3-HD-Charon"
    setup = "Set VOCE_GOOGLE_API_KEY, or sign in with gcloud and pass --google-project once."

    def __init__(self, name: str = "", api_key: str = "", project: str = "") -> None:
        super().__init__(name)
        self.api_key, self.project = api_key, project
        self.token, self.token_at = "", 0.0

    @classmethod
    def configured(cls, state) -> bool:
        return bool(os.environ.get("VOCE_GOOGLE_API_KEY", "").strip()) or shutil.which("gcloud") is not None

    @classmethod
    def build(cls, name: str, state) -> Google:
        key = os.environ.get("VOCE_GOOGLE_API_KEY", "").strip()
        project = "" if key else os.environ.get("VOCE_GOOGLE_PROJECT", "").strip() or state.get("google_project", "")
        return cls(name, api_key=key, project=project)

    @classmethod
    def owns(cls, name: str) -> bool:
        return re.fullmatch(r"[a-z]{2,3}-[A-Z]{2}-(Chirp3-HD|Chirp-HD|Neural2|Wavenet|Standard|Studio|Journey|"
                            r"Polyglot|News|Casual)-\w+", name) is not None

    @property
    def short(self) -> str:
        return self.name.rsplit("-", 1)[-1]

    def next_name(self, step: int = 1) -> str:
        """The next Chirp 3 HD voice in the same language."""
        language = "-".join(self.name.split("-")[:2]) if self.name.count("-") >= 3 else "en-US"
        current = self.name.rsplit("-", 1)[-1]
        i = self.voices.index(current) if current in self.voices else -1
        return f"{language}-Chirp3-HD-{self.voices[(i + step) % len(self.voices)]}"

    def _gcloud(self, *args: str) -> str:
        return subprocess.run(["gcloud", *args], capture_output=True, text=True, check=True,
                              timeout=30).stdout.strip()

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            return headers
        with self.lock:
            if not self.token or time.monotonic() - self.token_at > 45 * 60:
                self.token = self._gcloud("auth", "print-access-token")
                self.token_at = time.monotonic()
                if not self.project:
                    self.project = self._gcloud("config", "get-value", "project")
            headers["Authorization"] = f"Bearer {self.token}"
            if self.project:
                headers["x-goog-user-project"] = self.project
        return headers

    def _refresh(self) -> dict[str, str]:
        with self.lock:
            self.token = ""
        return self._headers()

    def synthesize(self, text: str, out: Path) -> None:
        language = "-".join(self.name.split("-")[:2])
        body = json.dumps({"input": {"text": text},
                           "voice": {"languageCode": language, "name": self.name},
                           "audioConfig": {"audioEncoding": "MP3", "sampleRateHertz": self.rate}})
        url = "/v1/text:synthesize" + ("?key=" + quote(self.api_key) if self.api_key else "")
        status, data = self.post(url, body, self._headers(), refresh=None if self.api_key else self._refresh)
        self.check(status, data)
        out.write_bytes(base64.b64decode(json.loads(data)["audioContent"]))


class Azure(Cloud):
    kind, title = "azure", "Azure"
    free_chars = 500_000  # neural characters free each month, at the time of writing
    voices = ("en-US-AvaMultilingualNeural", "en-US-AndrewMultilingualNeural", "en-US-EmmaMultilingualNeural",
              "en-US-BrianMultilingualNeural", "en-GB-SoniaNeural", "en-GB-RyanNeural", "en-GB-LibbyNeural",
              "en-GB-OllieMultilingualNeural")
    default = voices[0]
    setup = "Set VOCE_AZURE_KEY and VOCE_AZURE_REGION (such as uksouth) for a Speech resource."

    def __init__(self, name: str = "", key: str = "", region: str = "") -> None:
        super().__init__(name)
        self.key, self.region = key, region
        self.host = f"{region}.tts.speech.microsoft.com"

    @staticmethod
    def _env() -> tuple[str, str]:
        key = os.environ.get("VOCE_AZURE_KEY") or os.environ.get("AZURE_SPEECH_KEY") or ""
        region = os.environ.get("VOCE_AZURE_REGION") or os.environ.get("AZURE_SPEECH_REGION") or ""
        return key.strip(), region.strip()

    @classmethod
    def configured(cls, state) -> bool:
        return all(cls._env())

    @classmethod
    def build(cls, name: str, state) -> Azure:
        return cls(name, *cls._env())

    @classmethod
    def owns(cls, name: str) -> bool:
        return re.fullmatch(r"[a-z]{2,3}-[A-Z]{2}-\w+Neural", name) is not None

    @property
    def short(self) -> str:
        return re.sub(r"(Multilingual)?Neural$", "", self.name.rsplit("-", 1)[-1])

    def synthesize(self, text: str, out: Path) -> None:
        language = "-".join(self.name.split("-")[:2])
        body = (f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="{language}">'
                f'<voice name="{self.name}">{escape(text)}</voice></speak>')
        headers = {"Ocp-Apim-Subscription-Key": self.key, "Content-Type": "application/ssml+xml",
                   "X-Microsoft-OutputFormat": "audio-24khz-96kbitrate-mono-mp3", "User-Agent": "voce"}
        status, data = self.post("/cognitiveservices/v1", body, headers)
        self.check(status, data)
        out.write_bytes(data)


class ElevenLabs(Cloud):
    kind, title, host, rate = "elevenlabs", "ElevenLabs", "api.elevenlabs.io", 44100
    free_chars = 10_000  # characters free each month, at the time of writing
    takes_names = True
    voices = ("George", "Sarah", "Brian", "Alice", "Daniel", "Matilda", "Liam", "Lily")
    default = "George"
    setup = "Set VOCE_ELEVENLABS_API_KEY."
    PREMADE: ClassVar[dict[str, str]] = {
               "Aria": "9BWtsMINqrJLrRacOk9x", "Roger": "CwhRBWXzGAHq8TQ4Fs17", "Sarah": "EXAVITQu4vr4xnSDxMaL",
               "Laura": "FGY2WhTYpPnrIDTdsKH5", "Charlie": "IKne3meq5aSn8XLyUdCD", "George": "JBFqnCBsd6RMkjVDRZzb",
               "Callum": "N2lVS1w4EtoT3dr4eOWO", "River": "SAz9YHcvj6GT2YYXdXww", "Liam": "TX3LPaxmHKxFdv7VOQHJ",
               "Charlotte": "XB0fDUnXU5powFXDhCwa", "Alice": "Xb7hH8MSUJpSbSDYk0k2", "Matilda": "XrExE9yKIg4WAyW8CHtE",
               "Will": "bIHbv24MWmeRgasZH58o", "Jessica": "cgSgspJ2msm6clMJCrPF", "Eric": "cjVigY5qzO86Huf0OWal",
               "Chris": "iP95p4xoKVk53GoZ742B", "Brian": "nPczCjzI2devNBz1zQrb", "Daniel": "onwK4e9ZLuTAKqWW03F9",
               "Lily": "pFZP5JQG7iQjIQuC4Bku", "Bill": "pqHfZKP75CvOlQylNhV4"}

    def __init__(self, name: str = "", key: str = "", model: str = "") -> None:
        super().__init__(name)
        self.key, self.model = key, model or "eleven_multilingual_v2"
        self.ids: dict[str, str] | None = None  # the account's voices by lower-case name, listed once

    @classmethod
    def configured(cls, state) -> bool:
        return bool((os.environ.get("VOCE_ELEVENLABS_API_KEY") or os.environ.get("ELEVENLABS_API_KEY") or "").strip())

    @classmethod
    def build(cls, name: str, state) -> ElevenLabs:
        key = (os.environ.get("VOCE_ELEVENLABS_API_KEY") or os.environ.get("ELEVENLABS_API_KEY") or "").strip()
        return cls(name, key, os.environ.get("VOCE_ELEVENLABS_MODEL", "").strip())

    @classmethod
    def owns(cls, name: str) -> bool:
        return re.fullmatch(r"[A-Za-z0-9]{20}", name) is not None

    @property
    def short(self) -> str:
        return self.name if not self.owns(self.name) else self.name[:6]

    def _listed(self) -> dict[str, str]:
        """The voices this key can use, by name: the account's own first, then the library's premade ones."""
        with self.lock:
            if self.ids is None:
                self.ids = {k.lower(): v for k, v in self.PREMADE.items()}
                try:
                    req = urllib.request.Request(f"https://{self.host}/v2/voices?page_size=100",
                                                 headers={"xi-api-key": self.key})
                    with urllib.request.urlopen(req, timeout=30) as r:
                        for v in json.load(r).get("voices", []):
                            self.ids[str(v.get("name", "")).lower()] = v["voice_id"]
                except Exception:
                    pass  # the built-in list will do
            return self.ids

    def voice_id(self) -> str:
        if self.owns(self.name):
            return self.name
        voice_id = self._listed().get(self.name.lower())
        if not voice_id:
            raise RuntimeError(f"ElevenLabs has no voice called {self.name}; give its name or voice ID")
        return voice_id

    def synthesize(self, text: str, out: Path) -> None:
        body = json.dumps({"text": text, "model_id": self.model})
        headers = {"xi-api-key": self.key, "Content-Type": "application/json", "Accept": "audio/mpeg"}
        status, data = self.post(f"/v1/text-to-speech/{self.voice_id()}?output_format=mp3_44100_128", body, headers)
        self.check(status, data)
        out.write_bytes(data)


class OpenAI(Cloud):
    kind, title, host = "openai", "OpenAI", "api.openai.com"
    voices = ("ash", "alloy", "coral", "echo", "fable", "nova", "onyx", "sage", "shimmer", "ballad", "verse")
    default = "ash"
    setup = "Set VOCE_OPENAI_API_KEY."
    INSTRUCTIONS = ("Read the text exactly as written, word for word, at a steady unhurried pace, like a colleague "
                    "reading notes aloud. Never add, drop or reword anything.")

    def __init__(self, name: str = "", key: str = "", model: str = "") -> None:
        super().__init__(name)
        self.key, self.model = key, model or "gpt-4o-mini-tts"

    @classmethod
    def configured(cls, state) -> bool:
        return bool((os.environ.get("VOCE_OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY") or "").strip())

    @classmethod
    def build(cls, name: str, state) -> OpenAI:
        key = (os.environ.get("VOCE_OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY") or "").strip()
        return cls(name, key, os.environ.get("VOCE_OPENAI_TTS_MODEL", "").strip())

    @classmethod
    def owns(cls, name: str) -> bool:
        return name in cls.voices

    @property
    def short(self) -> str:
        return self.name.capitalize()

    def synthesize(self, text: str, out: Path) -> None:
        request = {"model": self.model, "input": text, "voice": self.name, "response_format": "mp3"}
        if self.model.startswith("gpt-"):
            request["instructions"] = self.INSTRUCTIONS
        headers = {"Authorization": f"Bearer {self.key}", "Content-Type": "application/json"}
        status, data = self.post("/v1/audio/speech", json.dumps(request), headers)
        self.check(status, data)
        out.write_bytes(data)


ENGINES: dict[str, type[Engine]] = {e.kind: e for e in (Kokoro, Mac, Google, Azure, ElevenLabs, OpenAI)}
CLOUD = ["google", "azure", "elevenlabs", "openai"]   # the order they are preferred in when more than one is set up
PATTERNED = ["google", "azure", "kokoro", "openai", "elevenlabs"]   # whose voice names can be told apart


def available(state) -> list[str]:
    """The engines that can be used here, in the order the V key goes through them."""
    return [kind for kind in ENGINES if ENGINES[kind].configured(state)]


def default_engine(state) -> str:
    """The engine to use when none is asked for: the one chosen last time, else a cloud one that is set up,
    else Kokoro, else the Mac."""
    kinds = available(state)
    saved = state.get("engine", "")
    if saved in kinds:
        return saved
    for kind in CLOUD:
        if kind in kinds:
            return kind
    return "mac" if "mac" in kinds and "kokoro" not in kinds else "kokoro"


def engine_for(name: str, state) -> str:
    """The engine a voice name belongs to: by its shape where that is unmistakable, else the engine in use if
    it takes plain names (ElevenLabs), else the Mac."""
    for kind in PATTERNED:
        if ENGINES[kind].owns(name):
            return kind
    kind = default_engine(state)
    return kind if ENGINES[kind].takes_names else "mac"


def saved_name(state, kind: str) -> str:
    names = state.get("voices") or {}
    if kind == "google" and not names.get(kind):
        return state.get("voice", "")  # where voce kept its one Google voice before there were other engines
    return names.get(kind, "")


def remember(state, voice: Voice) -> None:
    state.set("engine", voice.kind)
    names = dict(state.get("voices") or {})
    names[voice.kind] = voice.name
    state.set("voices", names)


def make(kind: str, name: str, state, cache: Path | None = None) -> Voice:
    engine = ENGINES[kind].build(name or saved_name(state, kind), state)
    return Voice(engine, state, cache=cache)


def backup_for(engine: Engine, state) -> Engine | None:
    """What says a sentence when engine can't: Kokoro for the cloud engines, the Mac for Kokoro, nothing for the Mac.
    Off a Mac there are no Mac voices, so Kokoro has no backup."""
    if engine.kind == "mac":
        return None
    if engine.kind != "kokoro" and Kokoro.configured(state) and Kokoro().ready():
        return Kokoro()
    return Mac() if Mac.configured(state) else None


# ---------------------------------------------------------------- the cache and the fetching

class Voice:
    """One engine and voice, turning text into a cached audio file and fetching ahead on a small thread pool."""

    def __init__(self, engine: Engine, state, *, cache: Path | None = None) -> None:
        self.engine, self.state = engine, state
        self.cache = cache or paths.cache_dir()
        self.lock = threading.Lock()
        self.failures = 0
        self.resting_until = 0.0
        self.durations: dict[Path, float] = {}
        self.warning = ""
        self.backup: Voice | None = None
        self.pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)
        self.futures: dict[str, concurrent.futures.Future] = {}

    @property
    def kind(self) -> str:
        return self.engine.kind

    @property
    def name(self) -> str:
        return self.engine.name

    @property
    def label(self) -> str:
        return self.engine.label

    @property
    def local(self) -> bool:
        return self.engine.local

    @property
    def metered(self) -> bool:
        """Whether sentences are sent to a service that counts them."""
        return not self.engine.local

    def downloading(self) -> str:
        return self.engine.downloading()

    def usage(self) -> str:
        """A line for the metered engines: the characters sent this month, and the free allowance if there is one."""
        if not self.metered:
            return ""
        line = f"{self.engine.title} characters this month: {self.state.month_chars(self.kind):,}"
        return line + (f" of {self.engine.free_chars:,} free" if self.engine.free_chars else "")

    def over_free(self, chars: int) -> bool:
        """Whether fetching chars more would take this month past the free allowance."""
        return self.metered and bool(self.engine.free_chars) and \
            chars + self.state.month_chars(self.kind) > self.engine.free_chars

    # ---- cache

    def key(self, text: str) -> str:
        return hashlib.sha256(f"{self.kind}:{self.name}|{text}".encode()).hexdigest()

    def path(self, text: str) -> Path:
        k = self.key(text)
        return self.cache / "audio" / k[:2] / f"{k}.{self.engine.ext}"

    # ---- fetching

    def fetch(self, text: str) -> Path:
        """The audio file for text, made or fetched first if it isn't cached."""
        path = self.path(text)
        if path.exists():
            return path
        if time.monotonic() < self.resting_until:
            return self._fallback(text)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(f"{path.name}.{threading.get_ident()}.tmp")
        try:
            self.engine.synthesize(text, tmp)
            with self.lock:
                self.failures = 0
        except Refused as e:
            tmp.unlink(missing_ok=True)
            return self._fallback(text, f"{str(e)[:110]} Using the {self._backup_title()} voice for that one.")
        except Exception as e:
            tmp.unlink(missing_ok=True)
            with self.lock:
                self.failures += 1
                if self.failures >= _GIVE_UP_AFTER:
                    self.failures = 0
                    self.resting_until = time.monotonic() + _REST_SECONDS
            return self._fallback(text, f"{self.engine.title} voice failed ({str(e)[:90]}); using the "
                                        f"{self._backup_title()} voice for now.")
        if self.metered:
            self.state.count(self.kind, len(text))
        tmp.replace(path)
        return path

    def _backup_title(self) -> str:
        backup = backup_for(self.engine, self.state)
        return backup.title if backup else "backup"

    def _fallback(self, text: str, warning: str = "") -> Path:
        if self.backup is None:
            engine = backup_for(self.engine, self.state)
            if engine is None:
                raise RuntimeError(warning or f"{self.engine.title} voice failed")
            self.backup = Voice(engine, self.state, cache=self.cache)
        if warning:
            self.warning = warning
        path = self.backup.fetch(text)
        if self.backup.warning:
            self.warning = self.backup.warning
            self.backup.warning = ""
        return path

    def duration(self, path: Path) -> float:
        d = self.durations.get(path)
        if d is None:
            d = self.durations[path] = audio_seconds(path) or 3.0
        return d

    def get(self, text: str) -> tuple[Path, float]:
        path = self.fetch(text)
        return path, self.duration(path)

    def want(self, text: str) -> concurrent.futures.Future:
        """A future for text's audio and duration, started if it isn't already."""
        k = self.key(text)
        future = self.futures.get(k)
        if future is None or (future.done() and future.exception() is not None):
            future = self.futures[k] = self.pool.submit(self.get, text)
        return future

    def close(self) -> None:
        self.pool.shutdown(wait=False, cancel_futures=True)
        if self.backup is not None:
            self.backup.close()


# ---------------------------------------------------------------- how long a file plays

def audio_seconds(path: Path) -> float | None:
    """How long an audio file plays: WAV and MP3 are read here, anything else is asked of afinfo or ffprobe."""
    try:
        if path.suffix == ".wav":
            with wave.open(str(path), "rb") as w:
                return w.getnframes() / w.getframerate()
        if path.suffix == ".mp3":
            return mp3_seconds(path.read_bytes())
    except (OSError, EOFError, wave.Error):
        pass
    if shutil.which("afinfo"):
        out = subprocess.run(["afinfo", str(path)], capture_output=True, text=True).stdout
        m = re.search(r"estimated duration: ([\d.]+)", out)
        return float(m.group(1)) if m else None
    if shutil.which("ffprobe"):
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                              str(path)], capture_output=True, text=True).stdout
        try:
            return float(out)
        except ValueError:
            return None
    return None


_MP3_KBPS = {  # bitrates by index, for MPEG-1 and for MPEG-2 and 2.5, layer III
    1: (0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320),
    2: (0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160),
}
_MP3_RATES = {3: (44100, 48000, 32000), 2: (22050, 24000, 16000), 0: (11025, 12000, 8000)}


def mp3_seconds(data: bytes) -> float | None:
    """The length of an MP3, by walking its frames, so variable bitrates come out right too."""
    i = 0
    if data[:3] == b"ID3" and len(data) >= 10:
        i = 10 + ((data[6] & 0x7F) << 21 | (data[7] & 0x7F) << 14 | (data[8] & 0x7F) << 7 | (data[9] & 0x7F))
    seconds, frames = 0.0, 0
    while i + 4 <= len(data):
        b1, b2 = data[i + 1], data[i + 2]
        version, layer = (b1 >> 3) & 3, (b1 >> 1) & 3
        bitrate, rate = b2 >> 4, (b2 >> 2) & 3
        if data[i] != 0xFF or b1 & 0xE0 != 0xE0 or version == 1 or layer != 1 or bitrate in (0, 15) or rate == 3:
            i += 1  # not a layer III frame header: look further on
            continue
        hz = _MP3_RATES[version][rate]
        kbps = _MP3_KBPS[1 if version == 3 else 2][bitrate]
        samples = 1152 if version == 3 else 576
        i += samples // 8 * kbps * 1000 // hz + ((b2 >> 1) & 1)
        seconds += samples / hz
        frames += 1
    return seconds if frames else None


def _error_message(data: bytes) -> str:
    try:
        err = json.loads(data)
        err = err.get("error", err.get("detail", err)) if isinstance(err, dict) else err
        if isinstance(err, dict):
            err = err.get("message") or err.get("status") or err
        return str(err)[:120]
    except (ValueError, KeyError, TypeError):
        return data[:120].decode("utf-8", "replace")
