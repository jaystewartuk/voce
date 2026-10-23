from __future__ import annotations

import pytest

from voce.speech import spoken_line
from voce.speech.words import RUST, language


def test_rust_is_found_by_its_fence_names():
    assert language("rust") is RUST
    assert language("rs") is RUST


@pytest.mark.parametrize("line, spoken", [
    ("pub fn new(path: &Path) -> Self {", "public function new path colon borrow Path returns Self"),
    ("let mut buf = Vec::with_capacity(8);", "let mutable buffer equals vector double colon with capacity 8"),
    ("match value { Some(x) => x, None => 0 }", "match value Some x match arm x, None match arm 0"),
    ("let arc = Arc::clone(&shared);", "let arc equals Arc double colon clone borrow shared"),
    ("let file = File::open(path)?;", "let file equals File double colon open path try"),
    ("let rest = total % 7;", "let rest equals total remainder 7"),
    ("let h = a ^ b;", "let h equals a bitwise X O R b"),
    ("fn len(&self) -> usize {", "function length borrow self returns U size"),
    ("let x: i32 = -5;", "let x colon I 32 equals minus 5"),
    ("pub mod tests;", "public module tests"),
    ("let rc = Rc::new(RefCell::new(0));", "let R C equals R C double colon new Ref Cell double colon new 0"),
    ("let e: &dyn Error = &err;", "let e colon borrow dynamic Error equals borrow error"),
    ("let n: u64 = x as u64 + 1;", "let n colon U 64 equals x as U 64 plus 1"),
    ("let s = std::str::from_utf8(bytes)?;",
     "let s equals standard double colon string double colon from U T F 8 bytes try"),
    ("let rdr = BufReader::new(file);", "let reader equals buffer Reader double colon new file"),
    ("pub(crate) fn ty(&self) -> f64 {", "public crate function type borrow self returns F 64"),
    ("let lock = RwLock::new(0);", "let lock equals R W Lock double colon new 0"),
    ("let wtr = io::stdout();", "let writer equals I O double colon standard out"),
    ("use std::ffi::OsStr;", "use standard double colon F F I double colon O S string"),
    ("if a.ne(&b) {", "if a dot not equal borrow b"),
    ("hash ^= byte;", "hash bitwise X O R equals byte"),
    ("n %= 10;", "n remainder equals 10"),
])
def test_rust_lines_read_as_a_person_says_them(line, spoken):
    assert spoken_line(line, "rust") == spoken


# Tokens, macros, lifetimes and doc comments that code.py takes whole for Rust, then two rules it still lacks.
@pytest.mark.parametrize("line, spoken", [
    pytest.param("let n = reader.read(&mut buf)?;", "let n equals reader dot read mutable borrow buffer try"),
    pytest.param("for i in 0..len {", "for i in 0 up to length"),
    pytest.param("for i in 0..=n {", "for i in 0 up to and including n"),
    pytest.param("#[derive(Clone, Debug)]", "outer attribute derive Clone, Debug"),
    pytest.param("#![allow(dead_code)]", "inner attribute allow dead code"),
    pytest.param("let v = s.parse::<i32>();", "let v equals s dot parse turbofish I 32"),
    pytest.param("mask |= 1 << bit;", "mask or equals 1 left shift bit"),
    pytest.param("flags &= !mask;", "flags and equals not mask"),
    pytest.param("x <<= 2;", "x left shift equals 2"),
    pytest.param("h >>= 4;", "h right shift equals 4"),
    pytest.param('println!("hello {}", name);', "print line hello, name"),
    pytest.param("assert_eq!(a, b);", "assert equal a, b"),
    pytest.param("let s: &'static str = name;", "let s colon borrow lifetime static string equals name"),
    pytest.param("let x = *ptr;", "let x equals dereference pointer",
                 marks=pytest.mark.xfail(reason="needs code.py: a * before a value is a dereference", strict=True)),
    pytest.param("let m = a & b;", "let m equals a bitwise and b"),
    pytest.param("/// Returns the path.", "Returns the path"),
])
def test_rust_tokens_macros_and_lifetimes(line, spoken):
    assert spoken_line(line, "rust") == spoken
