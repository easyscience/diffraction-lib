# SPDX-FileCopyrightText: 2021-2026 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

def test_module_import():
    import easydiffraction.display.plotting as MUT

    expected_module_name = 'easydiffraction.display.plotting'
    actual_module_name = MUT.__name__
    assert expected_module_name == actual_module_name


def test_plotter_configuration_and_engine_switch(capsys):
    from easydiffraction.display.plotting import Plotter

    p = Plotter()
    # show config prints a table
    p.show_config()
    out1 = capsys.readouterr().out
    assert 'Current plotter configuration' in out1

    # show supported engines prints a table (now via base RendererBase title)
    p.show_supported_engines()
    out2 = capsys.readouterr().out
    # assert 'Supported plotter engines' in out2
    assert 'Supported engines' in out2

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


def test_plotter_factory_supported_and_unsupported():
    from easydiffraction.display.plotting import PlotterFactory

    # Supported engine creates a backend instance
    obj = PlotterFactory.create('asciichartpy')
    assert obj is not None

    # Unsupported engine should raise ValueError (unified policy)
    try:
        PlotterFactory.create('nope')
        assert False, 'Expected ValueError for unsupported engine name'
    except ValueError:
        pass


def test_plotter_error_paths_and_filtering(capsys):
    from easydiffraction.experiments.experiment.enums import BeamModeEnum
    from easydiffraction.experiments.experiment.enums import SampleFormEnum
    from easydiffraction.experiments.experiment.enums import ScatteringTypeEnum
    from easydiffraction.display.plotting import Plotter

    class Ptn:
        def __init__(self, two_theta=None, intensity_meas=None, intensity_calc=None, d_spacing=None):
            self.two_theta = two_theta
            self.intensity_meas = intensity_meas
            self.intensity_calc = intensity_calc
            self.d_spacing = d_spacing if d_spacing is not None else two_theta

    class ExptType:
        def __init__(self):
            self.sample_form = type('SF', (), {'value': SampleFormEnum.POWDER})
            self.scattering_type = type('S', (), {'value': ScatteringTypeEnum.BRAGG})
            self.beam_mode = type('B', (), {'value': BeamModeEnum.CONSTANT_WAVELENGTH})

    p = Plotter()

    # Error paths (now log errors via console; messages are printed)
    p.plot_meas(Ptn(two_theta=None, intensity_meas=None), 'E', ExptType())
    out = capsys.readouterr().out
    assert 'No two_theta data available for experiment E' in out

    p.plot_meas(Ptn(two_theta=[1], intensity_meas=None), 'E', ExptType())
    out = capsys.readouterr().out
    assert 'No measured data available for experiment E' in out

    p.plot_calc(Ptn(two_theta=None, intensity_calc=None), 'E', ExptType())
    out = capsys.readouterr().out
    assert 'No two_theta data available for experiment E' in out

    p.plot_calc(Ptn(two_theta=[1], intensity_calc=None), 'E', ExptType())
    out = capsys.readouterr().out
    assert 'No calculated data available for experiment E' in out

    p.plot_meas_vs_calc(Ptn(two_theta=None, intensity_meas=None, intensity_calc=None), 'E', ExptType())
    out = capsys.readouterr().out
    assert 'No measured data available for experiment E' in out
    p.plot_meas_vs_calc(Ptn(two_theta=[1], intensity_meas=None, intensity_calc=[1]), 'E', ExptType())
    out = capsys.readouterr().out
    assert 'No measured data available for experiment E' in out
    p.plot_meas_vs_calc(Ptn(two_theta=[1], intensity_meas=[1], intensity_calc=None), 'E', ExptType())
    out = capsys.readouterr().out
    assert 'No calculated data available for experiment E' in out

    # Filtering
    import numpy as np

    p.x_min, p.x_max = 0.5, 1.5
    arr = np.array([0.0, 1.0, 2.0])
    filt = p._filtered_y_array(arr, arr, None, None)
    assert np.allclose(filt, np.array([1.0]))


def test_plotter_routes_to_ascii_plotter(monkeypatch):
    import numpy as np

    import easydiffraction.display.plotters.ascii as ascii_mod
    from easydiffraction.experiments.experiment.enums import BeamModeEnum
    from easydiffraction.experiments.experiment.enums import SampleFormEnum
    from easydiffraction.experiments.experiment.enums import ScatteringTypeEnum
    from easydiffraction.display.plotting import Plotter

    called = {}

    def fake_plot_powder(self, x, y_series, labels, axes_labels, title, height=None):
        called['labels'] = tuple(labels)
        called['axes'] = tuple(axes_labels)
        called['title'] = title

    monkeypatch.setattr(ascii_mod.AsciiPlotter, 'plot_powder', fake_plot_powder)

    class Ptn:
        def __init__(self):
            self.two_theta = np.array([0.0, 1.0])
            self.intensity_meas = np.array([1.0, 2.0])
            self.d_spacing = self.two_theta

    class ExptType:
        def __init__(self):
            self.sample_form = type('SF', (), {'value': SampleFormEnum.POWDER})
            self.scattering_type = type('S', (), {'value': ScatteringTypeEnum.BRAGG})
            self.beam_mode = type('B', (), {'value': BeamModeEnum.CONSTANT_WAVELENGTH})

    p = Plotter()
    p.engine = 'asciichartpy'  # ensure AsciiPlotter
    p.plot_meas(Ptn(), 'E', ExptType())
    assert called['labels'] == ('meas',)
    assert 'Measured data' in called['title']
