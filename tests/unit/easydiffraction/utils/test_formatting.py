# Auto-generated scaffold. Replace TODOs with concrete tests.
import pytest
import numpy as np

# expected vs actual helpers

def _assert_equal(expected, actual):
    assert expected == actual


# Module under test: easydiffraction.utils.formatting

# TODO: Replace with real, small tests per class/method.
# Keep names explicit: expected_*, actual_*; compare in a single assert.

def test_module_import():
    import easydiffraction.utils.formatting as MUT
    expected_module_name = "easydiffraction.utils.formatting"
    actual_module_name = MUT.__name__
    _assert_equal(expected_module_name, actual_module_name)


def test_chapter_uppercase_and_length():
    import easydiffraction.utils.formatting as MUT
    title = "Intro"
    s = MUT.chapter(title)
    assert title.upper() in s and len(s) > len(title)


def test_section_formatting_contains_markers():
    import easydiffraction.utils.formatting as MUT
    s = MUT.section("part")
    assert "*** PART ***" in s.upper()


def test_paragraph_preserves_quotes():
    import easydiffraction.utils.formatting as MUT
    s = MUT.paragraph("Hello 'World'")
    # quoted part should appear verbatim
    assert "'World'" in s


def test_error_warning_info_prefixes():
    import easydiffraction.utils.formatting as MUT
    assert "Error" in MUT.error("x")
    assert "Warning" in MUT.warning("x")
    assert "Info" in MUT.info("x")
