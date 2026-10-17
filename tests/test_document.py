from voce.document import load, quiz_pairs


def write(tmp_path, md):
    path = tmp_path / "doc.md"
    path.write_text(md, encoding="utf-8")
    return path


def test_units_follow_sentences_headings_and_rows(tmp_path):
    doc = load(write(tmp_path, "# Title\n\nOne. Two.\n\n| a | b |\n|---|---|\n| 1 | 2 |\n\n```\ncode\n```"))
    assert [u.say for u in doc.units] == ["Title", "One.", "Two.", "a, b", "1, 2"]
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
