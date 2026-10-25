"""TypeScript's own words, by the handbook's names: ``Promise<User>`` is "Promise of User", ``A | B`` is "A or B"
(a union), ``user!`` is "user non-null" (the non-null assertion), and ``name?: string`` is "name optional string".

On top of JavaScript's, which are MDN's names.
"""

from __future__ import annotations

from voce.speech.words.common import Language
from voce.speech.words.javascript import JAVASCRIPT

TYPESCRIPT = Language("typescript", comments=JAVASCRIPT.comments, words={
    **JAVASCRIPT.words, "keyof": "key of", "typeof": "type of", "readonly": "read only", "infer": "infer",
    "tsx": "T S X", "ts": "T S", "dto": "D T O",
}, operators={
    **JAVASCRIPT.operators, "?:": "optional",
}, aliases=("typescript", "ts", "tsx", "mts", "cts"),
    manual="https://www.typescriptlang.org/docs/handbook/2/everyday-types.html")
