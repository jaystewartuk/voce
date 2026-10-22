"""JavaScript's own words, by MDN's names: ``===`` is "strictly equal", ``??`` is "nullish coalescing"."""

from __future__ import annotations

from voce.speech.words.common import Language

JAVASCRIPT = Language("javascript", comments=("//", "/*"), words={
    "el": "element", "evt": "event", "btn": "button", "arr": "array", "fn": "function", "init": "init",
    "DOM": "DOM", "params": "params", "args": "args", "props": "props", "ref": "ref", "ctx": "context",
}, operators={
    "===": "is strictly equal to", "!==": "is not strictly equal to", "=>": "arrow", "?.": "optional chaining",
    "??": "nullish coalescing", "??=": "nullish assignment", "...": "spread", "**": "to the power of",
}, aliases=("javascript", "js", "typescript", "ts", "jsx", "tsx", "mjs", "cjs", "vue", "svelte"),
    manual="https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators")
