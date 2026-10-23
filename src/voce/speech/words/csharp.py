"""C#'s own words, named as Microsoft Learn's C# reference names them: ``??`` is "null coalescing", ``?.`` is
"null conditional", ``=>`` is the "lambda" operator and ``::`` the "namespace alias qualifier"."""

from __future__ import annotations

from voce.speech.words.common import Language

_OPERATORS = "https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/operators/"

# A preprocessor directive, #region or #if DEBUG, is read as a comment is: C# has no other use for #.
CSHARP = Language("csharp", comments=("//", "/*", "#"), words={
    # keywords that run two words together
    "nameof": "name of", "typeof": "type of", "sizeof": "size of", "stackalloc": "stack alloc",
    "readonly": "read only", "foreach": "for each", "uint": "U int", "ulong": "U long", "ushort": "U short",
    "sbyte": "S byte", "nint": "N int", "nuint": "N U int", "ctor": "constructor",
    # names said by letter or in full
    "dto": "D T O", "ct": "C T", "guid": "G U I D", "uri": "U R I", "utc": "U T C", "xml": "X M L",
    "http": "H T T P", "linq": "link", "dict": "dictionary", "ptr": "pointer", "expr": "expression",
    "attr": "attribute", "prop": "property", "gc": "G C", "ef": "E F", "asp": "A S P", "xunit": "X unit",
    "md5": "M D 5", "sha1": "S H A 1", "sha256": "S H A 256",
    "Func": "Func",  # the delegate type Func<T, TResult>, not "function"
}, operators={
    "?.": "null conditional",                     # member-access-operators: the null-conditional operators
    "?[": "null conditional",                     # the same page, ?[] (needs the tokeniser to know ?[)
    "??": "null coalescing",                      # null-coalescing-operator
    "??=": "null coalescing assignment",          # the same page
    "=>": "lambda",                               # lambda-operator: the lambda operator
    "::": "namespace alias qualifier",            # namespace-alias-qualifier
    "^": "index from end",                        # member-access-operators: index from end (prefix ^1)
    "..": "range",                                # member-access-operators: the range operator
    "->": "pointer member access",                # pointer-related-operators
    "%": "remainder",                             # arithmetic-operators: the remainder operator
    "%=": "remainder equals",
    "<<": "left shift", ">>": "right shift", ">>>": "unsigned right shift",  # bitwise-and-shift-operators
    "<<=": "left shift equals", ">>=": "right shift equals", ">>>=": "unsigned right shift equals",
    "&": "logical and", "|": "logical or", "~": "bitwise complement",       # boolean-logical, bitwise
    "&=": "logical and equals", "|=": "logical or equals", "^=": "logical exclusive or equals",
    "$": "interpolated string",                   # tokens/interpolated: $"..." is an interpolated string
    "@": "verbatim",                              # tokens/verbatim: @"..." and @class
},
    # bitwise-and-shift-operators: a ^ b is "logical exclusive OR"; before a value, ^1 is index from end
    after_value={"^": "logical exclusive or"},
    aliases=("csharp", "cs", "c#"),
    manual=_OPERATORS)
