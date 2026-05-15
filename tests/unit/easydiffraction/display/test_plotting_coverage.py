# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Additional unit tests for display/plotting.py to cover patch gaps."""

import numpy as np


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
            'my_param,my_param.uncertainty,diffrn.temperature\n1.0,0.1,300\n2.0,0.2,400\n'
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

        class VersusDesc:
            name = 'temperature'
            description = 'Temperature'
            units = 'K'

        p._plot_param_series_from_csv(str(csv), 'my_param', ParamDesc(), VersusDesc())
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
            'param_a', 'ambient_temperature', experiments, snapshots
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
