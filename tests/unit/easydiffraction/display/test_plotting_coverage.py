# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Additional unit tests for display/plotting.py to cover patch gaps."""

import numpy as np
import pytest

# ------------------------------------------------------------------
# PlotterEngineEnum
# ------------------------------------------------------------------


class TestPlotterEngineEnum:
    def test_default_returns_ascii_outside_jupyter(self, monkeypatch):
        import easydiffraction.display.plotting as mod

        monkeypatch.setattr(mod, 'in_jupyter', lambda: False)
        result = mod.PlotterEngineEnum.default()
        assert result is mod.PlotterEngineEnum.ASCII

    def test_default_returns_plotly_in_jupyter(self, monkeypatch):
        import easydiffraction.display.plotting as mod

        monkeypatch.setattr(mod, 'in_jupyter', lambda: True)
        result = mod.PlotterEngineEnum.default()
        assert result is mod.PlotterEngineEnum.PLOTLY

    def test_description_ascii(self):
        from easydiffraction.display.plotting import PlotterEngineEnum

        desc = PlotterEngineEnum.ASCII.description()
        assert 'ASCII' in desc or 'Console' in desc

    def test_description_plotly(self):
        from easydiffraction.display.plotting import PlotterEngineEnum

        desc = PlotterEngineEnum.PLOTLY.description()
        assert 'Interactive' in desc or 'browser' in desc

    def test_description_unknown_returns_empty(self):
        """Cover the fallback return '' branch for an unrecognised member."""
        from easydiffraction.display.plotting import PlotterEngineEnum

        # Both known members should return non-empty descriptions
        for member in PlotterEngineEnum:
            assert isinstance(member.description(), str)


# ------------------------------------------------------------------
# Plotter property setters
# ------------------------------------------------------------------


class TestPlotterProperties:
    def test_x_min_setter_with_value(self):
        from easydiffraction.display.plotting import Plotter

        p = Plotter()
        p.x_min = 10.0
        assert p.x_min == 10.0

    def test_x_min_setter_with_none_resets_default(self):
        from easydiffraction.display.plotters.base import DEFAULT_MIN
        from easydiffraction.display.plotting import Plotter

        p = Plotter()
        p.x_min = 42.0
        p.x_min = None
        assert p.x_min == DEFAULT_MIN

    def test_x_max_setter_with_value(self):
        from easydiffraction.display.plotting import Plotter

        p = Plotter()
        p.x_max = 100.0
        assert p.x_max == 100.0

    def test_x_max_setter_with_none_resets_default(self):
        from easydiffraction.display.plotters.base import DEFAULT_MAX
        from easydiffraction.display.plotting import Plotter

        p = Plotter()
        p.x_max = 42.0
        p.x_max = None
        assert p.x_max == DEFAULT_MAX

    def test_height_setter_with_value(self):
        from easydiffraction.display.plotting import Plotter

        p = Plotter()
        p.height = 50
        assert p.height == 50
        assert p._composite_plot_height() == 50

    def test_height_setter_with_none_resets_default(self):
        from easydiffraction.display.plotters.base import DEFAULT_HEIGHT
        from easydiffraction.display.plotting import Plotter

        p = Plotter()
        p.height = 99
        p.height = None
        assert p.height == DEFAULT_HEIGHT
        assert p._composite_plot_height() is None

    def test_default_height_uses_backend_composite_default(self):
        from easydiffraction.display.plotters.base import DEFAULT_HEIGHT
        from easydiffraction.display.plotting import Plotter

        p = Plotter()
        assert p.height == DEFAULT_HEIGHT
        assert p._composite_plot_height() is None


# ------------------------------------------------------------------
# Plotter._set_project / _update_project_categories
# ------------------------------------------------------------------


class TestPlotterProjectWiring:
    def test_set_project_stores_reference(self):
        from easydiffraction.display.plotting import Plotter

        p = Plotter()
        sentinel = object()
        p._set_project(sentinel)
        assert p._project is sentinel

    def test_update_project_categories(self):
        """Exercise _update_project_categories with stub objects."""
        from easydiffraction.display.plotting import Plotter

        called = []

        class FakeStructure:
            def _update_categories(self):
                called.append('struct')

        class FakeExperiment:
            def _update_categories(self):
                called.append('expt')

        class FakeAnalysis:
            def _update_categories(self):
                called.append('analysis')

        class FakeProject:
            structures = [FakeStructure()]
            analysis = FakeAnalysis()
            experiments = {'E1': FakeExperiment()}

        p = Plotter()
        p._set_project(FakeProject())
        p._update_project_categories('E1')
        assert 'struct' in called
        assert 'analysis' in called
        assert 'expt' in called


# ------------------------------------------------------------------
# Plotter._resolve_x_axis
# ------------------------------------------------------------------


class TestResolveXAxis:
    def test_auto_detect_from_beam_mode(self):
        from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
        from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
        from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum
        from easydiffraction.display.plotting import Plotter

        class ExptType:
            sample_form = type('SF', (), {'value': SampleFormEnum.POWDER})()
            scattering_type = type('S', (), {'value': ScatteringTypeEnum.BRAGG})()
            beam_mode = type('B', (), {'value': BeamModeEnum.CONSTANT_WAVELENGTH})()

        x_axis, _x_name, _sf, _st, _bm = Plotter._resolve_x_axis(ExptType(), None)
        assert x_axis.value == 'two_theta'

    def test_explicit_x_passed_through(self):
        from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
        from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
        from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum
        from easydiffraction.display.plotting import Plotter

        class ExptType:
            sample_form = type('SF', (), {'value': SampleFormEnum.POWDER})()
            scattering_type = type('S', (), {'value': ScatteringTypeEnum.BRAGG})()
            beam_mode = type('B', (), {'value': BeamModeEnum.CONSTANT_WAVELENGTH})()

        x_axis, _, _, _, _ = Plotter._resolve_x_axis(ExptType(), 'd_spacing')
        assert x_axis == 'd_spacing'


# ------------------------------------------------------------------
# Plotter._resolve_diffrn_descriptor
# ------------------------------------------------------------------


class TestResolveDiffrnDescriptor:
    def test_none_name_returns_none(self):
        from easydiffraction.display.plotting import Plotter

        assert Plotter._resolve_diffrn_descriptor(object(), None) is None

    def test_ambient_temperature(self):
        from easydiffraction.display.plotting import Plotter

        sentinel = object()

        class Diffrn:
            ambient_temperature = sentinel

        assert Plotter._resolve_diffrn_descriptor(Diffrn(), 'ambient_temperature') is sentinel

    def test_ambient_pressure(self):
        from easydiffraction.display.plotting import Plotter

        sentinel = object()

        class Diffrn:
            ambient_pressure = sentinel

        assert Plotter._resolve_diffrn_descriptor(Diffrn(), 'ambient_pressure') is sentinel

    def test_ambient_magnetic_field(self):
        from easydiffraction.display.plotting import Plotter

        sentinel = object()

        class Diffrn:
            ambient_magnetic_field = sentinel

        assert Plotter._resolve_diffrn_descriptor(Diffrn(), 'ambient_magnetic_field') is sentinel

    def test_ambient_electric_field(self):
        from easydiffraction.display.plotting import Plotter

        sentinel = object()

        class Diffrn:
            ambient_electric_field = sentinel

        assert Plotter._resolve_diffrn_descriptor(Diffrn(), 'ambient_electric_field') is sentinel

    def test_unknown_name_returns_none(self):
        from easydiffraction.display.plotting import Plotter

        assert Plotter._resolve_diffrn_descriptor(object(), 'unknown_field') is None


# ------------------------------------------------------------------
# Plotter._auto_x_range_for_ascii
# ------------------------------------------------------------------


class TestAutoXRangeForAscii:
    def test_narrows_range_for_ascii(self, monkeypatch):
        from easydiffraction.display.plotters.ascii import AsciiPlotter
        from easydiffraction.display.plotting import Plotter

        p = Plotter()
        p.engine = 'asciichartpy'
        monkeypatch.setattr(AsciiPlotter, '_chart_point_count', lambda: 80)

        class Ptn:
            intensity_meas = np.zeros(200)

        Ptn.intensity_meas[100] = 10.0  # max at index 100
        x_array = np.arange(200, dtype=float)
        x_min, x_max = p._auto_x_range_for_ascii(Ptn(), x_array, None, None)
        assert x_min == 60.0
        assert x_max == 139.0

    def test_keeps_full_range_when_series_is_within_crop_threshold(self, monkeypatch):
        from easydiffraction.display.plotters.ascii import AsciiPlotter
        from easydiffraction.display.plotting import Plotter

        p = Plotter()
        p.engine = 'asciichartpy'
        monkeypatch.setattr(AsciiPlotter, '_chart_point_count', lambda: 80)

        class Ptn:
            intensity_meas = np.zeros(120)

        Ptn.intensity_meas[60] = 10.0
        x_array = np.arange(120, dtype=float)
        x_min, x_max = p._auto_x_range_for_ascii(Ptn(), x_array, None, None)
        assert x_min is None
        assert x_max is None

    def test_keeps_explicit_partial_limit_for_ascii(self, monkeypatch):
        from easydiffraction.display.plotters.ascii import AsciiPlotter
        from easydiffraction.display.plotting import Plotter

        p = Plotter()
        p.engine = 'asciichartpy'
        monkeypatch.setattr(AsciiPlotter, '_chart_point_count', lambda: 80)

        class Ptn:
            intensity_meas = np.zeros(200)

        Ptn.intensity_meas[100] = 10.0
        x_array = np.arange(200, dtype=float)
        x_min, x_max = p._auto_x_range_for_ascii(Ptn(), x_array, 20.0, None)
        assert x_min == 20.0
        assert x_max is None

    def test_no_narrowing_when_limits_provided(self):
        from easydiffraction.display.plotting import Plotter

        p = Plotter()
        p.engine = 'asciichartpy'

        class Ptn:
            intensity_meas = np.zeros(200)

        x_array = np.arange(200, dtype=float)
        x_min, x_max = p._auto_x_range_for_ascii(Ptn(), x_array, 0.0, 199.0)
        assert x_min == 0.0
        assert x_max == 199.0

    def test_no_narrowing_for_plotly_engine(self):
        from easydiffraction.display.plotting import Plotter

        p = Plotter()
        p.engine = 'plotly'

        class Ptn:
            intensity_meas = np.zeros(200)

        x_array = np.arange(200, dtype=float)
        x_min, x_max = p._auto_x_range_for_ascii(Ptn(), x_array, None, None)
        assert x_min is None
        assert x_max is None


# ------------------------------------------------------------------
# Plotter._plot_param_series_from_csv
# ------------------------------------------------------------------


class TestPlotParamSeriesFromCsv:
    def test_csv_param_not_found_logs_warning(self, tmp_path, monkeypatch, capsys):
        from easydiffraction.display.plotting import Plotter
        from easydiffraction.utils.logging import Logger

        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)

        csv = tmp_path / 'results.csv'
        csv.write_text('col_a,col_b\n1.0,2.0\n')

        p = Plotter()

        class Desc:
            unique_name = 'no_such_col'
            description = 'test'
            units = 'A'

        p._plot_param_series_from_csv(str(csv), 'no_such_col', Desc(), None)
        out = capsys.readouterr().out
        assert 'not found in CSV' in out

    def test_csv_plots_with_versus_descriptor(self, tmp_path, monkeypatch):
        from easydiffraction.display.plotting import Plotter

        csv = tmp_path / 'results.csv'
        csv.write_text(
            'my_param,my_param.uncertainty,diffrn.ambient_temperature\n1.0,0.1,300\n2.0,0.2,400\n'
        )

        plot_calls = []

        class FakeBackend:
            def plot_scatter(self, **kwargs):
                plot_calls.append(kwargs)

        p = Plotter()
        p._backend = FakeBackend()

        class ParamDesc:
            unique_name = 'my_param'
            description = 'A param'
            units = 'Å'

        p._plot_param_series_from_csv(
            str(csv),
            'my_param',
            ParamDesc(),
            'diffrn.ambient_temperature',
        )
        assert len(plot_calls) == 1
        assert plot_calls[0]['x'] == [300.0, 400.0]
        assert plot_calls[0]['y'] == [1.0, 2.0]

    def test_csv_plots_without_versus(self, tmp_path, monkeypatch):
        from easydiffraction.display.plotting import Plotter

        csv = tmp_path / 'results.csv'
        csv.write_text('my_param,my_param.uncertainty\n1.0,0.1\n2.0,0.2\n')

        plot_calls = []

        class FakeBackend:
            def plot_scatter(self, **kwargs):
                plot_calls.append(kwargs)

        p = Plotter()
        p._backend = FakeBackend()

        class ParamDesc:
            unique_name = 'my_param'
            description = 'A param'
            units = ''

        p._plot_param_series_from_csv(str(csv), 'my_param', ParamDesc(), None)
        assert len(plot_calls) == 1
        assert plot_calls[0]['x'] == [1, 2]
        assert 'Experiment No.' in plot_calls[0]['axes_labels']


# ------------------------------------------------------------------
# Plotter.plot_param_series_from_snapshots (public method)
# ------------------------------------------------------------------


class TestPlotParamSeriesFromSnapshots:
    def test_snapshot_plot(self):
        from easydiffraction.display.plotting import Plotter

        plot_calls = []

        class FakeBackend:
            def plot_scatter(self, **kwargs):
                plot_calls.append(kwargs)

        class Diffrn:
            ambient_temperature = type(
                'T', (), {'value': 300, 'description': 'Temp', 'name': 'ambient_temperature'}
            )()

        class Expt:
            diffrn = Diffrn()

        p = Plotter()
        p._backend = FakeBackend()
        experiments = {'expt1': Expt()}
        snapshots = {
            'expt1': {
                'param_a': {'value': 1.23, 'uncertainty': 0.01, 'units': 'Å'},
            },
        }
        p.plot_param_series_from_snapshots(
            'param_a', 'diffrn.ambient_temperature', experiments, snapshots
        )
        assert len(plot_calls) == 1
        assert plot_calls[0]['y'] == [1.23]
        assert plot_calls[0]['x'] == [300]

    def test_snapshot_plot_no_versus(self):
        from easydiffraction.display.plotting import Plotter

        plot_calls = []

        class FakeBackend:
            def plot_scatter(self, **kwargs):
                plot_calls.append(kwargs)

        class Diffrn:
            pass

        class Expt:
            diffrn = Diffrn()

        p = Plotter()
        p._backend = FakeBackend()
        experiments = {'expt1': Expt()}
        snapshots = {
            'expt1': {
                'param_a': {'value': 2.0, 'uncertainty': 0.05, 'units': 'Å'},
            },
        }
        p.plot_param_series_from_snapshots('param_a', None, experiments, snapshots)
        assert len(plot_calls) == 1
        assert plot_calls[0]['x'] == [1]  # fallback to index
        assert 'Experiment No.' in plot_calls[0]['axes_labels']


# ------------------------------------------------------------------
# Plotter public methods (plot_meas, plot_calc, plot_meas_vs_calc)
# ------------------------------------------------------------------


class TestPlotterPublicMethods:
    def _make_plotter_with_project(self, monkeypatch):
        from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
        from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
        from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum
        from easydiffraction.display.plotting import Plotter

        class ExptType:
            sample_form = type('SF', (), {'value': SampleFormEnum.POWDER})()
            scattering_type = type('S', (), {'value': ScatteringTypeEnum.BRAGG})()
            beam_mode = type('B', (), {'value': BeamModeEnum.CONSTANT_WAVELENGTH})()

        class Data:
            two_theta = np.array([0.0, 1.0, 2.0])
            d_spacing = two_theta
            intensity_meas = np.array([10.0, 20.0, 10.0])
            intensity_calc = np.array([11.0, 19.0, 10.5])
            intensity_meas_su = np.array([0.5, 0.5, 0.5])

        class Expt:
            data = Data()
            type = ExptType()

            def _update_categories(self):
                pass

        class FakeStructure:
            def _update_categories(self):
                pass

        class FakeAnalysis:
            def _update_categories(self):
                pass

        class FakeProject:
            structures = [FakeStructure()]
            analysis = FakeAnalysis()
            experiments = {'E1': Expt()}

        calls = []

        class FakeBackend:
            def plot_powder(self, **kwargs):
                calls.append(('powder', kwargs))

            def plot_powder_meas_vs_calc(self, **kwargs):
                calls.append(('powder_meas_vs_calc', kwargs['plot_spec']))

        p = Plotter()
        p._set_project(FakeProject())
        p._backend = FakeBackend()
        return p, calls

    def test_plot_meas(self, monkeypatch):
        p, calls = self._make_plotter_with_project(monkeypatch)
        p.plot_meas('E1')
        assert len(calls) == 1
        assert calls[0][0] == 'powder'
        assert calls[0][1]['labels'] == ['meas']

    def test_plot_calc(self, monkeypatch):
        p, calls = self._make_plotter_with_project(monkeypatch)
        p.plot_calc('E1')
        assert len(calls) == 1
        assert calls[0][1]['labels'] == ['calc']

    def test_plot_meas_vs_calc(self, monkeypatch):
        p, calls = self._make_plotter_with_project(monkeypatch)
        p.plot_meas_vs_calc('E1')
        assert len(calls) == 1
        assert calls[0][0] == 'powder_meas_vs_calc'
        assert calls[0][1].y_resid is not None
        assert calls[0][1].bragg_tick_sets == ()

    def test_plot_meas_vs_calc_without_residual(self, monkeypatch):
        p, calls = self._make_plotter_with_project(monkeypatch)
        p.plot_meas_vs_calc('E1', show_residual=False)
        assert len(calls) == 1
        assert calls[0][0] == 'powder_meas_vs_calc'
        assert calls[0][1].y_resid is None
        assert calls[0][1].bragg_tick_sets == ()


# ------------------------------------------------------------------
# PlotterEngineEnum.description fallback (unknown member)
# ------------------------------------------------------------------


