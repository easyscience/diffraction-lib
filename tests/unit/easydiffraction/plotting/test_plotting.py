# Auto-generated scaffold. Replace TODOs with concrete tests.
import pytest

# expected vs actual helpers

def _assert_equal(expected, actual):
    assert expected == actual


# Module under test: easydiffraction.plotting.plotting

# TODO: Replace with real, small tests per class/method.
# Keep names explicit: expected_*, actual_*; compare in a single assert.

def test_module_import():
    import easydiffraction.plotting.plotting as MUT
    expected_module_name = "easydiffraction.plotting.plotting"
    actual_module_name = MUT.__name__
    _assert_equal(expected_module_name, actual_module_name)


def test_plotter_configuration_and_engine_switch(capsys):
    from easydiffraction.plotting.plotting import Plotter

    p = Plotter()
    # show config prints a table
    p.show_config()
    out1 = capsys.readouterr().out
    assert 'Current plotter configuration' in out1

    # show supported engines prints a table
    p.show_supported_engines()
    out2 = capsys.readouterr().out
    assert 'Supported plotter engines' in out2

    # Switch engine to its current value (no-op, but exercise setter)
    cur = p.engine
    p.engine = cur
    # And to an unsupported engine (prints error and leaves engine unchanged)
    p.engine = '___not_supported___'
    assert p.engine == cur

    # Supported engines include both known backends
    p.show_supported_engines()
    out3 = capsys.readouterr().out
    assert 'asciichartpy' in out3 or 'plotly' in out3


def test_plotter_factory_unsupported(capsys):
    from easydiffraction.plotting.plotting import PlotterFactory

    obj = PlotterFactory.create_plotter('nope')
    assert obj is None
    out = capsys.readouterr().out
    assert 'Unsupported plotting engine' in out


def test_plotter_error_paths_and_filtering(capsys):
    from easydiffraction.plotting.plotting import Plotter
    from easydiffraction.experiments.experiment.enums import BeamModeEnum, ScatteringTypeEnum

    class Ptn:
        def __init__(self, x=None, meas=None, calc=None, d=None):
            self.x = x
            self.meas = meas
            self.calc = calc
            self.d = d if d is not None else x

    class ExptType:
        def __init__(self):
            self.scattering_type = type('S', (), {'value': ScatteringTypeEnum.BRAGG})
            self.beam_mode = type('B', (), {'value': BeamModeEnum.CONSTANT_WAVELENGTH})

    p = Plotter()

    # Error paths
    p.plot_meas(Ptn(x=None, meas=None), 'E', ExptType())
    out = capsys.readouterr().out
    # plot_meas uses formatting.error(...) without printing -> no stdout
    assert out == ''

    p.plot_meas(Ptn(x=[1], meas=None), 'E', ExptType())
    out = capsys.readouterr().out
    # Same here: no print, so no stdout
    assert out == ''

    p.plot_calc(Ptn(x=None, calc=None), 'E', ExptType())
    out = capsys.readouterr().out
    # plot_calc also uses formatting.error(...) without printing for x is None
    assert out == ''

    p.plot_calc(Ptn(x=[1], calc=None), 'E', ExptType())
    out = capsys.readouterr().out
    assert 'No calculated data available' in out or 'No calculated data' in out

    p.plot_meas_vs_calc(Ptn(x=None), 'E', ExptType())
    out = capsys.readouterr().out
    assert 'No data available' in out
    p.plot_meas_vs_calc(Ptn(x=[1], meas=None, calc=[1]), 'E', ExptType())
    out = capsys.readouterr().out
    assert 'No measured data available' in out
    p.plot_meas_vs_calc(Ptn(x=[1], meas=[1], calc=None), 'E', ExptType())
    out = capsys.readouterr().out
    assert 'No calculated data available' in out

    # Filtering
    import numpy as np
    p.x_min, p.x_max = 0.5, 1.5
    arr = np.array([0.0, 1.0, 2.0])
    filt = p._filtered_y_array(arr, arr, None, None)
    assert np.allclose(filt, np.array([1.0]))


def test_plotter_routes_to_ascii_plotter(monkeypatch):
    from easydiffraction.plotting.plotting import Plotter
    from easydiffraction.experiments.experiment.enums import BeamModeEnum, ScatteringTypeEnum
    import easydiffraction.plotting.plotters.plotter_ascii as ascii_mod
    import numpy as np

    called = {}

    def fake_plot(self, x, y_series, labels, axes_labels, title, height=None):
        called['labels'] = tuple(labels)
        called['axes'] = tuple(axes_labels)
        called['title'] = title

    monkeypatch.setattr(ascii_mod.AsciiPlotter, 'plot', fake_plot)

    class Ptn:
        def __init__(self):
            self.x = np.array([0.0, 1.0])
            self.meas = np.array([1.0, 2.0])
            self.d = self.x

    class ExptType:
        def __init__(self):
            self.scattering_type = type('S', (), {'value': ScatteringTypeEnum.BRAGG})
            self.beam_mode = type('B', (), {'value': BeamModeEnum.CONSTANT_WAVELENGTH})

    p = Plotter()
    p.engine = 'asciichartpy'  # ensure AsciiPlotter
    p.plot_meas(Ptn(), 'E', ExptType())
    assert called['labels'] == ('meas',)
    assert 'Measured data' in called['title']
