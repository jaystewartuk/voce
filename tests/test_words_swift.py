from __future__ import annotations

import pytest

from voce.speech import spoken_line

# A line of Swift and exactly how it should sound. Operator names are The Swift Programming Language's own.
SAID = [
    ("func greet(person: String) -> String {", "function greet person colon String return arrow String"),
    ('let name = user?.name ?? "Anonymous"', "let name equals user optional chaining name nil coalescing Anonymous"),
    ("for index in 1...5 {", "for index in 1 closed range 5"),
    ("let head = items[...4]", "let head equals items closed range 4"),
    ("if a === b { return }", "if A is identical to b return"),
    ("if a !== b {", "if A is not identical to b"),
    ("let view = UIViewController()", "let view equals U I View Controller"),
    ("let width: CGFloat = 10", "let width colon C G Float equals 10"),
    ("class Model: NSObject {", "class Model colon N S Object"),
    ("fileprivate var count = 0", "file private var count equals 0"),
    ("deinit {", "de init"),
    ("func swap(_ a: inout Int, _ b: inout Int) {",
     "function swap underscore A colon in out Int, underscore b colon in out Int"),
    ("let value = try? decoder.decode(User.self, from: data)",
     "let value equals try optional decoder dot decode User dot self, from colon data"),
    ("if let cell = view as? UITableViewCell {", "if let cell equals view as optional U I Table View Cell"),
    ("func f(a: Int?, b: Int) {", "function f A colon Int optional, b colon Int"),
    ("let names = people.map(\\.name)", "let names equals people dot map key path dot name"),
    ("let n = count % 2", "let n equals count remainder 2"),
    ("let mask = ~bits | flags ^ other", "let mask equals bitwise not bits bitwise or flags bitwise X O R other"),
    ("let high = value >> 8", "let high equals value bitwise right shift 8"),
    ('request.httpMethod = "POST"', "request dot HTTP Method equals POST"),
    ("guard let response = response as? HTTPURLResponse else { return }",
     "guard let response equals response as optional HTTP URL Response else return"),
    ("XCTAssertEqual(a, b)", "X C T Assert Equal A, b"),
    ("@inlinable public func f() rethrows -> Int", "at inline able public function f re throws return arrow Int"),
    ("case iOS, tvOS", "case I O S, T V O S"),
]


@pytest.mark.parametrize("line, spoken", SAID)
def test_swift_reads_as_a_person_says_it(line, spoken):
    assert spoken_line(line, "swift") == spoken


# Operators and a doc comment that code.py now takes whole.
SWIFT_OPERATORS = [
    ("for i in 0..<count {", "for i in 0 half open range count"),
    ("let range = ..<5", "let range equals half open range 5"),
    ("let total = a &+ b &- c &* d",
     "let total equals A overflow addition b overflow subtraction c overflow multiplication d"),
    ("let shifted = x << 2", "let shifted equals x bitwise left shift 2"),
    ("/// The base collection.", "The base collection"),
]


@pytest.mark.parametrize("line, spoken", SWIFT_OPERATORS)
def test_swift_operators_and_doc_comments(line, spoken):
    assert spoken_line(line, "swift") == spoken


@pytest.mark.xfail(reason="needs tokeniser: # is not an operator character", strict=True)
def test_swift_hash_available():
    assert spoken_line("if #available(iOS 15, *) {", "swift") == "if hash available I O S 15, star"


# These wait on rules in speech/code.py that only Swift needs.
NEEDS_RULES = [
    ("let y = cond ? 1 : 2", "let y equals cond then 1 else 2"),  # a ternary ? has a space before it
    ("let x = optional!", "let x equals optional force unwrap"),  # a ! straight after a value
    ("func sum(_ numbers: Int...) -> Int {", "function sum underscore numbers colon Int variadic returns Int"),
    ("swap(&a, &b)", "swap in out a, in out b"),  # an & before a variable passes it in-out
]


@pytest.mark.parametrize("line, spoken", NEEDS_RULES)
@pytest.mark.xfail(reason="needs code.py: Swift's postfix ? and !, variadic ... and in-out &", strict=True)
def test_swift_lines_that_need_their_own_rules(line, spoken):
    assert spoken_line(line, "swift") == spoken
