from pathlib import Path

from voce.document import Doc, Unit
from voce.markdown import parse
from voce.ui.layout import CODE_GUTTER, layout, word_at, wrap


def doc_of(md):
    return Doc(Path("x.md"), "x", parse(md))


def test_wrap_breaks_at_spaces_and_splits_long_words():
    text = "aaa bbb ccc " + "x" * 12
    assert [text[a:z] for a, z in wrap(text, 7)] == ["aaa bbb", "ccc", "xxxxxxx", "xxxxx"]


def test_layout_gaps_bullets_and_first_lines():
    lines, where = layout(doc_of("# T\n\n- one\n- two\n\nPara."), 40)
    shown = [(ln.prefix, ln.block) for ln in lines]
    assert shown == [("", 0), ("", -1), ("• ", 1), ("• ", 2), ("", -1), ("", 3)]
    assert where == {0: 0, 1: 2, 2: 3, 3: 5}


def test_code_keeps_spacing_label_and_wraps_long_lines():
    doc = doc_of("```py\n" + "    x = 1\n" + "y" * 50 + "\n```")
    lines, _ = layout(doc, 32)
    text = doc.blocks[0].text
    assert lines[0].prefix == CODE_GUTTER + "py"
    assert [text[ln.start:ln.end] for ln in lines[1:]] == ["    x = 1", "y" * 30, "y" * 20]


def test_word_highlight_moves_through_the_sentence():
    text = "one two three"
    unit = Unit(0, 0, len(text), text)
    assert text[slice(*word_at(unit, text, 0.0, 2.0))] == "one"
    assert text[slice(*word_at(unit, text, 1.99, 2.0))] == "three"
    assert word_at(unit, text, 1.0, 0) is None
