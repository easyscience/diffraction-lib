import importlib
import types
import pytest

# expected vs actual helpers

def _assert_equal(expected, actual):
    assert expected == actual


# Module under test: easydiffraction.plotting.plotters.plotter_base

def test_module_import():
    import easydiffraction.plotting.plotters.plotter_base as MUT
    expected_module_name = "easydiffraction.plotting.plotters.plotter_base"
    actual_module_name = MUT.__name__
    _assert_equal(expected_module_name, actual_module_name)


def test_default_engine_switches_with_notebook(monkeypatch):
    # Force is_notebook() to True, then reload module
    import easydiffraction.plotting.plotters.plotter_base as pb
    import easydiffraction.utils.utils as utils

    monkeypatch.setattr(utils, 'is_notebook', lambda: True)
    pb2 = importlib.reload(pb)
    assert pb2.DEFAULT_ENGINE == 'plotly'

    # Now force False
    monkeypatch.setattr(utils, 'is_notebook', lambda: False)
    pb3 = importlib.reload(pb)
    assert pb3.DEFAULT_ENGINE == 'asciichartpy'


def test_default_axes_labels_keys_present():
    import easydiffraction.plotting.plotters.plotter_base as pb
    from easydiffraction.experiments.experiment.enums import BeamModeEnum, ScatteringTypeEnum

    assert (ScatteringTypeEnum.BRAGG, BeamModeEnum.CONSTANT_WAVELENGTH) in pb.DEFAULT_AXES_LABELS
    assert (ScatteringTypeEnum.BRAGG, BeamModeEnum.TIME_OF_FLIGHT) in pb.DEFAULT_AXES_LABELS
