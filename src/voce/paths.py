"""Where voce keeps its state and cache, following the XDG base directory conventions."""

from __future__ import annotations

import os
from pathlib import Path


def _base(variable: str, default: str) -> Path:
    value = os.environ.get(variable)
    return Path(value).expanduser() if value else Path.home() / default


def state_dir() -> Path:
    """Saved places, settings, usage and clipboard clips. VOCE_STATE points it at a synced folder."""
    own = os.environ.get("VOCE_STATE")
    return Path(own).expanduser() if own else _base("XDG_STATE_HOME", ".local/state") / "voce"


def cache_dir() -> Path:
    """Fetched audio and the compiled audio player. Safe to delete at any time."""
    return _base("XDG_CACHE_HOME", ".cache") / "voce"


def clips_dir() -> Path:
    return state_dir() / "clips"
