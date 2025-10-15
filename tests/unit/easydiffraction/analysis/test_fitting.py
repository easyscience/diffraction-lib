# Auto-generated scaffold. Replace TODOs with concrete tests.
import pytest
import numpy as np

# expected vs actual helpers

def _assert_equal(expected, actual):
    assert expected == actual


# Module under test: easydiffraction.analysis.fitting

# TODO: Replace with real, small tests per class/method.
# Keep names explicit: expected_*, actual_*; compare in a single assert.

def test_module_import():
    import easydiffraction.analysis.fitting as MUT
    expected_module_name = "easydiffraction.analysis.fitting"
    actual_module_name = MUT.__name__
    _assert_equal(expected_module_name, actual_module_name)


def test_fitter_early_exit_when_no_params(capsys, monkeypatch):
    from easydiffraction.analysis.fitting import Fitter

    class DummyCollection:
        free_parameters = []
        def __init__(self):
            self._names = ['e1']
        @property
        def names(self):
            return self._names
    class DummyMin:
        tracker = type('T', (), {'track': staticmethod(lambda a,b: a)})()
        def fit(self, params, obj):
            return None

    f = Fitter()
    # Avoid creating a real minimizer
    f.minimizer = DummyMin()
    f.fit(sample_models=DummyCollection(), experiments=DummyCollection(), calculator=object())
    out = capsys.readouterr().out
    assert 'No parameters selected for fitting' in out
