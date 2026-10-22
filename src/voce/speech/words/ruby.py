"""Ruby's own words, by the names Ruby's documentation gives them: ``<<`` is "append", ``&.`` is "safe navigation",
``=>`` is "hash rocket" (the Hash page's own name for it), ``|item|`` is said without its pipes."""

from __future__ import annotations

from voce.speech.words.common import Language

RUBY = Language("ruby", comments=("#",), words={
    "elsif": "else if", "attr": "attribute", "cattr": "class attribute", "mattr": "module attribute",
    "klass": "class", "kwargs": "keyword args", "opts": "options", "attrs": "attributes", "blk": "block",
    "ary": "array", "hsh": "hash", "sym": "symbol", "meth": "method", "ivar": "instance variable",
    "cvar": "class variable", "puts": "put S", "pp": "P P", "gsub": "G sub", "lstrip": "L strip",
    "rstrip": "R strip", "ljust": "L just", "rjust": "R just", "uniq": "unique", "chr": "char", "dup": "dupe",
    "succ": "successor", "pred": "predecessor", "usec": "microseconds", "nsec": "nanoseconds", "utc": "U T C",
    "tzinfo": "T Z info", "i18n": "I 18 N", "stdin": "standard in", "stdout": "standard out",
    "stderr": "standard error", "rb": "R B", "erb": "E R B", "rspec": "R spec", "gemspec": "gem spec",
    "ostruct": "O struct", "progname": "prog name", "logdev": "log dev", "callstack": "call stack",
    "bytesize": "byte size", "fname": "file name", "pid": "P I D", "ssl": "S S L", "fs": "F S",
    "TZInfo": "T Z info",
}, operators={
    # The names Ruby's operator methods go by: https://docs.ruby-lang.org/en/master/syntax/methods_rdoc.html
    "<=>": "spaceship",  # "comparison aka spaceship operator" on that page
    "===": "case equals",  # "case equality"
    "=~": "matches", "!~": "does not match",  # "pattern match", "does not match"
    "<<": "append",  # "left-shift, append": most often Array#<< and String#<<
    ">>": "right shift", "^": "exclusive or",  # "right-shift", "XOR (exclusive OR)"
    # "The original syntax for a hash entry uses the 'hash rocket', =>":
    # https://docs.ruby-lang.org/en/master/Hash.html
    "=>": "hash rocket",
    # "&., called 'safe navigation operator'": https://docs.ruby-lang.org/en/master/syntax/calling_methods_rdoc.html
    "&.": "safe navigation",
    # "Lambda Proc Literals: a lambda proc can be created with ->":
    # https://docs.ruby-lang.org/en/master/syntax/literals_rdoc.html
    "->": "lambda",
    # "the double-dot (included end) or triple-dot (excluded end) notation":
    # https://docs.ruby-lang.org/en/master/Range.html
    "..": "double dot", "...": "triple dot",
    "|": "",  # a block's parameters, do |item|, are said without their pipes
}, aliases=("ruby", "rb", "rake", "gemspec"),
    manual="https://docs.ruby-lang.org/en/master/syntax/methods_rdoc.html")
