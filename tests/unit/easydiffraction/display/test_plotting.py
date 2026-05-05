# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import re

import pytest


def _strip_markup(text: str) -> str:
    """Remove Rich color markup tags like [red]...[/red]."""
    return re.sub(r'\[(\w+)\](.*?)\[/\1\]', r'\2', text)


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
    with pytest.raises(
        ValueError,
        match=r"Unsupported engine 'nope'\. Supported engines: .*",
    ):
        PlotterFactory.create('nope')


def test_plotter_error_paths_and_filtering(capsys, monkeypatch):
    from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
    from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
    from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum
    from easydiffraction.display.plotting import Plotter
    from easydiffraction.display.plotting import _MeasVsCalcPlotOptions
    from easydiffraction.utils.logging import Logger

    monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)

    class Ptn:
        def __init__(
            self, two_theta=None, intensity_meas=None, intensity_calc=None, d_spacing=None
        ):
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
    p._plot_meas_data(Ptn(two_theta=None, intensity_meas=None), 'E', ExptType())
    out = capsys.readouterr().out
    assert 'No two_theta data available for experiment E' in out

    p._plot_meas_data(Ptn(two_theta=[1], intensity_meas=None), 'E', ExptType())
    out = capsys.readouterr().out
    assert 'No measured data available for experiment E' in out

    p._plot_calc_data(Ptn(two_theta=None, intensity_calc=None), 'E', ExptType())
    out = capsys.readouterr().out
    assert 'No two_theta data available for experiment E' in out

    p._plot_calc_data(Ptn(two_theta=[1], intensity_calc=None), 'E', ExptType())
    out = capsys.readouterr().out
    assert 'No calculated data available for experiment E' in out

    class Expt:
        def __init__(self, pattern, expt_type):
            self.data = pattern
            self.type = expt_type

    p._plot_meas_vs_calc_data(
        Expt(Ptn(two_theta=None, intensity_meas=None, intensity_calc=None), ExptType()),
        'E',
        _MeasVsCalcPlotOptions(),
    )
    out = capsys.readouterr().out
    assert 'No measured data available for experiment E' in out
    p._plot_meas_vs_calc_data(
        Expt(Ptn(two_theta=[1], intensity_meas=None, intensity_calc=[1]), ExptType()),
        'E',
        _MeasVsCalcPlotOptions(),
    )
    out = capsys.readouterr().out
    assert 'No measured data available for experiment E' in out
    p._plot_meas_vs_calc_data(
        Expt(Ptn(two_theta=[1], intensity_meas=[1], intensity_calc=None), ExptType()),
        'E',
        _MeasVsCalcPlotOptions(),
    )
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
    from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
    from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
    from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum
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
    p._plot_meas_data(Ptn(), 'E', ExptType())
    assert called['labels'] == ('meas',)
    assert 'Measured data' in called['title']


def test_extract_bragg_tick_sets_groups_and_filters():
    import numpy as np

    from easydiffraction.display.plotting import Plotter
    from easydiffraction.display.plotting import XAxisType

    class Refln:
        phase_id = np.array(['phase-a', 'phase-a', 'phase-b', 'phase-b'])
        two_theta = np.array([0.5, 1.5, 2.5, 3.5])
        index_h = np.array([1, 2, 3, 4])
        index_k = np.array([0, 1, 1, 2])
        index_l = np.array([1, 0, 2, 1])
        f_squared_calc = np.array([10.0, 20.0, 30.0, 40.0])
        f_calc = np.array([3.0, 4.0, 5.0, 6.0])

    class Experiment:
        refln = Refln()

    tick_sets = Plotter()._extract_bragg_tick_sets(
        experiment=Experiment(),
        expt_name='E1',
        x_axis=XAxisType.TWO_THETA,
        x_min=1.0,
        x_max=3.0,
    )

    assert [tick_set.phase_id for tick_set in tick_sets] == ['phase-a', 'phase-b']
    assert np.allclose(tick_sets[0].x, np.array([1.5]))
    assert np.array_equal(tick_sets[0].h, np.array([2]))
    assert np.array_equal(tick_sets[1].h, np.array([3]))
    assert np.array_equal(tick_sets[1].k, np.array([1]))
    assert np.array_equal(tick_sets[1].ell, np.array([2]))
    assert np.allclose(tick_sets[0].f_squared_calc, np.array([20.0]))
    assert np.allclose(tick_sets[1].f_calc, np.array([5.0]))


