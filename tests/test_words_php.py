"""PHP read the way a person says it, with the PHP manual's names for its operators."""

from __future__ import annotations

import pytest

from voce.speech import spoken_line


@pytest.mark.parametrize("line, spoken", [
    # operators, by the manual's names
    ("if ($a <> $b) {", "if A is not equal to b"),
    ("$flags = $mask >> 2;", "flags equals mask shifted right by 2"),
    ("$hash = $hash ^ ord($char);", "hash equals hash exclusive or ord char"),
    ("$this->bitfield &= ~$mask;", "this arrow bitfield ampersand equals bitwise not mask"),
    ("if ($a xor $b) {", "if A exclusive or b"),
    ("$a ??= [];", "A null coalescing assignment empty array"),
    ("return $a <=> $b;", "return A spaceship b"),
    ("$x = $a ** 2 % 3;", "x equals A to the power of 2 modulo 3"),
    # names said by their letters or in full
    ("$this->buffer .= \\PHP_EOL;", "this arrow buffer dot equals P H P end of line"),
    ("use Illuminate\\Http\\Request;", "use Illuminate HTTP Request"),
    ("$uri = $request->getUri();", "U R I equals request arrow get U R I"),
    ("return hash_hmac('sha256', $payload, $key);", "return hash H MAC sha256, payload, key"),
    ("$roll = mt_rand(1, 6);", "roll equals M T rand 1, 6"),
    ("if (ctype_xdigit($value)) {", "if C type hex digit value"),
    ("spl_autoload_register([$this, 'loadClass']);", "S P L autoload register array of this, load Class"),
    ("if (!ini_get('display_errors')) {", "if not I N I get display errors"),
    ("$iv = openssl_random_pseudo_bytes(16);", "I V equals open S S L random pseudo bytes 16"),
    ("curl_setopt($ch, CURLOPT_TIMEOUT, 10);", "curl set option ch, curl option TIMEOUT, 10"),
    ("$script = $argv[0];", "script equals arg V 0"),
    ("$db = new SQLiteConnection($pdo);", "D B equals new S Q L Lite Connection P D O"),
    ("public function executeTty($command, ?string $cwd = null): int",
     "public function execute T T Y command, nullable string C W D equals null colon int"),
    ("$pos = strrchr($path, '/');", "position equals string R char path, a slash"),
    ("natcasesort($names);", "natural case sort names"),
    ("goto retry;", "go to retry"),
])
def test_php_reads_as_a_person_says_it(line, spoken):
    assert spoken_line(line, "php") == spoken


@pytest.mark.parametrize("line, spoken", [
    ("$value = $x << 3;", "value equals x shifted left by 3"),
    ("$value <<= 1;", "value left shift equals 1"),
    ("$value >>= 1;", "value right shift equals 1"),
    ("$length = $text |> strlen($text);", "length equals text piped into string length text"),
])
def test_php_operators_the_tokeniser_does_not_know_yet(line, spoken):
    assert spoken_line(line, "php") == spoken
