"""Running the reader inside curses: the terminal, the theme, the optional menu, and tidying up after."""

from __future__ import annotations

import curses
import locale
import os
import signal
from typing import Callable

from voce.playlist import Entry
from voce.state import State
from voce.ui.menu import menu
from voce.ui.reader import Options, Reader
from voce.ui.terminal import Terminal
from voce.ui.theme import Theme
from voce.voices import Voice


def play(playlist: list[Entry], start: int, options: Options, state: State, voice: Voice,
         switch: Callable[[Voice, str], Voice | None], player, show_menu: bool = False) -> None:
    """Read the playlist from the file at start, in the terminal, until the listener quits."""

    def session(scr) -> None:
        locale.setlocale(locale.LC_ALL, "")
        term, theme = Terminal(scr), Theme()
        term.start()
        theme.start()
        try:
            index = start
            if show_menu and len(playlist) > 1:
                choice = menu(term, theme, state, playlist, start)
                if choice is None:
                    return
                index = choice
            Reader(term, theme, options, state, voice, switch, player, playlist, index).run()
        finally:
            term.stop()

    def interrupted(*_) -> None:
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, interrupted)
    os.environ.setdefault("ESCDELAY", "25")
    try:
        curses.wrapper(session)
    except KeyboardInterrupt:
        pass
    finally:
        player.close()
        state.save(force=True)
