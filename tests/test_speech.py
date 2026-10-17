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


def test_speakable_versioned_codes_are_not_money():
    assert speakable("PHP 8 and PHP 7.4.1") == "P H P 8 and P H P 7.4.1"
    assert speakable("BSD 3, CRC 32, CVE 24") == "B S D 3, C R C 32, C V E 24"
    assert speakable("PHP is fine. PHP8 and CVE-2024-3094 too") == "PHP is fine. PHP8 and CVE-2024-3094 too"
    assert speakable("PHP 1,500 or PHP 500 or USD 8") == "PHP 1,500 or PHP 500 or USD 8"


def test_speakable_table_separators():
    assert speakable("Name │ Size") == "Name, Size"