def test_extract_bragg_tick_sets_returns_empty_without_category():
    from easydiffraction.display.plotting import Plotter
    from easydiffraction.display.plotting import XAxisType

    class Experiment:
        pass

    tick_sets = Plotter()._extract_bragg_tick_sets(
        experiment=Experiment(),
        expt_name='E1',
        x_axis=XAxisType.TWO_THETA,
        x_min=1.0,
        x_max=3.0,
    )

    assert tick_sets == ()


def test_extract_bragg_tick_sets_uses_derived_d_spacing_for_cwl_ticks():
    import numpy as np

    from easydiffraction.display.plotting import Plotter
    from easydiffraction.display.plotting import XAxisType
    from easydiffraction.utils.utils import twotheta_to_d

    class Refln:
        phase_id = np.array(['phase-a'])
        two_theta = np.array([20.0])
        d_spacing = np.array([999.0])
        index_h = np.array([1])
        index_k = np.array([0])
        index_l = np.array([1])
        f_squared_calc = np.array([10.0])
        f_calc = np.array([3.0])

    class Instrument:
        setup_wavelength = type('Wavelength', (), {'value': 1.0})()

    class Experiment:
        refln = Refln()
        instrument = Instrument()

    tick_sets = Plotter()._extract_bragg_tick_sets(
        experiment=Experiment(),
        expt_name='E1',
        x_axis=XAxisType.D_SPACING,
        x_min=0.1,
        x_max=10.0,
    )

    np.testing.assert_allclose(tick_sets[0].x, twotheta_to_d(np.array([20.0]), 1.0))


def test_plot_meas_vs_calc_routes_powder_bragg_to_composite_backend():
    import numpy as np

    from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
    from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
    from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum
    from easydiffraction.display.plotting import Plotter
    from easydiffraction.display.plotting import _MeasVsCalcPlotOptions

    captured = {}

    class FakeBackend:
        def plot_powder_meas_vs_calc(self, **kwargs):
            captured['powder_meas_vs_calc'] = kwargs['plot_spec']

        def plot_powder(self, **kwargs):
            captured['powder'] = kwargs

    class Pattern:
        two_theta = np.array([0.0, 1.0, 2.0, 3.0])
        d_spacing = two_theta
        intensity_meas = np.array([10.0, 20.0, 30.0, 40.0])
        intensity_bkg = np.array([1.0, 2.0, 3.0, 4.0])
        intensity_calc = np.array([9.0, 18.0, 27.0, 39.0])

    class Refln:
        phase_id = np.array(['phase-a', 'phase-a', 'phase-b'])
        two_theta = np.array([0.5, 1.5, 2.0])
        index_h = np.array([1, 2, 3])
        index_k = np.array([0, 1, 1])
        index_l = np.array([1, 0, 2])
        f_squared_calc = np.array([100.0, 80.0, 60.0])
        f_calc = np.array([10.0, 9.0, 8.0])

    class ExptType:
        sample_form = type('SF', (), {'value': SampleFormEnum.POWDER})()
        scattering_type = type('S', (), {'value': ScatteringTypeEnum.BRAGG})()
        beam_mode = type('B', (), {'value': BeamModeEnum.CONSTANT_WAVELENGTH})()

    class Experiment:
        data = Pattern()
        type = ExptType()
        refln = Refln()

    plotter = Plotter()
    plotter._backend = FakeBackend()
    plotter._plot_meas_vs_calc_data(
        experiment=Experiment(),
        expt_name='E1',
        plot_options=_MeasVsCalcPlotOptions(x_min=1.0, x_max=2.0),
    )

    assert 'powder_meas_vs_calc' in captured
    assert 'powder' not in captured
    call = captured['powder_meas_vs_calc']
    assert np.allclose(call.x, np.array([1.0, 2.0]))
    assert np.allclose(call.y_meas, np.array([20.0, 30.0]))
    assert np.allclose(call.y_bkg, np.array([2.0, 3.0]))
    assert np.allclose(call.y_calc, np.array([18.0, 27.0]))
    assert np.allclose(call.y_resid, np.array([2.0, 3.0]))
    assert [tick_set.phase_id for tick_set in call.bragg_tick_sets] == [
        'phase-a',
        'phase-b',
    ]
    assert np.allclose(call.bragg_tick_sets[0].x, np.array([1.5]))
    assert np.allclose(call.bragg_tick_sets[1].x, np.array([2.0]))


