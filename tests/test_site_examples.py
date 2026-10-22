"""The landing page's language switcher says what voce says: nothing on it is typed by hand."""

from __future__ import annotations

import html
import importlib.util
import re
from pathlib import Path

import pytest

from voce.speech import spoken_line
from voce.speech.words import ALL, language

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("site_examples", ROOT / "docs" / "hearing" / "site_examples.py")
site_examples = importlib.util.module_from_spec(spec)
spec.loader.exec_module(site_examples)

PAGE = (ROOT / "site" / "index.html").read_text()
ROW = re.compile(r"<tr><td><code>(.*?)</code></td><td>&quot;(.*?)&quot;</td></tr>")


def test_the_page_is_up_to_date():
    assert site_examples.rewrite(PAGE) == PAGE, "run .venv/bin/python docs/hearing/site_examples.py"


@pytest.mark.parametrize("label, fence, manual_name, lines", site_examples.EXAMPLES)
def test_each_line_on_the_page_reads_as_shown(label, fence, manual_name, lines):
    panel = re.search(rf'data-lang="{re.escape(fence)}".*?</tbody>', PAGE, re.S)
    assert panel, f"no panel for {label}"
    rows = [(html.unescape(code), html.unescape(said)) for code, said in ROW.findall(panel.group())]
    assert [code for code, _ in rows] == lines
    for code, said in rows:
        assert said == spoken_line(code, fence)


def test_every_language_on_the_page_has_its_own_rules_and_a_manual():
    for label, fence, _manual, _lines in site_examples.EXAMPLES:
        lang = language(fence)
        assert lang.name != "code", f"{label} falls back to the generic rules"
        assert lang.manual.startswith("https://"), f"{label} names no manual"


def test_every_language_with_rules_is_on_the_page():
    on_page = {language(fence).name for _, fence, _, _ in site_examples.EXAMPLES}
    assert {lang.name for lang in ALL if not lang.prose} <= on_page


README = (ROOT / "README.md").read_text()
README_FENCES = {"Python": "python", "JavaScript": "javascript", "Go": "go", "Rust": "rust", "Ruby": "ruby",
                 "Kotlin": "kotlin", "shell": "bash", "SQL": "sql", "": "php"}
README_ROW = re.compile(r"^\| `(.+?)`(?: \((\w+)\))? \| (.+?) \|$", re.M)


def test_the_readme_table_reads_as_shown():
    rows = [(code.replace("\\|", "|"), README_FENCES[lang], said) for code, lang, said in README_ROW.findall(README)
            if lang in README_FENCES and "What you hear" not in said]
    assert len(rows) >= 14
    for code, fence, said in rows:
        # the README says "zero" for what is sent as 0, because that is what the voice says
        sent = re.sub(r"\b0\b", "zero", spoken_line(code, fence))
        assert sent == said.replace("\\|", "|"), code
