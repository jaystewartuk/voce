"""An HTTP message, read the way a person reads one out to a colleague.

A request line is its method and path, with the query said as names and values: ``GET /orders/42?page=2
HTTP/1.1`` is "GET slash orders slash 42, query page equals 2". A status line is its code and reason: "200 OK".
A header is its name, then its value, with the hyphens in the name silent: ``Content-Type: application/json`` is
"Content Type, application JSON". Cookies are names and values, a long opaque value is "a long token" and a JSON
web token is "a JWT", since nobody reads those out. The body is read in its own format: a form as names and
values, JSON as code, anything else as a line of code.

Payloads matter in this kind of text, so the characters an attacker would change are always said: a quote is "a
quote", ``<`` is "less than".
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from voce.speech.code import spoken_line, spoken_name
from voce.speech.words import language

_REQUEST = re.compile(r"^([A-Z]{3,10})\s+(\S+)(?:\s+HTTP/\d(?:\.\d)?)?\s*$")
_STATUS = re.compile(r"^HTTP/\d(?:\.\d)?\s+(\d{3})(?:\s+(.*))?$")
_HEADER = re.compile(r"^([A-Za-z0-9!#$%&'*+.^_`|~-]+):[ \t]*(.*)$")
_JWT = re.compile(r"eyJ[\w-]*\.[\w-]*\.[\w-]*")
_OPAQUE = re.compile(r"[A-Za-z0-9+/=_.~-]{24,}")
_URL = re.compile(r"^([a-z][a-z0-9+.-]*)://([^/?#\s]*)(.*)$", re.I)

# Media types by what people call them. Anything else is said as its parts: "text slash plain".
_TYPES = {
    "application/json": "application JSON", "application/x-www-form-urlencoded": "form URL encoded",
    "multipart/form-data": "multipart form data", "text/html": "text HTML", "text/plain": "text plain",
    "application/xml": "application X M L", "text/xml": "text X M L",
    "application/javascript": "application JavaScript", "text/javascript": "text JavaScript",
    "text/css": "text C S S", "application/octet-stream": "octet stream",
    "application/graphql": "application GraphQL",
}

# Words said by their letters. Others are left as they are: in a payload, src is src.
_LETTERS = {"api", "url", "id", "uuid", "ip", "jwt", "sql", "css", "js", "xml", "csrf", "xss", "ssrf", "utf"}

# The characters that carry a payload, by name. Letters and digits are read as they are.
_SYMBOLS = {
    "'": " quote ", '"': " double quote ", "`": " backtick ", "<": " less than ", ">": " greater than ",
    "=": " equals ", "&": " ampersand ", ";": " semicolon ", "/": " slash ", "\\": " backslash ", "|": " pipe ",
    "(": " open bracket ", ")": " close bracket ", "{": " open brace ", "}": " close brace ",
    "[": " open square bracket ", "]": " close square bracket ", "$": " dollar ", "#": " hash ", "%": " percent ",
    "@": " at ", "*": " star ", "!": " bang ", "?": " question mark ", "~": " tilde ", "^": " caret ",
    "+": " plus ", ",": " comma ", ":": " colon ", ".": " dot ", "_": " underscore ",
}


def spoken_symbols(text: str) -> str:
    """Text with every symbol said by name, as a tester reads a payload: ``' OR 1=1--`` is "quote OR 1 equals 1
    dash dash"."""
    out = []
    for word in re.findall(r"[A-Za-z]+|\d+|\s+|-+|.", text):
        if word.isspace():
            continue
        if word.startswith("-"):
            out.append(" ".join(["dash"] * len(word)))
        elif word.lower() in _LETTERS:
            out.append(" ".join(word.upper()))
        else:
            out.append(_SYMBOLS.get(word, word).strip())
    return " ".join(out)


def _value(text: str) -> str:
    """A value in a header, a cookie or a query: a URL by its parts, a token by what it is, the rest word by word."""
    s = text.strip()
    if not s:
        return "empty"
    if _JWT.fullmatch(s):
        return "a JWT"
    if _OPAQUE.fullmatch(s) and re.search(r"\d", s) and re.search(r"[A-Za-z]", s):
        return "a long token"
    m = _URL.match(s)
    if m:
        scheme, host, rest = m.groups()
        said = scheme.upper() + ", " + _host(host)
        return said + (" " + _path(rest) if rest and rest != "/" else "")
    if s.startswith("/"):
        return _path(s)
    return _plain(s)


def _host(host: str) -> str:
    """``shop.example.com:8080`` is "shop dot example dot com port 8080"."""
    name, _, port = host.partition(":")
    said = " dot ".join(name.split("."))
    return said + (f" port {port}" if port else "")


def _plain(s: str) -> str:
    """A short value: words and numbers as they are, dots and slashes said, symbols by name."""
    return spoken_symbols(s)


