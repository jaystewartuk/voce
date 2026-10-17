"""Audio playback on macOS.

The native player is a small Swift program (player.swift, compiled once with the Xcode command line tools). It
plays sentences back to back with no gap, pauses mid-word, changes speed without changing pitch, and reports the
exact position so the word highlight keeps time. Without swiftc, voce falls back to one ``afplay`` per sentence.
"""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import threading
import time
from importlib import resources
from pathlib import Path

from voce import paths


def build_player(cache: Path | None = None, quiet: bool = False) -> Path | None:
    """The compiled native player, building it on first use; None if that isn't possible."""
    if not shutil.which("swiftc"):
        return None
    source = resources.files("voce").joinpath("player.swift").read_text(encoding="utf-8")
    digest = hashlib.sha256(source.encode()).hexdigest()[:12]
    binary = (cache or paths.cache_dir()) / "bin" / f"voce-player-{digest}"
    if binary.exists():
        return binary
    binary.parent.mkdir(parents=True, exist_ok=True)
    swift = binary.with_suffix(".swift")
    swift.write_text(source, encoding="utf-8")
    if not quiet:
        print("Preparing the audio player (once, about ten seconds)...", flush=True)
    result = subprocess.run(["swiftc", "-O", "-o", str(binary), str(swift)], capture_output=True, text=True)
    if result.returncode != 0:
        if not quiet:
            print("Couldn't build it, so using afplay instead:", result.stderr.strip()[:200])
        return None
    return binary


class NativePlayer:
    """Drives the Swift player over a pipe."""

    can_pause = True

    def __init__(self, binary: Path) -> None:
        self.proc = subprocess.Popen([str(binary)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.DEVNULL, text=True, bufsize=1)
        self.lock = threading.Lock()
        self.ids = 0
        self.id = ""
        self.pos = 0.0
        self.done: set[str] = set()
        self.length = 0.0
        self.rate: float | None = None
        self.error = ""
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self) -> None:
        for line in self.proc.stdout:
            parts = line.split()
            if not parts:
                continue
            with self.lock:
                if parts[0] == "pos" and len(parts) == 3 and parts[1] == self.id:
                    self.pos = float(parts[2])
                elif parts[0] == "done" and len(parts) == 2:
                    self.done.add(parts[1])
                elif parts[0] == "error":
                    self.error = line.strip()[6:]

    def _send(self, line: str) -> None:
        try:
            self.proc.stdin.write(line + "\n")
            self.proc.stdin.flush()
        except (BrokenPipeError, OSError):
            pass

    def play(self, path: Path, duration: float, speed: float) -> None:
        self.set_rate(speed)
        with self.lock:
            self.ids += 1
            self.id = str(self.ids)
            self.pos = 0.0
            self.length = duration
        self._send(f"play {self.id} {path}")

    def set_rate(self, speed: float) -> None:
        if speed != self.rate:
            self.rate = speed
            self._send(f"rate {speed:.2f}")

    def position(self) -> float:
        with self.lock:
            return self.pos

    def finished(self) -> bool:
        with self.lock:
            return self.id in self.done

    def pause(self) -> None:
        self._send("pause")

    def resume(self) -> None:
        self._send("resume")

    def stop(self) -> None:
        with self.lock:
            self.id = ""
        self._send("stop")

    def close(self) -> None:
        self._send("quit")
        try:
            self.proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            self.proc.kill()


class AfplayPlayer:
    """One afplay per sentence: a short gap between sentences, and pausing restarts the sentence."""

    can_pause = False

    def __init__(self, mute: bool = False) -> None:
        self.mute = mute
        self.proc: subprocess.Popen | None = None
        self.started, self.length, self.speed = 0.0, 0.0, 1.0
        self.error = ""

    def play(self, path: Path, duration: float, speed: float) -> None:
        self.stop()
        self.length, self.speed = duration, speed
        self.started = time.monotonic()
        if not self.mute:
            self.proc = subprocess.Popen(["afplay", "-q", "1", "-r", f"{speed:.2f}", str(path)],
                                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def set_rate(self, speed: float) -> None:
        self.speed = speed

    def position(self) -> float:
        lag = 0.0 if self.mute else 0.3
        return max(0.0, time.monotonic() - self.started - lag) * self.speed

    def finished(self) -> bool:
        if self.proc is not None:
            return self.proc.poll() is not None
        return self.position() >= self.length

    def pause(self) -> None:
        self.stop()

    def resume(self) -> None:
        pass

    def stop(self) -> None:
        if self.proc is not None and self.proc.poll() is None:
            self.proc.kill()
            try:
                self.proc.wait(timeout=1)
            except subprocess.TimeoutExpired:
                pass
        self.proc = None

    def close(self) -> None:
        self.stop()


def make_player(mute: bool = False, afplay: bool = False):
    if not mute and not afplay:
        binary = build_player()
        if binary:
            try:
                return NativePlayer(binary)
            except OSError:
                pass
    return AfplayPlayer(mute=mute)
