# Auto-generated scaffold. Replace TODOs with concrete tests.
import pytest
import numpy as np

# expected vs actual helpers

def _assert_equal(expected, actual):
    assert expected == actual


# Module under test: easydiffraction.plotting.plotters.plotter_ascii

# TODO: Replace with real, small tests per class/method.
# Keep names explicit: expected_*, actual_*; compare in a single assert.

def test_module_import():
    import easydiffraction.plotting.plotters.plotter_ascii as MUT
    expected_module_name = "easydiffraction.plotting.plotters.plotter_ascii"
    actual_module_name = MUT.__name__
    _assert_equal(expected_module_name, actual_module_name)


def test_ascii_plotter_plot_minimal(capsys):
    from easydiffraction.plotting.plotters.plotter_ascii import AsciiPlotter
    x = np.array([0.0, 1.0, 2.0])
    y = np.array([1.0, 2.0, 3.0])
    p = AsciiPlotter()
    p.plot(x=x, y_series=[y], labels=['meas'], axes_labels=['x', 'y'], title='T', height=5)
    out = capsys.readouterr().out
    assert 'Displaying data for selected x-range' in out
