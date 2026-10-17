from voce.speech import sentences, speakable


def split(text):
    return [text[a:z] for a, z in sentences(text)]


def test_splits_sentences():
    assert split("One. Two! Three? Four") == ["One.", "Two!", "Three?", "Four"]


def test_abbreviations_and_initials_do_not_split():
    assert split("See e.g. this. Dr. Who met J. Smith. Done.") == ["See e.g. this.", "Dr. Who met J. Smith.", "Done."]


def test_quotes_and_brackets_stay_with_their_sentence():
    assert split('He said "stop." Then (quietly.) More.') == ['He said "stop."', "Then (quietly.)", "More."]


def test_lowercase_after_a_full_stop_is_not_a_new_sentence():
    assert split("Version 2.5 is out. next steps follow.") == ["Version 2.5 is out. next steps follow."]


def test_speakable_symbols_and_abbreviations():
    assert speakable("a → b, e.g. x & y, ~3 vs 4") == "a to b, for example, x and y, about 3 versus 4"


def test_speakable_table_separators():
    assert speakable("Name │ Size") == "Name, Size"
