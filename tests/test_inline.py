from voce.markdown import inline, linked, plain


def styled(text, spans):
    return {text[a:z]: set(roles) for a, z, roles in spans}


def test_plain_text_is_unchanged():
    assert inline("Just words.") == ("Just words.", [])


def test_bold_italic_code_and_links_become_spans():
    text, spans = inline("Use **bold**, *italic*, `code` and [a link](https://example.com).")
    assert text == "Use bold, italic, code and a link."
    assert styled(text, spans) == {"bold": {"bold"}, "italic": {"italic"}, "code": {"code"}, "a link": {"link"}}


def test_nested_styles_combine():
    text, spans = inline("**bold with `code` inside**")
    assert text == "bold with code inside"
    assert styled(text, spans)["code"] == {"bold", "code"}


def test_italic_around_bold():
    text, spans = inline("*a **b** c*")
    assert text == "a b c"
    assert styled(text, spans)["b"] == {"bold", "italic"}


def test_underscores_inside_words_are_left_alone():
    assert plain("snake_case_name and file_name.md") == "snake_case_name and file_name.md"


def test_code_spans_keep_markup_literally():
    text, spans = inline("Run `**not bold**` now")
    assert text == "Run **not bold** now"
    assert styled(text, spans) == {"**not bold**": {"code"}}


def test_double_backticks_and_padding():
    assert plain("`` a `tick` here ``") == "a `tick` here"


def test_unclosed_markers_stay_as_text():
    assert plain("2 * 3 = 6 and a lone ` tick") == "2 * 3 = 6 and a lone ` tick"


def test_escapes_entities_and_html():
    assert plain(r"\*not italic\* &amp; <kbd>q</kbd> quits<br>now") == "*not italic* & q quits now"


def test_autolinks_and_images():
    text, spans = inline("See <https://example.com> and ![a diagram](d.png)")
    assert text == "See https://example.com and a diagram"
    assert styled(text, spans) == {"https://example.com": {"link"}, "a diagram": {"link"}}


def test_links_keep_where_they_lead():
    text, _, links = linked('Next: [How the **course** works](00/02.md "Part two") · <https://example.com> ![a](d.png)')
    assert text == "Next: How the course works · https://example.com a"
    assert [(text[a:z], to) for a, z, to in links] == [("How the course works", "00/02.md"),
                                                       ("https://example.com", "https://example.com")]


def test_strikethrough():
    assert styled(*inline("~~gone~~ here")) == {"gone": {"strike"}}


def test_white_space_collapses_and_spans_follow():
    text, spans = inline("  a   **b**\n c  ")
    assert text == "a b c"
    assert styled(text, spans) == {"b": {"bold"}}


def test_comparison_signs_are_not_tags():
    assert plain("if a < b and c > d") == "if a < b and c > d"
