from __future__ import annotations

import pytest

from voce.speech import spoken_line
from voce.speech.words import LANGUAGES, TYPESCRIPT


@pytest.mark.parametrize("line, spoken", [
    # Union and intersection types, by the Handbook's names: | is "or", & is "and".
    ("let value: string | number;", "let value colon string or number"),
    ("let id: string | null | undefined;", "let I D colon string or null or undefined"),
    ("type Pet = Fish & Bird;", "type Pet equals Fish and Bird"),
    ("  | 'darwin'", "or darwin"),
    # An optional property or parameter: ?: is "optional".
    ("interface User { name?: string; readonly id: number }",
     "interface User name optional string, read only I D colon number"),
    ("const f = (a: number, b?: number): void => {};",
     "const f equals a colon number, b optional number colon void arrow"),
    # A decorator.
    ("@Component({ selector: 'app' })", "decorator Component selector colon app"),
    ("@memoize", "decorator memoize"),
    # The type operators, said as words.
    ("type Keys = keyof typeof obj;", "type Keys equals key of type of object"),
    ("if (x instanceof Date) {}", "if x instance of Date"),
    ("readonly items: ReadonlyArray<Item>;", "read only items colon read only Array of Item"),
    ("const big: bigint = 10;", "const big colon big int equals 10"),
    ("const x = y as unknown as Foo;", "const x equals y as unknown as Foo"),
    ("const config = { a: 1 } satisfies Config;", "const config equals a colon 1 satisfies Config"),
    ("type T = U extends string ? 'yes' : never;", "type T equals U extends string then yes else never"),
    ("function isString(x: unknown): x is string {", "function is String x colon unknown colon x is string"),
    # The tools, by letter.
    ("const options = ts.readConfigFile(tsconfig);", "const options equals T S dot read Config File T S config"),
    # What TypeScript shares with JavaScript, by MDN's names.
    ("if (a === b && c !== d) {}", "if a is strictly equal to b and c is not strictly equal to d"),
    ("const v = obj?.a ?? fallback;", "const v equals object optional chaining a nullish coalescing fallback"),
])
def test_typescript_reads_by_the_handbook(line, spoken):
    assert spoken_line(line, "typescript") == spoken


@pytest.mark.parametrize("alias", ["typescript", "ts", "tsx", "mts", "cts"])
def test_typescript_fences(alias):
    assert LANGUAGES[alias] is TYPESCRIPT


@pytest.mark.parametrize("line, spoken", [
    pytest.param("const names: Array<string> = [];", "const names colon Array of string equals empty array"),
    pytest.param("let map: Map<string, Array<number>>;", "let map colon Map of string, Array of number"),
    pytest.param("const list: number[] = [];", "const list colon number array equals empty array",
                 marks=pytest.mark.xfail(reason="needs tokeniser: [] after a name is an array type", strict=True)),
    pytest.param("const el = document.getElementById('x')!;",
                 "const element equals document dot get Element By I D x, non-null assertion",
                 marks=pytest.mark.xfail(reason="needs tokeniser: a postfix ! is a non-null assertion", strict=True)),
    pytest.param("function greet(name: string): string {", "function greet name colon string returns string",
                 marks=pytest.mark.xfail(reason="needs tokeniser: ): is a return type annotation", strict=True)),
    pytest.param("private name!: string;", "private name definitely string",
                 marks=pytest.mark.xfail(reason="needs tokeniser: !: is a definite assignment assertion", strict=True)),
    pytest.param("type Getters = { [K in keyof T]: () => T[K] };",
                 "type Getters equals for each K in key of T colon arrow T K",
                 marks=pytest.mark.xfail(reason="needs tokeniser: [K in ...] is a mapped type", strict=True)),
])
def test_typescript_needs_the_tokeniser(line, spoken):
    assert spoken_line(line, "typescript") == spoken
