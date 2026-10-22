"""Voices: two engines that turn a sentence into audio, both on this computer, and the cache that keeps every
sentence once it is said. Nothing is sent anywhere and nothing costs anything.

* Kokoro  a small open model. The default: there is nothing to set up. The model (120 MB) is downloaded once,
          into the cache.
* Mac     the Mac's own voices, through ``say``. Used when Kokoro can't run, and as the backup. macOS only.

The engine chosen with ``--engine`` or the V key is remembered. Every sentence is made once and kept in the cache,
keyed by the engine, the voice and the exact text, so listening again is instant. When Kokoro fails, the sentence
is said by the Mac instead and the reader is told why.
"""

from __future__ import annotations

import concurrent.futures
import hashlib
import importlib.util
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

from voce import paths

_GIVE_UP_AFTER = 3      # failures in a row before an engine rests
_REST_SECONDS = 60      # how long the backup voice is used before the engine is tried again


# ---------------------------------------------------------------- engines

class Engine:
    """One way of turning text into audio. Subclasses say how to reach it and which voices it has."""

    kind = ""            # the word used on the command line and in the state file
    title = ""           # the word used in messages
    ext = "wav"          # what its audio files are
    rate = 24000         # their sample rate
    voices: tuple[str, ...] = ()   # the voices the v key cycles through
    default = ""
    setup = ""           # how to set it up, for messages

    def __init__(self, name: str = "") -> None:
        self.name = name or self.default

    @classmethod
    def configured(cls, state) -> bool:
        """Whether this engine can be used here: it is installed."""
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
    kind, title, ext, rate = "mac", "Mac", "aiff", 22050
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
    kind, title = "kokoro", "Kokoro"
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


ENGINES: dict[str, type[Engine]] = {e.kind: e for e in (Kokoro, Mac)}


def available(state) -> list[str]:
    """The engines that can be used here, in the order the V key goes through them."""
    return [kind for kind in ENGINES if ENGINES[kind].configured(state)]


def default_engine(state) -> str:
    """The engine to use when none is asked for: the one chosen last time, else Kokoro, else the Mac. A saved
    choice of an engine voce no longer has, such as Google, falls back the same way."""
    kinds = available(state)
    saved = state.get("engine", "")
    if saved in kinds:
        return saved
    return "mac" if "mac" in kinds and "kokoro" not in kinds else "kokoro"


def engine_for(name: str, state) -> str:
    """The engine a voice name belongs to: Kokoro's names have a shape of their own, anything else is the Mac's."""
    return "kokoro" if Kokoro.owns(name) else "mac"


def saved_name(state, kind: str) -> str:
    return (state.get("voices") or {}).get(kind, "")


def remember(state, voice: Voice) -> None:
    state.set("engine", voice.kind)
    names = dict(state.get("voices") or {})
    names[voice.kind] = voice.name
    state.set("voices", names)


def make(kind: str, name: str, state, cache: Path | None = None) -> Voice:
    engine = ENGINES[kind].build(name or saved_name(state, kind), state)
    return Voice(engine, state, cache=cache)


def backup_for(engine: Engine, state) -> Engine | None:
    """What says a sentence when engine can't: the Mac for Kokoro, nothing for the Mac. Off a Mac there are no
    Mac voices, so Kokoro has no backup."""
    if engine.kind == "mac":
        return None
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

    def downloading(self) -> str:
        return self.engine.downloading()

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
        except Exception as e:
            tmp.unlink(missing_ok=True)
            with self.lock:
                self.failures += 1
                if self.failures >= _GIVE_UP_AFTER:
                    self.failures = 0
                    self.resting_until = time.monotonic() + _REST_SECONDS
            return self._fallback(text, f"{self.engine.title} voice failed ({str(e)[:90]}); using the "
                                        f"{self._backup_title()} voice for now.")
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
    """How long an audio file plays: a WAV is read here, anything else is asked of afinfo or ffprobe."""
    try:
        if path.suffix == ".wav":
            with wave.open(str(path), "rb") as w:
                return w.getnframes() / w.getframerate()
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
