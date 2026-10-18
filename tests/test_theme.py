"""The theme's attributes, with colour pairs stood in for so no terminal is needed."""

import curses

from voce.markdown import Block
from voce.ui.theme import ITALIC, Theme


def theme():
    t = Theme()
    t.colour = t.many = True
    t.pairs = {name: n << 8 for n, name in enumerate(("sentence", "word", "keyword", "string", "comment"), start=1)}
    return t


def test_code_keeps_syntax_colour_until_it_is_read():
    t, code = theme(), Block("code", "x = 'a'  # note", lang="python")
    assert t.text(code, 0, frozenset({"string"}), None) == t.pair("string")
    assert t.text(code, 0, frozenset({"comment"}), None) == t.pair("comment") | ITALIC


def test_code_line_being_read_sits_on_the_band():
    t, code = theme(), Block("code", "x = 'a'  # note", lang="python")
    assert t.text(code, 0, frozenset({"string"}), "sentence") == t.pair("sentence")
    assert t.text(code, 0, frozenset({"comment"}), "sentence") == t.pair("sentence") | ITALIC
    assert t.text(code, 0, frozenset({"keyword"}), "word") == t.pair("word") | curses.A_BOLD


def test_prose_marks_are_unchanged():
    t, para = theme(), Block("p", "Plain text")
    assert t.text(para, 0, frozenset(), "sentence") == t.pair("sentence")
    assert t.text(para, 0, frozenset(), "word") == t.pair("word") | curses.A_BOLD
