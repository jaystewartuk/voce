"""Go's own words, named as the Go spec names them: ``:=`` is "short variable declaration", ``&^`` is "bit clear"."""

from __future__ import annotations

from voce.speech.words.common import Language

GO = Language("go", comments=("//", "/*"), words={
    # keywords and built-ins that read badly as written
    "chan": "channel", "fn": "function", "cap": "capacity", "goroutine": "go routine", "goroutines": "go routines",
    # the standard library's packages: https://pkg.go.dev/std
    "strconv": "string convert", "ioutil": "I O util", "bufio": "buf I O", "http": "HTTP", "httptest": "HTTP test",
    "httputil": "HTTP util", "filepath": "file path", "regexp": "reg exp", "fs": "F S", "slog": "S log",
    # fmt's and log's printing verbs: fmt.Println is "format dot print line" (fmt itself stays "format")
    "println": "print line", "sprint": "S print", "sprintln": "S print line", "fprint": "F print",
    "fprintf": "F print F", "fprintln": "F print line", "errorf": "error F", "fatalf": "fatal F",
    "fatalln": "fatal line", "panicf": "panic F", "panicln": "panic line", "logf": "log F", "skipf": "skip F",
    "sscanf": "S scan F", "scanf": "scan F", "scanln": "scan line", "sscan": "S scan", "fscan": "F scan",
    "fscanf": "F scan F", "infof": "info F", "warnf": "warn F", "debugf": "debug F", "tracef": "trace F",
    # strconv's: Itoa is "integer to ASCII"
    "itoa": "I to A", "atoi": "A to I",
    # names Go code uses everywhere, short for a word
    "mu": "mutex", "wg": "wait group", "rw": "R W", "resp": "response", "buf": "buffer", "addr": "address",
    "conn": "connection", "ptr": "pointer", "elem": "element", "dst": "destination", "getenv": "get env",
    "setenv": "set env", "mkdir": "make dir", "omitempty": "omit empty", "stdin": "standard in",
    "stdout": "standard out", "stderr": "standard error", "unsetenv": "unset env", "srv": "server",
    "recv": "receive", "sep": "separator", "cur": "current", "cmds": "commands", "subcmd": "sub command",
    "tmpl": "template", "tmpdir": "temp dir", "opts": "options", "opt": "option", "vals": "values",
    "elems": "elements", "errs": "errors", "errno": "error number", "typ": "type", "ptrs": "pointers",
    "uintptr": "U int pointer", "syscall": "sys call", "utf8": "U T F 8", "uri": "U R I", "csv": "C S V",
    "tsv": "T S V", "bson": "B S O N", "fd": "F D", "tc": "test case", "tt": "test", "jsoniter": "JSON iter",
    "errf": "error F", "tcp": "T C P", "udp": "U D P",
}, operators={
    # https://go.dev/ref/spec#Short_variable_declarations
    ":=": "short variable declaration",
    # https://go.dev/ref/spec#Slice_types: []T is a slice of T
    "[]": "slice of",
    # https://go.dev/ref/spec#Receive_operator: <-ch is a receive operation (ch <- v is a send statement)
    "<-": "receive from",
    # https://go.dev/ref/spec#Address_operators: &x is the address operation, far more common than bitwise AND
    "&": "address of",
    # https://go.dev/ref/spec#Arithmetic_operators
    "&^": "bit clear", "|": "bitwise or", "^": "bitwise X OR", "%": "remainder", "<<": "left shift",
    ">>": "right shift",
    # https://go.dev/ref/spec#Assignment_statements: x op= y is an assignment operation
    "&^=": "bit clear equals", "&=": "bitwise and equals", "|=": "bitwise or equals", "^=": "bitwise X OR equals",
    "%=": "remainder equals", "<<=": "left shift equals", ">>=": "right shift equals",
    # https://go.dev/ref/spec#Interface_types: ~T in a constraint is "the underlying type T"
    "~": "underlying type",
},
    # https://go.dev/ref/spec#Arithmetic_operators: a & b is "bitwise AND"; ch <- v is a send statement
    after_value={"&": "bitwise and", "<-": "send"},
    aliases=("go", "golang"),
    manual="https://go.dev/ref/spec")
