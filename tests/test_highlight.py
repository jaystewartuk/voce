from voce.highlight import code_spans


def roles(code, lang=""):
    return {code[a:z]: set(r) for a, z, r in code_spans(code, lang)}


def test_known_language():
    found = roles("const x = 42; // answer", "js")
    assert found["const"] == {"keyword"} and found["42"] == {"number"} and found["// answer"] == {"comment"}


def test_diffs_mark_insertions_and_deletions():
    found = roles("-old line\n+new line\n", "diff")
    assert found["-old line"] == {"deleted"} and found["+new line"] == {"inserted"}


def test_unknown_language_is_plain():
    assert code_spans("whatever", "no-such-language") == []


def test_single_unlabelled_line_is_not_guessed():
    assert code_spans("x = 1") == []


def test_offsets_match_the_source():
    code = "def é():\n    pass"
    for a, z, _ in code_spans(code, "python"):
        assert 0 <= a < z <= len(code)