def _path(target: str) -> str:
    """A request target: the path's segments, then "query" and its names and values, then any fragment."""
    path, _, frag = target.partition("#")
    path, q, query = path.partition("?")
    said = " ".join("slash " + _plain(seg) if seg else "slash" for seg in path.split("/")[1:]) or _plain(path)
    if path in ("", "/"):
        said = "slash"
    if q:
        said += ", query " + _pairs(query, "&")
    if frag:
        said += ", fragment " + _plain(frag)
    return said


def _pairs(text: str, sep: str) -> str:
    """``a=1&b=2`` is "a equals 1, b equals 2"; the same for cookies, split on semicolons."""
    out = []
    for part in text.split(sep):
        part = part.strip()
        if not part:
            continue
        name, eq, val = part.partition("=")
        out.append(_plain(name) + (" equals " + _value(val) if eq else ""))
    return ", ".join(out)


def _media(value: str) -> str:
    """``text/html; charset=utf-8`` is "text HTML, charset U T F 8"."""
    kind, *params = [p.strip() for p in value.split(";")]
    said = _TYPES.get(kind.lower(), _plain(kind))
    for p in params:
        name, _, val = p.partition("=")
        val = val.strip('"')
        said += ", " + _plain(name) + " " + ("U T F 8" if val.lower() in ("utf-8", "utf8") else _value(val))
    return said


def _header(name: str, value: str) -> str:
    said_name = " ".join(spoken_name(w) if w.lower() not in ("www",) else "W W W" for w in name.split("-"))
    low = name.lower()
    if low in ("content-type", "accept") and "/" in value:
        return f"{said_name}, {_media(value)}"
    if low == "cookie":
        return f"{said_name}, {_pairs(value, ';')}"
    if low == "set-cookie":
        first, _, attrs = value.partition(";")
        said = f"{said_name}, {_pairs(first, ';')}"
        return said + (", " + _pairs(attrs, ";") if attrs.strip() else "")
    if low in ("authorization", "proxy-authorization"):
        scheme, _, cred = value.partition(" ")
        return f"{said_name}, {scheme}" + (", " + _value(cred) if cred else "")
    return f"{said_name}, {_value(value)}"


@dataclass
class _Reading:
    """Where a message is: still in the head, or in a body of a given kind."""
    in_body: bool = False
    body: str = ""        # "json", "form", "multipart" or ""


def http_lines(code: str) -> list[str]:
    """What to say for each line of an HTTP message, one string per line; an empty string says nothing."""
    state = _Reading()
    out: list[str] = []
    for line in code.split("\n"):
        s = line.rstrip("\r")
        if not state.in_body:
            if not s.strip():
                if out:
                    state.in_body = True
                out.append("")
                continue
            m = _REQUEST.match(s)
            if m:
                out.append(f"{m.group(1)} {_path(m.group(2))}")
                continue
            m = _STATUS.match(s)
            if m:
                out.append(m.group(1) + (" " + m.group(2) if m.group(2) else ""))
                continue
            m = _HEADER.match(s)
            if m:
                name, value = m.groups()
                if name.lower() == "content-type":
                    kind = value.split(";")[0].strip().lower()
                    state.body = ("json" if "json" in kind else "form" if kind.endswith("urlencoded")
                                  else "multipart" if kind.startswith("multipart/") else "")
                out.append(_header(name, value))
                continue
            out.append(_body_line(s, state))  # a body on its own, or a line that isn't HTTP
            continue
        out.append(_body_line(s, state))
    return out


def _body_line(s: str, state: _Reading) -> str:
    if not s.strip():
        return ""
    if state.body == "form" or (not state.body and re.fullmatch(r"[\w.%+-]+=[^\s]*(?:&[\w.%+-]+=[^\s]*)*", s)):
        return _pairs(s, "&")
    if state.body == "multipart":
        if s.startswith("--"):
            return "boundary"
        m = _HEADER.match(s)
        if m:
            return _header(*m.groups())
        return _plain(s)
    if state.body == "json" or s.lstrip()[:1] in "{[":
        return spoken_line(s, language("javascript"))
    if "<" in s and ">" in s:
        return _markup(s)
    return spoken_line(s, language(""))


def _markup(s: str) -> str:
    """A line of HTML in a body, as tags and text: ``<p>Hi</p>`` is "p tag, Hi, end p"."""
    s = s.replace("...", " and so on ")
    s = re.sub(r"</\s*([\w-]+)\s*>", lambda m: f", end {spoken_name(m.group(1).lower())}, ", s)
    s = re.sub(r"<\s*([\w-]+)[^>]*>", lambda m: f", {spoken_name(m.group(1).lower())} tag, ", s)
    return re.sub(r"\s*,(\s*,)+", ",", re.sub(r"\s+", " ", s)).strip(" ,")
