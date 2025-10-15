import re


def test_list_and_show_supported_calculators_do_not_crash(capsys, monkeypatch):
    from easydiffraction.analysis.calculators.factory import CalculatorFactory

    # Simulate no engines available by forcing engine_imported to False
    class DummyCalc:
        def __call__(self):
            return self

        @property
        def engine_imported(self):
            return False

    monkeypatch = monkeypatch  # keep name
    monkeypatch.setitem(CalculatorFactory._potential_calculators, 'dummy', {
        'description': 'Dummy calc',
        'class': DummyCalc,
    })

    lst = CalculatorFactory.list_supported_calculators()
    assert isinstance(lst, list)

    CalculatorFactory.show_supported_calculators()
    out = capsys.readouterr().out
    # Should print the paragraph title
    assert 'Supported calculators' in out


def test_create_calculator_unknown_returns_none(capsys):
    from easydiffraction.analysis.calculators.factory import CalculatorFactory
    obj = CalculatorFactory.create_calculator('this_is_unknown')
    assert obj is None
    out = capsys.readouterr().out
    assert 'Unknown calculator' in out# Auto-generated scaffold. Replace TODOs with concrete tests.
import pytest
import numpy as np

# expected vs actual helpers

def _assert_equal(expected, actual):
    assert expected == actual


# Module under test: easydiffraction.analysis.calculators.factory

# TODO: Replace with real, small tests per class/method.
# Keep names explicit: expected_*, actual_*; compare in a single assert.

def test_module_import():
    import easydiffraction.analysis.calculators.factory as MUT
    expected_module_name = "easydiffraction.analysis.calculators.factory"
    actual_module_name = MUT.__name__
    _assert_equal(expected_module_name, actual_module_name)