class TestPlotterEngineDescriptionFallback:
    def test_unknown_member_returns_empty_string(self, monkeypatch):
        """A StrEnum member that is neither ASCII nor PLOTLY returns ''."""
        from easydiffraction.display.plotting import PlotterEngineEnum

        # Build a stand-in that is *not* one of the known singletons so
        # both `is` comparisons fall through to the empty-string return.
        class FakeMember:
            description = PlotterEngineEnum.description

        assert FakeMember().description() == ''


# ------------------------------------------------------------------
# Plotter._series_column_names
# ------------------------------------------------------------------


class TestSeriesColumnNames:
    def test_unique_name_then_name(self):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter

        param = SimpleNamespace(unique_name='u', name='n')
        assert Plotter._series_column_names(param) == ['u', 'n']

    def test_duplicate_unique_and_name_deduplicated(self):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter

        param = SimpleNamespace(unique_name='same', name='same')
        assert Plotter._series_column_names(param) == ['same']

    def test_only_name_when_unique_name_blank(self):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter

        param = SimpleNamespace(unique_name='', name='n')
        assert Plotter._series_column_names(param) == ['n']

    def test_empty_when_no_string_attributes(self):
        from easydiffraction.display.plotting import Plotter

        assert Plotter._series_column_names(object()) == []


# ------------------------------------------------------------------
# Plotter._numeric_series_values
# ------------------------------------------------------------------


class TestNumericSeriesValues:
    def test_bool_dtype_converted_to_float(self):
        from easydiffraction.display.plotting import Plotter

        assert Plotter._numeric_series_values([True, False, True]) == [1.0, 0.0, 1.0]

    def test_string_truth_values_mapped(self):
        from easydiffraction.display.plotting import Plotter

        assert Plotter._numeric_series_values(['True', 'False', 'true', 'false']) == [
            1.0,
            0.0,
            1.0,
            0.0,
        ]

    def test_numeric_strings_parsed(self):
        from easydiffraction.display.plotting import Plotter

        assert Plotter._numeric_series_values(['1.5', '2.5']) == [1.5, 2.5]

    def test_invalid_string_raises(self):
        import pytest

        from easydiffraction.display.plotting import Plotter

        with pytest.raises(ValueError, match='Unable to parse string'):
            Plotter._numeric_series_values(['not_a_number'])


# ------------------------------------------------------------------
# Plotter.plot_param_series routing
# ------------------------------------------------------------------


class TestPlotParamSeriesRouting:
    def test_warns_when_no_column_name(self, monkeypatch, capsys):
        from easydiffraction.display.plotting import Plotter
        from easydiffraction.utils.logging import Logger

        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)

        p = Plotter()
        # object() exposes neither unique_name nor name -> no columns
        p.plot_param_series(object())
        out = capsys.readouterr().out
        assert 'does not expose a CSV column name' in out

    def test_falls_back_to_snapshots_without_csv(self, monkeypatch):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter

        captured = {}

        class FakeAnalysis:
            _parameter_snapshots = {'expt1': {'param_a': {}}}

        class FakeProject:
            info = SimpleNamespace(path=None)
            experiments = {'expt1': object()}
            analysis = FakeAnalysis()

        p = Plotter()
        p._set_project(FakeProject())

        def fake_snapshots(unique_name, versus, experiments, snapshots):
            captured['unique_name'] = unique_name
            captured['versus'] = versus
            captured['snapshots'] = snapshots

        p.plot_param_series_from_snapshots = fake_snapshots
        p.plot_param_series(SimpleNamespace(unique_name='param_a', name='param_a'), versus='v')

        assert captured['unique_name'] == 'param_a'
        assert captured['versus'] == 'v'
        assert captured['snapshots'] == {'expt1': {'param_a': {}}}

    def test_uses_csv_when_results_file_present(self, monkeypatch, tmp_path):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter

        analysis_dir = tmp_path / 'analysis'
        analysis_dir.mkdir(parents=True)
        (analysis_dir / 'results.csv').write_text('param_a\n1.0\n')

        captured = {}

        class FakeProject:
            info = SimpleNamespace(path=str(tmp_path))
            experiments = {}
            analysis = SimpleNamespace(_parameter_snapshots={})

        p = Plotter()
        p._set_project(FakeProject())

        def fake_from_csv(*, csv_path, column_names, param_descriptor, versus_path):
            captured['csv_path'] = csv_path
            captured['column_names'] = column_names

        p._plot_param_series_from_csv = fake_from_csv
        p.plot_param_series(SimpleNamespace(unique_name='param_a', name='param_a'))

        assert captured['csv_path'].endswith('results.csv')
        assert captured['column_names'] == ['param_a']


# ------------------------------------------------------------------
# Plotter.plot_all_param_series
# ------------------------------------------------------------------


class TestPlotAllParamSeries:
    def test_warns_when_no_fitted_params(self, monkeypatch, capsys):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter
        from easydiffraction.utils.logging import Logger

        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)

        class FakeProject:
            info = SimpleNamespace(path=None)
            analysis = SimpleNamespace(_parameter_snapshots={})

        p = Plotter()
        p._set_project(FakeProject())
        p.plot_all_param_series()
        out = capsys.readouterr().out
        assert 'No fitted parameters found to plot' in out

    def test_plots_each_descriptor_and_skips_missing(self, monkeypatch, capsys):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter
        from easydiffraction.utils.logging import Logger

        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)

        p = Plotter()
        # Two fitted names; only one has a descriptor in the project.
        monkeypatch.setattr(
            Plotter,
            '_collect_fitted_param_unique_names',
            lambda self: ['present', 'missing'],
        )
        descriptor = SimpleNamespace(unique_name='present')
        monkeypatch.setattr(
            Plotter,
            '_fitted_param_descriptors_by_unique_name',
            lambda self: {'present': descriptor},
        )

        plotted = []
        p.plot_param_series = lambda *, param, versus: plotted.append((param, versus))

        p.plot_all_param_series(versus='temp')

        out = capsys.readouterr().out
        assert plotted == [(descriptor, 'temp')]
        assert "'missing' not found in project" in out


# ------------------------------------------------------------------
# Plotter._collect_fitted_param_unique_names
# ------------------------------------------------------------------


class TestCollectFittedParamUniqueNames:
    def test_from_csv_filters_meta_and_diffrn_and_uncertainty(self, tmp_path):
        from types import SimpleNamespace

        from easydiffraction.analysis.sequential import _META_COLUMNS
        from easydiffraction.display.plotting import Plotter

        analysis_dir = tmp_path / 'analysis'
        analysis_dir.mkdir(parents=True)
        meta_col = next(iter(_META_COLUMNS))
        header = f'{meta_col},param_a,param_a.uncertainty,diffrn.temp\n'
        (analysis_dir / 'results.csv').write_text(header + '1,2,0.1,300\n')

        class FakeProject:
            info = SimpleNamespace(path=str(tmp_path))
            analysis = SimpleNamespace(_parameter_snapshots={})

        p = Plotter()
        p._set_project(FakeProject())
        assert p._collect_fitted_param_unique_names() == ['param_a']

    def test_from_snapshots_when_no_csv(self):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter

        class FakeProject:
            info = SimpleNamespace(path=None)
            analysis = SimpleNamespace(_parameter_snapshots={'e1': {'param_a': {}, 'param_b': {}}})

        p = Plotter()
        p._set_project(FakeProject())
        assert p._collect_fitted_param_unique_names() == ['param_a', 'param_b']

    def test_empty_when_no_csv_and_no_snapshots(self):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter

        class FakeProject:
            info = SimpleNamespace(path=None)
            analysis = SimpleNamespace(_parameter_snapshots={})

        p = Plotter()
        p._set_project(FakeProject())
        assert p._collect_fitted_param_unique_names() == []


# ------------------------------------------------------------------
# Plotter._versus_field_name / _versus_axis_label
# ------------------------------------------------------------------


class TestVersusHelpers:
    def test_field_name_none(self):
        from easydiffraction.display.plotting import Plotter

        assert Plotter._versus_field_name(None) is None

    def test_field_name_strips_diffrn_prefix(self):
        from easydiffraction.display.plotting import Plotter

        assert Plotter._versus_field_name('diffrn.ambient_temperature') == 'ambient_temperature'

    def test_field_name_passthrough_without_prefix(self):
        from easydiffraction.display.plotting import Plotter

        assert Plotter._versus_field_name('ambient_temperature') == 'ambient_temperature'

    def test_axis_label_descriptor_with_units(self):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter

        descriptor = SimpleNamespace(description='Temperature', name='t', units='K')
        assert Plotter._versus_axis_label('diffrn.t', descriptor) == 'Temperature (K)'

    def test_axis_label_descriptor_without_units(self):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter

        descriptor = SimpleNamespace(description='Temperature', name='t', units=None)
        assert Plotter._versus_axis_label('diffrn.t', descriptor) == 'Temperature'

    def test_axis_label_falls_back_to_field_name(self):
        from easydiffraction.display.plotting import Plotter

        assert Plotter._versus_axis_label('diffrn.ambient_temperature', None) == (
            'ambient temperature'
        )

    def test_axis_label_default_experiment_number(self):
        from easydiffraction.display.plotting import Plotter

        assert Plotter._versus_axis_label(None, None) == 'Experiment No.'


# ------------------------------------------------------------------
# Plotter._resolve_versus_descriptor_from_path
# ------------------------------------------------------------------


class TestResolveVersusDescriptorFromPath:
    def test_none_path_returns_none(self):
        from easydiffraction.display.plotting import Plotter

        assert Plotter()._resolve_versus_descriptor_from_path(None) is None

    def test_no_project_returns_none(self):
        from easydiffraction.display.plotting import Plotter

        p = Plotter()
        p._project = None
        assert p._resolve_versus_descriptor_from_path('diffrn.ambient_temperature') is None

    def test_no_experiments_returns_none(self):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter

        p = Plotter()
        p._set_project(SimpleNamespace(experiments={}))
        assert p._resolve_versus_descriptor_from_path('diffrn.ambient_temperature') is None

    def test_resolves_descriptor_from_first_experiment(self):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter

        sentinel = object()

        class Diffrn:
            ambient_temperature = sentinel

        experiment = SimpleNamespace(diffrn=Diffrn())
        p = Plotter()
        p._set_project(SimpleNamespace(experiments={'e1': experiment}))
        result = p._resolve_versus_descriptor_from_path('diffrn.ambient_temperature')
        assert result is sentinel


# ------------------------------------------------------------------
# Plotter._validated_max_parameter_count
# ------------------------------------------------------------------


class TestValidatedMaxParameterCount:
    def test_valid_value_passes_through(self):
        from easydiffraction.display.plotting import Plotter

        assert Plotter._validated_max_parameter_count(5, minimum=1) == 5

    def test_non_integer_raises_type_error(self):
        import pytest

        from easydiffraction.display.plotting import Plotter

        with pytest.raises(TypeError, match='must be an integer'):
            Plotter._validated_max_parameter_count(2.5, minimum=1)

    def test_bool_rejected_as_non_integer(self):
        import pytest

        from easydiffraction.display.plotting import Plotter

        bool_value = True
        with pytest.raises(TypeError, match='must be an integer'):
            Plotter._validated_max_parameter_count(bool_value, minimum=1)

    def test_below_minimum_raises_value_error(self):
        import pytest

        from easydiffraction.display.plotting import Plotter

        with pytest.raises(ValueError, match='at least 2'):
            Plotter._validated_max_parameter_count(1, minimum=2)


# ------------------------------------------------------------------
# Plotter._auto_filtered_correlation_dataframe
# ------------------------------------------------------------------


class TestAutoFilteredCorrelationDataframe:
    def test_returns_unchanged_when_within_limit(self):
        import pandas as pd

        from easydiffraction.display.plotting import Plotter

        corr = pd.DataFrame(
            [[1.0, 0.5], [0.5, 1.0]],
            index=['a', 'b'],
            columns=['a', 'b'],
        )
        result, threshold = Plotter._auto_filtered_correlation_dataframe(corr, max_parameters=4)
        assert threshold == 0.0
        assert list(result.index) == ['a', 'b']

    def test_picks_threshold_to_fit_within_limit(self):
        import pandas as pd

        from easydiffraction.display.plotting import Plotter

        corr = pd.DataFrame(
            [
                [1.0, 0.9, 0.1],
                [0.9, 1.0, 0.1],
                [0.1, 0.1, 1.0],
            ],
            index=['a', 'b', 'c'],
            columns=['a', 'b', 'c'],
        )
        result, threshold = Plotter._auto_filtered_correlation_dataframe(corr, max_parameters=2)
        assert list(result.index) == ['a', 'b']
        assert threshold > 0.0

    def test_no_off_diagonal_correlation_truncates(self):
        import numpy as np
        import pandas as pd

        from easydiffraction.display.plotting import Plotter

        corr = pd.DataFrame(
            np.eye(3),
            index=['a', 'b', 'c'],
            columns=['a', 'b', 'c'],
        )
        result, threshold = Plotter._auto_filtered_correlation_dataframe(corr, max_parameters=2)
        assert list(result.index) == ['a', 'b']
        assert threshold == 0.0

    def test_falls_back_to_top_parameters_by_strength(self):
        import pandas as pd

        from easydiffraction.display.plotting import Plotter

        # No single threshold lands the count exactly in [1, 2]; the
        # final top-strength fallback selects the two strongest params.
        corr = pd.DataFrame(
            [
                [1.0, 0.8, 0.8, 0.8],
                [0.8, 1.0, 0.8, 0.8],
                [0.8, 0.8, 1.0, 0.8],
                [0.8, 0.8, 0.8, 1.0],
            ],
            index=['a', 'b', 'c', 'd'],
            columns=['a', 'b', 'c', 'd'],
        )
        result, threshold = Plotter._auto_filtered_correlation_dataframe(corr, max_parameters=2)
        assert result.shape == (2, 2)
        assert threshold == 0.0


# ------------------------------------------------------------------
# Plotter._correlation_filtered_title / _posterior_pair_title
# ------------------------------------------------------------------


class TestTitleHelpers:
    def test_filtered_title_without_threshold(self):
        from easydiffraction.display.plotting import Plotter

        assert Plotter._correlation_filtered_title('Base', 0.0) == 'Base'

    def test_filtered_title_with_threshold(self):
        from easydiffraction.display.plotting import Plotter

        title = Plotter._correlation_filtered_title('Base', 0.5)
        assert title.startswith('Base with |correlation|')
        assert '0.50' in title

    def test_posterior_pair_title_none(self):
        from easydiffraction.display.plotting import Plotter

        assert Plotter._posterior_pair_title(None) == 'Posterior pair plot'

    def test_posterior_pair_title_with_multiplier(self):
        from easydiffraction.display.plotting import Plotter

        title = Plotter._posterior_pair_title(2.0)
        assert '2' in title
        assert 'uncertainty region' in title


# ------------------------------------------------------------------
# Plotter._posterior_pair_uncertainty_multiplier
# ------------------------------------------------------------------


class TestPosteriorPairUncertaintyMultiplier:
    def _fit_results(self, multipliers):
        from types import SimpleNamespace

        parameters = [
            SimpleNamespace(unique_name=f'p{i}', fit_bounds_uncertainty_multiplier=mult)
            for i, mult in enumerate(multipliers)
        ]
        return SimpleNamespace(parameters=parameters)

    def test_shared_multiplier_returned(self):
        from easydiffraction.display.plotting import Plotter

        fit_results = self._fit_results([3.0, 3.0])
        result = Plotter._posterior_pair_uncertainty_multiplier(fit_results, ['p0', 'p1'])
        assert result == 3.0

    def test_missing_parameter_returns_none(self):
        from easydiffraction.display.plotting import Plotter

        fit_results = self._fit_results([3.0])
        assert Plotter._posterior_pair_uncertainty_multiplier(fit_results, ['missing']) is None

    def test_none_multiplier_returns_none(self):
        from easydiffraction.display.plotting import Plotter

        fit_results = self._fit_results([None])
        assert Plotter._posterior_pair_uncertainty_multiplier(fit_results, ['p0']) is None

    def test_inconsistent_multipliers_return_none(self):
        from easydiffraction.display.plotting import Plotter

        fit_results = self._fit_results([3.0, 5.0])
        assert Plotter._posterior_pair_uncertainty_multiplier(fit_results, ['p0', 'p1']) is None


# ------------------------------------------------------------------
# Plotter._get_fit_result_for_correlation
# ------------------------------------------------------------------


class TestGetFitResultForCorrelation:
    def test_warns_when_no_project(self, monkeypatch, capsys):
        from easydiffraction.display.plotting import Plotter
        from easydiffraction.utils.logging import Logger

        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)

        p = Plotter()
        p._project = None
        assert p._get_fit_result_for_correlation() is None
        assert 'not attached to a project' in capsys.readouterr().out

    def test_warns_when_no_fit_results(self, monkeypatch, capsys):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter
        from easydiffraction.utils.logging import Logger

        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)

        p = Plotter()
        p._set_project(SimpleNamespace(analysis=SimpleNamespace(fit_results=None)))
        assert p._get_fit_result_for_correlation() is None
        assert 'No fit results available' in capsys.readouterr().out

    def test_returns_fit_results_when_present(self):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter

        sentinel = object()
        p = Plotter()
        p._set_project(SimpleNamespace(analysis=SimpleNamespace(fit_results=sentinel)))
        assert p._get_fit_result_for_correlation() is sentinel


# ------------------------------------------------------------------
# Plotter._correlation_from_covariance / _get_correlation_labels
# ------------------------------------------------------------------