def test_plot_meas_vs_calc_extracts_bragg_ticks_with_default_bounds():
    import numpy as np

    from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
    from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
    from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum
    from easydiffraction.display.plotting import Plotter
    from easydiffraction.display.plotting import _MeasVsCalcPlotOptions

    captured = {}

    class FakeBackend:
        def plot_powder_meas_vs_calc(self, **kwargs):
            captured['powder_meas_vs_calc'] = kwargs['plot_spec']

    class Pattern:
        time_of_flight = np.array([10.0, 11.0, 12.0])
        intensity_meas = np.array([100.0, 110.0, 105.0])
        intensity_calc = np.array([99.0, 108.0, 104.0])

    class Refln:
        phase_id = np.array(['phase-a'])
        time_of_flight = np.array([11.0])
        index_h = np.array([1])
        index_k = np.array([0])
        index_l = np.array([1])
        f_squared_calc = np.array([50.0])
        f_calc = np.array([7.0])

    class ExptType:
        sample_form = type('SF', (), {'value': SampleFormEnum.POWDER})()
        scattering_type = type('S', (), {'value': ScatteringTypeEnum.BRAGG})()
        beam_mode = type('B', (), {'value': BeamModeEnum.TIME_OF_FLIGHT})()

    class Experiment:
        data = Pattern()
        type = ExptType()
        refln = Refln()

    plotter = Plotter()
    plotter._backend = FakeBackend()
    plotter._plot_meas_vs_calc_data(
        experiment=Experiment(),
        expt_name='E1',
        plot_options=_MeasVsCalcPlotOptions(),
    )

    call = captured['powder_meas_vs_calc']
    assert np.allclose(call.x, np.array([10.0, 11.0, 12.0]))
    assert [tick_set.phase_id for tick_set in call.bragg_tick_sets] == ['phase-a']
    assert np.allclose(call.bragg_tick_sets[0].x, np.array([11.0]))


def test_plot_meas_vs_calc_groups_numeric_bragg_structure_ids():
    import numpy as np

    from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
    from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
    from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum
    from easydiffraction.display.plotting import Plotter
    from easydiffraction.display.plotting import _MeasVsCalcPlotOptions

    captured = {}

    class FakeBackend:
        def plot_powder_meas_vs_calc(self, **kwargs):
            captured['powder_meas_vs_calc'] = kwargs['plot_spec']

    class Pattern:
        time_of_flight = np.array([10.0, 11.0, 12.0])
        intensity_meas = np.array([100.0, 110.0, 105.0])
        intensity_calc = np.array([99.0, 108.0, 104.0])

    class Refln:
        phase_id = np.array([1, 1, 2])
        time_of_flight = np.array([10.0, 11.0, 12.0])
        index_h = np.array([1, 2, 3])
        index_k = np.array([0, 1, 1])
        index_l = np.array([1, 0, 2])
        f_squared_calc = np.array([50.0, 40.0, 30.0])
        f_calc = np.array([7.0, 6.0, 5.0])

    class ExptType:
        sample_form = type('SF', (), {'value': SampleFormEnum.POWDER})()
        scattering_type = type('S', (), {'value': ScatteringTypeEnum.BRAGG})()
        beam_mode = type('B', (), {'value': BeamModeEnum.TIME_OF_FLIGHT})()

    class Experiment:
        data = Pattern()
        type = ExptType()
        refln = Refln()

    plotter = Plotter()
    plotter._backend = FakeBackend()
    plotter._plot_meas_vs_calc_data(
        experiment=Experiment(),
        expt_name='E1',
        plot_options=_MeasVsCalcPlotOptions(),
    )

    call = captured['powder_meas_vs_calc']
    assert [tick_set.phase_id for tick_set in call.bragg_tick_sets] == ['1', '2']
    assert np.allclose(call.bragg_tick_sets[0].x, np.array([10.0, 11.0]))
    assert np.allclose(call.bragg_tick_sets[1].x, np.array([12.0]))


