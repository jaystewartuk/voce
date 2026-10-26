from voce.speech import sentences, speakable, spoken_code, spoken_line


def split(text):
    return [text[a:z] for a, z in sentences(text)]


def test_splits_sentences():
    assert split("One. Two! Three? Four") == ["One.", "Two!", "Three?", "Four"]


def test_abbreviations_and_initials_do_not_split():
    assert split("See e.g. this. Dr. Who met J. Smith. Done.") == ["See e.g. this.", "Dr. Who met J. Smith.", "Done."]


def test_quotes_and_brackets_stay_with_their_sentence():
    assert split('He said "stop." Then (quietly.) More.') == ['He said "stop."', "Then (quietly.)", "More."]


def test_spanish_questions_exclamations_and_accented_capitals_start_sentences():
    assert split("Eso no dice nada. ¿Lo levantó? ¡Claro! Él dijo «sí». «Bueno», dijo. Ésta es otra.") == \
        ["Eso no dice nada.", "¿Lo levantó?", "¡Claro!", "Él dijo «sí».", "«Bueno», dijo.", "Ésta es otra."]


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
    assert spoken_code("fn") == "arrow function"


def test_spoken_line_reads_code_as_a_person_would():
    assert spoken_line("'1' == 1;        // true: the string is converted") == \
        "the string 1 is equal to 1, true: the string is converted"
    assert spoken_line("[] == false;") == "empty array is equal to false"
    assert spoken_line("$email = $r['guest']['email'] ?? 'none';") == "email equals r guest email null coalescing none"
    assert spoken_line("usort($list, fn ($a, $b) => $a['check_in'] <=> $b['check_in']);") == \
        "U sort list, arrow function a, b returns a check in spaceship b check in"
    assert spoken_line("foreach ($a as &$n) {") == "for each a as by reference n"
    assert spoken_line("$channels[] = 'vrbo';") == "channels append vrbo"
    assert spoken_line("$all = [...$a, ...$b];") == "all equals array of unpack a, unpack b"
    assert spoken_line("if ($i !== false) { ... }   // the key can be 0") == \
        "if i is not identical to false and so on, the key can be 0"
    assert spoken_line("explode(',', '');") == "explode a comma, the empty string"
    assert spoken_line("function f(?string $tz = null): int") == \
        "function f nullable string time zone equals null colon int"
    assert spoken_line("    ->filter(fn ($r) => $r['channel'] === 'airbnb')") == \
        "arrow filter arrow function r returns r channel is identical to airbnb"
    assert spoken_line("new BlockDates()   // has __invoke") == "new Block Dates, has invoke"
    assert spoken_line("];") == ""
    assert spoken_line("# a python comment") == "a python comment"
    assert spoken_line("'strtoupper'   // ['a' => 1, ...]") == "string to upper, 'a' double arrow 1, and so on"
    assert spoken_line('"Guest: $guest[name]";') == "Guest: guest name"
    assert spoken_line("(int) (19.99 * 100);") == "cast to int 19.99 times 100"
    assert spoken_line("$count++; }") == "count increment"
    assert spoken_line('query = "&".join(parts)') == "query equals an ampersand dot join parts"
    assert spoken_code("[") == "open square bracket"  # a lone bracket is said, not stripped as a subscript
    assert spoken_code("]") == "close square bracket"
    assert spoken_line('return f"{request.path}?{query}"') == "return f string request.path question mark query"
    assert spoken_line("function block(string ...$dates): void") == "function block string variadic dates colon void"


def test_each_language_has_its_own_words():
    assert spoken_line("def f(x: int, *args, **kwargs) -> str:  # note", "python") == \
        "def f x colon int, star args, double star keyword args returns string, note"
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


