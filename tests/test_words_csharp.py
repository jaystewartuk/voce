from __future__ import annotations

import pytest

from voce.speech import spoken_line
from voce.speech.words import CSHARP, language

# A line of C# and exactly how it should sound, with Microsoft Learn's names for the operators.
READS = [
    ("var result = items.Where(x => x.IsActive).Select(x => x.Name).ToList();",
     "var result equals items dot Where x lambda x dot Is Active dot Select x lambda x dot Name dot To List"),
    ("public int Count => _items.Count;", "public int Count lambda items dot Count"),
    ('var name = person?.Name ?? "unknown";',
     "var name equals person null conditional Name null coalescing unknown"),
    ("_cache ??= new Dictionary<string, int>();",
     "cache null coalescing assignment new Dictionary of string, int"),
    ("var last = values[^1];", "var last equals values index from end 1"),
    ("global::System.Console.WriteLine(nameof(value));",
     "global namespace alias qualifier System dot Console dot Write Line name of value"),
    ("var size = sizeof(int) + typeof(Foo).Name.Length % 4;",
     "var size equals size of int plus type of Foo dot Name dot Length remainder 4"),
    ("Span<byte> buffer = stackalloc byte[256];",
     "Span of byte buffer equals stack alloc byte 256"),
    ("var flags = a & b | c;", "var flags equals a logical and b logical or c"),
    ("flags &= mask; flags |= other;", "flags logical and equals mask, flags logical or equals other"),
    ("mask = ~mask;", "mask equals bitwise complement mask"),
    ("x = y >> 2;", "x equals y right shift 2"),
    ("x >>= 2;", "x right shift equals 2"),
    ("var n = p->Next;", "var n equals p pointer member access Next"),
    ('Console.WriteLine($"Hello {name}");', "Console dot Write Line interpolated string Hello name"),
    ('var path = @"C:\\temp";', "var path equals verbatim C:\\temp"),
    ("var dto = new UserDto { Id = id };", "var D T O equals new User D T O I D equals I D"),
    ("public Task<int> GetCountAsync(CancellationToken ct)",
     "public Task of int Get Count Async Cancellation Token C T"),
    ("foreach (var item in list) total += item;", "for each var item in list total plus equals item"),
    ("Func<int, bool> isEven = n => n % 2 == 0;",
     "Func of int, bool is Even equals n lambda n remainder 2 is equal to 0"),
    ("total %= 7;", "total remainder equals 7"),
    ("ulong big = 0; uint small = 1;", "U long big equals 0, U int small equals 1"),
    ("if (obj is not null && obj is string s) return s;",
     "if object is not null and object is string s return s"),
    ("var reader = stream as StreamReader;", "var reader equals stream as Stream Reader"),
    ("#region Private methods", "region Private methods"),
    ("#if DEBUG", "if DEBUG"),
    ('var tag = "#main";', "var tag equals #main"),
    ("if (c == '#') return;", "if c is equal to a hash return"),
    ("IEnumerable<Guid> ids = GetIds();", "I Enumerable of G U I D ids equals Get Ids"),
]


@pytest.mark.parametrize("line, spoken", READS)
def test_reads_csharp(line, spoken):
    assert spoken_line(line, "csharp") == spoken


@pytest.mark.parametrize("alias", ["csharp", "cs", "c#", "C#"])
def test_fence_labels_and_extension_mean_csharp(alias):
    assert language(alias) is CSHARP


# Shifts, ranges, ?[ and /// were the tokeniser's to learn; they read as the C# manual says now.
TOKENS = [
    ("var slice = values[1..^1];", "var slice equals values 1 range index from end 1"),
    ("var item = list?[0];", "var item equals list null conditional 0"),
    ("x = y << 2;", "x equals y left shift 2"),
    ("count <<= 1;", "count left shift equals 1"),
    ("x = y >>> 2;", "x equals y unsigned right shift 2"),
    ("hash ^= code;", "hash logical exclusive or equals code"),
    ("hash = hash ^ code;", "hash equals hash logical exclusive or code"),
    ("var last = values[^1];", "var last equals values index from end 1"),
    ("List<int> xs = new();", "List of int xs equals new"),
    ("/// Returns the value.", "Returns the value"),
]


@pytest.mark.parametrize(("line", "spoken"), TOKENS)
def test_csharp_operators_and_generics(line, spoken):
    assert spoken_line(line, "csharp") == spoken


# These still need a rule in code.py that only C# wants.
NEEDS_RULES = [
    ("return value!.ToString();", "return value null forgiving dot To String",
     "! after a value is the null-forgiving operator"),
    ("int? count = null;", "nullable int count equals null", "? after a type in a declaration is nullable"),
    ("[HttpGet]", "attribute H T T P Get", "[ starting a line is an attribute in C#"),
]


@pytest.mark.parametrize("line, spoken", [
    pytest.param(line, spoken, marks=pytest.mark.xfail(reason="needs code.py: " + reason, strict=True))
    for line, spoken, reason in NEEDS_RULES])
def test_reads_csharp_once_code_py_learns(line, spoken):
    assert spoken_line(line, "csharp") == spoken
