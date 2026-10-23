"""Swift's own words, by The Swift Programming Language's names: ``??`` is "nil coalescing", ``===`` is
"is identical to", ``->`` is "returns"."""

from __future__ import annotations

from voce.speech.words.common import Language

# Operator names are from the book: Basic Operators, Advanced Operators, Expressions, Type Casting.
# https://docs.swift.org/swift-book/documentation/the-swift-programming-language/basicoperators
SWIFT = Language("swift", comments=("//", "/*"), words={
    "deinit": "de init", "fileprivate": "file private", "inout": "in out", "typealias": "type alias",
    "associatedtype": "associated type", "precedencegroup": "precedence group", "NS": "N S", "CG": "C G",
    "objc": "obj C", "lhs": "L H S", "rhs": "R H S", "XCT": "X C T", "http": "HTTP", "iOS": "I O S",
    "tvOS": "T V O S", "iPadOS": "I Pad O S", "HTTPURLResponse": "HTTP URL Response",
    "rethrows": "re throws", "nonmutating": "non mutating", "nonisolated": "non isolated",
    "inlinable": "inline able", "autoclosure": "auto closure", "preconcurrency": "pre concurrency",
}, operators={
    # the book calls -> "the return arrow" (Closures, Error Handling); said in a line as Python's is
    "->": "return arrow", "??": "nil coalescing", "%": "remainder",  # Swift's % is a remainder, not a modulo
    # the closed range and half-open range operators, said as the standard library names their one-sided forms:
    # PartialRangeThrough (...5) and PartialRangeUpTo (..<5), and as stride(from:through:by:) says it
    "...": "closed range", "..<": "half open range",
    # a postfix ? is an optional type, try? or as?, far more often than the ternary conditional operator
    "?": "optional",
    "\\": "key path", "#": "number sign",  # a key-path expression; #if, #selector, #available (Lexical Structure)
    # https://docs.swift.org/swift-book/documentation/the-swift-programming-language/advancedoperators
    "&+": "overflow addition", "&-": "overflow subtraction", "&*": "overflow multiplication",
    "<<": "bitwise left shift",
    ">>": "bitwise right shift", "~": "bitwise not", "^": "bitwise X O R", "|": "bitwise or",
}, aliases=("swift",),
    manual="https://docs.swift.org/swift-book/documentation/the-swift-programming-language/basicoperators")