class TestCorrelationFromCovariance:
    def test_valid_covariance(self):
        import numpy as np

        from easydiffraction.display.plotting import Plotter

        covar = np.array([[4.0, 1.0], [1.0, 9.0]])
        corr = Plotter._correlation_from_covariance(covar, ['p1', 'p2'], [])
        np.testing.assert_allclose(np.diag(corr.to_numpy()), [1.0, 1.0])
        np.testing.assert_allclose(corr.iloc[0, 1], 1.0 / 6.0)

    def test_non_square_returns_none(self, monkeypatch, capsys):
        import numpy as np

        from easydiffraction.display.plotting import Plotter
        from easydiffraction.utils.logging import Logger

        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)

        covar = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
        assert Plotter._correlation_from_covariance(covar, ['a', 'b'], []) is None
        assert 'invalid covariance matrix' in capsys.readouterr().out

    def test_size_mismatch_with_var_names_returns_none(self, monkeypatch, capsys):
        import numpy as np

        from easydiffraction.display.plotting import Plotter
        from easydiffraction.utils.logging import Logger

        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)

        covar = np.array([[4.0, 1.0], [1.0, 9.0]])
        assert Plotter._correlation_from_covariance(covar, ['only_one'], []) is None
        assert 'does not match the fitted parameter list' in capsys.readouterr().out

    def test_labels_use_minimizer_uid_mapping(self):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter

        params = [
            SimpleNamespace(_minimizer_uid='u1', unique_name='phase.a', name='a'),
            SimpleNamespace(_minimizer_uid='u2', unique_name='phase.b', name='b'),
        ]
        labels = Plotter._get_correlation_labels(params, ['u1', 'u2', 'u3'])
        assert labels == ['phase.a', 'phase.b', 'u3']


# ------------------------------------------------------------------
# Plotter._get_param_correlation_dataframe_from_engine_params
# ------------------------------------------------------------------


class TestEngineParamsCorrelation:
    def test_no_params_returns_none(self):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter

        raw = SimpleNamespace(params=None, var_names=['p1'])
        assert Plotter()._get_param_correlation_dataframe_from_engine_params(raw, []) is None

    def test_no_correlations_returns_none(self):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter

        raw = SimpleNamespace(
            params={'p1': SimpleNamespace(correl=None), 'p2': SimpleNamespace(correl={})},
            var_names=['p1', 'p2'],
        )
        assert Plotter()._get_param_correlation_dataframe_from_engine_params(raw, []) is None

    def test_builds_symmetric_matrix_from_correl(self):
        from types import SimpleNamespace

        import numpy as np

        from easydiffraction.display.plotting import Plotter

        raw = SimpleNamespace(
            params={
                'p1': SimpleNamespace(correl={'p2': 0.5, 'unknown': 0.9}),
                'p2': SimpleNamespace(correl={'p1': 0.5}),
            },
            var_names=['p1', 'p2'],
        )
        params = [
            SimpleNamespace(_minimizer_uid='p1', unique_name='a', name='a'),
            SimpleNamespace(_minimizer_uid='p2', unique_name='b', name='b'),
        ]
        corr = Plotter()._get_param_correlation_dataframe_from_engine_params(raw, params)
        np.testing.assert_allclose(corr.to_numpy(), [[1.0, 0.5], [0.5, 1.0]])
        assert list(corr.index) == ['a', 'b']


# ------------------------------------------------------------------
# Plotter._excluded_ranges
# ------------------------------------------------------------------


class TestExcludedRanges:
    def test_none_excluded_regions_returns_empty(self):
        from easydiffraction.display.plotting import Plotter

        assert Plotter._excluded_ranges(experiment=object(), x_min=0.0, x_max=10.0) == ()

    def test_clips_to_view_window(self):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter

        region = SimpleNamespace(
            start=SimpleNamespace(value=1.0),
            end=SimpleNamespace(value=5.0),
        )
        experiment = SimpleNamespace(excluded_regions=[region])
        result = Plotter._excluded_ranges(experiment=experiment, x_min=2.0, x_max=4.0)
        assert result == ((2.0, 4.0),)

    def test_drops_regions_outside_window(self):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter

        inside = SimpleNamespace(
            start=SimpleNamespace(value=2.0),
            end=SimpleNamespace(value=3.0),
        )
        outside = SimpleNamespace(
            start=SimpleNamespace(value=20.0),
            end=SimpleNamespace(value=30.0),
        )
        experiment = SimpleNamespace(excluded_regions=[inside, outside])
        result = Plotter._excluded_ranges(experiment=experiment, x_min=0.0, x_max=10.0)
        assert result == ((2.0, 3.0),)

    def test_uses_infinite_bounds_when_none(self):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter

        region = SimpleNamespace(
            start=SimpleNamespace(value=1.0),
            end=SimpleNamespace(value=5.0),
        )
        experiment = SimpleNamespace(excluded_regions=[region])
        result = Plotter._excluded_ranges(experiment=experiment, x_min=None, x_max=None)
        assert result == ((1.0, 5.0),)


# ------------------------------------------------------------------
# Plotter._bragg_tick_d_spacing
# ------------------------------------------------------------------


class TestBraggTickDSpacing:
    def test_two_theta_path(self):
        from types import SimpleNamespace

        import numpy as np

        from easydiffraction.display.plotting import Plotter
        from easydiffraction.utils.utils import twotheta_to_d

        refln = SimpleNamespace(two_theta=np.array([20.0, 40.0]))
        experiment = SimpleNamespace(
            instrument=SimpleNamespace(setup_wavelength=SimpleNamespace(value=1.5))
        )
        result = Plotter._bragg_tick_d_spacing(refln=refln, experiment=experiment)
        np.testing.assert_allclose(result, twotheta_to_d(np.array([20.0, 40.0]), 1.5))

    def test_time_of_flight_path(self):
        from types import SimpleNamespace

        import numpy as np

        from easydiffraction.display.plotting import Plotter
        from easydiffraction.utils.utils import tof_to_d

        refln = SimpleNamespace(time_of_flight=np.array([1000.0, 2000.0]))
        # Intentionally has no two_theta attribute so the tof branch runs.
        instrument = SimpleNamespace(
            calib_d_to_tof_offset=SimpleNamespace(value=0.0),
            calib_d_to_tof_linear=SimpleNamespace(value=1.0),
            calib_d_to_tof_quad=SimpleNamespace(value=0.0),
        )
        experiment = SimpleNamespace(instrument=instrument)
        result = Plotter._bragg_tick_d_spacing(refln=refln, experiment=experiment)
        np.testing.assert_allclose(result, tof_to_d(np.array([1000.0, 2000.0]), 0.0, 1.0, 0.0))

    def test_falls_back_to_explicit_d_spacing(self):
        from types import SimpleNamespace

        import numpy as np

        from easydiffraction.display.plotting import Plotter

        refln = SimpleNamespace(d_spacing=np.array([1.1, 2.2]))
        result = Plotter._bragg_tick_d_spacing(refln=refln, experiment=object())
        np.testing.assert_allclose(result, np.array([1.1, 2.2]))


# ------------------------------------------------------------------
# Plotter._bragg_tick_x_values / _bragg_tick_attr / _bragg_tick_arrays
# ------------------------------------------------------------------


class TestBraggTickResolution:
    def test_unsupported_axis_warns_and_returns_none(self, monkeypatch, capsys):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter
        from easydiffraction.utils.logging import Logger

        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)

        result = Plotter._bragg_tick_x_values(
            refln=SimpleNamespace(),
            experiment=object(),
            expt_name='E1',
            x_axis='sin_theta_over_lambda',
        )
        assert result is None
        assert 'Unsupported Bragg tick x axis' in capsys.readouterr().out

    def test_attr_missing_warns_and_returns_none(self, monkeypatch, capsys):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter
        from easydiffraction.utils.logging import Logger

        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)

        result = Plotter._bragg_tick_attr(SimpleNamespace(two_theta=None), 'two_theta', 'E1')
        assert result is None
        assert "does not expose 'two_theta'" in capsys.readouterr().out

    def test_arrays_missing_field_warns_and_returns_none(self, monkeypatch, capsys):
        from types import SimpleNamespace

        import numpy as np

        from easydiffraction.display.plotting import Plotter
        from easydiffraction.utils.logging import Logger

        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)

        # phase_id present but f_calc missing -> returns None.
        refln = SimpleNamespace(
            phase_id=np.array(['a']),
            index_h=np.array([1]),
            index_k=np.array([0]),
            index_l=np.array([1]),
            f_squared_calc=np.array([1.0]),
            f_calc=None,
        )
        assert Plotter._bragg_tick_arrays(refln=refln, expt_name='E1') is None
        assert "missing 'f_calc'" in capsys.readouterr().out


# ------------------------------------------------------------------
# Plotter._square_matrix_axis_title_label(s)
# ------------------------------------------------------------------


class TestSquareMatrixAxisTitleLabel:
    def test_plain_name_without_dot(self):
        from easydiffraction.display.plotting import Plotter

        assert Plotter._square_matrix_axis_title_label('length_a') == 'length_a'

    def test_dotted_name_split_into_lines(self):
        from easydiffraction.display.plotting import Plotter

        assert Plotter._square_matrix_axis_title_label('phase.cell.length_a') == (
            'phase.<br>cell.<br>length_a'
        )

    def test_empty_name_returns_empty(self):
        from easydiffraction.display.plotting import Plotter

        assert Plotter._square_matrix_axis_title_label('   ') == ''

    def test_labels_helper_maps_each_name(self):
        from easydiffraction.display.plotting import Plotter

        result = Plotter._square_matrix_axis_title_labels(['a', 'x.y'])
        assert result == ['a', 'x.<br>y']

    def test_line_count(self):
        from easydiffraction.display.plotting import Plotter

        assert Plotter._square_matrix_axis_title_line_count('') == 1
        assert Plotter._square_matrix_axis_title_line_count('a<br>b<br>c') == 3


# ------------------------------------------------------------------
# Plotter._posterior_density_axis_range
# ------------------------------------------------------------------


class TestPosteriorDensityAxisRange:
    def test_empty_returns_none(self):
        import numpy as np

        from easydiffraction.display.plotting import Plotter

        assert Plotter._posterior_density_axis_range(np.array([])) is None

    def test_all_non_finite_returns_none(self):
        import numpy as np

        from easydiffraction.display.plotting import Plotter

        assert Plotter._posterior_density_axis_range(np.array([np.nan, np.inf])) is None

    def test_positive_range_padded_above(self):
        import numpy as np

        from easydiffraction.display.plotting import Plotter

        lower, upper = Plotter._posterior_density_axis_range(np.array([1.0, 2.0, 3.0]))
        assert lower == 0.0
        assert upper > 3.0

    def test_flat_values_use_fallback_padding(self):
        import numpy as np

        from easydiffraction.display.plotting import Plotter

        lower, upper = Plotter._posterior_density_axis_range(np.array([5.0, 5.0]))
        assert lower == 0.0
        assert upper > 5.0


# ------------------------------------------------------------------
# Plotter._posterior_axis_bounds
# ------------------------------------------------------------------


class TestPosteriorAxisBounds:
    def test_explicit_bounds_used_directly(self):
        import numpy as np

        from easydiffraction.display.plotting import Plotter

        lower, upper = Plotter._posterior_axis_bounds(
            np.array([1.0, 2.0, 3.0]),
            lower_bound=-1.0,
            upper_bound=10.0,
        )
        assert (lower, upper) == (-1.0, 10.0)

    def test_data_driven_bounds_padded(self):
        import numpy as np

        from easydiffraction.display.plotting import Plotter

        lower, upper = Plotter._posterior_axis_bounds(
            np.array([1.0, 2.0, 3.0]),
            lower_bound=None,
            upper_bound=None,
        )
        assert lower < 1.0
        assert upper > 3.0

    def test_flat_data_uses_fallback_padding(self):
        import numpy as np

        from easydiffraction.display.plotting import Plotter

        lower, upper = Plotter._posterior_axis_bounds(
            np.array([4.0, 4.0]),
            lower_bound=None,
            upper_bound=None,
        )
        assert lower < 4.0
        assert upper > 4.0


# ------------------------------------------------------------------
# Plotter._posterior_density_curve
# ------------------------------------------------------------------


class TestPosteriorDensityCurve:
    def test_too_few_samples_returns_none(self):
        import numpy as np

        from easydiffraction.display.plotting import Plotter

        assert (
            Plotter._posterior_density_curve(np.array([1.0]), lower_bound=None, upper_bound=None)
            is None
        )

    def test_constant_samples_make_narrow_peak(self):
        import numpy as np

        from easydiffraction.display.plotting import Plotter

        grid, density = Plotter._posterior_density_curve(
            np.array([2.0, 2.0, 2.0, 2.0]),
            lower_bound=1.0,
            upper_bound=3.0,
        )
        assert grid.shape == density.shape
        # Density integrates to ~1.
        np.testing.assert_allclose(np.trapezoid(density, grid), 1.0, rtol=1e-6)

    def test_inverted_bounds_returns_none(self):
        import numpy as np

        from easydiffraction.display.plotting import Plotter

        assert (
            Plotter._posterior_density_curve(
                np.array([1.0, 2.0, 3.0]),
                lower_bound=5.0,
                upper_bound=1.0,
            )
            is None
        )

    def test_varied_samples_normalize_to_unit_area(self):
        import numpy as np

        from easydiffraction.display.plotting import Plotter

        rng = np.random.default_rng(0)
        values = rng.normal(0.0, 1.0, size=500)
        grid, density = Plotter._posterior_density_curve(
            values,
            lower_bound=None,
            upper_bound=None,
        )
        np.testing.assert_allclose(np.trapezoid(density, grid), 1.0, rtol=1e-3)


# ------------------------------------------------------------------
# Plotter._selected_posterior_samples / _thin_posterior_samples
# ------------------------------------------------------------------


class TestSelectedAndThinnedSamples:
    def test_selected_reorders_columns(self):
        from types import SimpleNamespace

        import numpy as np

        from easydiffraction.display.plotting import Plotter

        flattened = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
        posterior = SimpleNamespace(
            parameter_names=['a', 'b', 'c'],
            flattened=lambda: flattened,
        )
        result = Plotter._selected_posterior_samples(posterior, ['c', 'a'])
        np.testing.assert_allclose(result, np.array([[3.0, 1.0], [6.0, 4.0]]))

    def test_selected_unknown_name_returns_none(self):
        from types import SimpleNamespace

        import numpy as np

        from easydiffraction.display.plotting import Plotter

        posterior = SimpleNamespace(
            parameter_names=['a', 'b'],
            flattened=lambda: np.zeros((2, 2)),
        )
        assert Plotter._selected_posterior_samples(posterior, ['missing']) is None

    def test_selected_empty_names_returns_none(self):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter

        posterior = SimpleNamespace(parameter_names=[], flattened=lambda: None)
        assert Plotter._selected_posterior_samples(posterior, ['a']) is None

    def test_thin_keeps_small_arrays(self):
        import numpy as np

        from easydiffraction.display.plotting import Plotter

        samples = np.arange(10).reshape(5, 2)
        np.testing.assert_array_equal(
            Plotter._thin_posterior_samples(samples, max_points=10),
            samples,
        )

    def test_thin_downsamples_large_arrays(self):
        import numpy as np

        from easydiffraction.display.plotting import Plotter

        samples = np.arange(200).reshape(100, 2)
        thinned = Plotter._thin_posterior_samples(samples, max_points=10)
        assert thinned.shape == (10, 2)


# ------------------------------------------------------------------
# Plotter._posterior_plot_labels
# ------------------------------------------------------------------


class TestPosteriorPlotLabels:
    def test_unknown_parameter_uses_name_directly(self):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter

        fit_results = SimpleNamespace(parameters=[])
        assert Plotter._posterior_plot_labels(fit_results, ['unknown']) == ['unknown']

    def test_entry_name_prefixes_short_name(self):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter

        parameter = SimpleNamespace(
            unique_name='phase.cell.length_a',
            name='length_a',
            _identity=SimpleNamespace(category_entry_name='cell'),
        )
        fit_results = SimpleNamespace(parameters=[parameter])
        assert Plotter._posterior_plot_labels(fit_results, ['phase.cell.length_a']) == [
            'cell length_a'
        ]

    def test_no_entry_name_uses_short_name(self):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter

        parameter = SimpleNamespace(
            unique_name='length_a',
            name='length_a',
            _identity=SimpleNamespace(category_entry_name=''),
        )
        fit_results = SimpleNamespace(parameters=[parameter])
        assert Plotter._posterior_plot_labels(fit_results, ['length_a']) == ['length_a']


# ------------------------------------------------------------------
# Plotter._posterior_summary_by_name / _posterior_parameter_bounds
# ------------------------------------------------------------------


class TestPosteriorSummaryAndBounds:
    def test_summary_by_name_maps_unique_names(self):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter

        summary = SimpleNamespace(unique_name='a')
        fit_results = SimpleNamespace(posterior_parameter_summaries=[summary])
        assert Plotter._posterior_summary_by_name(fit_results) == {'a': summary}

    def test_bounds_missing_parameter_returns_none_pair(self):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter

        fit_results = SimpleNamespace(parameters=[])
        assert Plotter._posterior_parameter_bounds(
            fit_results=fit_results, parameter_name='missing'
        ) == (None, None)

    def test_bounds_finite_values(self):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter

        parameter = SimpleNamespace(unique_name='a', fit_min=1.0, fit_max=5.0)
        fit_results = SimpleNamespace(parameters=[parameter])
        assert Plotter._posterior_parameter_bounds(
            fit_results=fit_results, parameter_name='a'
        ) == (1.0, 5.0)

    def test_bounds_non_finite_values_dropped(self):
        from types import SimpleNamespace

        import numpy as np

        from easydiffraction.display.plotting import Plotter

        parameter = SimpleNamespace(unique_name='a', fit_min=np.inf, fit_max=None)
        fit_results = SimpleNamespace(parameters=[parameter])
        assert Plotter._posterior_parameter_bounds(
            fit_results=fit_results, parameter_name='a'
        ) == (None, None)


# ------------------------------------------------------------------
# Plotter._posterior_pair_show_contours / contour panel counts
# ------------------------------------------------------------------