def test_plot_meas_vs_calc_skips_bragg_ticks_when_filtered_pattern_is_empty():
    import numpy as np

    from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
    from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
    from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum
    from easydiffraction.display.plotting import Plotter
    from easydiffraction.display.plotting import _MeasVsCalcPlotOptions

    captured = {}

    class FakeBackend:
        def plot_powder_meas_vs_calc(self, **kwargs):
            captured['powder_meas_vs_calc'] = kwargs['plot_spec']

    class Pattern:
        time_of_flight = np.array([10.0, 11.0, 12.0])
        intensity_meas = np.array([100.0, 110.0, 105.0])
        intensity_calc = np.array([99.0, 108.0, 104.0])

    class Refln:
        phase_id = np.array(['phase-a'])
        time_of_flight = np.array([8.0])
        index_h = np.array([1])
        index_k = np.array([0])
        index_l = np.array([1])
        f_squared_calc = np.array([50.0])
        f_calc = np.array([7.0])

    class ExptType:
        sample_form = type('SF', (), {'value': SampleFormEnum.POWDER})()
        scattering_type = type('S', (), {'value': ScatteringTypeEnum.BRAGG})()
        beam_mode = type('B', (), {'value': BeamModeEnum.TIME_OF_FLIGHT})()

    class Experiment:
        data = Pattern()
        type = ExptType()
        refln = Refln()

    plotter = Plotter()
    plotter._backend = FakeBackend()
    plotter._plot_meas_vs_calc_data(
        experiment=Experiment(),
        expt_name='E1',
        plot_options=_MeasVsCalcPlotOptions(x_min=7.0, x_max=9.0),
    )

    call = captured['powder_meas_vs_calc']
    assert call.x.size == 0
    assert call.bragg_tick_sets == ()


def test_plot_meas_vs_calc_does_not_accept_layout_fraction_overrides():
    from easydiffraction.display.plotting import Plotter

    plotter = Plotter()

    with pytest.raises(TypeError, match='residual_height_fraction'):
        plotter.plot_meas_vs_calc('E1', residual_height_fraction=0.20)

    with pytest.raises(TypeError, match='bragg_peaks_height_fraction'):
        plotter.plot_meas_vs_calc('E1', bragg_peaks_height_fraction=0.20)


def test_plot_meas_vs_calc_keeps_single_crystal_routing():
    import numpy as np

    from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
    from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
    from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum
    from easydiffraction.display.plotting import Plotter
    from easydiffraction.display.plotting import _MeasVsCalcPlotOptions

    captured = {}

    class FakeBackend:
        def plot_single_crystal(self, **kwargs):
            captured['single_crystal'] = kwargs

        def plot_powder_meas_vs_calc(self, **kwargs):
            captured['powder_meas_vs_calc'] = kwargs['plot_spec']

    class Pattern:
        intensity_calc = np.array([1.0, 2.0, 3.0])
        intensity_meas = np.array([1.1, 1.9, 3.2])
        intensity_meas_su = np.array([0.1, 0.1, 0.1])

    class ExptType:
        sample_form = type('SF', (), {'value': SampleFormEnum.SINGLE_CRYSTAL})()
        scattering_type = type('S', (), {'value': ScatteringTypeEnum.BRAGG})()
        beam_mode = type('B', (), {'value': BeamModeEnum.CONSTANT_WAVELENGTH})()

    class Experiment:
        data = Pattern()
        type = ExptType()

    plotter = Plotter()
    plotter._backend = FakeBackend()
    plotter._plot_meas_vs_calc_data(
        experiment=Experiment(),
        expt_name='E1',
        plot_options=_MeasVsCalcPlotOptions(),
    )

    assert 'single_crystal' in captured
    assert 'powder_meas_vs_calc' not in captured
    assert np.allclose(captured['single_crystal']['x_calc'], np.array([1.0, 2.0, 3.0]))
    assert np.allclose(captured['single_crystal']['y_meas'], np.array([1.1, 1.9, 3.2]))
    assert np.allclose(captured['single_crystal']['y_meas_su'], np.array([0.1, 0.1, 0.1]))


