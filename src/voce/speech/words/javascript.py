"""JavaScript's own words, by MDN's names: ``===`` is "strict equality" (said "is strictly equal to" in a line),
``??`` is "nullish coalescing".

TypeScript takes these words and operators and adds its own, so what is here should be true of plain JavaScript.
"""

from __future__ import annotations

from voce.speech.words.common import Language

# MDN's operator names: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators
# Each has its own page there, such as .../Operators/Strict_equality and .../Operators/Unsigned_right_shift.
JAVASCRIPT = Language("javascript", comments=("//", "/*"), words={
    "el": "element", "elem": "element", "elm": "element", "evt": "event", "btn": "button", "arr": "array",
    "fn": "function", "init": "init", "DOM": "DOM", "params": "params", "args": "args", "props": "props",
    "ref": "ref", "ctx": "context", "opts": "options", "attr": "attribute", "attrs": "attributes",
    "acc": "accumulator", "cur": "current", "curr": "current", "ctor": "constructor", "Ctor": "constructor",
    # keywords and globals that read badly run together
    "typeof": "type of", "instanceof": "instance of", "NaN": "NaN", "isNaN": "is NaN", "jQuery": "J query",
    "uri": "U R I", "http": "H T T P", "https": "H T T P S", "xml": "X M L", "href": "H ref",
    "btoa": "B to A", "atob": "A to B", "Uint8Array": "U int 8 Array", "textarea": "text area", "iframe": "I frame",
    "dataset": "data set", "onclick": "on click", "onchange": "on change", "onload": "on load",
    "onerror": "on error", "onsubmit": "on submit", "onmessage": "on message", "keydown": "key down",
    "keyup": "key up", "keypress": "key press", "mousedown": "mouse down", "mouseup": "mouse up",
    "mousemove": "mouse move", "mouseover": "mouse over", "mouseout": "mouse out", "dblclick": "double click",
    "contextmenu": "context menu",
    # Node: process, fs and path
    "fs": "F S", "npm": "N P M", "argv": "arg V", "cwd": "C W D", "pid": "P I D", "stdin": "standard in",
    "stdout": "standard out", "stderr": "standard error", "dirname": "dir name", "filename": "file name",
    "basename": "base name", "extname": "extension name", "mkdir": "make dir", "rmdir": "remove dir",
    "readdir": "read dir", "lstat": "L stat", "etag": "E tag", "vnode": "V node", "xhr": "X H R",
}, operators={
    "===": "is strictly equal to", "!==": "is not strictly equal to",
    "=>": "arrow",  # Arrow function expressions: .../Reference/Functions/Arrow_functions
    "?.": "optional chaining", "??": "nullish coalescing", "??=": "nullish coalescing assignment",
    "...": "spread",  # Spread syntax; MDN calls ...args in a function's parameters "rest parameters"
    "**": "to the power of", "%": "remainder",
    "&": "bitwise and", "|": "bitwise or", "^": "bitwise X O R", "~": "bitwise not",
    "<<": "left shift", ">>": "right shift", ">>>": "unsigned right shift",
    "<<=": "left shift equals", ">>=": "right shift equals", ">>>=": "unsigned right shift equals",
    "&=": "bitwise and equals", "|=": "bitwise or equals", "^=": "bitwise X O R equals", "%=": "remainder equals",
    "&&=": "and equals", "||=": "or equals",
}, aliases=("javascript", "js", "jsx", "mjs", "cjs", "vue", "svelte"),
    manual="https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators")
