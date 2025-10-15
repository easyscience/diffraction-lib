import re


def _strip_ansi(s: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", s)


def test_chapter_uppercase_and_length():
    import easydiffraction.utils.formatting as F
    title = "Intro"
    s = _strip_ansi(F.chapter(title))
    # chapter uses box drawing SYMBOL = '═'
    assert "═" in s and title.upper() in s


def test_section_formatting_contains_markers():
    import easydiffraction.utils.formatting as F
    s = _strip_ansi(F.section("part"))
    assert "*** PART ***" in s.upper()


def test_paragraph_preserves_quotes():
    import easydiffraction.utils.formatting as F
    s = _strip_ansi(F.paragraph("Hello 'World'"))
    assert "'World'" in s


def test_error_warning_info_prefixes():
    import easydiffraction.utils.formatting as F
    assert "Error" in _strip_ansi(F.error("x"))
    assert "Warning" in _strip_ansi(F.warning("x"))
    assert "Info" in _strip_ansi(F.info("x"))