def test_python_reads_like_micrograd_out_loud():
    # Lines from karpathy/micrograd's engine.py, the way a person talks through them.
    assert spoken_line('    """ stores a single scalar value and its gradient """', "python") == \
        "stores a single scalar value and its gradient"
    assert spoken_line('    """', "python") == ""
    assert spoken_line("    def __init__(self, data, _children=(), _op=''):", "python") == \
        "def dunder init self, data, children equals empty tuple, op equals the empty string"
    assert spoken_line("            for child in v._prev:", "python") == "for child in v dot previous"
    assert spoken_line("if x: return 1", "python") == "if x, return 1"
    assert spoken_line("        topo = []", "python") == "topo equals empty list"
    assert spoken_line("seen = {}", "python") == "seen equals empty dict"
    assert spoken_line("    def __radd__(self, other): # other + self", "python") == \
        "def dunder R add self, other, other plus self"
    assert spoken_line("    def __neg__(self): # -self", "python") == "def dunder neg self, minus self"
    assert spoken_line('        return f"Value(data={self.data}, grad={self.grad})"', "python") == \
        "return f string Value data equals self dot data, grad equals self dot grad"
    assert spoken_code("a ** n", "python") == "a to the power of n"
    assert spoken_code("nn.py") == "N N dot P Y"
    assert spoken_line("d = {'a': 1}", "python") == "d equals a colon 1"  # a colon inside a line is still said


def test_paths_and_file_names_are_said_with_their_slashes_and_letters():
    assert spoken_code("/stubs/job.stub") == "slash stubs slash job dot stub"  # a leading slash is said once
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


def test_doc_comment_lines_are_read_as_a_person_reads_them():
    assert spoken_line("/**", "php") == ""
    assert spoken_line(" */", "php") == ""
    assert spoken_line(" * Determine if the HTTP status code has been set.", "php") == \
        "Determine if the HTTP status code has been set"
    assert spoken_line(" * @param  array|string  $columns  The columns to select.", "php") == \
        "parameter array or string, columns, The columns to select"
    assert spoken_line(" * @return \\Illuminate\\Contracts\\Auth\\Authenticatable|null", "php") == \
        "returns Illuminate Contracts auth Authenticatable or null"
    assert spoken_line(" * @var array<int, string>", "php") == "var array of int, string"
    assert spoken_line(" * @param  \\Closure(TValue): bool  $callback", "php") == \
        "parameter Closure taking T Value returning bool, callback"
    assert spoken_line(" * @param  ?string  &$name", "php") == "parameter nullable string, by reference name"
    assert spoken_line(" * @param  mixed  ...$args", "php") == "parameter mixed, variadic args"
    assert spoken_line(" * @method static void mixin(object $mixin, bool $replace = true)", "php") == \
        "method static void mixin taking object mixin, bool replace equals true"
    assert spoken_line(" * @return array{\\DateTimeInterface, int}", "php") == \
        "returns array of Date Time Interface, int"
    assert spoken_line(" * {@inheritdoc}", "php") == "inherit doc"
    assert spoken_line("    * 2;", "php") == "star 2"  # a multiplication carried onto the next line


def test_php_attributes_tags_and_alternative_syntax():
    assert spoken_line("#[AsCommand(name: 'make:cast')]", "php") == "attribute As Command name colon make colon cast"
    assert spoken_line("<?php", "php") == "P H P open tag"
    assert spoken_line("<?= $title ?>", "php") == "P H P echo tag title P H P close tag"
    assert spoken_line("@endforeach", "php") == "at end for each"
    assert spoken_line("if ($p instanceof Arrayable) {", "php") == "if p instance of array able"


def test_append_ternary_and_union_types():
    assert spoken_line("$this->beforeCallbacks[] = $callback;", "php") == "this arrow before Callbacks append callback"
    assert spoken_line("return $request->expectsJson() ? null : $this->redirectTo($request);", "php") == \
        "return request arrow expects JSON then null else this arrow redirect To request"
    assert spoken_line("    : $default;", "php") == "else default"
    assert spoken_line("return [$a ?: 'x', $b ? $c : $d];", "php") == \
        "return array of a short ternary x, b then c else d"
    assert spoken_line("public function withScheme(Stringable|string $scheme): static", "php") == \
        "public function with Scheme Stringable or string scheme colon static"
    assert spoken_line("function foo(A&B $x, ?\\Closure $cb = null): int|null", "php") == \
        "function foo A and B x, nullable Closure callback equals null colon int or null"
    assert spoken_line("$flags = $a | $b;", "php") == "flags equals a pipe b"


