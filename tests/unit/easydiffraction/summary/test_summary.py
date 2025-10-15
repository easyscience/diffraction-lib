def test_summary_as_cif_returns_placeholder_string():
    from easydiffraction.summary.summary import Summary

    class P:
        pass

    s = Summary(P())
    out = s.as_cif()
    assert isinstance(out, str)
    assert "To be added" in out


def test_summary_show_report_prints_sections(capsys):
    from easydiffraction.summary.summary import Summary

    class Info:
        title = "T"
        description = ""

    class Project:
        def __init__(self):
            self.info = Info()
            self.sample_models = {}  # empty mapping to exercise loops safely
            self.experiments = {}    # empty mapping to exercise loops safely
            class A:
                current_calculator = "cryspy"
                current_minimizer = "lmfit"
                class R:
                    reduced_chi_square = 0.0
                fit_results = R()
            self.analysis = A()

    s = Summary(Project())
    s.show_report()
    out = capsys.readouterr().out
    # Verify that all top-level sections appear (titles are uppercased by formatter)
    assert "PROJECT INFO" in out
    assert "CRYSTALLOGRAPHIC DATA" in out
    assert "EXPERIMENTS" in out
    assert "FITTING" in out
# Auto-generated scaffold. Replace TODOs with concrete tests.
import pytest
import numpy as np

# expected vs actual helpers

def _assert_equal(expected, actual):
    assert expected == actual


# Module under test: easydiffraction.summary.summary

# TODO: Replace with real, small tests per class/method.
# Keep names explicit: expected_*, actual_*; compare in a single assert.

def test_module_import():
    import easydiffraction.summary.summary as MUT
    expected_module_name = "easydiffraction.summary.summary"
    actual_module_name = MUT.__name__
    _assert_equal(expected_module_name, actual_module_name)