def test_plot_meas_vs_calc_keeps_default_residual_off_for_line_paths():
    import numpy as np

    from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
    from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
    from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum
    from easydiffraction.display.plotting import Plotter
    from easydiffraction.display.plotting import _MeasVsCalcPlotOptions

    captured = {}

    class FakeBackend:
        def plot_powder(self, **kwargs):
            captured['powder'] = kwargs

        def plot_single_crystal(self, **kwargs):
            captured['single_crystal'] = kwargs

        def plot_powder_meas_vs_calc(self, **kwargs):
            captured['powder_meas_vs_calc'] = kwargs['plot_spec']

    class Pattern:
        d_spacing = np.array([1.0, 2.0, 3.0])
        intensity_meas = np.array([5.0, 6.0, 7.0])
        intensity_calc = np.array([4.5, 6.1, 7.2])

    class ExptType:
        sample_form = type('SF', (), {'value': SampleFormEnum.SINGLE_CRYSTAL})()
        scattering_type = type('S', (), {'value': ScatteringTypeEnum.BRAGG})()
        beam_mode = type('B', (), {'value': BeamModeEnum.CONSTANT_WAVELENGTH})()

    class Experiment:
        data = Pattern()
        type = ExptType()

    plotter = Plotter()
    plotter._backend = FakeBackend()
    plotter._plot_meas_vs_calc_data(
        experiment=Experiment(),
        expt_name='E1',
        plot_options=_MeasVsCalcPlotOptions(x='d_spacing'),
    )

    assert 'powder' in captured
    assert 'single_crystal' not in captured
    assert 'powder_meas_vs_calc' not in captured
    assert captured['powder']['labels'] == ['meas', 'calc']


def test_plot_param_correlations_renders_ascii_table(monkeypatch):
    import numpy as np

    from easydiffraction.display.plotting import Plotter
    from easydiffraction.display.tables import TableRenderer

    captured = {}

    class FakeTabler:
        def render(self, df):
            captured['df'] = df

    monkeypatch.setattr(TableRenderer, 'get', staticmethod(lambda: FakeTabler()))

    class Param:
        def __init__(self, uid, unique_name):
            self._minimizer_uid = uid
            self.unique_name = unique_name

    class RawResult:
        covar = np.array([[4.0, 1.0], [1.0, 9.0]])
        var_names = ['p1', 'p2']

    class FitResults:
        engine_result = RawResult()
        parameters = [
            Param('p1', 'phase.cell.length_a'),
            Param('p2', 'phase.cell.length_b'),
        ]

    class Analysis:
        fit_results = FitResults()

    class Project:
        analysis = Analysis()

    p = Plotter()
    p.engine = 'asciichartpy'
    p._set_project(Project())
    p.plot_param_correlations(threshold=0.1, precision=3)

    df = captured['df']
    assert [column.strip() for column in df.columns.get_level_values(0)] == [
        'parameter',
        '1',
    ]
    assert list(df.columns.get_level_values(1)) == ['left', 'right']
    assert list(df.index) == [0, 1]
    assert df.iloc[0, 0] == 'phase.cell.length_a'
    assert df.iloc[0, 1] == ''
    assert df.iloc[1, 0] == 'phase.cell.length_b'
    assert _strip_markup(df.iloc[1, 1]).strip() == '0.167'


