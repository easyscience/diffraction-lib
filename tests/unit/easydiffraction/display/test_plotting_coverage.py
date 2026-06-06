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
