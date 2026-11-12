"""Moving between the terminal and the web app on the same computer, at the same place in the same document.

Both name a document by the hash of its text (state.key), so the terminal opens the web app at #/doc/<hash>, and
the web app hands the terminal `voce --open <the first characters of the hash>`. Places travel through the synced
library, so each side pushes its place before handing over.
"""

from __future__ import annotations

import webbrowser
from typing import Callable

from voce import sync
from voce.playlist import Entry
from voce.state import State

SHORT = 12  # characters of the hash the web app puts in `voce --open`


def web_link(key: str) -> str:
    return f"{sync.WEB_APP}#/doc/{key}"


def to_browser(state: State, key: str, say: Callable[[str], None]) -> None:
    """Push this place to the library, then open the document in the browser. Runs off the reader's thread."""
    try:
        if sync.commit(state.root):
            sync.pull(state.root, timeout=15)
            sync.push(state.root, timeout=30)
    except sync.SyncError as e:
        say(f"Opened in the browser, but couldn't sync your place: {e}")
    else:
        say("Opened in the browser")
    webbrowser.open(web_link(key))


def find(code: str, entries: list[Entry], state: State) -> int | None:
    """Which of the entries `voce --open CODE` means: the one whose hash starts with the code."""
    code = code.strip().lower()
    if len(code) < 8:
        return None
    return next((i for i, e in enumerate(entries) if state.key(e.path).startswith(code)), None)