class TestPosteriorPairContourDecisions:
    def test_full_style_always_shows(self):
        from easydiffraction.display.plotting import Plotter
        from easydiffraction.display.plotting import PosteriorPairPlotStyleEnum

        assert (
            Plotter._posterior_pair_show_contours(
                n_parameters=20, style=PosteriorPairPlotStyleEnum.FULL
            )
            is True
        )

    def test_fast_style_never_shows(self):
        from easydiffraction.display.plotting import Plotter
        from easydiffraction.display.plotting import PosteriorPairPlotStyleEnum

        assert (
            Plotter._posterior_pair_show_contours(
                n_parameters=2, style=PosteriorPairPlotStyleEnum.FAST
            )
            is False
        )

    def test_auto_depends_on_parameter_count(self):
        from easydiffraction.display.plotting import POSTERIOR_PAIR_AUTO_MAX_CONTOUR_PARAMETERS
        from easydiffraction.display.plotting import Plotter
        from easydiffraction.display.plotting import PosteriorPairPlotStyleEnum

        assert Plotter._posterior_pair_show_contours(
            n_parameters=POSTERIOR_PAIR_AUTO_MAX_CONTOUR_PARAMETERS,
            style=PosteriorPairPlotStyleEnum.AUTO,
        )
        assert not Plotter._posterior_pair_show_contours(
            n_parameters=POSTERIOR_PAIR_AUTO_MAX_CONTOUR_PARAMETERS + 1,
            style=PosteriorPairPlotStyleEnum.AUTO,
        )

    def test_contour_panel_count_minimum(self):
        from easydiffraction.display.plotting import Plotter

        assert Plotter._posterior_pair_contour_panel_count(1) == 1
        assert Plotter._posterior_pair_contour_panel_count(4) == 6

    def test_validated_style_rejects_unknown(self):
        import pytest

        from easydiffraction.display.plotting import Plotter

        with pytest.raises(ValueError, match='style must be one of'):
            Plotter._validated_posterior_pair_plot_style('nope')

    def test_validated_style_accepts_enum_value(self):
        from easydiffraction.display.plotting import Plotter
        from easydiffraction.display.plotting import PosteriorPairPlotStyleEnum

        assert (
            Plotter._validated_posterior_pair_plot_style('full') is PosteriorPairPlotStyleEnum.FULL
        )


# ------------------------------------------------------------------
# Plotter._posterior_pair_correlation_value / contour colorscales
# ------------------------------------------------------------------


class TestPosteriorPairCorrelationValue:
    def test_too_few_finite_points_returns_none(self):
        import numpy as np

        from easydiffraction.display.plotting import Plotter

        x = np.array([1.0, np.nan])
        y = np.array([np.nan, 2.0])
        assert Plotter._posterior_pair_correlation_value(x, y) is None

    def test_positive_correlation(self):
        import numpy as np

        from easydiffraction.display.plotting import Plotter

        x = np.array([1.0, 2.0, 3.0, 4.0])
        y = np.array([1.0, 2.0, 3.0, 4.0])
        assert Plotter._posterior_pair_correlation_value(x, y) > 0.99

    def test_constant_input_returns_none(self):
        import numpy as np

        from easydiffraction.display.plotting import Plotter

        x = np.array([1.0, 1.0, 1.0])
        y = np.array([1.0, 2.0, 3.0])
        # corrcoef yields nan for a constant series (and warns on the
        # internal divide-by-zero); the helper detects the nan and
        # returns None.
        with np.errstate(invalid='ignore', divide='ignore'):
            assert Plotter._posterior_pair_correlation_value(x, y) is None

    def test_colorscales_negative_correlation(self):
        import numpy as np

        from easydiffraction.display.plotting import POSTERIOR_NEGATIVE_CONTOUR_FILL_COLORSCALE
        from easydiffraction.display.plotting import Plotter

        x = np.array([1.0, 2.0, 3.0, 4.0])
        y = np.array([4.0, 3.0, 2.0, 1.0])
        fill, _ = Plotter._posterior_pair_contour_colorscales(x, y)
        assert fill is POSTERIOR_NEGATIVE_CONTOUR_FILL_COLORSCALE

    def test_colorscales_positive_correlation(self):
        import numpy as np

        from easydiffraction.display.plotting import POSTERIOR_CONTOUR_FILL_COLORSCALE
        from easydiffraction.display.plotting import Plotter

        x = np.array([1.0, 2.0, 3.0, 4.0])
        y = np.array([1.0, 2.0, 3.0, 4.0])
        fill, _ = Plotter._posterior_pair_contour_colorscales(x, y)
        assert fill is POSTERIOR_CONTOUR_FILL_COLORSCALE


# ------------------------------------------------------------------
# Plotter._posterior_contour_levels
# ------------------------------------------------------------------


class TestPosteriorContourLevels:
    def test_uses_provided_finite_levels(self):
        import numpy as np

        from easydiffraction.display.plotting import Plotter

        start, end, size = Plotter._posterior_contour_levels(
            density=np.ones((3, 3)),
            contour_levels=np.array([0.1, 0.2, 0.4]),
        )
        assert start == 0.1
        assert end == 0.4
        assert size == pytest.approx(0.1)

    def test_single_level_uses_density_fallback_size(self):
        import numpy as np

        from easydiffraction.display.plotting import Plotter

        # Single level cannot yield end>start; falls back to density max.
        density = np.array([[0.0, 1.0], [1.0, 2.0]])
        start, end, size = Plotter._posterior_contour_levels(
            density=density,
            contour_levels=np.array([0.5]),
        )
        assert end > start
        assert size > 0

    def test_none_levels_derive_from_density(self):
        import numpy as np

        from easydiffraction.display.plotting import Plotter

        density = np.array([[0.0, 2.0], [4.0, 10.0]])
        start, end, size = Plotter._posterior_contour_levels(
            density=density,
            contour_levels=None,
        )
        assert start == pytest.approx(2.0)
        assert end == pytest.approx(9.5)
        assert size == pytest.approx(1.5)


# ------------------------------------------------------------------
# Plotter._correlation_heatmap_edges / centers / values / customdata
# ------------------------------------------------------------------


class TestCorrelationHeatmapArrays:
    def test_edges_zero_parameters(self):
        import numpy as np

        from easydiffraction.display.plotting import Plotter

        np.testing.assert_array_equal(Plotter._correlation_heatmap_edges(0), np.array([0.0]))

    def test_edges_single_parameter_no_gap(self):
        import numpy as np

        from easydiffraction.display.plotting import Plotter

        np.testing.assert_array_equal(Plotter._correlation_heatmap_edges(1), np.array([0.0, 1.0]))

    def test_edges_multiple_parameters_include_gaps(self):
        from easydiffraction.display.plotting import Plotter

        edges = Plotter._correlation_heatmap_edges(3)
        # 2*n - 1 widths => n + (n-1) gap segments => 2n edges.
        assert len(edges) == 6
        assert edges[0] == 0.0

    def test_centers_offset_by_half(self):
        import numpy as np

        from easydiffraction.display.plotting import Plotter

        centers = Plotter._correlation_heatmap_centers(2)
        np.testing.assert_allclose(centers[0], 0.5)

    def test_values_place_data_on_even_indices(self):
        import numpy as np
        import pandas as pd

        from easydiffraction.display.plotting import Plotter

        corr = pd.DataFrame(
            [[1.0, 0.5], [0.5, 1.0]],
            index=['a', 'b'],
            columns=['a', 'b'],
        )
        expanded = Plotter._correlation_heatmap_values(corr)
        assert expanded.shape == (3, 3)
        assert expanded[0, 0] == 1.0
        assert np.isnan(expanded[1, 1])

    def test_customdata_labels_on_even_indices(self):
        import pandas as pd

        from easydiffraction.display.plotting import Plotter

        corr = pd.DataFrame(
            [[1.0, 0.5], [0.5, 1.0]],
            index=['row0', 'row1'],
            columns=['col0', 'col1'],
        )
        custom = Plotter._correlation_heatmap_customdata(corr)
        assert custom.shape == (3, 3, 2)
        assert custom[0, 0, 0] == 'col0'
        assert custom[0, 0, 1] == 'row0'
        assert custom[1, 1, 0] == ''


# ------------------------------------------------------------------
# Plotter._square_matrix_gap_data_width / plot extent
# ------------------------------------------------------------------


class TestSquareMatrixGeometry:
    def test_gap_width_zero_for_single_parameter(self):
        from easydiffraction.display.plotting import Plotter

        assert Plotter._square_matrix_gap_data_width(1) == 0.0

    def test_gap_width_positive_for_multiple(self):
        from easydiffraction.display.plotting import Plotter

        assert Plotter._square_matrix_gap_data_width(4) > 0.0

    def test_plot_extent_matches_parameter_count_without_gap(self):
        from easydiffraction.display.plotting import Plotter

        assert Plotter._square_matrix_plot_extent(1) == 1.0

    def test_extra_axis_title_margin_zero_for_single_line(self):
        from easydiffraction.display.plotting import Plotter

        assert Plotter._square_matrix_extra_axis_title_margin(['a', 'b']) == 0

    def test_extra_axis_title_margin_for_multiline(self):
        from easydiffraction.display.plotting import SQUARE_MATRIX_AXIS_TITLE_LINE_HEIGHT_PIXELS
        from easydiffraction.display.plotting import Plotter

        margin = Plotter._square_matrix_extra_axis_title_margin(['a<br>b<br>c'])
        assert margin == 2 * SQUARE_MATRIX_AXIS_TITLE_LINE_HEIGHT_PIXELS

    def test_extra_axis_title_margin_empty_labels(self):
        from easydiffraction.display.plotting import Plotter

        assert Plotter._square_matrix_extra_axis_title_margin([]) == 0


# ------------------------------------------------------------------
# Plotter._posterior_pair_cell_size_pixels
# ------------------------------------------------------------------


class TestPosteriorPairCellSize:
    def test_zero_parameters_returns_default(self):
        from easydiffraction.display.plotting import PAIR_PLOT_CELL_SIZE_PIXELS
        from easydiffraction.display.plotting import Plotter

        assert (
            Plotter._posterior_pair_cell_size_pixels(0, available_width_pixels=980)
            == PAIR_PLOT_CELL_SIZE_PIXELS
        )

    def test_large_count_clamped_to_minimum(self):
        from easydiffraction.display.plotting import PAIR_PLOT_MIN_CELL_SIZE_PIXELS
        from easydiffraction.display.plotting import Plotter

        size = Plotter._posterior_pair_cell_size_pixels(100, available_width_pixels=980)
        assert size >= PAIR_PLOT_MIN_CELL_SIZE_PIXELS


# ------------------------------------------------------------------
# Plotter._show_background_enabled / _show_bragg_enabled
# ------------------------------------------------------------------


class TestShowFlags:
    def test_background_default_follows_availability(self):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter

        options = SimpleNamespace(show_background=None)
        assert Plotter._show_background_enabled(options, background_available=True) is True
        assert Plotter._show_background_enabled(options, background_available=False) is False

    def test_background_explicit_true_requires_availability(self):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter

        options = SimpleNamespace(show_background=True)
        assert Plotter._show_background_enabled(options, background_available=False) is False
        assert Plotter._show_background_enabled(options, background_available=True) is True

    def test_bragg_default_true(self):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter

        assert Plotter._show_bragg_enabled(SimpleNamespace(show_bragg=None)) is True

    def test_bragg_explicit_false(self):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter

        assert Plotter._show_bragg_enabled(SimpleNamespace(show_bragg=False)) is False


# ------------------------------------------------------------------
# Plotter.plot_posterior_predictive style validation
# ------------------------------------------------------------------


class TestPlotPosteriorPredictiveValidation:
    def test_invalid_style_raises(self):
        import pytest

        from easydiffraction.display.plotting import Plotter

        with pytest.raises(ValueError, match='style must be'):
            Plotter().plot_posterior_predictive('hrpt', style='invalid')

    def test_warns_when_no_project(self, monkeypatch, capsys):
        from easydiffraction.display.plotting import Plotter
        from easydiffraction.utils.logging import Logger

        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)

        p = Plotter()
        p._project = None
        p.plot_posterior_predictive('hrpt')
        assert 'not attached to a project' in capsys.readouterr().out


# ------------------------------------------------------------------
# Plotter._get_posterior_samples_and_fit_results
# ------------------------------------------------------------------


class TestGetPosteriorSamplesAndFitResults:
    def test_non_plotly_engine_warns(self, monkeypatch, capsys):
        from easydiffraction.display.plotting import Plotter
        from easydiffraction.utils.logging import Logger

        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)

        p = Plotter()
        p.engine = 'asciichartpy'
        samples, results = p._get_posterior_samples_and_fit_results()
        assert samples is None
        assert results is None
        assert 'require the Plotly plotting backend' in capsys.readouterr().out

    def test_no_posterior_samples_warns(self, monkeypatch, capsys):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter
        from easydiffraction.utils.logging import Logger

        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)

        p = Plotter()
        p.engine = 'plotly'
        monkeypatch.setattr(
            Plotter,
            '_get_fit_result_for_correlation',
            lambda self: SimpleNamespace(posterior_samples=None),
        )
        samples, results = p._get_posterior_samples_and_fit_results()
        assert samples is None
        assert results is None
        assert 'Posterior samples are unavailable' in capsys.readouterr().out


# ------------------------------------------------------------------
# Plotter._get_or_build_posterior_predictive_summary early returns
# ------------------------------------------------------------------


class TestGetOrBuildPosteriorPredictiveEarlyReturns:
    def test_no_fit_results_returns_none(self, monkeypatch):
        from easydiffraction.display.plotting import Plotter

        p = Plotter()
        monkeypatch.setattr(Plotter, '_get_fit_result_for_correlation', lambda self: None)
        assert (
            p._get_or_build_posterior_predictive_summary(
                experiment=object(), expt_name='e', x_axis='two_theta'
            )
            is None
        )

    def test_no_posterior_predictive_returns_none(self, monkeypatch):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter

        p = Plotter()
        monkeypatch.setattr(
            Plotter,
            '_get_fit_result_for_correlation',
            lambda self: SimpleNamespace(posterior_predictive=None),
        )
        assert (
            p._get_or_build_posterior_predictive_summary(
                experiment=object(), expt_name='e', x_axis='two_theta'
            )
            is None
        )


# ------------------------------------------------------------------
# Plotter._posterior_predictive_draw_indices
# ------------------------------------------------------------------


class TestPosteriorPredictiveDrawIndices:
    def test_small_count_returns_all_indices(self):
        import numpy as np

        from easydiffraction.display.plotting import Plotter

        np.testing.assert_array_equal(
            Plotter._posterior_predictive_draw_indices(3), np.array([0, 1, 2])
        )

    def test_large_count_evenly_spaced_and_unique(self):
        import numpy as np

        from easydiffraction.display.plotting import DEFAULT_POSTERIOR_PREDICTIVE_DRAWS
        from easydiffraction.display.plotting import Plotter

        indices = Plotter._posterior_predictive_draw_indices(10000)
        assert indices[0] == 0
        assert indices[-1] == 9999
        assert len(indices) <= DEFAULT_POSTERIOR_PREDICTIVE_DRAWS
        assert len(np.unique(indices)) == len(indices)


# ------------------------------------------------------------------
# Plotter._correlation_from_posterior_samples edge cases
# ------------------------------------------------------------------


class TestCorrelationFromPosteriorSamples:
    def test_no_parameter_names_returns_none(self, monkeypatch, capsys):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter
        from easydiffraction.utils.logging import Logger

        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)

        posterior = SimpleNamespace(parameter_names=[], flattened=lambda: None)
        assert Plotter._correlation_from_posterior_samples(posterior) is None
        assert 'do not expose parameter names' in capsys.readouterr().out

    def test_wrong_shape_returns_none(self, monkeypatch, capsys):
        from types import SimpleNamespace

        import numpy as np

        from easydiffraction.display.plotting import Plotter
        from easydiffraction.utils.logging import Logger

        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)

        # 3 columns but only 2 parameter names.
        posterior = SimpleNamespace(
            parameter_names=['a', 'b'],
            flattened=lambda: np.zeros((4, 3)),
        )
        assert Plotter._correlation_from_posterior_samples(posterior) is None
        assert 'invalid shape' in capsys.readouterr().out

    def test_too_few_draws_returns_none(self, monkeypatch, capsys):
        from types import SimpleNamespace

        import numpy as np

        from easydiffraction.display.plotting import Plotter
        from easydiffraction.utils.logging import Logger

        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)

        posterior = SimpleNamespace(
            parameter_names=['a', 'b'],
            flattened=lambda: np.zeros((1, 2)),
        )
        assert Plotter._correlation_from_posterior_samples(posterior) is None
        assert 'two posterior draws' in capsys.readouterr().out


# ------------------------------------------------------------------
# Plotter._raw_fit_result_for_correlation
# ------------------------------------------------------------------


class TestRawFitResultForCorrelation:
    def test_no_raw_result_returns_none(self):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter

        fit_results = SimpleNamespace(result=None, engine_result=None)
        assert Plotter()._raw_fit_result_for_correlation(fit_results) is None

    def test_no_var_names_returns_none(self):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter

        raw = SimpleNamespace(var_names=[])
        fit_results = SimpleNamespace(result=raw)
        assert Plotter()._raw_fit_result_for_correlation(fit_results) is None

    def test_returns_raw_with_var_names(self):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter

        raw = SimpleNamespace(var_names=['p1'])
        fit_results = SimpleNamespace(result=None, engine_result=raw)
        assert Plotter()._raw_fit_result_for_correlation(fit_results) is raw


# ------------------------------------------------------------------
# Plotter._trim_correlation_display_dataframe
# ------------------------------------------------------------------


