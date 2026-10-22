"""TypeScript's own words, on top of JavaScript's, by the Handbook's names: ``keyof`` is "key of", ``A | B``
is a union type (said "A or B"), ``name?: string`` is an optional property (said "name optional string")."""

from __future__ import annotations

from voce.speech.words.common import Language
from voce.speech.words.javascript import JAVASCRIPT

TYPESCRIPT = Language("typescript", comments=("//", "/*"), words={**JAVASCRIPT.words,
    "keyof": "key of", "typeof": "type of", "instanceof": "instance of", "readonly": "read only", "bigint": "big int",
    "ts": "T S", "tsx": "T S X", "tsc": "T S C", "tsconfig": "T S config",
}, operators={**JAVASCRIPT.operators,
    # Union and intersection types. In TypeScript they far outnumber the bitwise operators (about 20 to 1 in
    # VS Code's base and type-fest), so | and & are read as the types read: string | null is "string or null".
    # https://www.typescriptlang.org/docs/handbook/2/everyday-types.html#union-types
    # https://www.typescriptlang.org/docs/handbook/2/objects.html#intersection-types
    "|": "or", "&": "and",
    # An optional property or parameter, name?: string. JavaScript has no ?: operator, so the token means only this.
    # https://www.typescriptlang.org/docs/handbook/2/objects.html#optional-properties
    "?:": "optional",
    # A decorator, @Component(...). https://www.typescriptlang.org/docs/handbook/decorators.html
    "@": "decorator",
}, aliases=("typescript", "ts", "tsx", "mts", "cts"), manual="https://www.typescriptlang.org/docs/handbook/")
