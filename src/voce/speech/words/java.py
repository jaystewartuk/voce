"""Java's own words, by the Java Language Specification's names: ``%`` is "remainder", ``>>>`` is "unsigned right
shift", ``<>`` is "diamond"."""

from __future__ import annotations

from voce.speech.words.common import Language

# Operator names from the JLS, chapter 15 (https://docs.oracle.com/javase/specs/jls/se21/html/jls-15.html), and the
# Java Tutorials' summary of operators (https://docs.oracle.com/javase/tutorial/java/nutsandbolts/opsummary.html).
# "::" is a method reference (JLS 15.13).
JAVA = Language("java", comments=("//", "/*"), words={
    "println": "print line", "instanceof": "instance of", "jdk": "J D K", "jvm": "J V M", "jre": "J R E",
    "javax": "java X", "utf": "U T F", "uid": "U I D", "jdbc": "J D B C", "jpa": "J P A", "dao": "D A O",
    "dto": "D T O", "gwt": "G W T", "sb": "S B", "fn": "function", "classloader": "class loader",
    "varargs": "var args",
}, operators={
    "%": "remainder", "%=": "remainder equals",                                    # 15.17.3
    "<<": "left shift", ">>": "signed right shift", ">>>": "unsigned right shift",  # 15.19
    "<<=": "left shift equals", ">>=": "signed right shift equals", ">>>=": "unsigned right shift equals",
    "&": "bitwise and", "^": "bitwise exclusive or", "|": "bitwise inclusive or",  # 15.22, the tutorial's names
    "&=": "bitwise and equals", "^=": "bitwise exclusive or equals", "|=": "bitwise inclusive or equals",
    "~": "bitwise complement",                                                      # 15.15.5
    "->": "arrow",            # 15.2: "the arrow of a lambda expression"
    "::": "method reference",  # 15.13
    "...": "variable arity",  # 8.4.1: a variable arity parameter, String... args
    "<>": "diamond",          # 15.9: "or a diamond (<>)", new ArrayList<>()
}, aliases=("java",), manual="https://docs.oracle.com/javase/specs/jls/se21/html/jls-15.html")