class TestTrimCorrelationDisplayDataframe:
    def test_show_diagonal_keeps_all(self):
        import numpy as np
        import pandas as pd

        from easydiffraction.display.plotting import Plotter

        corr = pd.DataFrame(np.eye(3))
        result, rows, cols = Plotter._trim_correlation_display_dataframe(
            corr, preserve_all_rows=True, show_diagonal=True
        )
        assert result.shape == (3, 3)
        assert rows == [1, 2, 3]
        assert cols == [1, 2, 3]

    def test_preserve_all_rows_trims_last_column_only(self):
        import numpy as np
        import pandas as pd

        from easydiffraction.display.plotting import Plotter

        corr = pd.DataFrame(np.eye(3))
        result, rows, cols = Plotter._trim_correlation_display_dataframe(
            corr, preserve_all_rows=True, show_diagonal=False
        )
        assert result.shape == (3, 2)
        assert rows == [1, 2, 3]
        assert cols == [1, 2]

    def test_graphical_trims_first_row_and_last_column(self):
        import numpy as np
        import pandas as pd

        from easydiffraction.display.plotting import Plotter

        corr = pd.DataFrame(np.eye(3))
        result, rows, cols = Plotter._trim_correlation_display_dataframe(
            corr, preserve_all_rows=False, show_diagonal=False
        )
        assert result.shape == (2, 2)
        assert rows == [2, 3]
        assert cols == [1, 2]

    def test_single_dimension_not_trimmed(self):
        import pandas as pd

        from easydiffraction.display.plotting import Plotter

        corr = pd.DataFrame([[1.0]])
        result, rows, cols = Plotter._trim_correlation_display_dataframe(
            corr, preserve_all_rows=False, show_diagonal=False
        )
        assert result.shape == (1, 1)
        assert rows == [1]
        assert cols == [1]


# ------------------------------------------------------------------
# Plotter._mask_correlation_lower_triangle
# ------------------------------------------------------------------


class TestMaskCorrelationLowerTriangle:
    def test_upper_triangle_and_diagonal_masked(self):
        import numpy as np
        import pandas as pd

        from easydiffraction.display.plotting import Plotter

        corr = pd.DataFrame(
            [[1.0, 0.5, 0.3], [0.5, 1.0, 0.2], [0.3, 0.2, 1.0]],
            index=['a', 'b', 'c'],
            columns=['a', 'b', 'c'],
        )
        masked = Plotter._mask_correlation_lower_triangle(corr)
        # Diagonal and upper triangle are NaN.
        assert np.isnan(masked.iloc[0, 0])
        assert np.isnan(masked.iloc[0, 1])
        # Lower triangle retained.
        assert masked.iloc[1, 0] == 0.5
        assert masked.iloc[2, 0] == 0.3


# ------------------------------------------------------------------
# Plotter._filter_correlation_dataframe
# ------------------------------------------------------------------


class TestFilterCorrelationDataframe:
    def test_zero_threshold_returns_unchanged(self):
        import pandas as pd

        from easydiffraction.display.plotting import Plotter

        corr = pd.DataFrame([[1.0, 0.5], [0.5, 1.0]], index=['a', 'b'], columns=['a', 'b'])
        result = Plotter._filter_correlation_dataframe(corr, threshold=0)
        assert result is corr

    def test_above_one_raises(self):
        import pytest

        from easydiffraction.display.plotting import Plotter

        with pytest.raises(ValueError, match='between 0 and 1'):
            Plotter._filter_correlation_dataframe(object(), threshold=2.0)

    def test_no_pairs_above_threshold_returns_none(self, monkeypatch, capsys):
        import pandas as pd

        from easydiffraction.display.plotting import Plotter
        from easydiffraction.utils.logging import Logger

        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)

        corr = pd.DataFrame(
            [[1.0, 0.1], [0.1, 1.0]],
            index=['a', 'b'],
            columns=['a', 'b'],
        )
        assert Plotter._filter_correlation_dataframe(corr, threshold=0.9) is None
        assert 'No parameter pairs' in capsys.readouterr().out

    def test_keeps_correlated_pairs(self):
        import pandas as pd

        from easydiffraction.display.plotting import Plotter

        corr = pd.DataFrame(
            [
                [1.0, 0.95, 0.1],
                [0.95, 1.0, 0.1],
                [0.1, 0.1, 1.0],
            ],
            index=['a', 'b', 'c'],
            columns=['a', 'b', 'c'],
        )
        result = Plotter._filter_correlation_dataframe(corr, threshold=0.5)
        assert list(result.index) == ['a', 'b']


# ------------------------------------------------------------------
# Plotter._show_plot_figure
# ------------------------------------------------------------------


class TestShowPlotFigure:
    def test_uses_backend_show_figure_when_available(self):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter

        shown = []
        p = Plotter()
        p._backend = SimpleNamespace(_show_figure=shown.append)
        sentinel = object()
        p._show_plot_figure(sentinel)
        assert shown == [sentinel]

    def test_falls_back_to_figure_show(self):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter

        # Backend has no _show_figure attribute -> figure.show() is used.
        p = Plotter()
        p._backend = SimpleNamespace()
        calls = []

        class Figure:
            def show(self):
                calls.append('shown')

        p._show_plot_figure(Figure())
        assert calls == ['shown']


# ------------------------------------------------------------------
# Plotter._plot_axis_frame_color / _plot_legend_background_color /
# _plot_correlation_colorscale (backend callable vs static fallback)
# ------------------------------------------------------------------


class TestPlotStyleHelpers:
    def test_axis_frame_color_uses_backend_callable(self):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter

        p = Plotter()
        p._backend = SimpleNamespace(_axis_frame_color=lambda: 'rgb(1, 2, 3)')
        assert p._plot_axis_frame_color() == 'rgb(1, 2, 3)'

    def test_axis_frame_color_falls_back_to_plotly_static(self):
        from types import SimpleNamespace

        from easydiffraction.display.plotters.plotly import PlotlyPlotter
        from easydiffraction.display.plotting import Plotter

        p = Plotter()
        p._backend = SimpleNamespace()
        assert p._plot_axis_frame_color() == PlotlyPlotter._axis_frame_color()

    def test_legend_background_color_uses_backend_callable(self):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter

        p = Plotter()
        p._backend = SimpleNamespace(_legend_background_color=lambda: 'rgba(0, 0, 0, 0.1)')
        assert p._plot_legend_background_color() == 'rgba(0, 0, 0, 0.1)'

    def test_legend_background_color_falls_back_to_plotly_static(self):
        from types import SimpleNamespace

        from easydiffraction.display.plotters.plotly import PlotlyPlotter
        from easydiffraction.display.plotting import Plotter

        p = Plotter()
        p._backend = SimpleNamespace()
        assert p._plot_legend_background_color() == PlotlyPlotter._legend_background_color()

    def test_correlation_colorscale_uses_backend_callable(self):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter

        sentinel = [(0.0, 'red'), (1.0, 'blue')]
        p = Plotter()
        p._backend = SimpleNamespace(_correlation_colorscale=lambda: sentinel)
        assert p._plot_correlation_colorscale() is sentinel

    def test_correlation_colorscale_falls_back_to_plotly_static(self):
        from types import SimpleNamespace

        from easydiffraction.display.plotters.plotly import PlotlyPlotter
        from easydiffraction.display.plotting import Plotter

        p = Plotter()
        p._backend = SimpleNamespace()
        assert p._plot_correlation_colorscale() == PlotlyPlotter._correlation_colorscale()


# ------------------------------------------------------------------
# Plotter._get_posterior_samples_and_fit_results
# ------------------------------------------------------------------


class TestGetPosteriorSamplesAndFitResultsEngineGuards:
    def test_non_plotly_engine_warns_and_returns_none(self, monkeypatch, capsys):
        from easydiffraction.display.plotting import Plotter
        from easydiffraction.utils.logging import Logger

        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)

        p = Plotter()
        p.engine = 'asciichartpy'
        samples, fit_results = p._get_posterior_samples_and_fit_results()
        assert samples is None
        assert fit_results is None
        assert 'require the Plotly plotting backend' in capsys.readouterr().out

    def test_no_fit_results_returns_none(self, monkeypatch):
        from easydiffraction.display.plotting import Plotter

        p = Plotter()
        p.engine = 'plotly'
        monkeypatch.setattr(Plotter, '_get_fit_result_for_correlation', lambda self: None)
        assert p._get_posterior_samples_and_fit_results() == (None, None)

    def test_no_posterior_samples_warns(self, monkeypatch, capsys):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter
        from easydiffraction.utils.logging import Logger

        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)

        fit_results = SimpleNamespace(posterior_samples=None)
        p = Plotter()
        p.engine = 'plotly'
        monkeypatch.setattr(Plotter, '_get_fit_result_for_correlation', lambda self: fit_results)
        assert p._get_posterior_samples_and_fit_results() == (None, None)
        assert 'Posterior samples are unavailable' in capsys.readouterr().out

    def test_returns_samples_and_fit_results(self, monkeypatch):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter

        samples = object()
        fit_results = SimpleNamespace(posterior_samples=samples)
        p = Plotter()
        p.engine = 'plotly'
        monkeypatch.setattr(Plotter, '_get_fit_result_for_correlation', lambda self: fit_results)
        assert p._get_posterior_samples_and_fit_results() == (samples, fit_results)


# ------------------------------------------------------------------
# Plotter._cached_posterior_density_curve
# ------------------------------------------------------------------


class TestCachedPosteriorDensityCurve:
    def test_no_project_returns_none(self):
        from easydiffraction.display.plotting import Plotter

        p = Plotter()
        p._project = None
        assert p._cached_posterior_density_curve('param') is None

    def test_missing_cache_entry_returns_none(self):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter

        analysis = SimpleNamespace(_persisted_fit_state_sidecar={'distribution_caches': {}})
        p = Plotter()
        p._set_project(SimpleNamespace(analysis=analysis))
        assert p._cached_posterior_density_curve('param') is None

    def test_valid_cache_returned(self):
        from types import SimpleNamespace

        import numpy as np

        from easydiffraction.display.plotting import Plotter

        analysis = SimpleNamespace(
            _persisted_fit_state_sidecar={
                'distribution_caches': {
                    'param': {'x': [1.0, 2.0, 3.0], 'density': [0.1, 0.2, 0.1]},
                }
            }
        )
        p = Plotter()
        p._set_project(SimpleNamespace(analysis=analysis))
        x_values, density = p._cached_posterior_density_curve('param')
        np.testing.assert_allclose(x_values, [1.0, 2.0, 3.0])
        np.testing.assert_allclose(density, [0.1, 0.2, 0.1])

    def test_invalid_shape_warns_and_returns_none(self, monkeypatch, capsys):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter
        from easydiffraction.utils.logging import Logger

        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)

        analysis = SimpleNamespace(
            _persisted_fit_state_sidecar={
                'distribution_caches': {
                    # density length differs from x -> invalid
                    'param': {'x': [1.0, 2.0, 3.0], 'density': [0.1, 0.2]},
                }
            }
        )
        p = Plotter()
        p._set_project(SimpleNamespace(analysis=analysis))
        assert p._cached_posterior_density_curve('param') is None
        assert 'cache is invalid' in capsys.readouterr().out


# ------------------------------------------------------------------
# Plotter._cached_posterior_pair_surface
# ------------------------------------------------------------------


class TestCachedPosteriorPairSurface:
    def test_no_project_returns_none(self):
        from easydiffraction.display.plotting import Plotter

        p = Plotter()
        p._project = None
        assert p._cached_posterior_pair_surface(x_parameter_name='a', y_parameter_name='b') is None

    def test_no_matching_cache_returns_none(self):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter

        analysis = SimpleNamespace(
            _persisted_fit_state_sidecar={
                'pair_caches': {
                    'c0': {'param_unique_name_x': 'x', 'param_unique_name_y': 'z'},
                }
            }
        )
        p = Plotter()
        p._set_project(SimpleNamespace(analysis=analysis))
        assert p._cached_posterior_pair_surface(x_parameter_name='a', y_parameter_name='b') is None

    def test_matched_cache_returned(self):
        from types import SimpleNamespace

        import numpy as np

        from easydiffraction.display.plotting import Plotter

        analysis = SimpleNamespace(
            _persisted_fit_state_sidecar={
                'pair_caches': {
                    'c0': {
                        'param_unique_name_x': 'a',
                        'param_unique_name_y': 'b',
                        'x': [0.0, 1.0],
                        'y': [0.0, 1.0, 2.0],
                        'density': np.zeros((3, 2)).tolist(),
                        'contour_levels': None,
                    },
                }
            }
        )
        p = Plotter()
        p._set_project(SimpleNamespace(analysis=analysis))
        surface = p._cached_posterior_pair_surface(x_parameter_name='a', y_parameter_name='b')
        assert surface is not None
        x_grid, y_grid, density, contour_levels = surface
        assert x_grid.shape == (2,)
        assert y_grid.shape == (3,)
        assert density.shape == (3, 2)
        assert contour_levels is None

    def test_swapped_axes_transposes_density(self):
        from types import SimpleNamespace

        import numpy as np

        from easydiffraction.display.plotting import Plotter

        density = np.arange(6.0).reshape(3, 2)
        analysis = SimpleNamespace(
            _persisted_fit_state_sidecar={
                'pair_caches': {
                    'c0': {
                        'param_unique_name_x': 'a',
                        'param_unique_name_y': 'b',
                        'x': [0.0, 1.0],
                        'y': [0.0, 1.0, 2.0],
                        'density': density.tolist(),
                        'contour_levels': [0.1, 0.2],
                    },
                }
            }
        )
        p = Plotter()
        p._set_project(SimpleNamespace(analysis=analysis))
        # Request with axes swapped relative to the cache entry.
        surface = p._cached_posterior_pair_surface(x_parameter_name='b', y_parameter_name='a')
        assert surface is not None
        x_grid, y_grid, returned_density, contour_levels = surface
        # x/y grids swap and density transposes to (2, 3).
        np.testing.assert_allclose(x_grid, [0.0, 1.0, 2.0])
        np.testing.assert_allclose(y_grid, [0.0, 1.0])
        assert returned_density.shape == (2, 3)
        np.testing.assert_allclose(contour_levels, [0.1, 0.2])

    def test_invalid_density_shape_warns_and_returns_none(self, monkeypatch, capsys):
        from types import SimpleNamespace

        import numpy as np

        from easydiffraction.display.plotting import Plotter
        from easydiffraction.utils.logging import Logger

        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)

        analysis = SimpleNamespace(
            _persisted_fit_state_sidecar={
                'pair_caches': {
                    'c0': {
                        'param_unique_name_x': 'a',
                        'param_unique_name_y': 'b',
                        'x': [0.0, 1.0],
                        'y': [0.0, 1.0, 2.0],
                        'density': np.zeros((2, 2)).tolist(),  # wrong shape
                        'contour_levels': None,
                    },
                }
            }
        )
        p = Plotter()
        p._set_project(SimpleNamespace(analysis=analysis))
        assert p._cached_posterior_pair_surface(x_parameter_name='a', y_parameter_name='b') is None
        assert 'pair cache is invalid' in capsys.readouterr().out


# ------------------------------------------------------------------
# Plotter._posterior_contour_levels
# ------------------------------------------------------------------


class TestPosteriorContourLevelsSingleLevel:
    def test_single_level_falls_back_to_density(self):
        import numpy as np

        from easydiffraction.display.plotting import Plotter

        # A single finite level cannot form (start < end), so the density
        # fallback drives start/end/size.
        start, end, size = Plotter._posterior_contour_levels(
            density=np.array([[0.0, 10.0]]),
            contour_levels=np.array([5.0]),
        )
        assert start == 10.0 * 0.20
        assert end == 10.0 * 0.95
        assert size == 10.0 * 0.15

    def test_non_increasing_levels_fall_back_to_density(self):
        import numpy as np

        from easydiffraction.display.plotting import Plotter

        # end <= start across the provided levels -> density fallback.
        start, end, size = Plotter._posterior_contour_levels(
            density=np.array([[0.0, 4.0]]),
            contour_levels=np.array([3.0, 3.0]),
        )
        assert start == 4.0 * 0.20
        assert end == 4.0 * 0.95
        assert size == 4.0 * 0.15


# ------------------------------------------------------------------
# Plotter._posterior_pair_correlation_value / _contour_colorscales
# ------------------------------------------------------------------


class TestPosteriorPairCorrelation:
    def test_too_few_finite_points_returns_none(self):
        import numpy as np

        from easydiffraction.display.plotting import Plotter

        assert (
            Plotter._posterior_pair_correlation_value(np.array([np.nan]), np.array([1.0])) is None
        )

    def test_positive_correlation(self):
        import numpy as np

        from easydiffraction.display.plotting import Plotter

        x = np.array([1.0, 2.0, 3.0, 4.0])
        y = np.array([2.0, 4.0, 6.0, 8.0])
        value = Plotter._posterior_pair_correlation_value(x, y)
        assert value == pytest.approx(1.0)

    def test_non_finite_correlation_returns_none(self):
        import numpy as np

        from easydiffraction.display.plotting import Plotter

        # Constant y -> correlation undefined (nan) -> None. The source's
        # np.corrcoef call divides by a zero std, so silence that warning.
        x = np.array([1.0, 2.0, 3.0])
        y = np.array([5.0, 5.0, 5.0])
        with np.errstate(invalid='ignore'):
            assert Plotter._posterior_pair_correlation_value(x, y) is None

    def test_colorscales_negative_uses_negative_palette(self):
        import numpy as np

        from easydiffraction.display.plotting import POSTERIOR_NEGATIVE_CONTOUR_FILL_COLORSCALE
        from easydiffraction.display.plotting import POSTERIOR_NEGATIVE_CONTOUR_LINE_COLORSCALE
        from easydiffraction.display.plotting import Plotter

        x = np.array([1.0, 2.0, 3.0, 4.0])
        y = np.array([8.0, 6.0, 4.0, 2.0])
        fill, line = Plotter._posterior_pair_contour_colorscales(x, y)
        assert fill == POSTERIOR_NEGATIVE_CONTOUR_FILL_COLORSCALE
        assert line == POSTERIOR_NEGATIVE_CONTOUR_LINE_COLORSCALE

    def test_colorscales_positive_uses_positive_palette(self):
        import numpy as np

        from easydiffraction.display.plotting import POSTERIOR_CONTOUR_FILL_COLORSCALE
        from easydiffraction.display.plotting import POSTERIOR_CONTOUR_LINE_COLORSCALE
        from easydiffraction.display.plotting import Plotter

        x = np.array([1.0, 2.0, 3.0, 4.0])
        y = np.array([2.0, 4.0, 6.0, 8.0])
        fill, line = Plotter._posterior_pair_contour_colorscales(x, y)
        assert fill == POSTERIOR_CONTOUR_FILL_COLORSCALE
        assert line == POSTERIOR_CONTOUR_LINE_COLORSCALE


