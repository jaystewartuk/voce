from voce.document import load, quiz_pairs, spoken


def write(tmp_path, md):
    path = tmp_path / "doc.md"
    path.write_text(md, encoding="utf-8")
    return path


def test_units_follow_sentences_headings_and_rows(tmp_path):
    doc = load(write(tmp_path, "# Title\n\nOne. Two.\n\n| a | b |\n|---|---|\n| 1 | 2 |\n\n```\ncode\n```"))
    assert [u.say for u in doc.units] == ["Title", "One.", "Two.", "a, b", "1, 2", "code"]
    assert doc.title == "Title"


def test_ordered_items_say_their_number(tmp_path):
    doc = load(write(tmp_path, "1. Apples\n2. Pears"))
    assert [u.say for u in doc.units] == ["1. Apples", "2. Pears"]


QUIZ = "# Q\n\n## Quiz\n\n1. What is 2 + 2?\n2. Capital of France?\n\n## Answers\n\n1. Four.\n2. Paris.\n"


def test_quiz_answers_follow_their_questions_after_a_wait(tmp_path):
    doc = load(write(tmp_path, QUIZ))
    assert len(quiz_pairs(doc.blocks)) == 2
    says = [(u.say, u.wait) for u in doc.units]
    assert says == [("Q", False), ("Quiz", False), ("1. What is 2 + 2?", True), ("Answer. Four.", False),
                    ("2. Capital of France?", True), ("Answer. Paris.", False)]


def test_quiz_only_mode(tmp_path):
    doc = load(write(tmp_path, "Intro text.\n\n" + QUIZ), quiz_only=True)
    assert doc.units[0].say == "Quiz: Q." and doc.units[0].block == -1
    assert "Intro text." not in [u.say for u in doc.units]


def test_mismatched_quiz_reads_normally(tmp_path):
    doc = load(write(tmp_path, "## Quiz\n\n1. A?\n2. B?\n\n## Answers\n\n1. Only one.\n"))
    assert quiz_pairs(doc.blocks) == []
    assert "1. Only one." in [u.say for u in doc.units]


def test_inline_code_is_said_as_a_person_reads_it(tmp_path):
    md = "Wrap it in `array_values`. Use `===`, not `==`.\n\n| f | order |\n|---|---|\n| `array_map` | first |"
    doc = load(write(tmp_path, md))
    assert [u.say for u in doc.units] == ["Wrap it in array values.", "Use identical, not equal.",
                                          "f, order", "array map, first"]
    assert doc.blocks[0].text == "Wrap it in array_values. Use ===, not ==."


def test_spoken_joins_what_is_said():
    assert spoken("# `str_len`\n\nOne `->` two.") == "string length One arrow two."


CODE = ("Intro.\n\n```php\n$r = ['nights' => 0];\n\n"
        "isset($r['notes']);   // false: null counts as not set\n```\n\nAfter.")


def test_code_is_read_line_by_line_as_a_person_would(tmp_path):
    doc = load(write(tmp_path, CODE))
    says = [(u.say, u.block, u.start, u.end) for u in doc.units]
    assert says == [("Intro.", 0, 0, 6),
                    ("r equals array of nights double arrow 0", 1, 0, 21),
                    ("is set r notes, false: null counts as not set", 1, 23, 77),
                    ("After.", 2, 0, 6)]
    assert doc.units[1].pause == 0.45   # the blank line after it
    assert doc.units[2].pause == 0.5    # the end of the block


def test_skip_code_shows_code_without_reading_it(tmp_path):
    doc = load(write(tmp_path, CODE), skip_code=True)
    assert [u.say for u in doc.units] == ["Intro.", "After."]
    assert doc.title == "Intro."


DIFF = ("Before.\n\n````diff python\n@@ -10,3 +10,4 @@ def f(self):\n     x = 1\n-    return x\n+    y = x ** 2\n"
        "+\n+    return y  # squared\n````\n\n```diff markdown\n@@ -1,2 +1,2 @@\n-- Old **bullet** here.\n"
        "+- New bullet, with `code`.\n```\n")


def test_a_diff_is_read_as_a_reviewer_reads_it(tmp_path):
    doc = load(write(tmp_path, DIFF))
    assert doc.language == "python"
    says = [(u.say, u.pause) for u in doc.units]
    assert says == [("Before.", 0.4), ("Line 10.", 0.35), ("Removed, return x", 0.25),
                    ("Added, y equals x to the power of 2", 0.45), ("return y, squared", 0.5),
                    ("Line 1.", 0.35), ("Removed, Old bullet here.", 0.25), ("Added, New bullet, with code.", 0.5)]
    block = doc.blocks[1]
    assert block.text[doc.units[2].start:doc.units[2].end] == "-    return x"  # the band covers the marker too


def test_a_new_files_hunk_header_and_context_lines_are_not_read(tmp_path):
    doc = load(write(tmp_path, "```diff\n@@ -0,0 +1,2 @@\n+a = 1\n+b = 2\n```\n\n```diff\n ctx only\n another\n```"))
    assert [u.say for u in doc.units] == ["Added, a equals 1", "b equals 2", "context only", "another"]


def test_inline_code_follows_the_documents_main_language(tmp_path):
    doc = load(write(tmp_path, "Use `a === b` and `fn`.\n\n```js\nx\n```\n\n```js\ny\n```\n\n```php\nz\n```"))
    assert doc.units[0].say == "Use a is strictly equal to b and function."
