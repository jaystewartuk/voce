"""Voices: Google's Chirp 3 HD voices when they are set up, the Mac's own voices otherwise.

Every sentence is fetched once and kept in the cache, keyed by the voice and the exact text, so listening again
costs nothing and works offline.

Google is used when either of these is available:

* ``VOCE_GOOGLE_API_KEY``: an API key for a Google Cloud project with the Text-to-Speech API enabled.
* the ``gcloud`` CLI, signed in. The quota project comes from ``VOCE_GOOGLE_PROJECT``, then
  ``voce --google-project``, then ``gcloud config get-value project``.
"""

from __future__ import annotations

import base64
import concurrent.futures
import hashlib
import http.client
import json
import os
import re
import shutil
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote

from voce import paths

CHIRP_VOICES = ["Charon", "Leda", "Orus", "Kore", "Puck", "Aoede", "Fenrir", "Despina"]
DEFAULT_GOOGLE_VOICE = "en-US-Chirp3-HD-Charon"
FREE_CHARS = 1_000_000  # Chirp 3 HD characters free each month, at the time of writing
_GIVE_UP_AFTER = 3      # consecutive Google failures before using the Mac voice for the rest of the session


@dataclass
class Google:
    """How to reach Google's Text-to-Speech API."""

    api_key: str = ""
    project: str = ""

    @classmethod
    def from_environment(cls, saved_project: str = "") -> Google | None:
        key = os.environ.get("VOCE_GOOGLE_API_KEY", "").strip()
        if key:
            return cls(api_key=key)
        if shutil.which("gcloud"):
            return cls(project=os.environ.get("VOCE_GOOGLE_PROJECT", "").strip() or saved_project)
        return None


def next_google_voice(name: str, step: int = 1) -> str:
    """The next Chirp 3 HD voice in the same language as name."""
    language = "-".join(name.split("-")[:2]) if name.count("-") >= 3 else "en-US"
    current = name.rsplit("-", 1)[-1]
    i = CHIRP_VOICES.index(current) if current in CHIRP_VOICES else -1
    return f"{language}-Chirp3-HD-{CHIRP_VOICES[(i + step) % len(CHIRP_VOICES)]}"


class Voice:
    """Turns text into a cached audio file, fetching ahead on a small thread pool."""

    def __init__(self, name: str, state, *, mac: bool = False, google: Google | None = None,
                 cache: Path | None = None) -> None:
        self.mac = mac or google is None
        self.name = name if mac or google is None else (name or DEFAULT_GOOGLE_VOICE)
        if self.mac and name.count("-") >= 3:
            self.name = ""  # a Google voice name means nothing to the Mac: use its default voice
        self.state, self.google = state, google
        self.cache = cache or paths.cache_dir()
        self.local = threading.local()
        self.lock = threading.Lock()
        self.token, self.token_at = "", 0.0
        self.failures = 0
        self.durations: dict[Path, float] = {}
        self.warning = ""
        self.pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)
        self.futures: dict[str, concurrent.futures.Future] = {}

    @property
    def label(self) -> str:
        if self.mac:
            return f"Mac {self.name}" if self.name else "Mac voice"
        return self.name.rsplit("-", 1)[-1]

    @property
    def uses_google(self) -> bool:
        return not self.mac

    # ---- cache

    def key(self, text: str) -> str:
        who = f"mac:{self.name}" if self.mac else self.name
        return hashlib.sha256(f"{who}|{text}".encode()).hexdigest()

    def path(self, text: str) -> Path:
        k = self.key(text)
        return self.cache / "audio" / k[:2] / (k + (".aiff" if self.mac else ".mp3"))

    # ---- Google

    def _gcloud(self, *args: str) -> str:
        return subprocess.run(["gcloud", *args], capture_output=True, text=True, check=True,
                              timeout=30).stdout.strip()

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.google.api_key:
            return headers
        with self.lock:
            if not self.token or time.monotonic() - self.token_at > 45 * 60:
                self.token = self._gcloud("auth", "print-access-token")
                self.token_at = time.monotonic()
                if not self.google.project:
                    self.google.project = self._gcloud("config", "get-value", "project")
            headers["Authorization"] = f"Bearer {self.token}"
            if self.google.project:
                headers["x-goog-user-project"] = self.google.project
        return headers

    def _synthesize(self, text: str) -> bytes:
        language = "-".join(self.name.split("-")[:2])
        body = json.dumps({"input": {"text": text},
                           "voice": {"languageCode": language, "name": self.name},
                           "audioConfig": {"audioEncoding": "MP3", "sampleRateHertz": 24000}})
        url = "/v1/text:synthesize"
        if self.google.api_key:
            url += "?key=" + quote(self.google.api_key)
        headers = self._headers()
        for attempt in range(3):
            conn = getattr(self.local, "conn", None)
            if conn is None:
                conn = self.local.conn = http.client.HTTPSConnection("texttospeech.googleapis.com", timeout=30)
            try:
                conn.request("POST", url, body, headers)
                response = conn.getresponse()
                data = response.read()
            except (OSError, http.client.HTTPException):
                self.local.conn = None
                if attempt == 2:
                    raise
                time.sleep(0.5 * (attempt + 1))
                continue
            if response.status == 401 and attempt < 2 and not self.google.api_key:
                with self.lock:
                    self.token = ""
                headers = self._headers()
                continue
            if response.status != 200:
                raise RuntimeError(f"Google Text-to-Speech said {response.status}: {_error_message(data)}")
            self.state.count(len(text))
            return base64.b64decode(json.loads(data)["audioContent"])
        raise RuntimeError("Google Text-to-Speech failed")

    # ---- the Mac

    def _say(self, text: str, out: Path, name: str) -> None:
        voice = ["-v", name] if name else []
        subprocess.run(["say", *voice, "-o", str(out), "--file-format=AIFF"], input=text, text=True,
                       check=True, capture_output=True)

    # ---- fetching

    def fetch(self, text: str) -> Path:
        """The audio file for text, made or fetched first if it isn't cached."""
        path = self.path(text)
        if path.exists():
            return path
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(f"{path.name}.{threading.get_ident()}.tmp")
        if self.mac:
            self._say(text, tmp, self.name)
        elif self.failures >= _GIVE_UP_AFTER:
            return self._fallback(text)
        else:
            try:
                tmp.write_bytes(self._synthesize(text))
                self.failures = 0
            except Exception as e:
                self.failures += 1
                self.warning = f"Google voice failed ({str(e)[:90]}); using the Mac voice for now."
                return self._fallback(text)
        tmp.replace(path)
        return path

    def _fallback(self, text: str) -> Path:
        path = self.cache / "audio" / "mac" / (hashlib.sha256(text.encode()).hexdigest() + ".aiff")
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_name(f"{path.name}.{threading.get_ident()}.tmp")
            self._say(text, tmp, "")
            tmp.replace(path)
        return path

    def duration(self, path: Path) -> float:
        d = self.durations.get(path)
        if d is None:
            out = subprocess.run(["afinfo", str(path)], capture_output=True, text=True).stdout
            m = re.search(r"estimated duration: ([\d.]+)", out)
            d = self.durations[path] = float(m.group(1)) if m else 3.0
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


def _error_message(data: bytes) -> str:
    try:
        return json.loads(data)["error"]["message"][:120]
    except (ValueError, KeyError, TypeError):
        return data[:120].decode("utf-8", "replace")
