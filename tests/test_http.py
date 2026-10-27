"""HTTP messages, payloads and diagrams in fenced blocks: what is said for each."""

from voce.document import from_markdown
from voce.speech.http import http_lines, spoken_symbols


def said(md: str) -> list[str]:
    return [u.say for u in from_markdown(md).units]


def test_a_request_is_read_as_a_person_reads_one_out():
    lines = http_lines(
        "POST /account/email?redirect=/settings HTTP/1.1\n"
        "Host: shop.example.com\n"
        "Cookie: session=8f3a1c; theme=dark\n"
        "Content-Type: application/x-www-form-urlencoded\n"
        "Origin: https://shop.example.com\n"
        "\n"
        "email=jay%40example.com&next=/home")
    assert lines == [
        "POST slash account slash email, query redirect equals slash settings",
        "Host, shop dot example dot com",
        "Cookie, session equals 8 f 3 a 1 c, theme equals dark",
        "Content Type, form URL encoded",
        "Origin, HTTPS, shop dot example dot com",
        "",
        "email equals jay percent 40 example dot com, next equals slash home",
    ]


def test_a_response_says_its_status_and_cookie_attributes():
    lines = http_lines(
        "HTTP/1.1 302 Found\n"
        "Content-Type: text/html; charset=utf-8\n"
        "Set-Cookie: session=8f3a1cA9zQ7mK2pL0xV5nB3wR6tY; Path=/; Secure; HttpOnly; SameSite=Lax\n"
        "\n"
        "<p>Moved</p>")
    assert lines == [
        "302 Found",
        "Content Type, text HTML, charset U T F 8",
        "Set Cookie, session equals a long token, Path equals slash, Secure, HttpOnly, SameSite equals Lax",
        "",
        "p tag, Moved, end p",
    ]


def test_tokens_are_named_not_spelt():
    assert http_lines("Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.c2lnbmF0dXJl") == [
        "Authorization, Bearer, a JWT"]


def test_a_json_body_is_read_as_code():
    lines = http_lines('PATCH /api/users/7 HTTP/1.1\nContent-Type: application/json\n\n{"role": "admin"}')
    assert lines[0] == "PATCH slash A P I slash users slash 7"
    assert lines[1] == "Content Type, application JSON"
    assert "role" in lines[3] and "admin" in lines[3]


def test_a_body_on_its_own_is_read_in_its_format():
    assert http_lines("q=red+shoes&page=2") == ["q equals red plus shoes, page equals 2"]


def test_a_payload_says_every_symbol():
    assert spoken_symbols("' OR 1=1--") == "quote OR 1 equals 1 dash dash"
    assert spoken_symbols("../../etc/passwd") == "dot dot slash dot dot slash etc slash passwd"
    assert spoken_symbols("<img src=x onerror=alert(1)>") == (
        "less than img src equals x onerror equals alert open bracket 1 close bracket greater than")


def test_fences_choose_the_reading():
    md = ("Before.\n\n```http\nGET /orders/42 HTTP/1.1\n```\n\n```payload\n' OR 1=1--\n```\n\n"
          "```diagram\nBrowser ──► Server\n```\n\n```mermaid\ngraph LR; A-->B\n```\n\nAfter.")
    assert said(md) == ["Before.", "GET slash orders slash 42", "quote OR 1 equals 1 dash dash", "After."]
