"""Rust's own words, named as The Rust Reference names them: ``&`` is "borrow", ``?`` is "try", ``fn`` is
"function"."""

from __future__ import annotations

from voce.speech.words.common import Language

RUST = Language("rust", comments=("//", "/*"), words={
    # keywords that read badly as written: https://doc.rust-lang.org/reference/keywords.html
    "fn": "function", "mut": "mutable", "pub": "public", "dyn": "dynamic", "mod": "module",
    # the primitive types, by letter: https://doc.rust-lang.org/reference/types/numeric.html
    "u8": "U 8", "u16": "U 16", "u32": "U 32", "u64": "U 64", "u128": "U 128", "usize": "U size",
    "i8": "I 8", "i16": "I 16", "i32": "I 32", "i64": "I 64", "i128": "I 128", "isize": "I size",
    "f32": "F 32", "f64": "F 64",
    # the standard library's names: https://doc.rust-lang.org/std/ (vec covers Vec, rc covers Rc and RwLock's rw)
    "std": "standard", "vec": "vector", "rc": "R C", "rw": "R W", "ffi": "F F I", "utf8": "U T F 8",
    "println": "print line", "eprintln": "E print line", "eprint": "E print", "writeln": "write line",
    "dbg": "debug", "eq": "equal", "ne": "not equal", "stdin": "standard in", "stdout": "standard out",
    "stderr": "standard error",
    # names Rust code uses everywhere, short for a word
    "buf": "buffer", "ptr": "pointer", "rdr": "reader", "wtr": "writer", "ty": "type", "attr": "attribute",
    "attrs": "attributes",
}, operators={
    # https://doc.rust-lang.org/reference/expressions/operator-expr.html: borrow, the try propagation expression
    # ("sometimes called the question mark operator ... or the try operator"), remainder, XOR, compound assignment
    "&": "borrow", "&mut": "mutable borrow", "?": "try", "%": "remainder", "^": "bitwise X O R",
    "%=": "remainder equals",
    "^=": "bitwise X O R equals", "&=": "and equals", "|=": "or equals", "<<": "left shift", "<<=": "left shift equals",
    ">>=": "right shift equals",
    # https://doc.rust-lang.org/book/appendix-02-operators.html: "Function and closure return type",
    # "Part of match arm syntax", "Right-exclusive range literal", "Right-inclusive range literal"
    "->": "returns", "=>": "match arm", "..": "up to", "..=": "up to and including",
    # the same page, Table B-6, "Outer attribute" and "Inner attribute"; Table B-4 (the Book, not the Reference) says
    # ::<> is "often referred to as turbofish"
    "#[": "outer attribute", "#![": "inner attribute", "::<": "turbofish",
},
    # the Book, Table B-1: expr & expr is "Bitwise AND", where &expr is a borrow
    after_value={"&": "bitwise and"},
    aliases=("rust", "rs"),
    manual="https://doc.rust-lang.org/reference/expressions/operator-expr.html")