# ------------------------------------------------------------------
# Plotter._posterior_distribution histogram / axis-range helpers
# ------------------------------------------------------------------


class TestPosteriorDistributionHelpers:
    def test_histogram_bin_edges_empty_returns_none(self):
        import numpy as np

        from easydiffraction.display.plotting import Plotter

        assert Plotter._posterior_distribution_histogram_bin_edges(np.array([np.nan])) is None

    def test_histogram_bin_edges_for_real_data(self):
        import numpy as np

        from easydiffraction.display.plotting import Plotter

        edges = Plotter._posterior_distribution_histogram_bin_edges(np.linspace(0.0, 1.0, 50))
        assert edges is not None
        assert edges.ndim == 1
        assert edges.size >= 2

    def test_histogram_density_none_edges_returns_none(self):
        import numpy as np

        from easydiffraction.display.plotting import Plotter

        assert Plotter._posterior_distribution_histogram_density(np.array([1.0]), None) is None

    def test_histogram_density_matches_edges(self):
        import numpy as np

        from easydiffraction.display.plotting import Plotter

        values = np.array([0.0, 0.5, 1.0, 0.5, 0.25])
        edges = np.array([0.0, 0.5, 1.0])
        density = Plotter._posterior_distribution_histogram_density(values, edges)
        assert density is not None
        assert density.shape == (2,)

    def test_x_axis_range_prefers_density_trace(self):
        from types import SimpleNamespace

        import numpy as np

        from easydiffraction.display.plotting import Plotter

        density_trace = SimpleNamespace(x=np.array([1.0, 2.0, 3.0]))
        result = Plotter._posterior_distribution_x_axis_range(
            values=np.array([0.0]),
            density_trace=density_trace,
            histogram_bin_edges=None,
        )
        assert result == (1.0, 3.0)

    def test_x_axis_range_uses_histogram_edges(self):
        import numpy as np

        from easydiffraction.display.plotting import Plotter

        result = Plotter._posterior_distribution_x_axis_range(
            values=np.array([0.0]),
            density_trace=None,
            histogram_bin_edges=np.array([2.0, 4.0, 6.0]),
        )
        assert result == (2.0, 6.0)

    def test_x_axis_range_falls_back_to_values(self):
        import numpy as np

        from easydiffraction.display.plotting import Plotter

        result = Plotter._posterior_distribution_x_axis_range(
            values=np.array([3.0, 1.0, 2.0, np.nan]),
            density_trace=None,
            histogram_bin_edges=None,
        )
        assert result == (1.0, 3.0)

    def test_x_axis_range_no_finite_values_returns_none(self):
        import numpy as np

        from easydiffraction.display.plotting import Plotter

        result = Plotter._posterior_distribution_x_axis_range(
            values=np.array([np.nan, np.inf]),
            density_trace=None,
            histogram_bin_edges=None,
        )
        assert result is None

    def test_y_axis_range_none_when_no_density_sources(self):
        import numpy as np

        from easydiffraction.display.plotting import Plotter

        p = Plotter()
        result = p._posterior_distribution_y_axis_range(
            values=np.array([np.nan]),
            density_trace=None,
            histogram_bin_edges=None,
        )
        assert result is None

    def test_y_axis_range_combines_histogram_and_density(self):
        from types import SimpleNamespace

        import numpy as np

        from easydiffraction.display.plotting import Plotter

        p = Plotter()
        density_trace = SimpleNamespace(y=np.array([0.5, 0.9]))
        result = p._posterior_distribution_y_axis_range(
            values=np.array([0.0, 0.5, 1.0, 0.5]),
            density_trace=density_trace,
            histogram_bin_edges=np.array([0.0, 0.5, 1.0]),
        )
        assert result is not None
        lower, upper = result
        assert lower == 0.0
        assert upper > 0.0


# ------------------------------------------------------------------
# Plotter._posterior_pair_density_surface (success path + edge cases)
# ------------------------------------------------------------------


class TestPosteriorPairDensitySurface:
    def test_too_few_samples_returns_none(self):
        import numpy as np

        from easydiffraction.display.plotting import Plotter

        surface = Plotter._posterior_pair_density_surface(
            x_values=np.array([1.0]),
            y_values=np.array([1.0]),
            x_bounds=(0.0, 2.0),
            y_bounds=(0.0, 2.0),
        )
        assert surface is None

    def test_constant_x_and_y_returns_none(self):
        import numpy as np

        from easydiffraction.display.plotting import Plotter

        surface = Plotter._posterior_pair_density_surface(
            x_values=np.full(10, 3.0),
            y_values=np.full(10, 5.0),
            x_bounds=(2.0, 4.0),
            y_bounds=(4.0, 6.0),
        )
        assert surface is None

    def test_correlated_cloud_returns_surface(self):
        import numpy as np

        from easydiffraction.display.plotting import Plotter

        rng = np.random.default_rng(1)
        x = rng.normal(0.0, 1.0, size=400)
        y = x * 0.8 + rng.normal(0.0, 0.4, size=400)
        surface = Plotter._posterior_pair_density_surface(
            x_values=x,
            y_values=y,
            x_bounds=(float(x.min()), float(x.max())),
            y_bounds=(float(y.min()), float(y.max())),
            grid_size=24,
        )
        assert surface is not None
        x_grid, y_grid, density = surface
        assert x_grid.shape == (24,)
        assert y_grid.shape == (24,)
        assert density.shape == (24, 24)
        assert np.all(np.isfinite(density))


# ------------------------------------------------------------------
# Plotter._posterior_predictive_sampling_inputs / _parameters
# ------------------------------------------------------------------


class TestPosteriorPredictiveSamplingInputs:
    def test_no_posterior_samples_returns_none(self):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter

        fit_results = SimpleNamespace(posterior_samples=None)
        assert Plotter._posterior_predictive_sampling_inputs(fit_results) is None

    def test_bad_dimensionality_warns_and_returns_none(self, monkeypatch, capsys):
        from types import SimpleNamespace

        import numpy as np

        from easydiffraction.display.plotting import Plotter
        from easydiffraction.utils.logging import Logger

        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)

        posterior_samples = SimpleNamespace(
            flattened=lambda: np.zeros(4),  # 1D -> wrong ndim
            parameter_names=['a', 'b'],
        )
        fit_results = SimpleNamespace(posterior_samples=posterior_samples)
        assert Plotter._posterior_predictive_sampling_inputs(fit_results) is None
        assert 'unavailable for predictive summaries' in capsys.readouterr().out

    def test_valid_inputs_returned(self):
        from types import SimpleNamespace

        import numpy as np

        from easydiffraction.display.plotting import Plotter

        posterior_samples = SimpleNamespace(
            flattened=lambda: np.zeros((5, 2)),
            parameter_names=['a', 'b'],
        )
        fit_results = SimpleNamespace(posterior_samples=posterior_samples)
        flattened, names = Plotter._posterior_predictive_sampling_inputs(fit_results)
        assert flattened.shape == (5, 2)
        assert names == ['a', 'b']

    def test_parameters_resolved_in_order(self):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter

        p_a = SimpleNamespace(unique_name='a')
        p_b = SimpleNamespace(unique_name='b')
        fit_results = SimpleNamespace(parameters=[p_b, p_a])
        result = Plotter._posterior_predictive_parameters(
            fit_results=fit_results,
            parameter_names=['a', 'b'],
        )
        assert result == [p_a, p_b]

    def test_missing_parameter_warns_and_returns_none(self, monkeypatch, capsys):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter
        from easydiffraction.utils.logging import Logger

        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)

        fit_results = SimpleNamespace(parameters=[SimpleNamespace(unique_name='a')])
        result = Plotter._posterior_predictive_parameters(
            fit_results=fit_results,
            parameter_names=['a', 'missing'],
        )
        assert result is None
        assert "matching fitted parameters for 'missing'" in capsys.readouterr().out


# ------------------------------------------------------------------
# Plotter._evaluate_posterior_predictive_state
# ------------------------------------------------------------------


class TestEvaluatePosteriorPredictiveState:
    def test_missing_calc_data_warns_and_returns_none(self, monkeypatch, capsys):
        from types import SimpleNamespace

        import numpy as np

        import easydiffraction.display.plotting as mod
        from easydiffraction.display.plotting import Plotter
        from easydiffraction.display.plotting import XAxisType
        from easydiffraction.utils.logging import Logger

        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)

        applied = []

        class Param:
            def _set_value_from_minimizer(self, value):
                applied.append(value)

        # Pattern is missing intensity_calc -> warning.
        pattern = SimpleNamespace(two_theta=np.array([1.0]), intensity_calc=None)
        monkeypatch.setattr(mod, 'intensity_category_for', lambda experiment: pattern)

        p = Plotter()
        monkeypatch.setattr(Plotter, '_update_project_categories', lambda self, expt_name: None)

        y_calc, x_values = p._evaluate_posterior_predictive_state(
            sampled_parameters=[Param()],
            values=np.array([1.5]),
            experiment=object(),
            expt_name='E1',
            x_axis=XAxisType.TWO_THETA,
        )
        assert y_calc is None
        assert x_values is None
        assert applied == [1.5]
        assert 'Posterior predictive data is unavailable' in capsys.readouterr().out

    def test_returns_arrays_when_available(self, monkeypatch):
        from types import SimpleNamespace

        import numpy as np

        import easydiffraction.display.plotting as mod
        from easydiffraction.display.plotting import Plotter
        from easydiffraction.display.plotting import XAxisType

        class Param:
            def _set_value_from_minimizer(self, value):
                pass

        pattern = SimpleNamespace(
            two_theta=np.array([1.0, 2.0]),
            intensity_calc=np.array([10.0, 20.0]),
        )
        monkeypatch.setattr(mod, 'intensity_category_for', lambda experiment: pattern)

        p = Plotter()
        monkeypatch.setattr(Plotter, '_update_project_categories', lambda self, expt_name: None)

        y_calc, x_values = p._evaluate_posterior_predictive_state(
            sampled_parameters=[Param()],
            values=np.array([1.5]),
            experiment=object(),
            expt_name='E1',
            x_axis=XAxisType.TWO_THETA,
        )
        np.testing.assert_allclose(y_calc, [10.0, 20.0])
        np.testing.assert_allclose(x_values, [1.0, 2.0])


# ------------------------------------------------------------------
# Plotter._filtered_posterior_predictive_summary
# ------------------------------------------------------------------


class TestFilteredPosteriorPredictiveSummary:
    def test_empty_after_filter_returns_none(self):
        from easydiffraction.analysis.fit_helpers.bayesian import PosteriorPredictiveSummary
        from easydiffraction.display.plotting import Plotter

        summary = PosteriorPredictiveSummary(
            experiment_name='E1',
            x_axis_name='two_theta',
            x=np.array([1.0, 2.0, 3.0]),
            best_sample_prediction=np.array([1.0, 2.0, 3.0]),
            lower_95=np.array([0.5, 1.5, 2.5]),
            upper_95=np.array([1.5, 2.5, 3.5]),
            lower_68=np.array([0.8, 1.8, 2.8]),
            upper_68=np.array([1.2, 2.2, 3.2]),
            draws=None,
        )
        p = Plotter()
        # Window entirely outside the data range -> no points remain.
        result = p._filtered_posterior_predictive_summary(
            summary=summary,
            x_min=100.0,
            x_max=200.0,
            include_draws=False,
        )
        assert result is None

    def test_filters_band_and_draws(self):
        from easydiffraction.analysis.fit_helpers.bayesian import PosteriorPredictiveSummary
        from easydiffraction.display.plotting import Plotter

        summary = PosteriorPredictiveSummary(
            experiment_name='E1',
            x_axis_name='two_theta',
            x=np.array([1.0, 2.0, 3.0]),
            best_sample_prediction=np.array([10.0, 20.0, 30.0]),
            lower_95=np.array([9.0, 19.0, 29.0]),
            upper_95=np.array([11.0, 21.0, 31.0]),
            lower_68=np.array([9.5, 19.5, 29.5]),
            upper_68=np.array([10.5, 20.5, 30.5]),
            draws=np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]),
        )
        p = Plotter()
        result = p._filtered_posterior_predictive_summary(
            summary=summary,
            x_min=1.5,
            x_max=2.5,
            include_draws=True,
        )
        assert result is not None
        np.testing.assert_allclose(result.x, [2.0])
        np.testing.assert_allclose(result.best_sample_prediction, [20.0])
        np.testing.assert_allclose(result.lower_95, [19.0])
        assert result.draws is not None
        assert result.draws.shape == (2, 1)
        np.testing.assert_allclose(result.draws[:, 0], [2.0, 5.0])

    def test_none_band_arrays_stay_none(self):
        from easydiffraction.analysis.fit_helpers.bayesian import PosteriorPredictiveSummary
        from easydiffraction.display.plotting import Plotter

        summary = PosteriorPredictiveSummary(
            experiment_name='E1',
            x_axis_name='two_theta',
            x=np.array([1.0, 2.0, 3.0]),
            best_sample_prediction=np.array([10.0, 20.0, 30.0]),
            lower_95=None,
            upper_95=None,
            lower_68=None,
            upper_68=None,
            draws=None,
        )
        p = Plotter()
        result = p._filtered_posterior_predictive_summary(
            summary=summary,
            x_min=1.5,
            x_max=2.5,
            include_draws=True,
        )
        assert result is not None
        assert result.lower_95 is None
        assert result.upper_95 is None
        assert result.draws is None


# ------------------------------------------------------------------
# Plotter.plot_posterior_predictive routing and validation
# ------------------------------------------------------------------


class TestPlotPosteriorPredictiveRouting:
    def test_single_crystal_non_plotly_warns(self, monkeypatch, capsys):
        from types import SimpleNamespace

        from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
        from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
        from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum
        from easydiffraction.display.plotting import Plotter
        from easydiffraction.utils.logging import Logger

        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)

        class ExptType:
            sample_form = type('SF', (), {'value': SampleFormEnum.SINGLE_CRYSTAL})()
            scattering_type = type('S', (), {'value': ScatteringTypeEnum.BRAGG})()
            beam_mode = type('B', (), {'value': BeamModeEnum.CONSTANT_WAVELENGTH})()

        experiment = SimpleNamespace(type=ExptType())
        project = SimpleNamespace(experiments={'E1': experiment})

        p = Plotter()
        p.engine = 'asciichartpy'
        p._set_project(project)
        monkeypatch.setattr(Plotter, '_update_project_categories', lambda self, expt_name: None)

        p.plot_posterior_predictive('E1', x='intensity_calc')
        assert 'require the Plotly backend' in capsys.readouterr().out


# ------------------------------------------------------------------
# Plotter._plot_single_crystal_posterior_predictive (validation warnings)
# ------------------------------------------------------------------


class TestSingleCrystalPosteriorPredictiveValidation:
    def _plotter(self, monkeypatch):
        from easydiffraction.display.plotting import Plotter

        p = Plotter()
        p.engine = 'plotly'
        monkeypatch.setattr(Plotter, '_update_project_categories', lambda self, expt_name: None)
        return p

    def test_non_bragg_scattering_warns(self, monkeypatch, capsys):
        from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum
        from easydiffraction.display.plotting import XAxisType
        from easydiffraction.utils.logging import Logger

        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)

        p = self._plotter(monkeypatch)
        p._plot_single_crystal_posterior_predictive(
            experiment=object(),
            expt_name='E1',
            x_axis=XAxisType.INTENSITY_CALC,
            scattering_type=ScatteringTypeEnum.TOTAL,
            plot_options=_options(),
            style='band',
        )
        assert 'support Bragg data only' in capsys.readouterr().out

    def test_unsupported_x_axis_warns(self, monkeypatch, capsys):
        from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum
        from easydiffraction.display.plotting import XAxisType
        from easydiffraction.utils.logging import Logger

        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)

        p = self._plotter(monkeypatch)
        p._plot_single_crystal_posterior_predictive(
            experiment=object(),
            expt_name='E1',
            x_axis=XAxisType.TWO_THETA,
            scattering_type=ScatteringTypeEnum.BRAGG,
            plot_options=_options(),
            style='band',
        )
        assert "x='intensity_calc' only" in capsys.readouterr().out


def _options(**overrides):
    """Build a _MeasVsCalcPlotOptions with sensible defaults."""
    from easydiffraction.display.plotting import _MeasVsCalcPlotOptions

    defaults = {
        'x_min': None,
        'x_max': None,
        'show_residual': None,
        'show_excluded': False,
        'x': None,
    }
    defaults.update(overrides)
    return _MeasVsCalcPlotOptions(**defaults)


# ------------------------------------------------------------------
# Plotter._plot_single_crystal_posterior_predictive_summary (shape guards)
# ------------------------------------------------------------------


class TestSingleCrystalPosteriorPredictiveSummary:
    def test_missing_intervals_warns(self, monkeypatch, capsys):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter
        from easydiffraction.utils.logging import Logger

        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)

        summary = SimpleNamespace(
            best_sample_prediction=np.array([1.0, 2.0]),
            lower_95=None,
            upper_95=None,
        )
        p = Plotter()
        p._plot_single_crystal_posterior_predictive_summary(
            expt_name='E1',
            summary=summary,
            y_meas=np.array([1.0, 2.0]),
            y_meas_su=np.array([0.1, 0.1]),
            axes_labels=['x', 'y'],
        )
        assert 'require 95% predictive intervals' in capsys.readouterr().out

    def test_invalid_interval_shapes_warn(self, monkeypatch, capsys):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter
        from easydiffraction.utils.logging import Logger

        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)

        summary = SimpleNamespace(
            best_sample_prediction=np.array([1.0, 2.0]),
            lower_95=np.array([0.5]),  # wrong shape
            upper_95=np.array([1.5, 2.5]),
        )
        p = Plotter()
        p._plot_single_crystal_posterior_predictive_summary(
            expt_name='E1',
            summary=summary,
            y_meas=np.array([1.0, 2.0]),
            y_meas_su=np.array([0.1, 0.1]),
            axes_labels=['x', 'y'],
        )
        assert 'interval arrays have invalid shapes' in capsys.readouterr().out

    def test_valid_summary_builds_figure_with_diagonal(self, monkeypatch):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter

        summary = SimpleNamespace(
            best_sample_prediction=np.array([1.0, 2.0, 3.0]),
            lower_95=np.array([0.8, 1.8, 2.8]),
            upper_95=np.array([1.2, 2.2, 3.2]),
        )
        captured = {}
        p = Plotter()
        monkeypatch.setattr(p, '_show_plot_figure', lambda fig: captured.update(fig=fig))
        p._plot_single_crystal_posterior_predictive_summary(
            expt_name='E1',
            summary=summary,
            y_meas=np.array([1.1, 2.1, 2.9]),
            y_meas_su=np.array([0.1, 0.1, 0.1]),
            axes_labels=['calc', 'meas'],
        )
        # A single y=x diagonal reference line spanning the padded range.
        shapes = captured['fig'].layout.shapes
        assert len(shapes) == 1
        diagonal = shapes[0]
        assert diagonal.type == 'line'
        assert diagonal.x0 == diagonal.y0
        assert diagonal.x1 == diagonal.y1
        assert diagonal.x1 > diagonal.x0


