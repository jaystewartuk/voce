"""How SQL reads: the PostgreSQL manual's names for operators, and type and key word names said as people say them."""

from __future__ import annotations

import pytest

from voce.speech import spoken_line


def said(line: str) -> str:
    return spoken_line(line, "sql")


@pytest.mark.parametrize("line, spoken", [
    # the cast and concatenation operators (manual 4.2.9 and Table 9.9)
    ("SELECT created_at::date FROM orders;", "SELECT created at cast to date FROM orders"),
    ("nextval('customer_customer_id_seq'::regclass)", "next value customer customer I D sequence cast to reg class"),
    ("SELECT first_name || ' ' || last_name FROM customer",
     "SELECT first name concatenated with a space concatenated with last name FROM customer"),
    # comparison (Table 9.1)
    ("WHERE id = 1 AND status <> 'done'", "WHERE I D equals 1 AND status is not equal to done"),
    ("WHERE a != b", "WHERE A is not equal to b"),
    ("WHERE a <=> b", "WHERE A is null-safe equal to b"),
    # mathematical operators (Table 9.4)
    ("SELECT 2 ^ 3, 5 % 4", "SELECT 2 to the power of 3, 5 modulo 4"),
    ("flags | 4", "flags bitwise or 4"),
    ("flags & 4", "flags bitwise and 4"),
    ("8 >> 2", "8 bitwise shift right 2"),
    # JSON, the one with a single arrow
    ("WHERE data->'user' IS NULL", "WHERE data extracts user IS NULL"),
    # PL/pgSQL assignment and named notation
    ("v_total := v_total + 1;", "v total is assigned v total plus 1"),
    ("SELECT concat_lower_or_upper(a => 'Hello', b => 'World')",
     "SELECT concat lower or upper A is Hello, b is World"),
    # a parameter marker is not a ternary
    ("WHERE id = ?", "WHERE I D equals placeholder"),
    ("VALUES (?, ?)", "VALUES placeholder, placeholder"),
    ("special_features text[]", "special features text array"),
    ("WHERE tags && ARRAY['a']", "WHERE tags overlaps ARRAY A"),
    # types, key words and names
    ("email VARCHAR(255) NOT NULL UNIQUE,", "email var char 255 NOT NULL UNIQUE"),
    ("order_id BIGINT NOT NULL,", "order I D big int NOT NULL"),
    ("created_at TIMESTAMPTZ NOT NULL DEFAULT now(),", "created at timestamp with time zone NOT NULL DEFAULT now"),
    ("store_id smallint NOT NULL REFERENCES store(store_id),",
     "store I D small int NOT NULL REFERENCES store store I D"),
    ("WHERE name ILIKE '%smith%'", "WHERE name I like percent smith percent"),
    ("body jsonb DEFAULT '{}'::jsonb", "body JSON B DEFAULT empty braces cast to JSON B"),
    ("n int4 CHECK (n > 0), q tsquery", "n int 4 CHECK n greater than 0, q T S query"),
    ("LANGUAGE plpgsql AS $$", "LANGUAGE P L P G S Q L AS dollar dollar"),
    ("ALTER TABLE ONLY rental ADD CONSTRAINT rental_pkey PRIMARY KEY (rental_id);",
     "ALTER TABLE ONLY rental ADD CONSTRAINT rental P key PRIMARY KEY rental I D"),
    ("CREATE INDEX idx_fk_customer_id ON payment USING btree (customer_id);",
     "CREATE INDEX index F K customer I D ON payment USING B tree customer I D"),
    ("ORDER BY rental_date DESC", "ORDER BY rental date descending"),
    ("DEFAULT CHARSET=utf8mb4", "DEFAULT CHARSET equals U T F 8 M B 4"),
    ("SELECT id FROM t WHERE a <> b -- why", "SELECT I D FROM t WHERE A is not equal to b, why"),
])
def test_sql_reads_the_way_the_manual_names_it(line, spoken):
    assert said(line) == spoken


# These need the tokeniser to know the operator as one token (see the report): today ->> is "->" and ">".
def test_json_field_as_text():
    assert said("WHERE data->'user'->>'email' = 'a@b.c'") == \
        "WHERE data extracts user extracts as text email equals a@b.c"


def test_json_path():
    assert said("SELECT doc #> '{a,b}', doc #>> '{a,b}'") == \
        "SELECT doc extracts path a,b, doc extracts path as text a,b"


def test_json_delete_path():
    assert said("SELECT doc #- '{a}'") == "SELECT doc deletes path a"


def test_contains_and_is_contained_in():
    assert said("WHERE tags @> ARRAY['x'] AND ARRAY['x'] <@ tags") == \
        "WHERE tags contains ARRAY x AND ARRAY x is contained in tags"


def test_json_key_exists():
    assert said("WHERE meta ?| array['a'] AND meta ?& array['b']") == \
        "WHERE meta has any of array A AND meta has all of array b"


def test_regular_expression_matches():
    assert said("WHERE a ~ 'x' AND b ~* 'y' AND c !~ 'z' AND d !~* 'w'") == \
        "WHERE A matches x AND b matches case-insensitively y AND c does not match z " \
        "AND d does not match case-insensitively w"


def test_starts_with():
    assert said("WHERE name ^@ 'al'") == "WHERE name starts with al"


def test_shift_left():
    assert said("SELECT 1 << 4") == "SELECT 1 bitwise shift left 4"


def test_roots():
    assert said("SELECT |/ 25.0, ||/ 64.0") == "SELECT square root 25.0, cube root 64.0"


def test_select_star():
    assert said("SELECT * FROM film") == "SELECT star FROM film"


def test_json_key_exists_question_mark():
    assert said("WHERE meta ? 'admin'") == "WHERE meta exists admin"


def test_column_line_is_not_prose():
    assert said("id BIGINT NOT NULL,") == "I D big int NOT NULL"
