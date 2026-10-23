from __future__ import annotations

import pytest

from voce.speech import spoken_line
from voce.speech.words import GO, language


@pytest.mark.parametrize("line, spoken", [
    # := is the spec's short variable declaration, & the address operation
    ("if err := json.Unmarshal(data, &v); err != nil {",
     "if error short variable declaration JSON dot Unmarshal data, address of v, error is not equal to nil"),
    ("srv := &http.Server{Addr: addr}",
     "server short variable declaration address of HTTP dot Server address colon address"),
    # fmt's printing verbs, said as words
    ('return fmt.Errorf("open %s: %w", path, err)', "return format dot error F open percent s: percent w, path, error"),
    ('fmt.Println("hello, world")', "format dot print line hello, world"),
    ('t.Errorf("got %v, want %v", got, want)', "t dot error F got percent v, want percent v, got, want"),
    ("n, err := strconv.Atoi(s)", "n, error short variable declaration string convert dot A to I s"),
    ("key := strconv.Itoa(i)", "key short variable declaration string convert dot I to A i"),
    # keywords, built-ins and the names Go code uses everywhere
    ("ch := make(chan int, 10)", "ch short variable declaration make channel int, 10"),
    ("mu.Lock()", "mutex dot Lock"),
    ("defer wg.Done()", "defer wait group dot Done"),
    ("go func() {", "go function"),
    ("c := cap(buf)", "c short variable declaration capacity buffer"),
    ("var goroutines int", "var go routines int"),
    ("r := bufio.NewReader(os.Stdin)", "r short variable declaration buf I O dot New Reader O S dot standard in"),
    ("body, err := ioutil.ReadAll(resp.Body)",
     "body, error short variable declaration I O util dot Read All response dot Body"),
    ('conn, err := net.Dial("tcp", addr)', "connection, error short variable declaration net dot Dial T C P, address"),
    # []T is a slice type
    ('names := []string{"a", "b"}', "names short variable declaration slice of string a, b"),
    # the arithmetic operators, by the spec's names
    ("y := x ^ mask", "y short variable declaration x bitwise X OR mask"),
    ("flags := os.O_CREATE | os.O_WRONLY",
     "flags short variable declaration O S dot O CREATE bitwise or O S dot O WRONLY"),
    ("n := size >> 10", "n short variable declaration size right shift 10"),
    ("if i%2 == 0 {", "if i remainder 2 is equal to 0"),
    ("d := 5 * time.Second", "d short variable declaration 5 times time dot Second"),
    ("for i := 0; i < len(xs); i++ {", "for i short variable declaration 0, i less than length xs, i increment"),
    # assignment operations
    ("x |= flag", "x bitwise or equals flag"),
    ("x ^= flag", "x bitwise X OR equals flag"),
    ("x >>= 1", "x right shift equals 1"),
    ("mask %= 8", "mask remainder equals 8"),
    # ~T in a constraint is the underlying type T
    ("type Number interface { ~int | ~float64 }",
     "type Number interface underlying type int bitwise or underlying type float64"),
])
def test_go_lines(line, spoken):
    assert spoken_line(line, "go") == spoken


# These need the tokeniser to learn Go's operators, or code.py to tell their uses apart. They pass once it does.
@pytest.mark.parametrize("line, spoken", [
    pytest.param("x := <-ch", "x short variable declaration receive from ch"),
    pytest.param("ch <- v", "ch send v"),
    pytest.param("y := x &^ mask", "y short variable declaration x bit clear mask"),
    pytest.param("x &^= mask", "x bit clear equals mask"),
    pytest.param("x &= mask", "x bitwise and equals mask"),
    pytest.param("y := 1 << n", "y short variable declaration 1 left shift n"),
    pytest.param("x <<= 2", "x left shift equals 2"),
    pytest.param("if d&mask != 0 {", "if d bitwise and mask is not equal to 0"),
    pytest.param("func (s *Server) Close() error {", "function s pointer to Server Close error",
                 marks=pytest.mark.xfail(reason="needs code.py: * before a type is a pointer type", strict=True)),
    pytest.param("func f(xs ...string) {", "function f xs variadic string",
                 marks=pytest.mark.xfail(reason="needs code.py: a func signature is variadic", strict=True)),
    pytest.param('Name string `json:"name,omitempty"`', "Name string, JSON name, omit empty",
                 marks=pytest.mark.xfail(reason="needs code.py: a struct tag read as its keys", strict=True)),
])
def test_go_lines_that_need_the_tokeniser(line, spoken):
    assert spoken_line(line, "go") == spoken


def test_go_is_found_by_its_fence_names():
    assert language("go") is GO
    assert language("golang") is GO