# ------------------------------------------------------------------
# Plotter._bragg_tick_x_values routing (d_spacing branch)
# ------------------------------------------------------------------


class TestBraggTickXValuesRouting:
    def test_d_spacing_routes_to_d_spacing_helper(self):
        from types import SimpleNamespace

        import numpy as np

        from easydiffraction.display.plotting import Plotter
        from easydiffraction.display.plotting import XAxisType

        refln = SimpleNamespace(d_spacing=np.array([1.1, 2.2]))
        result = Plotter._bragg_tick_x_values(
            refln=refln,
            experiment=object(),
            expt_name='E1',
            x_axis=XAxisType.D_SPACING,
        )
        np.testing.assert_allclose(result, [1.1, 2.2])

    def test_time_of_flight_routes_to_attr(self):
        from types import SimpleNamespace

        import numpy as np

        from easydiffraction.display.plotting import Plotter
        from easydiffraction.display.plotting import XAxisType

        refln = SimpleNamespace(time_of_flight=np.array([100.0, 200.0]))
        result = Plotter._bragg_tick_x_values(
            refln=refln,
            experiment=object(),
            expt_name='E1',
            x_axis=XAxisType.TIME_OF_FLIGHT,
        )
        np.testing.assert_allclose(result, [100.0, 200.0])


# ------------------------------------------------------------------
# Plotter._bragg_tick_mask / _group_bragg_tick_sets
# ------------------------------------------------------------------


class TestBraggTickMaskAndGrouping:
    def test_mask_uses_defaults_when_bounds_none(self):
        import numpy as np

        from easydiffraction.display.plotting import Plotter

        x = np.array([-1e9, 0.0, 1e9])
        mask = Plotter._bragg_tick_mask(x, x_min=None, x_max=None)
        # The default range spans the whole representable window.
        assert mask.tolist() == [True, True, True]

    def test_mask_respects_explicit_bounds(self):
        import numpy as np

        from easydiffraction.display.plotting import Plotter

        x = np.array([0.0, 1.0, 2.0, 3.0])
        mask = Plotter._bragg_tick_mask(x, x_min=1.0, x_max=2.0)
        assert mask.tolist() == [False, True, True, False]

    def test_group_splits_by_phase(self):
        import numpy as np

        from easydiffraction.display.plotting import Plotter

        arrays = {
            'phase_id': np.array(['a', 'a', 'b']),
            'index_h': np.array([1, 2, 3]),
            'index_k': np.array([0, 0, 0]),
            'index_l': np.array([1, 1, 1]),
            'f_squared_calc': np.array([10.0, 20.0, 30.0]),
            'f_calc': np.array([3.0, 4.0, 5.0]),
            'x': np.array([0.5, 1.5, 2.5]),
        }
        mask = np.array([True, True, True])
        tick_sets = Plotter._group_bragg_tick_sets(arrays=arrays, mask=mask)
        assert [ts.phase_id for ts in tick_sets] == ['a', 'b']
        np.testing.assert_allclose(tick_sets[0].x, [0.5, 1.5])
        np.testing.assert_allclose(tick_sets[1].f_calc, [5.0])


# ------------------------------------------------------------------
# Plotter._extract_bragg_tick_sets (empty-mask short-circuit)
# ------------------------------------------------------------------


class TestExtractBraggTickSetsEmptyMask:
    def test_no_ticks_in_window_returns_empty(self):
        import numpy as np

        from easydiffraction.display.plotting import Plotter
        from easydiffraction.display.plotting import XAxisType

        class Refln:
            phase_id = np.array(['phase-a'])
            two_theta = np.array([5.0])
            index_h = np.array([1])
            index_k = np.array([0])
            index_l = np.array([1])
            f_squared_calc = np.array([10.0])
            f_calc = np.array([3.0])

        class Experiment:
            refln = Refln()

        result = Plotter()._extract_bragg_tick_sets(
            experiment=Experiment(),
            expt_name='E1',
            x_axis=XAxisType.TWO_THETA,
            x_min=100.0,
            x_max=200.0,
        )
        assert result == ()


# ------------------------------------------------------------------
# Plotter._get_axes_labels / _filtered_optional_y_array
# ------------------------------------------------------------------


class TestAxesLabelsAndOptionalFilter:
    def test_get_axes_labels_returns_pair(self):
        from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
        from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum
        from easydiffraction.display.plotters.base import XAxisType
        from easydiffraction.display.plotting import Plotter

        labels = Plotter._get_axes_labels(
            SampleFormEnum.POWDER.value,
            ScatteringTypeEnum.BRAGG.value,
            XAxisType.TWO_THETA,
        )
        assert isinstance(labels, list)
        assert len(labels) == 2

    def test_filtered_optional_y_array_none_passthrough(self):
        import numpy as np

        from easydiffraction.display.plotting import Plotter

        p = Plotter()
        x = np.array([0.0, 1.0, 2.0])
        assert p._filtered_optional_y_array(None, x, 0.0, 2.0) is None

    def test_filtered_optional_y_array_filters(self):
        import numpy as np

        from easydiffraction.display.plotting import Plotter

        p = Plotter()
        x = np.array([0.0, 1.0, 2.0])
        y = np.array([10.0, 20.0, 30.0])
        result = p._filtered_optional_y_array(y, x, 0.5, 1.5)
        np.testing.assert_allclose(result, [20.0])


# ------------------------------------------------------------------
# Plotter correlation-matrix per-panel grid helpers (real subplots)
# ------------------------------------------------------------------


class TestCorrelationHeatmapPanels:
    def _context(self):
        import numpy as np
        import pandas as pd

        from easydiffraction.display.plotting import _CorrelationHeatmapContext

        # Masked lower-triangle correlation matrix (upper triangle NaN).
        values = np.array([
            [np.nan, np.nan],
            [-0.7, np.nan],
        ])
        corr_df = pd.DataFrame(values, index=['p0', 'p1'], columns=['p0', 'p1'])
        return _CorrelationHeatmapContext(
            corr_df=corr_df,
            row_labels=['p0', 'p1'],
            col_labels=['p0', 'p1'],
            threshold=0.0,
            precision=2,
        )

    def _figure(self):
        make_subplots = __import__('plotly.subplots', fromlist=['make_subplots']).make_subplots
        return make_subplots(rows=2, cols=2)

    def test_populate_panel_adds_value_and_decorations(self):
        from easydiffraction.display.plotting import Plotter

        p = Plotter()
        context = self._context()
        fig = self._figure()
        title_annotations = []
        border_shapes = []
        # Lower-left value cell (row 1, col 0) -> value -0.7 present.
        p._populate_correlation_heatmap_panel(
            fig=fig,
            context=context,
            row_index=1,
            col_index=0,
            subplot_title_annotations=title_annotations,
            subplot_border_shapes=border_shapes,
        )
        # A heatmap trace and a text trace should have been added.
        types = [trace.type for trace in fig.data]
        assert 'heatmap' in types
        assert 'scatter' in types
        # Both an x-axis (col 0) and y-axis (last row) title get collected,
        # plus one border rectangle.
        assert len(title_annotations) == 2
        assert len(border_shapes) == 1

    def test_populate_panel_hides_upper_triangle(self):
        from easydiffraction.display.plotting import Plotter

        p = Plotter()
        context = self._context()
        fig = self._figure()
        title_annotations = []
        border_shapes = []
        # Upper-right cell (row 0, col 1) -> hidden, no traces or shapes.
        p._populate_correlation_heatmap_panel(
            fig=fig,
            context=context,
            row_index=0,
            col_index=1,
            subplot_title_annotations=title_annotations,
            subplot_border_shapes=border_shapes,
        )
        assert len(fig.data) == 0
        assert title_annotations == []
        assert border_shapes == []

    def test_value_panel_below_threshold_skips_text(self):
        import numpy as np
        import pandas as pd

        from easydiffraction.display.plotting import Plotter
        from easydiffraction.display.plotting import _CorrelationHeatmapContext

        corr_df = pd.DataFrame(
            np.array([[np.nan, np.nan], [0.1, np.nan]]),
            index=['p0', 'p1'],
            columns=['p0', 'p1'],
        )
        context = _CorrelationHeatmapContext(
            corr_df=corr_df,
            row_labels=['p0', 'p1'],
            col_labels=['p0', 'p1'],
            threshold=0.5,  # |0.1| < 0.5 -> no text label
            precision=2,
        )
        p = Plotter()
        fig = self._figure()
        p._add_correlation_heatmap_value_panel(
            fig=fig,
            context=context,
            row_index=1,
            col_index=0,
            value=0.1,
        )
        # Only the heatmap cell, no text scatter trace.
        types = [trace.type for trace in fig.data]
        assert types == ['heatmap']


# ------------------------------------------------------------------
# Plotter._resolve_posterior_parameter_names / _name (warning paths)
# ------------------------------------------------------------------


class TestResolvePosteriorParameterNames:
    def test_no_parameter_names_warns(self, monkeypatch, capsys):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter
        from easydiffraction.utils.logging import Logger

        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)

        fit_results = SimpleNamespace(posterior_samples=SimpleNamespace(parameter_names=[]))
        result = Plotter._resolve_posterior_parameter_names(
            fit_results=fit_results,
            parameters=None,
        )
        assert result is None
        assert 'do not expose parameter names' in capsys.readouterr().out

    def test_parameters_none_returns_all_available(self):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter

        fit_results = SimpleNamespace(
            posterior_samples=SimpleNamespace(parameter_names=['a', 'b'])
        )
        result = Plotter._resolve_posterior_parameter_names(
            fit_results=fit_results,
            parameters=None,
        )
        assert result == ['a', 'b']

    def test_object_without_unique_name_warns(self, monkeypatch, capsys):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter
        from easydiffraction.utils.logging import Logger

        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)

        fit_results = SimpleNamespace(
            posterior_samples=SimpleNamespace(parameter_names=['a']),
            parameters=[],
        )
        # An object with unique_name None triggers the guard.
        result = Plotter._resolve_posterior_parameter_names(
            fit_results=fit_results,
            parameters=[SimpleNamespace(unique_name=None)],
        )
        assert result is None
        assert 'expects parameter objects' in capsys.readouterr().out

    def test_object_unique_name_not_available_warns(self, monkeypatch, capsys):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter
        from easydiffraction.utils.logging import Logger

        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)

        fit_results = SimpleNamespace(
            posterior_samples=SimpleNamespace(parameter_names=['a']),
            parameters=[],
        )
        result = Plotter._resolve_posterior_parameter_names(
            fit_results=fit_results,
            parameters=[SimpleNamespace(unique_name='zzz')],
        )
        assert result is None
        assert 'do not contain the selected parameter' in capsys.readouterr().out

    def test_object_unique_name_resolved(self):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter

        fit_results = SimpleNamespace(
            posterior_samples=SimpleNamespace(parameter_names=['a', 'b']),
            parameters=[],
        )
        result = Plotter._resolve_posterior_parameter_names(
            fit_results=fit_results,
            parameters=[SimpleNamespace(unique_name='b')],
        )
        assert result == ['b']

    def test_empty_string_selection_warns(self, monkeypatch, capsys):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter
        from easydiffraction.utils.logging import Logger

        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)

        fit_results = SimpleNamespace(
            posterior_samples=SimpleNamespace(parameter_names=['a']),
            parameters=[],
            posterior_parameter_summaries=[],
        )
        result = Plotter._resolve_posterior_parameter_names(
            fit_results=fit_results,
            parameters=['   '],
        )
        assert result is None
        assert 'cannot use an empty string' in capsys.readouterr().out

    def test_string_exact_unique_name_match(self):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter

        fit_results = SimpleNamespace(
            posterior_samples=SimpleNamespace(parameter_names=['a', 'b']),
            parameters=[],
            posterior_parameter_summaries=[],
        )
        result = Plotter._resolve_posterior_parameter_names(
            fit_results=fit_results,
            parameters=['a'],
        )
        assert result == ['a']

    def test_string_no_match_warns(self, monkeypatch, capsys):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter
        from easydiffraction.utils.logging import Logger

        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)

        fit_results = SimpleNamespace(
            posterior_samples=SimpleNamespace(parameter_names=['a']),
            parameters=[],
            posterior_parameter_summaries=[],
        )
        result = Plotter._resolve_posterior_parameter_names(
            fit_results=fit_results,
            parameters=['nonexistent'],
        )
        assert result is None
        assert 'do not contain the selected parameter or label' in capsys.readouterr().out

    def test_string_resolves_via_short_name_candidate(self):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter

        parameter = SimpleNamespace(unique_name='phase.cell.length_a', name='length_a')
        fit_results = SimpleNamespace(
            posterior_samples=SimpleNamespace(parameter_names=['phase.cell.length_a']),
            parameters=[parameter],
            posterior_parameter_summaries=[],
        )
        result = Plotter._resolve_posterior_parameter_names(
            fit_results=fit_results,
            parameters=['length_a'],
        )
        assert result == ['phase.cell.length_a']


# ------------------------------------------------------------------
# Plotter._correlation_dataframe_from_persisted_projection
# ------------------------------------------------------------------


def _corr_row(i_name, j_name, value, source_kind):
    from types import SimpleNamespace

    return SimpleNamespace(
        param_unique_name_i=SimpleNamespace(value=i_name),
        param_unique_name_j=SimpleNamespace(value=j_name),
        correlation=SimpleNamespace(value=value),
        source_kind=SimpleNamespace(value=source_kind),
    )


class TestCorrelationDataframeFromPersistedProjection:
    def _project_with_rows(self, rows, result_kind_value):
        from types import SimpleNamespace

        analysis = SimpleNamespace(
            fit_result=SimpleNamespace(
                result_kind=SimpleNamespace(value=result_kind_value),
            ),
            fit_parameter_correlations=rows,
        )
        return SimpleNamespace(analysis=analysis)

    def test_no_project_returns_none(self):
        from easydiffraction.display.plotting import Plotter

        p = Plotter()
        p._project = None
        assert p._correlation_dataframe_from_persisted_projection(object()) is None

    def test_no_matching_rows_returns_none(self):
        from types import SimpleNamespace

        from easydiffraction.analysis.enums import FitResultKindEnum
        from easydiffraction.display.plotting import Plotter

        # No correlation rows at all -> None.
        project = self._project_with_rows([], FitResultKindEnum.BAYESIAN.value)
        p = Plotter()
        p._set_project(project)
        fit_results = SimpleNamespace(parameters=[], posterior_parameter_summaries=[])
        assert p._correlation_dataframe_from_persisted_projection(fit_results) is None

    def test_builds_symmetric_matrix_from_rows(self):
        from types import SimpleNamespace

        import numpy as np

        from easydiffraction.analysis.enums import FitResultKindEnum
        from easydiffraction.display.plotting import FitCorrelationSourceEnum
        from easydiffraction.display.plotting import Plotter

        rows = [
            _corr_row('p1', 'p2', 0.4, FitCorrelationSourceEnum.DETERMINISTIC.value),
        ]
        project = self._project_with_rows(rows, FitResultKindEnum.DETERMINISTIC.value)
        p = Plotter()
        p._set_project(project)
        fit_results = SimpleNamespace(
            parameters=[
                SimpleNamespace(unique_name='p1'),
                SimpleNamespace(unique_name='p2'),
            ],
            posterior_parameter_summaries=[],
        )
        corr_df = p._correlation_dataframe_from_persisted_projection(fit_results)
        assert corr_df is not None
        np.testing.assert_allclose(corr_df.loc['p1', 'p2'], 0.4)
        np.testing.assert_allclose(corr_df.loc['p2', 'p1'], 0.4)
        np.testing.assert_allclose(np.diag(corr_df.to_numpy()), [1.0, 1.0])

    def test_too_few_parameters_returns_none(self):
        from types import SimpleNamespace

        from easydiffraction.analysis.enums import FitResultKindEnum
        from easydiffraction.display.plotting import FitCorrelationSourceEnum
        from easydiffraction.display.plotting import Plotter

        # A single self-correlation row yields only one unique name -> None.
        rows = [
            _corr_row('p1', 'p1', 1.0, FitCorrelationSourceEnum.DETERMINISTIC.value),
        ]
        project = self._project_with_rows(rows, FitResultKindEnum.DETERMINISTIC.value)
        p = Plotter()
        p._set_project(project)
        fit_results = SimpleNamespace(parameters=[], posterior_parameter_summaries=[])
        assert p._correlation_dataframe_from_persisted_projection(fit_results) is None

    def test_uses_posterior_source_for_bayesian(self):
        from types import SimpleNamespace

        from easydiffraction.analysis.enums import FitResultKindEnum
        from easydiffraction.display.plotting import FitCorrelationSourceEnum
        from easydiffraction.display.plotting import Plotter

        # Deterministic rows are ignored when the fit kind is Bayesian.
        rows = [
            _corr_row('p1', 'p2', 0.4, FitCorrelationSourceEnum.DETERMINISTIC.value),
        ]
        project = self._project_with_rows(rows, FitResultKindEnum.BAYESIAN.value)
        p = Plotter()
        p._set_project(project)
        fit_results = SimpleNamespace(parameters=[], posterior_parameter_summaries=[])
        assert p._correlation_dataframe_from_persisted_projection(fit_results) is None

    def test_names_fall_back_to_summaries(self):
        from types import SimpleNamespace

        import numpy as np

        from easydiffraction.analysis.enums import FitResultKindEnum
        from easydiffraction.display.plotting import FitCorrelationSourceEnum
        from easydiffraction.display.plotting import Plotter

        rows = [
            _corr_row('s1', 's2', -0.3, FitCorrelationSourceEnum.POSTERIOR.value),
        ]
        project = self._project_with_rows(rows, FitResultKindEnum.BAYESIAN.value)
        p = Plotter()
        p._set_project(project)
        # No parameter unique names -> names come from summaries.
        fit_results = SimpleNamespace(
            parameters=[],
            posterior_parameter_summaries=[
                SimpleNamespace(unique_name='s1'),
                SimpleNamespace(unique_name='s2'),
            ],
        )
        corr_df = p._correlation_dataframe_from_persisted_projection(fit_results)
        assert corr_df is not None
        np.testing.assert_allclose(corr_df.loc['s1', 's2'], -0.3)


