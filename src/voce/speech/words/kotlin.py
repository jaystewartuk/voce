"""Kotlin's own words, by the Kotlin docs' names: ``?.`` is "safe call", ``?:`` is "elvis", ``===`` is "is
referentially equal to"."""

from __future__ import annotations

from voce.speech.words.common import Language

# Operator names are from https://kotlinlang.org/docs/keyword-reference.html#operators-and-special-symbols
# unless a line says otherwise.
KOTLIN = Language("kotlin", comments=("//", "/*"), words={
    "val": "val",  # a keyword, said as written, not "value"
    "lateinit": "late init", "vararg": "var arg", "tailrec": "tail rec", "noinline": "no inline",
    "crossinline": "cross inline", "typealias": "type alias", "println": "print line", "readln": "read line",
    "jvm": "J V M", "kotlinx": "kotlin X",
    # Said by letter in network code, which is much of what Kotlin is written for (OkHttp, Ktor).
    "http": "H T T P", "https": "H T T P S", "dns": "D N S", "tls": "T L S", "ssl": "S S L", "utf8": "U T F 8",
    # https://kotlinlang.org/docs/numbers.html#bitwise-operations
    "shl": "shift left", "shr": "shift right", "ushr": "unsigned shift right", "xor": "X or",
}, operators={
    # https://kotlinlang.org/docs/null-safety.html: the safe call operator, the Elvis operator, the not-null
    # assertion operator, nullable types and the safe cast operator as?.
    "?.": "safe call", "?:": "elvis", "!!": "not null assertion", "?": "nullable", "as?": "safe cast to",
    # https://kotlinlang.org/docs/equality.html: structural equality is == and referential equality is ===.
    "===": "is referentially equal to", "!==": "is not referentially equal to",
    # https://kotlinlang.org/docs/ranges.html: the .. operator calls rangeTo() and ..< calls rangeUntil().
    "..": "range to", "..<": "range until",
    # https://kotlinlang.org/docs/operator-overloading.html#arithmetic-operators: a % b is a.rem(b), the
    # remainder, which differs from mod() for negative numbers.
    "%": "remainder",
    # https://kotlinlang.org/docs/operator-overloading.html#in-operator and typecasts: !in and !is.
    "!in": "not in", "!is": "is not",
}, aliases=("kotlin", "kt", "kts"),
    manual="https://kotlinlang.org/docs/keyword-reference.html")
