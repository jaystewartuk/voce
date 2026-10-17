from voce.markdown import parse


def kinds(md):
    return [(b.kind, b.text) for b in parse(md)]


def test_headings_paragraphs_and_sections():
    blocks = parse("# Title\n\nSome text\nwrapped.\n\n## Part two\n\nMore.")
    assert [(b.kind, b.text) for b in blocks] == [
        ("h1", "Title"), ("p", "Some text wrapped."), ("h2", "Part two"), ("p", "More.")]
    assert blocks[-1].section == "part two"


def test_lists_ordered_nested_and_tasks():
    blocks = parse("1. First\n2. Second\n   carried on\n- [x] done\n- [ ] to do\n  - nested")
    assert [(b.prefix, b.text, b.indent) for b in blocks] == [
        ("1. ", "First", 0), ("2. ", "Second carried on", 0), ("☑ ", "done", 0), ("☐ ", "to do", 0),
        ("• ", "nested", 1)]
    assert blocks[0].ordered and not blocks[2].ordered


def test_fenced_code_keeps_language_spacing_and_highlighting():
    md = "Before.\n\n```python\ndef f(x):\n    return 'hi'  # greet\n```\n\nAfter."
    code = parse(md)[1]
    assert code.kind == "code" and code.lang == "python" and not code.spoken
    assert code.text == "def f(x):\n    return 'hi'  # greet"
    roles = {code.text[a:z]: set(r) for a, z, r in code.spans}
    assert roles["def"] == {"keyword"}
    assert roles["f"] == {"function"}
    assert roles["'hi'"] == {"string"}
    assert roles["# greet"] == {"comment"}


def test_longer_fences_and_tildes_contain_shorter_ones():
    md = "````md\n```\ninner\n```\n````\n\n~~~\nplain\n~~~"
    blocks = parse(md)
    assert [b.text for b in blocks] == ["```\ninner\n```", "plain"]


def test_indented_fence_inside_a_list_is_dedented():
    blocks = parse("- step:\n\n  ```bash\n  echo hi\n  ```")
    assert blocks[1].text == "echo hi" and blocks[1].lang == "bash"


def test_unclosed_fence_runs_to_the_end():
    assert parse("```\nno end")[0].text == "no end"


def test_tables_line_up_and_read_row_by_row():
    md = "| Name | Size |\n|------|-----:|\n| a | 1 |\n| longer | 200 |"
    rows = parse(md)
    assert [b.kind for b in rows] == ["row", "rule", "row", "row"]
    assert rows[0].text == "Name   │ Size"
    assert rows[2].text == "a      │    1"
    assert rows[3].say == "longer, 200"
    assert rows[0].spans[0] == (0, len(rows[0].text), frozenset({"bold"}))
    assert not rows[1].spoken


def test_table_cell_styles_shift_with_padding():
    rows = parse("| a | b |\n|---|---|\n| x | `code` |")
    row = rows[2]
    code = [(a, z) for a, z, r in row.spans if "code" in r]
    assert [row.text[a:z] for a, z in code] == ["code"]


def test_table_without_leading_pipe():
    assert [b.kind for b in parse("a | b\n--|--\n1 | 2")] == ["row", "rule", "row"]


def test_wide_tables_are_joined_not_padded():
    cell = "word " * 30
    rows = parse(f"| {cell} | {cell} |\n|---|---|\n| x | y |")
    assert [b.kind for b in rows] == ["row", "row"]
    assert rows[1].text == "x │ y"


def test_quotes_rules_and_navigation():
    blocks = parse("> quoted\n> text\n\n---\n\n[Home](a.md) · [Up](b.md)\n\nNext: [More](c.md)")
    assert [(b.kind, b.spoken) for b in blocks] == [("quote", True), ("hr", True), ("meta", False), ("meta", False)]


def test_details_are_shown_but_not_read():
    blocks = parse("<details>\n<summary>Hint</summary>\n\nHidden text.\n\n</details>\n\nVisible.")
    assert [(b.kind, b.text, b.spoken) for b in blocks] == [
        ("html", "▸ Hint", False), ("p", "Hidden text.", False), ("p", "Visible.", True)]


def test_inline_html_at_line_start_is_kept():
    assert kinds("<kbd>q</kbd> quits.") == [("p", "q quits.")]


def test_comments_are_dropped():
    assert kinds("<!-- a\nmulti-line comment -->\nText.") == [("p", "Text.")]


def test_horizontal_rule_is_not_a_list():
    assert kinds("* * *") == [("hr", "")]
