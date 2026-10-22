"""SQL's own words, by the PostgreSQL manual's names: ``::`` is "cast to", ``desc`` is "descending"."""

from __future__ import annotations

from voce.speech.words.common import Language

SQL = Language("sql", comments=("--", "/*"), words={
    "id": "I D", "db": "D B", "desc": "descending", "asc": "ascending",
    # types said as two words, or by their letters
    "varchar": "var char", "nvarchar": "N var char", "nchar": "N char", "bpchar": "B P char",
    "smallint": "small int", "bigint": "big int", "tinyint": "tiny int", "mediumint": "medium int",
    "bigserial": "big serial", "smallserial": "small serial", "int2": "int 2", "int4": "int 4", "int8": "int 8",
    "float4": "float 4", "float8": "float 8", "timestamptz": "timestamp with time zone",
    "timetz": "time with time zone", "datetime": "date time", "longtext": "long text", "mediumtext": "medium text",
    "tinytext": "tiny text", "varbinary": "var binary", "jsonb": "JSON B", "tsvector": "T S vector",
    "tsquery": "T S query", "cidr": "C I D R", "macaddr": "mac addr", "regclass": "reg class",
    "regtype": "reg type", "oid": "O I D", "rowid": "row I D", "xml": "X M L",
    # functions and key words that read badly as written
    "nextval": "next value", "currval": "current value", "setval": "set value", "ifnull": "if null",
    "nullif": "null if", "isnull": "is null", "notnull": "not null", "ilike": "I like", "regexp": "reg exp",
    "substr": "sub string", "strpos": "string position", "initcap": "init cap", "lpad": "L pad", "rpad": "R pad",
    "ltrim": "L trim", "rtrim": "R trim", "btrim": "B trim", "unnest": "un nest",
    # abbreviations in table, column and index names: rental_pkey, customer_customer_id_seq
    "pk": "P K", "fk": "F K", "pkey": "P key", "fkey": "F key", "seq": "sequence", "tbl": "table",
    "btree": "B tree",
    # the databases and their languages
    "plpgsql": "P L P G S Q L", "psql": "P S Q L", "mysql": "My S Q L", "sqlite": "S Q Lite",
    "postgresql": "Postgres Q L", "utf8": "U T F 8", "utf8mb4": "U T F 8 M B 4", "dbo": "D B O",
}, operators={
    "<>": "is not equal to", "=": "equals", "!=": "is not equal to",  # manual 9.2, Table 9.1: "Not equal"
    "<=>": "is null-safe equal to",  # MySQL: "NULL-safe equal to operator"
    "::": "cast to",  # manual 4.2.9, Type Casts: CAST(x AS type), "the syntax with :: is historical"
    "||": "concatenated with",  # manual 9.4, Table 9.9: "Concatenates the two strings"; MySQL: or, by default
    "->": "extracts", "->>": "extracts as text", "#>": "extracts path", "#>>": "extracts path as text",
    # manual 9.16, Tables 9.47 and 9.48: "Extracts JSON object field", "Deletes the field ... at the specified path"
    "#-": "deletes path",
    "@>": "contains", "<@": "is contained in", "?|": "has any of", "?&": "has all of",  # Table 9.48
    "&&": "overlaps",  # manual 9.19, Table 9.56: "Do the arrays overlap"; MySQL: and
    "^@": "starts with",  # Table 9.10: "Returns true if the first string starts with the second string"
    "~": "matches", "~*": "matches case-insensitively", "!~": "does not match",
    "!~*": "does not match case-insensitively",  # manual 9.7.3, Table 9.16: "String matches regular expression"
    "^": "to the power of",  # manual 9.3, Table 9.4: "Exponentiation"; MySQL: bitwise exclusive or
    "|": "bitwise or", "&": "bitwise and", "<<": "bitwise shift left", ">>": "bitwise shift right",
    "|/": "square root", "||/": "cube root",  # Table 9.4: "Square root", "Cube root"
    ":=": "is assigned",  # PL/pgSQL, manual 43.5.1: an assignment
    "=>": "is",  # manual 4.3.2, Using Named Notation: "the argument's name is specified using =>"
    "?": "placeholder",  # a parameter marker in MySQL, SQLite and JDBC
    "[]": "array",  # manual 8.15: integer[] is an array type
},
    # https://www.postgresql.org/docs/current/functions-json.html: jsonb ? text, "Does the text string exist as a
    # top-level key"; a ? after =, ( or , is a placeholder
    after_value={"?": "exists"},
    aliases=("sql", "mysql", "postgresql", "postgres", "sqlite", "plpgsql"),
    manual="https://www.postgresql.org/docs/current/functions-comparison.html")