def test_strings_say_their_symbols_and_their_code():
    assert spoken_line("$query->where('votes', '>=', 100);", "php") == \
        "query arrow where votes, greater than or equal to, 100"
    assert spoken_line("str_contains($key, '@');", "php") == "string contains key, an at sign"
    assert spoken_line("explode('\\\\', $class);", "php") == "explode a backslash, class"
    assert spoken_line('$column = Str::after($column, "{$this->model->getTable()}.");', "php") == \
        "column equals string double colon after column, this arrow model arrow get Table"
    assert spoken_line('$sql = "where id = ?";', "php") == "S Q L equals where id = question mark"


def test_a_where_with_its_operator_left_out_says_the_equals_it_means():
    assert spoken_line("->where('property_id', 1),", "php") == "arrow where property I D is equal to 1"
    assert spoken_line("$q->where('property_id', '=', 1);", "php") == "q arrow where property I D is equal to 1"
    assert spoken_line("->orWhere('status', 'active')", "php") == "arrow or Where status is equal to active"
    assert spoken_line("->whereIn('id', $ids)", "php") == "arrow where In I D, ids"  # no operator is implied
    assert spoken_line("->where('a', [1, 2])", "php") == "arrow where a, array of 1, 2"
    assert spoken_code("->where('property_id', 1)", "php") == "arrow where property I D is equal to 1"


def test_abbreviations_inside_camel_case_names():
    assert spoken_code("expectsJson") == "expects JSON"
    assert spoken_code("getId") == "get I D"
    assert spoken_code("toHtml") == "to HTML"
    assert spoken_code("SqsQueue") == "S Q S Queue"
    assert spoken_code("IoC") == "I O C"
    assert spoken_code("rtrim") == "R trim"


def test_a_class_declaration_is_not_prose():
    assert spoken_line("class Router implements BindingRegistrar, RegistrarContract", "php") == \
        "class Router implements Binding Registrar, Registrar Contract"
    assert spoken_line("return 'The table is empty';", "php") == "return 'The table is empty';"


def test_an_arrow_function_returns_its_expression_and_keeps_its_double_arrows():
    assert spoken_line("fn ($x) => ['a' => $x, 'b' => fn () => 2]", "php") == \
        "arrow function x returns array of a double arrow x, b double arrow arrow function returns 2"
    assert spoken_line("$items->map(fn ($item) => $item->toArray())->filter(fn ($i) => $i > 1);", "php") == \
        "items arrow map arrow function item returns item arrow to Array " \
        "arrow filter arrow function i returns i greater than 1"
    assert spoken_line("const fn = () => 1;", "javascript") == "const function equals arrow 1"


def test_a_path_inside_a_string_is_read_as_a_path():
    assert spoken_line("Route::middleware(['web', 'auth:sanctum'])->group(base_path('routes/web.php'));", "php") == \
        "Route double colon middleware array of web, auth colon sanctum arrow group base path " \
        "routes slash web dot P H P"
    assert spoken_line("str_ends_with($host, 'booking.com')", "php") == "string ends with host, booking dot com"


def test_each_language_has_its_aliases_and_a_manual():
    from voce.speech.words import ALL, LANGUAGES, PROSE, language

    claimed = [alias for lang in ALL for alias in lang.aliases]
    assert len(claimed) == len(set(claimed)), "an alias is claimed by two languages"
    assert set(LANGUAGES) == set(claimed)
    for lang in ALL:
        assert lang.aliases, lang.name
        assert language(lang.aliases[0]) is lang
        if lang is not PROSE:
            assert lang.manual.startswith("https://"), lang.name


def test_prepared_documents_are_remade_when_a_language_file_changes(monkeypatch):
    from pathlib import Path

    import voce
    from voce import prepared

    here, seen, real = Path(voce.__file__).parent, [], Path.read_bytes
    monkeypatch.setattr(Path, "read_bytes", lambda self: seen.append(self.relative_to(here).as_posix()) or real(self))
    prepared._reading_code()
    assert "speech/words/php.py" in seen and "speech/words/common.py" in seen
