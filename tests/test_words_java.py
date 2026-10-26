from __future__ import annotations

import pytest

from voce.speech import spoken_code, spoken_line
from voce.speech.words import language

# A line of Java and exactly how it should sound, with the JLS's operator names.
READS = [
    ('System.out.println("Hello, world");', "System dot out dot print line Hello, world"),
    ("StringBuilder sb = new StringBuilder();", "String Builder S B equals new String Builder"),
    ("int n = Integer.parseInt(args[0]);", "int n equals Integer dot parse Int args 0"),
    ("if (obj instanceof String s) {", "if object instance of String s"),
    ("names.forEach(System.out::println);", "names dot for Each System dot out method reference print line"),
    ("list.stream().map(x -> x * 2).collect(Collectors.toList());",
     "list dot stream dot map x arrow x times 2 dot collect Collectors dot to List"),
    ('case MONDAY -> System.out.println("start");', "case MONDAY arrow System dot out dot print line start"),
    ("int r = a % b;", "int r equals A remainder b"),
    ("count %= 10;", "count remainder equals 10"),
    ("int k = y >> 2;", "int k equals y signed right shift 2"),
    ("k >>= 1;", "k signed right shift equals 1"),
    ("int low = hash & 15;", "int low equals hash bitwise and 15"),
    ("int mixed = a ^ b;", "int mixed equals A bitwise exclusive or b"),
    ("int both = a | b;", "int both equals A bitwise inclusive or b"),
    ("flags |= MASK;", "flags bitwise inclusive or equals MASK"),
    ("flags &= ~MASK;", "flags bitwise and equals bitwise complement MASK"),
    ("bits ^= 1;", "bits bitwise exclusive or equals 1"),
    ("void log(String format, Object... params) {", "void log String format, Object variable arity params"),
    ("Map<String, Integer> counts = new HashMap<>();",
     "Map of String, Integer counts equals new Hash Map diamond"),
    ('String s = ok ? "yes" : "no";', "String s equals ok then yes else no"),
    ("boolean ok = a && !b || c;", "boolean ok equals A and not b or c"),
    ("@Override", "at Override"),
    ("private static final long serialVersionUID = 1L;", "private static final long serial Version U I D equals 1 L"),
    ("import javax.annotation.Nullable;", "import java X dot annotation dot Nullable"),
    ("byte[] b = s.getBytes(StandardCharsets.UTF_8);",
     "byte array b equals s dot get Bytes Standard Charsets dot U T F 8"),
    ("UserDao dao = new UserDaoImpl();", "User D A O D A O equals new User D A O implementation"),
    ("String url = jdbcUrl; // the JDK default", "String URL equals J D B C URL, the JDK default"),
    ("} catch (IOException e) {", "catch I O Exception e"),
]


@pytest.mark.parametrize(("line", "spoken"), READS)
def test_java_reads_as_a_person_would(line, spoken):
    assert spoken_line(line, "java") == spoken


READS_NOW = [
    ("int m = x << 3;", "int m equals x left shift 3"),
    ("int h = hash >>> 16;", "int h equals hash unsigned right shift 16"),
    ("m <<= 1;", "m left shift equals 1"),
    ("h >>>= 4;", "h unsigned right shift equals 4"),
    ("List<String> names = new ArrayList<>();", "List of String names equals new Array List diamond"),
    ("Map<String, List<Integer>> index;", "Map of String, List of Integer index"),
    ("List<? extends Number> nums;", "List of wildcard extends Number nums"),
    ("int mask = 0xFF;", "int mask equals hex FF"),
]


@pytest.mark.parametrize(("line", "spoken"), READS_NOW)
def test_java_shifts_generics_and_hex(line, spoken):
    assert spoken_line(line, "java") == spoken


# These still need a rule in code.py that only Java wants.
@pytest.mark.parametrize(("line", "spoken"), [
    pytest.param("} catch (IOException | InterruptedException e) {", "catch I O Exception or Interrupted Exception e",
                 marks=pytest.mark.xfail(reason="needs code.py: | in a catch is a multi-catch", strict=True)),
    pytest.param("char c = (char) b;", "char c equals cast to char b",
                 marks=pytest.mark.xfail(reason="needs code.py: casts are read only for PHP", strict=True)),
])
def test_java_once_code_py_learns(line, spoken):
    assert spoken_line(line, "java") == spoken



def test_java_fence_and_inline_code():
    assert language("java").name == "java"
    assert language("Java").name == "java"
    assert spoken_code("println", "java") == "print line"
    assert spoken_code("instanceof", "java") == "instance of"
