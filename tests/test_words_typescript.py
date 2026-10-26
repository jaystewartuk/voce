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
    pytest.param("const list: number[] = [];", "const list colon number array equals empty array"),
    pytest.param("const el = document.getElementById('x')!;",
                 "const element equals document dot get Element By I D x, non-null assertion"),
    pytest.param("function greet(name: string): string {", "function greet name colon string returns string"),
    pytest.param("private name!: string;", "private name definitely string"),
    pytest.param("type Getters = { [K in keyof T]: () => T[K] };",
                 "type Getters equals for each K in key of T colon arrow T K"),
])
def test_typescript_needs_the_tokeniser(line, spoken):
    assert spoken_line(line, "typescript") == spoken


@pytest.mark.parametrize("line, spoken", [
    # A type's arguments and parameters, also when they run over several lines.
    ("function first<T>(items: readonly T[]): T | undefined {",
     "function first of T items colon read only T array returns T or undefined"),
    ("const pick = <T>(xs: T[]) => xs[0];", "const pick equals generic T xs colon T array arrow xs 0"),
    ("const app = new Hono<{", "const app equals new Hono of"),
    ("}>()", ""),
    ("if (a < b && c > d) return;", "if a less than b and c greater than d return"),
    # JSX: an element by its name.
    ("return <div>{id}</div>", "return div I D end div"),
    ("<Suspense fallback={<p>Loading...</p>}>", "Suspense fallback equals p Loading and so on end p"),
    ("<>{a}</>", "fragment a end fragment"),
    ('<h1 class="title">Hello!</h1>', "h1 class equals title Hello end h1"),
    ("  />", ""),
    ("const [first, ...rest] = xs;", "const first, spread rest equals xs"),
    ("type Opt<T> = { [P in keyof T]?: T[P] };", "type Opt of T equals for each P in key of T optional T P"),
    ("const xs = [a, b];", "const xs equals array of a, b"),
    # A regular expression by the words in it.
    ("expect(type).toMatch(/^text\\/plain/i)", "expect type dot to Match regular expression text plain"),
    ("const half = total / 2 / count;", "const half equals total divided by 2 divided by count"),
    # An example in a doc comment is code; a doc comment's sentence is not.
    (" * const app = new Hono()", "const app equals new Hono"),
    (" * Returns the user (or null).", "Returns the user (or null)"),
])
def test_typescript_and_jsx_as_hono_is_written(line, spoken):
    assert spoken_line(line, "tsx") == spoken


def test_jsx_in_javascript():
    assert spoken_line("render(<App />, root)", "jsx") == "render App, root"
