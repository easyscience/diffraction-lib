# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import pytest


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
    )
    out = capsys.readouterr().out
    assert 'No measured data available for experiment E' in out
    p._plot_meas_vs_calc_data(
        Expt(Ptn(two_theta=[1], intensity_meas=None, intensity_calc=[1]), ExptType()),
        'E',
    )
    out = capsys.readouterr().out
    assert 'No measured data available for experiment E' in out
    p._plot_meas_vs_calc_data(
        Expt(Ptn(two_theta=[1], intensity_meas=[1], intensity_calc=None), ExptType()),
        'E',
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
    assert df.iloc[1, 1].strip() == '0.167'


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


def test_plot_param_correlations_can_show_diagonal(monkeypatch):
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
        covar = np.array([[1.0, 0.4], [0.4, 1.0]])
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
    p.engine = 'asciichartpy'
    p._set_project(Project())
    p.plot_param_correlations(threshold=0.1, show_diagonal=True)

    df = captured['df']
    assert df.iloc[0, 1].strip() == '1.00'
    assert df.iloc[0, 2] == ''
    assert df.iloc[1, 2].strip() == '1.00'


def test_plot_param_correlations_can_show_full_matrix(monkeypatch):
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
        covar = np.array([[1.0, 0.4], [0.4, 1.0]])
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
    p.engine = 'asciichartpy'
    p._set_project(Project())
    p.plot_param_correlations(threshold=0.1, triangle='full', show_diagonal=False)

    df = captured['df']
    assert df.iloc[0, 1] == ''
    assert df.iloc[0, 2].strip() == '0.40'
    assert df.iloc[1, 1].strip() == '0.40'
    assert df.iloc[1, 2] == ''


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
    assert df.iloc[1, 1].strip() == '0.82'


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
    assert df.iloc[2, 2].strip() == '-0.91'
    assert df.iloc[3, 1] == ''
    assert df.iloc[3, 2] == ''
    assert df.iloc[3, 3].strip() == '-0.89'
    assert df.iloc[4, 1].strip() == '0.82'
    assert df.iloc[4, 2] == ''
    assert df.iloc[4, 3] == ''
    assert df.iloc[4, 4] == ''


def test_plot_param_correlations_threshold_validation():
    from easydiffraction.display.plotting import Plotter

    with pytest.raises(ValueError, match='between 0 and 1'):
        Plotter._filter_correlation_dataframe(object(), threshold=1.1)


def test_plot_param_correlations_triangle_validation():
    import pandas as pd

    from easydiffraction.display.plotting import Plotter

    df = pd.DataFrame([[1.0]])
    with pytest.raises(ValueError, match='lower'):
        Plotter._mask_correlation_triangle(df, triangle='sideways', show_diagonal=False)