def test_plot_param_correlations_renders_plotly_heatmap(monkeypatch):
    import numpy as np

    import easydiffraction.display.plotters.plotly as plotly_mod
    from easydiffraction.display.plotting import Plotter

    captured = {}

    def fake_show_figure(self, fig):
        captured['fig'] = fig

    monkeypatch.setattr(plotly_mod.PlotlyPlotter, '_show_figure', fake_show_figure)

    class Param:
        def __init__(self, uid, unique_name):
            self._minimizer_uid = uid
            self.unique_name = unique_name

    class RawResult:
        covar = np.array([[1.0, -0.5], [-0.5, 1.0]])
        var_names = ['p1', 'p2']

    class FitResults:
        engine_result = RawResult()
        parameters = [
            Param('p1', 'phase.scale'),
            Param('p2', 'phase.cell.length_c'),
        ]

    class Analysis:
        fit_results = FitResults()

    class Project:
        analysis = Analysis()

    p = Plotter()
    p.engine = 'plotly'
    p._set_project(Project())
    p.plot_param_correlations(threshold=0.1)

    fig = captured['fig']
    assert len(fig.data) == 2
    assert fig.data[0].type == 'heatmap'
    assert list(fig.data[0].x) == [0.0, 1.0]
    assert list(fig.data[0].y) == [0.0, 1.0]
    assert fig.data[0].xgap in (None, 0)
    assert fig.data[0].ygap in (None, 0)
    assert fig.data[0].colorbar.lenmode == 'fraction'
    assert fig.data[0].colorbar.len == 1.0
    assert fig.data[0].colorbar.title.text == ''
    assert fig.data[0].hovertemplate == 'x: %{x}<br>y: %{y}<br>corr: %{z:.2f}<extra></extra>'
    assert pytest.approx(fig.data[0].z[0][0], rel=1e-9) == -0.5
    assert fig.data[1].type == 'scatter'
    assert fig.data[1].mode == 'text'
    assert list(fig.data[1].x) == [0.5]
    assert list(fig.data[1].y) == [0.5]
    assert list(fig.data[1].text) == ['-0.50']
    assert fig.data[1].textposition == 'middle center'
    assert fig.data[1].hoverinfo == 'skip'
    assert fig.layout.xaxis.side == 'bottom'
    assert fig.layout.xaxis.tickangle < 0
    assert list(fig.layout.xaxis.tickvals) == [0.5]
    assert list(fig.layout.xaxis.ticktext) == ['phase.scale']
    assert fig.layout.xaxis.showline is False
    assert fig.layout.xaxis.mirror is False
    assert fig.layout.xaxis.layer == 'above traces'
    assert list(fig.layout.yaxis.tickvals) == [0.5]
    assert list(fig.layout.yaxis.ticktext) == ['phase.cell.length_c']
    assert fig.layout.yaxis.showline is False
    assert fig.layout.yaxis.mirror is False
    assert fig.layout.yaxis.layer == 'above traces'
    assert fig.layout.yaxis.ticklabelstandoff == 8
    assert len(fig.layout.shapes) == 1
    assert fig.layout.shapes[-1].type == 'rect'
    assert fig.layout.shapes[-1].xref == 'paper'
    assert fig.layout.shapes[-1].yref == 'paper'


def test_plot_param_correlations_plotly_labels_respect_threshold(monkeypatch):
    import easydiffraction.display.plotters.plotly as plotly_mod
    from easydiffraction.display.plotting import Plotter

    captured = {}

    def fake_show_figure(self, fig):
        captured['fig'] = fig

    monkeypatch.setattr(plotly_mod.PlotlyPlotter, '_show_figure', fake_show_figure)

    class Param:
        def __init__(self, uid, unique_name):
            self._minimizer_uid = uid
            self.unique_name = unique_name

    class RawResult:
        covar = None
        var_names = ['p1', 'p2', 'p3', 'p4', 'p5']

        class ParamResult:
            def __init__(self, correl):
                self.correl = correl

        params = {
            'p1': ParamResult({'p4': 0.02, 'p5': 0.82}),
            'p2': ParamResult({'p3': -0.91, 'p4': 0.83, 'p5': 0.02}),
            'p3': ParamResult({'p2': -0.91, 'p4': -0.89, 'p5': -0.01}),
            'p4': ParamResult({'p1': 0.02, 'p2': 0.83, 'p3': -0.89, 'p5': 0.01}),
            'p5': ParamResult({'p1': 0.82, 'p2': 0.02, 'p3': -0.01, 'p4': 0.01}),
        }

    class FitResults:
        engine_result = RawResult()
        parameters = [
            Param('p1', 'lbco.cell.length_a'),
            Param('p2', 'hrpt.peak.broad_gauss_u'),
            Param('p3', 'hrpt.peak.broad_gauss_v'),
            Param('p4', 'hrpt.peak.broad_gauss_w'),
            Param('p5', 'hrpt.instrument.twotheta_offset'),
        ]

    class Analysis:
        fit_results = FitResults()

    class Project:
        analysis = Analysis()

    p = Plotter()
    p.engine = 'plotly'
    p._set_project(Project())
    p.plot_param_correlations()

    fig = captured['fig']
    assert len(fig.data) == 2
    assert fig.data[0].type == 'heatmap'
    assert fig.data[1].type == 'scatter'
    assert fig.data[1].mode == 'text'
    assert list(fig.data[1].text) == ['-0.91', '0.83', '-0.89', '0.82']