# ------------------------------------------------------------------
# Plotter._correlation_dataframe_from_engine_result
# ------------------------------------------------------------------


class TestCorrelationDataframeFromEngineResult:
    def test_uses_covariance_when_present(self):
        from types import SimpleNamespace

        import numpy as np

        from easydiffraction.display.plotting import Plotter

        raw = SimpleNamespace(
            covar=np.array([[4.0, 1.0], [1.0, 9.0]]),
            var_names=['p1', 'p2'],
        )
        p = Plotter()
        corr_df = p._correlation_dataframe_from_engine_result(raw_result=raw, parameters=[])
        np.testing.assert_allclose(np.diag(corr_df.to_numpy()), [1.0, 1.0])

    def test_falls_back_to_engine_params_when_no_covariance(self, monkeypatch):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter

        raw = SimpleNamespace(covar=None, var_names=['p1', 'p2'])
        sentinel = object()
        monkeypatch.setattr(
            Plotter,
            '_get_param_correlation_dataframe_from_engine_params',
            lambda self, *, raw_result, parameters: sentinel,
        )
        p = Plotter()
        result = p._correlation_dataframe_from_engine_result(raw_result=raw, parameters=[])
        assert result is sentinel


# ------------------------------------------------------------------
# Plotter._plot_posterior_predictive_summary (Plotly band+draws path)
# ------------------------------------------------------------------


class TestPlotPosteriorPredictiveSummaryPlotly:
    def _plotter(self):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter

        captured = {}
        p = Plotter()
        p.engine = 'plotly'
        p._backend = SimpleNamespace(_show_figure=lambda fig: captured.setdefault('fig', fig))
        return p, captured

    def test_band_draws_and_excluded_render_traces(self):
        from types import SimpleNamespace

        p, captured = self._plotter()
        summary = SimpleNamespace(
            x=np.array([1.0, 2.0, 3.0]),
            lower_95=np.array([8.0, 9.0, 10.0]),
            upper_95=np.array([10.0, 11.0, 12.0]),
            best_sample_prediction=np.array([9.0, 10.0, 11.0]),
            draws=np.array([[8.5, 9.5, 10.5], [9.0, 10.0, 11.0]]),
        )
        p._plot_posterior_predictive_summary(
            expt_name='hrpt',
            summary=summary,
            y_meas=np.array([9.5, 10.5, 11.5]),
            axes_labels=['2θ', 'Intensity'],
            show_band=True,
            show_draws=True,
            excluded_ranges=((1.2, 1.4),),
        )
        fig = captured['fig']
        names = {trace.name for trace in fig.data}
        assert '95% credible interval' in names
        assert 'Posterior draw' in names
        assert 'Measured' in names
        assert 'Best posterior sample' in names
        # The excluded region adds a vrect shape.
        assert len(fig.layout.shapes) >= 1

    def test_draws_unavailable_warns(self, monkeypatch, capsys):
        from types import SimpleNamespace

        from easydiffraction.utils.logging import Logger

        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)

        p, _ = self._plotter()
        summary = SimpleNamespace(
            x=np.array([1.0, 2.0]),
            lower_95=np.array([8.0, 9.0]),
            upper_95=np.array([10.0, 11.0]),
            best_sample_prediction=np.array([9.0, 10.0]),
            draws=None,
        )
        p._plot_posterior_predictive_summary(
            expt_name='hrpt',
            summary=summary,
            y_meas=np.array([9.5, 10.5]),
            axes_labels=['2θ', 'Intensity'],
            show_band=False,
            show_draws=True,
        )
        assert 'draws are unavailable for plotting' in capsys.readouterr().out


# ------------------------------------------------------------------
# Plotter._plot_posterior_predictive_data (Plotly composite path)
# ------------------------------------------------------------------


class TestPlotPosteriorPredictiveDataPlotly:
    def _experiment(self):
        from types import SimpleNamespace

        from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
        from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
        from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum

        expt_type = SimpleNamespace(
            sample_form=SimpleNamespace(value=SampleFormEnum.POWDER),
            scattering_type=SimpleNamespace(value=ScatteringTypeEnum.BRAGG),
            beam_mode=SimpleNamespace(value=BeamModeEnum.CONSTANT_WAVELENGTH),
        )
        pattern = SimpleNamespace(
            two_theta=np.array([1.0, 2.0, 3.0]),
            intensity_meas=np.array([10.0, 12.0, 11.0]),
            intensity_bkg=np.array([1.0, 1.0, 1.0]),
        )
        return SimpleNamespace(type=expt_type, data=pattern)

    def test_plotly_band_draws_builds_composite_spec(self, monkeypatch):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter
        from easydiffraction.display.plotting import XAxisType

        captured = {}
        plotter = Plotter()
        plotter.engine = 'plotly'
        plotter._backend = SimpleNamespace(
            plot_powder_meas_vs_calc=lambda *, plot_spec: captured.setdefault('spec', plot_spec)
        )

        monkeypatch.setattr(
            Plotter,
            '_get_or_build_posterior_predictive_summary',
            lambda self, **kwargs: SimpleNamespace(
                x=np.array([1.0, 2.0, 3.0]),
                lower_95=np.array([8.0, 9.0, 10.0]),
                upper_95=np.array([10.0, 11.0, 12.0]),
                best_sample_prediction=np.array([9.0, 11.0, 10.5]),
                draws=np.array([[8.5, 9.5, 10.5]]),
            ),
        )
        monkeypatch.setattr(Plotter, '_extract_bragg_tick_sets', lambda self, **kwargs: ())

        plotter._plot_posterior_predictive_data(
            experiment=self._experiment(),
            expt_name='hrpt',
            plot_options=SimpleNamespace(
                x_min=None,
                x_max=None,
                show_residual=None,
                show_background=None,
                show_bragg=None,
                show_excluded=False,
                x=None,
            ),
            x_axis=XAxisType.TWO_THETA,
            style='band+draws',
        )

        spec = captured['spec']
        # Band + draws arrays are wired into the composite spec.
        assert spec.predictive_lower_95 is not None
        assert spec.predictive_upper_95 is not None
        assert spec.predictive_draws is not None
        np.testing.assert_allclose(spec.y_bkg, [1.0, 1.0, 1.0])
        assert spec.y_calc_name == 'Best posterior sample'

    def test_plotly_draws_unavailable_warns(self, monkeypatch, capsys):
        from types import SimpleNamespace

        from easydiffraction.display.plotting import Plotter
        from easydiffraction.display.plotting import XAxisType
        from easydiffraction.utils.logging import Logger

        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)

        plotter = Plotter()
        plotter.engine = 'plotly'
        plotter._backend = SimpleNamespace(plot_powder_meas_vs_calc=lambda *, plot_spec: None)
        monkeypatch.setattr(
            Plotter,
            '_get_or_build_posterior_predictive_summary',
            lambda self, **kwargs: SimpleNamespace(
                x=np.array([1.0, 2.0, 3.0]),
                lower_95=np.array([8.0, 9.0, 10.0]),
                upper_95=np.array([10.0, 11.0, 12.0]),
                best_sample_prediction=np.array([9.0, 11.0, 10.5]),
                draws=None,
            ),
        )

        plotter._plot_posterior_predictive_data(
            experiment=self._experiment(),
            expt_name='hrpt',
            plot_options=SimpleNamespace(
                x_min=None,
                x_max=None,
                show_residual=None,
                show_background=None,
                show_bragg=None,
                show_excluded=False,
                x=None,
            ),
            x_axis=XAxisType.TWO_THETA,
            style='draws',
        )
        assert 'draws are unavailable for plotting' in capsys.readouterr().out


# ------------------------------------------------------------------
# Plotter._plot_posterior_predictive_request (powder routing)
# ------------------------------------------------------------------


class TestPlotPosteriorPredictiveRequestRouting:
    def _make_project(self, sample_form, scattering_type):
        from types import SimpleNamespace

        from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum

        expt_type = SimpleNamespace(
            sample_form=SimpleNamespace(value=sample_form),
            scattering_type=SimpleNamespace(value=scattering_type),
            beam_mode=SimpleNamespace(value=BeamModeEnum.CONSTANT_WAVELENGTH),
        )
        experiment = SimpleNamespace(type=expt_type)
        return SimpleNamespace(experiments={'E1': experiment}), experiment

    def test_unsupported_sample_form_warns(self, monkeypatch, capsys):
        from easydiffraction.display.plotting import Plotter
        from easydiffraction.utils.logging import Logger

        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)

        # A sample form that is neither single-crystal nor powder. An
        # explicit x bypasses the DEFAULT_X_AXIS lookup keyed by enums.
        project, _ = self._make_project('unknown_form', 'bragg')
        p = Plotter()
        p.engine = 'plotly'
        p._set_project(project)
        monkeypatch.setattr(Plotter, '_update_project_categories', lambda self, expt_name: None)

        p.plot_posterior_predictive('E1', x='two_theta')
        assert 'support powder experiments only' in capsys.readouterr().out

    def test_bragg_powder_routes_to_predictive_data(self, monkeypatch):
        from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
        from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum
        from easydiffraction.display.plotting import Plotter

        project, experiment = self._make_project(SampleFormEnum.POWDER, ScatteringTypeEnum.BRAGG)
        captured = {}
        p = Plotter()
        p.engine = 'plotly'
        p._set_project(project)
        monkeypatch.setattr(Plotter, '_update_project_categories', lambda self, expt_name: None)
        monkeypatch.setattr(
            Plotter,
            '_plot_posterior_predictive_data',
            lambda self, **kwargs: captured.update(kwargs),
        )
        p.plot_posterior_predictive('E1', style='band')
        assert captured['expt_name'] == 'E1'
        assert captured['style'] == 'band'
        assert captured['experiment'] is experiment

    def test_non_bragg_powder_routes_to_non_bragg_handler(self, monkeypatch):
        from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
        from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum
        from easydiffraction.display.plotting import Plotter

        project, experiment = self._make_project(SampleFormEnum.POWDER, ScatteringTypeEnum.TOTAL)
        captured = {}
        p = Plotter()
        p.engine = 'plotly'
        p._set_project(project)
        monkeypatch.setattr(Plotter, '_update_project_categories', lambda self, expt_name: None)
        monkeypatch.setattr(
            Plotter,
            '_plot_non_bragg_posterior_predictive',
            lambda self, **kwargs: captured.update(kwargs),
        )
        p.plot_posterior_predictive('E1', style='band')
        assert captured['expt_name'] == 'E1'
        assert captured['experiment'] is experiment
        assert captured['scattering_type'] == ScatteringTypeEnum.TOTAL

    def test_single_crystal_plotly_routes_to_single_crystal_handler(self, monkeypatch):
        from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
        from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum
        from easydiffraction.display.plotting import Plotter

        project, experiment = self._make_project(
            SampleFormEnum.SINGLE_CRYSTAL, ScatteringTypeEnum.BRAGG
        )
        captured = {}
        p = Plotter()
        p.engine = 'plotly'
        p._set_project(project)
        monkeypatch.setattr(Plotter, '_update_project_categories', lambda self, expt_name: None)
        monkeypatch.setattr(
            Plotter,
            '_plot_single_crystal_posterior_predictive',
            lambda self, **kwargs: captured.update(kwargs),
        )
        p.plot_posterior_predictive('E1', x='intensity_calc', style='band')
        assert captured['expt_name'] == 'E1'
        assert captured['experiment'] is experiment


# ------------------------------------------------------------------
# Plotter._plot_single_crystal_posterior_predictive (main body branches)
# ------------------------------------------------------------------


class TestSingleCrystalPosteriorPredictiveBody:
    def _plotter(self, monkeypatch):
        from easydiffraction.display.plotting import Plotter

        p = Plotter()
        p.engine = 'plotly'
        monkeypatch.setattr(Plotter, '_update_project_categories', lambda self, expt_name: None)
        return p

    def _call(self, p, *, style='band', show_residual=None):
        from easydiffraction.display.plotting import ScatteringTypeEnum
        from easydiffraction.display.plotting import XAxisType

        p._plot_single_crystal_posterior_predictive(
            experiment=object(),
            expt_name='sxd',
            x_axis=XAxisType.INTENSITY_CALC,
            scattering_type=ScatteringTypeEnum.BRAGG,
            plot_options=_options(show_residual=show_residual),
            style=style,
        )

    def test_summary_none_returns_quietly(self, monkeypatch):
        from easydiffraction.display.plotting import Plotter

        monkeypatch.setattr(
            Plotter,
            '_get_or_build_posterior_predictive_summary',
            lambda self, **kwargs: None,
        )
        p = self._plotter(monkeypatch)
        # No exception, no further work.
        self._call(p)

    def test_show_residual_and_style_warn(self, monkeypatch, capsys):
        from easydiffraction.display.plotting import Plotter
        from easydiffraction.utils.logging import Logger

        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)
        monkeypatch.setattr(
            Plotter,
            '_get_or_build_posterior_predictive_summary',
            lambda self, **kwargs: None,
        )
        p = self._plotter(monkeypatch)
        show_residual = True
        self._call(p, style='draws', show_residual=show_residual)
        out = capsys.readouterr().out
        assert 'residuals are unavailable for' in out
        assert 'style="band" only' in out

    def test_missing_measured_data_warns(self, monkeypatch, capsys):
        from types import SimpleNamespace

        import easydiffraction.display.plotting as mod
        from easydiffraction.display.plotting import Plotter
        from easydiffraction.utils.logging import Logger

        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)
        monkeypatch.setattr(
            Plotter,
            '_get_or_build_posterior_predictive_summary',
            lambda self, **kwargs: SimpleNamespace(best_sample_prediction=np.array([1.0, 2.0])),
        )
        monkeypatch.setattr(
            mod, 'intensity_category_for', lambda experiment: SimpleNamespace(intensity_meas=None)
        )
        p = self._plotter(monkeypatch)
        self._call(p)
        assert 'No measured data available' in capsys.readouterr().out

    def test_shape_mismatch_warns(self, monkeypatch, capsys):
        from types import SimpleNamespace

        import easydiffraction.display.plotting as mod
        from easydiffraction.display.plotting import Plotter
        from easydiffraction.utils.logging import Logger

        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)
        monkeypatch.setattr(
            Plotter,
            '_get_or_build_posterior_predictive_summary',
            lambda self, **kwargs: SimpleNamespace(
                best_sample_prediction=np.array([1.0, 2.0, 3.0])
            ),
        )
        monkeypatch.setattr(
            mod,
            'intensity_category_for',
            lambda experiment: SimpleNamespace(intensity_meas=np.array([1.0, 2.0])),
        )
        p = self._plotter(monkeypatch)
        self._call(p)
        assert 'do not match the measured reflection array shape' in capsys.readouterr().out

    def test_su_shape_mismatch_warns(self, monkeypatch, capsys):
        from types import SimpleNamespace

        import easydiffraction.display.plotting as mod
        from easydiffraction.display.plotting import Plotter
        from easydiffraction.utils.logging import Logger

        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)
        monkeypatch.setattr(
            Plotter,
            '_get_or_build_posterior_predictive_summary',
            lambda self, **kwargs: SimpleNamespace(best_sample_prediction=np.array([1.0, 2.0])),
        )
        monkeypatch.setattr(
            mod,
            'intensity_category_for',
            lambda experiment: SimpleNamespace(
                intensity_meas=np.array([1.0, 2.0]),
                intensity_meas_su=np.array([0.1]),  # wrong shape
            ),
        )
        p = self._plotter(monkeypatch)
        self._call(p)
        assert 'uncertainties do not' in capsys.readouterr().out

    def test_missing_su_defaults_to_zeros_and_renders(self, monkeypatch, capsys):
        from types import SimpleNamespace

        import easydiffraction.display.plotting as mod
        from easydiffraction.display.plotting import Plotter
        from easydiffraction.utils.logging import Logger

        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)
        monkeypatch.setattr(
            Plotter,
            '_get_or_build_posterior_predictive_summary',
            lambda self, **kwargs: SimpleNamespace(best_sample_prediction=np.array([1.0, 2.0])),
        )
        monkeypatch.setattr(
            mod,
            'intensity_category_for',
            lambda experiment: SimpleNamespace(
                intensity_meas=np.array([1.0, 2.0]),
                intensity_meas_su=None,
            ),
        )
        captured = {}
        monkeypatch.setattr(
            Plotter,
            '_plot_single_crystal_posterior_predictive_summary',
            lambda self, **kwargs: captured.update(kwargs),
        )
        p = self._plotter(monkeypatch)
        self._call(p)
        assert 'No measurement uncertainties' in capsys.readouterr().out
        np.testing.assert_allclose(captured['y_meas_su'], [0.0, 0.0])
        np.testing.assert_allclose(captured['y_meas'], [1.0, 2.0])
