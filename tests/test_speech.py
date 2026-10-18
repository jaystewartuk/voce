from voce.speech import sentences, speakable, spoken_code, spoken_line


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


def test_spoken_code_reads_names_as_a_person_would():
    assert spoken_code("array_values") == "array values"
    assert spoken_code("str_contains") == "string contains"
    assert spoken_code("mb_strlen") == "M B string length"
    assert spoken_code("usort()") == "U sort"
    assert spoken_code("json_encode") == "JSON encode"
    assert spoken_code("__invoke") == "invoke"
    assert spoken_code("ValueError") == "Value Error"
    assert spoken_code("checkInDate") == "check In Date"


def test_spoken_code_variables_arrows_and_operators():
    assert spoken_code("$reservation->nights") == "reservation arrow nights"
    assert spoken_code("$guest['email']") == "guest email"
    assert spoken_code("Str::slug") == "string double colon slug"
    assert spoken_code("===") == "identical"
    assert spoken_code("??=") == "null coalescing assignment"
    assert spoken_code("<=>") == "spaceship"
    assert spoken_code("fn") == "F N"


def test_spoken_line_reads_code_as_a_person_would():
    assert spoken_line("'1' == 1;        // true: the string is converted") == \
        "the string 1 is equal to 1, true: the string is converted"
    assert spoken_line("[] == false;") == "empty array is equal to false"
    assert spoken_line("$email = $r['guest']['email'] ?? 'none';") == "email equals r guest email null coalescing none"
    assert spoken_line("usort($list, fn ($a, $b) => $a['check_in'] <=> $b['check_in']);") == \
        "U sort list, F N a, b double arrow a check in spaceship b check in"
    assert spoken_line("foreach ($a as &$n) {") == "for each a as by reference n"
    assert spoken_line("$channels[] = 'vrbo';") == "channels square brackets equals vrbo"
    assert spoken_line("$all = [...$a, ...$b];") == "all equals array of unpack a, unpack b"
    assert spoken_line("if ($i !== false) { ... }   // the key can be 0") == \
        "if i is not identical to false and so on, the key can be 0"
    assert spoken_line("explode(',', '');") == "explode a comma, the empty string"
    assert spoken_line("function f(?string $tz = null): int") == "function f nullable string tz equals null colon int"
    assert spoken_line("    ->filter(fn ($r) => $r['channel'] === 'airbnb')") == \
        "arrow filter F N r double arrow r channel is identical to airbnb"
    assert spoken_line("new BlockDates()   // has __invoke") == "new Block Dates, has invoke"
    assert spoken_line("];") == ""
    assert spoken_line("# a python comment") == "a python comment"
    assert spoken_line("'strtoupper'   // ['a' => 1, ...]") == "string to upper, 'a' double arrow 1, and so on"
    assert spoken_line('"Guest: $guest[name]";') == "Guest: guest name"
    assert spoken_line("(int) (19.99 * 100);") == "cast to int 19.99 times 100"
    assert spoken_line("$count++; }") == "count increment"
    assert spoken_line('query = "&".join(parts)') == "query equals an ampersand dot join parts"
    assert spoken_line('return f"{request.path}?{query}"') == "return f string request.path question mark query"
    assert spoken_line("function block(string ...$dates): void") == "function block string variadic dates colon void"


def test_each_language_has_its_own_words():
    assert spoken_line("def f(x: int, *args, **kwargs) -> str:  # note", "python") == \
        "def f x colon int, star args, double star keyword args returns string colon, note"
    assert spoken_line("total = a // b if a != b else self.__init__", "py") == \
        "total equals a floor divided by b if a is not equal to b else self dot dunder init"
    assert spoken_line("const go = (a, b) => a?.x ?? [...b];  // js", "js") == \
        "const go equals a, b arrow a optional chaining x nullish coalescing array of spread b, js"
    assert spoken_line("if (a === b) {}", "typescript") == "if a is strictly equal to b"
    assert spoken_line("SELECT id FROM t WHERE a <> b -- why", "sql") == \
        "SELECT I D FROM t WHERE a is not equal to b, why"
    assert spoken_line("cat a.txt | grep x && echo ok  # shell", "bash") == \
        "cat a dot txt pipe grep x and then echo ok, shell"
    assert spoken_line("$x = 1; // php", "php") == "x equals 1, php"
    assert spoken_line("$x = 1; // unknown language reads like PHP", "cobol") == \
        "x equals 1, unknown language reads like PHP"


def test_paths_and_file_names_are_said_with_their_slashes_and_letters():
    assert spoken_code("src/voce/cli.py") == "source slash voce slash C L I dot P Y"
    assert spoken_code("test_reader.py") == "test reader dot P Y"
    assert spoken_code(".github/workflows/ci.yml") == "dot github slash workflows slash C I dot yaml"
    assert spoken_code("$a === $b") == "a is identical to b"
    assert spoken_code("a/b") == "a slash b"
    assert spoken_code("array.length") == "array dot length"
    assert spoken_code("docs/") == "docs slash"


def test_prose_inside_code_is_read_as_prose():
    assert spoken_line("    Immutability is enforced only after a release is published.") == \
        "Immutability is enforced only after a release is published"
    assert spoken_line("return x;  // done.") == "return x, done"
    assert spoken_line("import os, sys") == "import O S, sys"  # too short and too code-like to be prose


def test_speakable_diff_stats_and_middle_dots():
    assert speakable("`cli.py` (+12 −3)") == "`cli.py`, 12 added, 3 removed"
    assert speakable("x (+4) and y (−2)") == "x, 4 added and y, 2 removed"
    assert speakable("Part 1 · 12 min") == "Part 1, 12 min"
    assert speakable("(x)") == "(x)"