def test_plot_param_correlations_filters_by_default_threshold(monkeypatch):
    from easydiffraction.display.plotting import Plotter
    from easydiffraction.display.tables import TableRenderer

    captured = {}

    class FakeTabler:
        def render(self, df):
            captured['df'] = df

    monkeypatch.setattr(TableRenderer, 'get', staticmethod(lambda: FakeTabler()))

    class Param:
        def __init__(self, uid, unique_name):
            self._minimizer_uid = uid
            self.unique_name = unique_name

    class RawResult:
        covar = None
        var_names = ['p1', 'p2', 'p3']

        class ParamResult:
            def __init__(self, correl):
                self.correl = correl

        params = {
            'p1': ParamResult({'p2': 0.82}),
            'p2': ParamResult({'p1': 0.82}),
            'p3': ParamResult({'p1': 0.25}),
        }

    class FitResults:
        engine_result = RawResult()
        parameters = [
            Param('p1', 'phase.scale'),
            Param('p2', 'phase.cell.length_a'),
            Param('p3', 'phase.background'),
        ]

    class Analysis:
        fit_results = FitResults()

    class Project:
        analysis = Analysis()

    p = Plotter()
    p.engine = 'asciichartpy'
    p._set_project(Project())
    p.plot_param_correlations()

    df = captured['df']
    assert [column.strip() for column in df.columns.get_level_values(0)] == [
        'parameter',
        '1',
    ]
    assert list(df.index) == [0, 1]
    assert df.iloc[0, 0] == 'phase.scale'
    assert df.iloc[0, 1] == ''
    assert df.iloc[1, 0] == 'phase.cell.length_a'
    assert _strip_markup(df.iloc[1, 1]).strip() == '0.82'


def test_plot_param_correlations_hides_subthreshold_table_values(monkeypatch):
    from easydiffraction.display.plotting import Plotter
    from easydiffraction.display.tables import TableRenderer

    captured = {}

    class FakeTabler:
        def render(self, df):
            captured['df'] = df

    monkeypatch.setattr(TableRenderer, 'get', staticmethod(lambda: FakeTabler()))

    class Param:
        def __init__(self, uid, unique_name):
            self._minimizer_uid = uid
            self.unique_name = unique_name

    class RawResult:
        covar = None
        var_names = ['p1', 'p2', 'p3', 'p4', 'p5']

        class ParamResult:
            def __init__(self, correl):
                self.correl = correl

        params = {
            'p1': ParamResult({'p4': 0.02, 'p5': 0.82}),
            'p2': ParamResult({'p3': -0.91, 'p5': 0.02}),
            'p3': ParamResult({'p2': -0.91, 'p4': -0.89, 'p5': -0.01}),
            'p4': ParamResult({'p1': 0.02, 'p3': -0.89, 'p5': 0.01}),
            'p5': ParamResult({'p1': 0.82, 'p2': 0.02, 'p3': -0.01, 'p4': 0.01}),
        }

    class FitResults:
        engine_result = RawResult()
        parameters = [
            Param('p1', 'lbco.cell.length_a'),
            Param('p2', 'hrpt.peak.broad_gauss_u'),
            Param('p3', 'hrpt.peak.broad_gauss_v'),
            Param('p4', 'hrpt.peak.broad_gauss_w'),
            Param('p5', 'hrpt.instrument.twotheta_offset'),
        ]

    class Analysis:
        fit_results = FitResults()

    class Project:
        analysis = Analysis()

    p = Plotter()
    p.engine = 'asciichartpy'
    p._set_project(Project())
    p.plot_param_correlations()

    df = captured['df']
    assert [column.strip() for column in df.columns.get_level_values(0)] == [
        'parameter',
        '1',
        '2',
        '3',
        '4',
    ]
    assert list(df.index) == [0, 1, 2, 3, 4]
    assert df.iloc[0, 1] == ''
    assert df.iloc[1, 1] == ''
    assert df.iloc[2, 1] == ''
    assert _strip_markup(df.iloc[2, 2]).strip() == '-0.91'
    assert df.iloc[3, 1] == ''
    assert df.iloc[3, 2] == ''
    assert _strip_markup(df.iloc[3, 3]).strip() == '-0.89'
    assert _strip_markup(df.iloc[4, 1]).strip() == '0.82'
    assert df.iloc[4, 2] == ''
    assert df.iloc[4, 3] == ''
    assert df.iloc[4, 4] == ''


def test_plot_param_correlations_threshold_validation():
    from easydiffraction.display.plotting import Plotter

    with pytest.raises(ValueError, match='between 0 and 1'):
        Plotter._filter_correlation_dataframe(object(), threshold=1.1)
