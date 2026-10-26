from __future__ import annotations

import pytest

from voce.speech import spoken_line
from voce.speech.words import JAVASCRIPT, language

# A line of JavaScript and exactly how it should sound, with operators by MDN's names.
SAID = [
    ("if (typeof value === 'function') return value;",
     "if type of value is strictly equal to function return value"),
    ("if (err instanceof TypeError) throw err;", "if error instance of Type Error throw error"),
    ("if (a !== b && a == c || a != d) return;",
     "if A is not strictly equal to b and A is equal to c or A is not equal to d return"),
    ("const total = items?.length ?? 0;",
     "const total equals items optional chaining length nullish coalescing 0"),
    ("options ??= {};", "options nullish coalescing assignment"),
    ("user.name ||= 'Anonymous';", "user dot name or equals Anonymous"),
    ("user.ready &&= check(user);", "user dot ready and equals check user"),
    ("const merged = { ...defaults, ...options };", "const merged equals spread defaults, spread options"),
    ("const area = r ** 2 * Math.PI;", "const area equals r to the power of 2 times Math dot PI"),
    ("const isEven = n % 2 === 0;", "const is Even equals n remainder 2 is strictly equal to 0"),
    ("i %= size;", "i remainder equals size"),
    ("const low = bits & mask;", "const low equals bits bitwise and mask"),
    ("bitmask |= WRAP_CURRY_FLAG;", "bitmask bitwise or equals WRAP CURRY FLAG"),
    ("flags ^= MASK;", "flags bitwise X O R equals MASK"),
    ("this._flags &= ~COMPONENT_DIRTY;", "this dot flags bitwise and equals bitwise not COMPONENT DIRTY"),
    ("const parity = a ^ b | c;", "const parity equals A bitwise X O R b bitwise or c"),
    ("const mid = (skew + hi) >> 1;", "const mid equals skew plus hi right shift 1"),
    ("n >>= 1;", "n right shift equals 1"),
    ("const double = (x) => x * 2;", "const double equals x arrow x times 2"),
    ("const reduce = (acc, cur) => acc + cur;",
     "const reduce equals accumulator, current arrow accumulator plus current"),
    ("if (Number.isNaN(x)) return NaN;", "if Number dot is NaN x return NaN"),
    ("link.href = encodeURIComponent(path);", "link dot H ref equals encode U R I Component path"),
    ("el.addEventListener('keydown', onKeyDown);", "element dot add Event Listener key down, on Key Down"),
    ("const xhr = new XMLHttpRequest();", "const X H R equals new X M L H T T P Request"),
    ("const data = JSON.parse(atob(token));", "const data equals JSON dot parse A to B token"),
    ("fs.mkdirSync(dir, { recursive: true });", "F S dot make dir Sync dir, recursive colon true"),
    ("const root = path.join(__dirname, 'views');", "const root equals path dot join dir name, views"),
    ("const attrs = Object.keys(opts);", "const attributes equals Object dot keys options"),
]


@pytest.mark.parametrize("line, spoken", SAID)
def test_a_line_of_javascript_is_said_with_mdn_names(line, spoken):
    assert spoken_line(line, "javascript") == spoken


# These need the tokeniser to know <<, <<=, >>> and >>>= as one operator each.
NEEDS_TOKENISER = [
    ("const mask = 1 << bit;", "const mask equals 1 left shift bit"),
    ("mask <<= 2;", "mask left shift equals 2"),
    ("const mid = (low + high) >>> 1;", "const mid equals low plus high unsigned right shift 1"),
    ("start >>>= 0;", "start unsigned right shift equals 0"),
]


@pytest.mark.parametrize("line, spoken", NEEDS_TOKENISER)
def test_shifts_the_tokeniser_does_not_know_yet(line, spoken):
    assert spoken_line(line, "javascript") == spoken


def test_javascript_fences_and_extensions_are_javascript_but_typescript_is_not():
    for alias in ("javascript", "js", "jsx", "mjs", "cjs", "vue", "svelte"):
        assert language(alias) is JAVASCRIPT
    assert JAVASCRIPT.aliases == ("javascript", "js", "jsx", "mjs", "cjs", "vue", "svelte")
    assert JAVASCRIPT.manual.startswith("https://developer.mozilla.org/")
