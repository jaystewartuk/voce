from voce.highlight import code_spans


def roles(code, lang=""):
    return {code[a:z]: set(r) for a, z, r in code_spans(code, lang)}


def test_known_language():
    found = roles("const x = 42; // answer", "js")
    assert found["const"] == {"keyword"} and found["42"] == {"number"} and found["// answer"] == {"comment"}


def test_diffs_mark_insertions_and_deletions():
    found = roles("@@ -1,2 +1,2 @@\n same\n-old line\n+new line\n", "diff")
    assert found["-old line"] == {"deleted"} and found["+"] == {"inserted"}
    assert found[" same"] == {"context"} and found["@@ -1,2 +1,2 @@"] == {"prompt"}


def test_a_diff_of_a_language_highlights_the_added_lines_as_that_language():
    code = "@@ -1,3 +1,4 @@ def f\n def f(x):\n-    return 1\n+    s = \"\"\"a\n+    b\"\"\"\n+    return 2  # c\n"
    found = roles(code, "diff python")
    assert found["return"] == {"keyword"} and found["# c"] == {"comment"} and found["-    return 1"] == {"deleted"}
    assert found['"""a'] == {"string"} and found['    b"""'] == {"string"}  # a string over two added lines
    assert " def f(x):" in found and found[" def f(x):"] == {"context"}  # context is dimmed, not lexed


def test_unknown_language_is_plain():
    assert code_spans("whatever", "no-such-language") == []


def test_single_unlabelled_line_is_not_guessed():
    assert code_spans("x = 1") == []


def test_offsets_match_the_source():
    code = "def é():\n    pass"
    for a, z, _ in code_spans(code, "python"):
        assert 0 <= a < z <= len(code)


def test_php_without_an_opening_tag_is_still_highlighted():
    spans = code_spans("$total = number_format($cents / 100, 2); // edge\n", "php")
    roles = {role for _, _, roles in spans for role in roles}
    assert {"variable", "comment"} <= roles
    assert any(r for _, _, r in code_spans("<?php\n$x = 1;", "php"))
