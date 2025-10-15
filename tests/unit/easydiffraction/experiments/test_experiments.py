# Auto-generated scaffold. Replace TODOs with concrete tests.
import pytest
import numpy as np

# expected vs actual helpers

def _assert_equal(expected, actual):
    assert expected == actual


# Module under test: easydiffraction.experiments.experiments

# TODO: Replace with real, small tests per class/method.
# Keep names explicit: expected_*, actual_*; compare in a single assert.

def test_module_import():
    import easydiffraction.experiments.experiments as MUT
    expected_module_name = "easydiffraction.experiments.experiments"
    actual_module_name = MUT.__name__
    _assert_equal(expected_module_name, actual_module_name)


def test_experiments_show_and_remove(monkeypatch, capsys):
    from easydiffraction.experiments.experiments import Experiments
    from easydiffraction.experiments.experiment.base import ExperimentBase

    class DummyType:
        def __init__(self):
            self.sample_form = type('E', (), {'value': 'powder'})
            self.beam_mode = type('E', (), {'value': 'constant wavelength'})

    class DummyExp(ExperimentBase):
        def __init__(self, name='e1'):
            super().__init__(name=name, type=DummyType())
        def _load_ascii_data_to_experiment(self, data_path: str) -> None:
            pass

    exps = Experiments()
    exps.add(DummyExp('a'))
    exps.add(DummyExp('b'))
    exps.show_names()
    out = capsys.readouterr().out
    assert 'Defined experiments' in out

    # Remove by name should not raise
    exps.remove('a')
    # Still can show names
    exps.show_names()
    out2 = capsys.readouterr().out
    assert 'Defined experiments' in out2
