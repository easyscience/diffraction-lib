# Auto-generated scaffold. Replace TODOs with concrete tests.
import pytest
import numpy as np

# expected vs actual helpers

def _assert_equal(expected, actual):
    assert expected == actual


# Module under test: easydiffraction.analysis.calculation

# TODO: Replace with real, small tests per class/method.
# Keep names explicit: expected_*, actual_*; compare in a single assert.

def test_module_import():
    import easydiffraction.analysis.calculation as MUT
    expected_module_name = "easydiffraction.analysis.calculation"
    actual_module_name = MUT.__name__
    _assert_equal(expected_module_name, actual_module_name)


def test_calculator_wrapper_set_and_calls(monkeypatch):
    from easydiffraction.analysis.calculation import Calculator

    calls = {}
    class DummyCalc:
        def calculate_structure_factors(self, sm, exps):
            calls['sf'] = True
            return ['hkl']
        def calculate_pattern(self, sm, expt):
            calls['pat'] = True
    class DummyFactory:
        def create_calculator(self, engine):
            calls['engine'] = engine
            return DummyCalc()

    c = Calculator(engine='cryspy')
    # Inject dummy factory
    c.calculator_factory = DummyFactory()
    c.set_calculator('pdffit')
    assert calls['engine'] == 'pdffit'

    # Call delegates
    assert c.calculate_structure_factors('sm', 'exps') == ['hkl']
    c.calculate_pattern('sm', 'expt')
    assert calls['sf'] and calls['pat']
