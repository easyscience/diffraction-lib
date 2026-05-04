# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import numpy as np
import pytest


def test_module_import():
    import easydiffraction.display.plotters.plotly as MUT

    expected_module_name = 'easydiffraction.display.plotters.plotly'
    actual_module_name = MUT.__name__
    assert expected_module_name == actual_module_name


def test_default_template_name_prefers_jupyter_theme(monkeypatch):
    import easydiffraction.display.plotters.plotly as pp

    monkeypatch.setattr(pp, 'in_jupyter', lambda: True)
    monkeypatch.setattr(pp, 'is_dark', lambda: True)
    monkeypatch.setattr(pp.darkdetect, 'isDark', lambda: False)

    assert pp.PlotlyPlotter._default_template_name() == 'plotly_dark'


def test_correlation_colorscale_uses_black_center_in_dark_mode(monkeypatch):
    import easydiffraction.display.plotters.plotly as pp

    monkeypatch.setattr(pp.PlotlyPlotter, '_is_dark_mode', staticmethod(lambda: True))

    assert pp.PlotlyPlotter._correlation_colorscale()[1] == (0.5, '#000000')


def test_default_template_name_uses_system_theme_outside_jupyter(monkeypatch):
    import easydiffraction.display.plotters.plotly as pp

    monkeypatch.setattr(pp, 'in_jupyter', lambda: False)
    monkeypatch.setattr(pp, 'is_dark', lambda: False)
    monkeypatch.setattr(pp.darkdetect, 'isDark', lambda: False)

    assert pp.PlotlyPlotter._default_template_name() == 'plotly_white'


def test_correlation_colorscale_uses_white_center_in_light_mode(monkeypatch):
    import easydiffraction.display.plotters.plotly as pp

    monkeypatch.setattr(pp.PlotlyPlotter, '_is_dark_mode', staticmethod(lambda: False))

    assert pp.PlotlyPlotter._correlation_colorscale()[1] == (0.5, '#f7f7f7')


def test_get_trace_and_plot(monkeypatch):
    import easydiffraction.display.plotters.plotly as pp

    # Arrange: force non-PyCharm branch and stub fig.show/HTML/display so nothing opens
    monkeypatch.setattr(pp, 'in_pycharm', lambda: False)

    shown = {'count': 0}

    class DummyFig:
        def update_xaxes(self, **kwargs):
            pass

        def update_yaxes(self, **kwargs):
            pass

        def show(self, **kwargs):
            shown['count'] += 1

    # Patch go.Scatter and go.Figure to minimal dummies
    class DummyScatter:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class DummyGO:
        class Scatter(DummyScatter):
            pass

        class Figure(DummyFig):
            def __init__(self, data=None, layout=None):
                self.data = data
                self.layout = layout

        class Layout:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

    class DummyPIO:
        @staticmethod
        def to_html(fig, include_plotlyjs=None, full_html=None, config=None):
            return '<div>plot</div>'

    dummy_display_calls = {'count': 0}

    def dummy_display(obj):
        dummy_display_calls['count'] += 1

    class DummyHTML:
        def __init__(self, html):
            self.html = html

    monkeypatch.setattr(pp, 'go', DummyGO)
    monkeypatch.setattr(pp, 'pio', DummyPIO)
    monkeypatch.setattr(pp, 'display', dummy_display)
    monkeypatch.setattr(pp, 'HTML', DummyHTML)

    plotter = pp.PlotlyPlotter()

    # Exercise _get_powder_trace
    x = [0, 1, 2]
    y = [1, 2, 3]
    trace = plotter._get_powder_trace(x, y, label='calc')
    assert hasattr(trace, 'kwargs')
    assert trace.kwargs['x'] == x
    assert trace.kwargs['y'] == y

    # Exercise plot_powder (non-PyCharm, display path)
    plotter.plot_powder(
        x,
        y_series=[y],
        labels=['calc'],
        axes_labels=['x', 'y'],
        title='t',
        height=None,
    )

    # One HTML display call expected
    assert dummy_display_calls['count'] == 1 or shown['count'] == 1


def test_plotly_single_crystal_trace_and_plot(monkeypatch):
    import easydiffraction.display.plotters.plotly as pp

    # Arrange: force non-PyCharm branch
    monkeypatch.setattr(pp, 'in_pycharm', lambda: False)

    shown = {'count': 0}

    class DummyFig:
        def update_xaxes(self, **kwargs):
            pass

        def update_yaxes(self, **kwargs):
            pass

        def show(self, **kwargs):
            shown['count'] += 1

    class DummyScatter:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class DummyGO:
        class Scatter(DummyScatter):
            pass

        class Figure(DummyFig):
            def __init__(self, data=None, layout=None):
                self.data = data
                self.layout = layout

        class Layout:
            def __init__(self, **kwargs):
                self.kwargs = kwargs

    class DummyPIO:
        @staticmethod
        def to_html(fig, include_plotlyjs=None, full_html=None, config=None):
            return '<div>plot</div>'

    dummy_display_calls = {'count': 0}

    def dummy_display(obj):
        dummy_display_calls['count'] += 1

    class DummyHTML:
        def __init__(self, html):
            self.html = html

    monkeypatch.setattr(pp, 'go', DummyGO)
    monkeypatch.setattr(pp, 'pio', DummyPIO)
    monkeypatch.setattr(pp, 'display', dummy_display)
    monkeypatch.setattr(pp, 'HTML', DummyHTML)

    plotter = pp.PlotlyPlotter()

    # Exercise _get_single_crystal_trace
    x_calc = [1.0, 2.0, 3.0]
    y_meas = [1.1, 1.9, 3.2]
    y_meas_su = [0.1, 0.1, 0.1]
    trace = plotter._get_single_crystal_trace(x_calc, y_meas, y_meas_su)
    assert hasattr(trace, 'kwargs')
    assert trace.kwargs['x'] == x_calc
    assert trace.kwargs['y'] == y_meas
    assert trace.kwargs['mode'] == 'markers'
    assert 'error_y' in trace.kwargs

    # Exercise _get_diagonal_shape
    shape = plotter._get_diagonal_shape()
    assert shape['type'] == 'line'
    assert shape['xref'] == 'paper'
    assert shape['yref'] == 'paper'

    # Exercise plot_single_crystal
    plotter.plot_single_crystal(
        x_calc=x_calc,
        y_meas=y_meas,
        y_meas_su=y_meas_su,
        axes_labels=['F²calc', 'F²meas'],
        title='SC Test',
        height=None,
    )
    # One display call expected
    assert dummy_display_calls['count'] == 1 or shown['count'] == 1


def test_get_bragg_tick_trace_includes_peak_metadata():
    from easydiffraction.display.plotters.base import BraggTickSet
    from easydiffraction.display.plotters.plotly import PlotlyPlotter

    trace = PlotlyPlotter._get_bragg_tick_trace(
        tick_set=BraggTickSet(
            phase_id='phase-a',
            x=np.array([1.5, 2.5]),
            h=np.array([1, 2]),
            k=np.array([0, 1]),
            ell=np.array([1, 0]),
            f_squared_calc=np.array([100.0, 80.0]),
            f_calc=np.array([10.0, 9.0]),
        ),
        row_y=2.0,
        color='#123456',
    )

    assert list(trace.x) == [1.5, 2.5]
    assert list(trace.y) == [2.0, 2.0]
    assert trace.mode == 'markers'
    assert trace.marker.symbol == 'line-ns-open'
    assert trace.hovertemplate == '%{text}'
    assert 'phase_id: phase-a' in trace.text[0]
    assert 'hkl: (1 0 1)' in trace.text[0]
    assert 'f_squared_calc: 100' in trace.text[0]
    assert 'f_calc: 10' in trace.text[0]


def test_plot_powder_meas_vs_calc_creates_synced_three_panel_figure(monkeypatch):
    import easydiffraction.display.plotters.plotly as pp

    from easydiffraction.display.plotters.base import BraggTickSet
    from easydiffraction.display.plotters.base import PowderMeasVsCalcSpec

    captured = {}

    def fake_show_figure(self, fig):
        captured['fig'] = fig

    monkeypatch.setattr(pp.PlotlyPlotter, '_show_figure', fake_show_figure)

    plot_spec = PowderMeasVsCalcSpec(
        x=np.array([1.0, 2.0, 3.0]),
        y_meas=np.array([10.0, 12.0, 11.0]),
        y_calc=np.array([9.0, 11.0, 10.5]),
        y_resid=np.array([1.0, 1.0, 0.5]),
        bragg_tick_sets=(
            BraggTickSet(
                phase_id='phase-a',
                x=np.array([1.5]),
                h=np.array([1]),
                k=np.array([0]),
                ell=np.array([1]),
                f_squared_calc=np.array([100.0]),
                f_calc=np.array([10.0]),
            ),
            BraggTickSet(
                phase_id='phase-b',
                x=np.array([2.5]),
                h=np.array([2]),
                k=np.array([1]),
                ell=np.array([0]),
                f_squared_calc=np.array([80.0]),
                f_calc=np.array([9.0]),
            ),
        ),
        axes_labels=['2θ (degree)', 'Intensity (arb. units)'],
        title='Powder',
        residual_height_fraction=0.25,
        bragg_peaks_height_fraction=0.10,
        height=None,
    )

    plotter = pp.PlotlyPlotter()
    plotter.plot_powder_meas_vs_calc(plot_spec=plot_spec)

    fig = captured['fig']
    assert len(fig.data) == 5
    assert fig.layout.xaxis.matches == 'x'
    assert fig.layout.xaxis2.matches == 'x'
    assert fig.layout.xaxis3.matches == 'x'

    main_height = fig.layout.yaxis.domain[1] - fig.layout.yaxis.domain[0]
    bragg_height = fig.layout.yaxis2.domain[1] - fig.layout.yaxis2.domain[0]
    residual_height = fig.layout.yaxis3.domain[1] - fig.layout.yaxis3.domain[0]
    assert residual_height == pytest.approx(main_height * 0.25)
    assert bragg_height == pytest.approx(
        main_height * pp.PlotlyPlotter._scaled_bragg_row_height(plot_spec)
    )

    bragg_traces = [trace for trace in fig.data if trace.name.startswith('Bragg')]
    assert [trace.name for trace in bragg_traces] == ['Bragg (phase-a)', 'Bragg (phase-b)']
    assert list(fig.layout.yaxis2.ticktext) == ['phase-a', 'phase-b']
    assert fig.layout.yaxis2.title.text is None
    assert fig.layout.yaxis3.title.text is None
    assert fig.layout.yaxis3.zeroline is False
    assert fig.layout.xaxis3.title.text == '2θ (degree)'
    assert 'hkl: (1 0 1)' in bragg_traces[0].text[0]
    assert 'f_squared_calc: 100' in bragg_traces[0].text[0]


def test_scaled_bragg_row_height_preserves_single_phase_baseline():
    from easydiffraction.display.plotters.base import BraggTickSet
    from easydiffraction.display.plotters.base import PowderMeasVsCalcSpec
    from easydiffraction.display.plotters.plotly import PlotlyPlotter

    single_phase = PowderMeasVsCalcSpec(
        x=np.array([1.0, 2.0]),
        y_meas=np.array([1.0, 2.0]),
        y_calc=np.array([1.0, 2.0]),
        y_resid=np.array([0.0, 0.0]),
        bragg_tick_sets=(
            BraggTickSet(
                phase_id='phase-a',
                x=np.array([1.5]),
                h=np.array([1]),
                k=np.array([0]),
                ell=np.array([1]),
                f_squared_calc=np.array([100.0]),
                f_calc=np.array([10.0]),
            ),
        ),
        axes_labels=['2θ (degree)', 'Intensity (arb. units)'],
        title='Powder',
        residual_height_fraction=0.25,
        bragg_peaks_height_fraction=0.10,
        height=None,
    )
    two_phase = PowderMeasVsCalcSpec(
        x=single_phase.x,
        y_meas=single_phase.y_meas,
        y_calc=single_phase.y_calc,
        y_resid=single_phase.y_resid,
        bragg_tick_sets=(
            single_phase.bragg_tick_sets[0],
            BraggTickSet(
                phase_id='phase-b',
                x=np.array([2.5]),
                h=np.array([2]),
                k=np.array([1]),
                ell=np.array([0]),
                f_squared_calc=np.array([80.0]),
                f_calc=np.array([9.0]),
            ),
        ),
        axes_labels=single_phase.axes_labels,
        title=single_phase.title,
        residual_height_fraction=single_phase.residual_height_fraction,
        bragg_peaks_height_fraction=single_phase.bragg_peaks_height_fraction,
        height=single_phase.height,
    )

    single_height = PlotlyPlotter._scaled_bragg_row_height(single_phase)
    two_phase_height = PlotlyPlotter._scaled_bragg_row_height(two_phase)

    single_phase_normalized = single_height / (
        1.0 + single_phase.residual_height_fraction + single_height
    )
    two_phase_normalized_per_phase = (two_phase_height / (1.0 + two_phase.residual_height_fraction + two_phase_height)) / 2

    assert two_phase_normalized_per_phase == pytest.approx(single_phase_normalized)


def test_plot_powder_meas_vs_calc_skips_bragg_row_when_no_ticks(monkeypatch):
    import easydiffraction.display.plotters.plotly as pp

    from easydiffraction.display.plotters.base import PowderMeasVsCalcSpec

    captured = {}

    def fake_show_figure(self, fig):
        captured['fig'] = fig

    monkeypatch.setattr(pp.PlotlyPlotter, '_show_figure', fake_show_figure)

    plotter = pp.PlotlyPlotter()
    plotter.plot_powder_meas_vs_calc(
        plot_spec=PowderMeasVsCalcSpec(
            x=np.array([1.0, 2.0, 3.0]),
            y_meas=np.array([10.0, 12.0, 11.0]),
            y_calc=np.array([9.0, 11.0, 10.5]),
            y_resid=np.array([1.0, 1.0, 0.5]),
            bragg_tick_sets=(),
            axes_labels=['2θ (degree)', 'Intensity (arb. units)'],
            title='Powder',
            residual_height_fraction=0.25,
            bragg_peaks_height_fraction=0.15,
            height=None,
        ),
    )

    fig = captured['fig']
    assert len(fig.data) == 3
    assert fig.layout.xaxis.matches == 'x'
    assert fig.layout.xaxis2.matches == 'x'
    assert fig.layout.yaxis2.title.text is None
    assert fig.layout.xaxis2.title.text == '2θ (degree)'
    assert [trace.name for trace in fig.data] == [
        'Measured (Imeas)',
        'Total calculated (Icalc)',
        'Residual (Imeas - Icalc)',
    ]


def test_plot_powder_meas_vs_calc_keeps_exact_residual_scale_match(monkeypatch):
    import easydiffraction.display.plotters.plotly as pp

    from easydiffraction.display.plotters.base import PowderMeasVsCalcSpec

    captured = {}

    def fake_show_figure(self, fig):
        captured['fig'] = fig

    monkeypatch.setattr(pp.PlotlyPlotter, '_show_figure', fake_show_figure)

    plotter = pp.PlotlyPlotter()
    plotter.plot_powder_meas_vs_calc(
        plot_spec=PowderMeasVsCalcSpec(
            x=np.array([1.0, 2.0, 3.0]),
            y_meas=np.array([200.0, 3600.0, 220.0]),
            y_calc=np.array([180.0, 3400.0, 210.0]),
            y_resid=np.array([20.0, 200.0, 10.0]),
            bragg_tick_sets=(),
            axes_labels=['2θ (degree)', 'Intensity (arb. units)'],
            title='Powder',
            residual_height_fraction=0.25,
            bragg_peaks_height_fraction=0.15,
            height=None,
        ),
    )

    fig = captured['fig']
    expected_limit = 0.5 * (3600.0 - 180.0) * 0.25
    assert fig.layout.yaxis2.range[0] == pytest.approx(-expected_limit)
    assert fig.layout.yaxis2.range[1] == pytest.approx(expected_limit)
    assert list(fig.layout.yaxis2.tickvals) == pytest.approx([-400.0, 0.0, 400.0])


def test_plot_powder_meas_vs_calc_clips_large_residual_spikes(monkeypatch):
    import easydiffraction.display.plotters.plotly as pp

    from easydiffraction.display.plotters.base import PowderMeasVsCalcSpec

    captured = {}

    def fake_show_figure(self, fig):
        captured['fig'] = fig

    monkeypatch.setattr(pp.PlotlyPlotter, '_show_figure', fake_show_figure)

    plotter = pp.PlotlyPlotter()
    plotter.plot_powder_meas_vs_calc(
        plot_spec=PowderMeasVsCalcSpec(
            x=np.array([1.0, 2.0, 3.0]),
            y_meas=np.array([200.0, 3600.0, 220.0]),
            y_calc=np.array([180.0, 3400.0, 210.0]),
            y_resid=np.array([20.0, 1200.0, 10.0]),
            bragg_tick_sets=(),
            axes_labels=['2θ (degree)', 'Intensity (arb. units)'],
            title='Powder',
            residual_height_fraction=0.25,
            bragg_peaks_height_fraction=0.15,
            height=None,
        ),
    )

    fig = captured['fig']
    expected_limit = 0.5 * (3600.0 - 180.0) * 0.25
    assert fig.layout.yaxis2.range[0] == pytest.approx(-expected_limit)
    assert fig.layout.yaxis2.range[1] == pytest.approx(expected_limit)
    assert list(fig.layout.yaxis2.tickvals) == pytest.approx([-400.0, 0.0, 400.0])


def test_plot_powder_meas_vs_calc_accepts_empty_filtered_range(monkeypatch):
    import easydiffraction.display.plotters.plotly as pp

    from easydiffraction.display.plotters.base import PowderMeasVsCalcSpec

    captured = {}

    def fake_show_figure(self, fig):
        captured['fig'] = fig

    monkeypatch.setattr(pp.PlotlyPlotter, '_show_figure', fake_show_figure)

    plotter = pp.PlotlyPlotter()
    plotter.plot_powder_meas_vs_calc(
        plot_spec=PowderMeasVsCalcSpec(
            x=np.array([], dtype=float),
            y_meas=np.array([], dtype=float),
            y_calc=np.array([], dtype=float),
            y_resid=np.array([], dtype=float),
            bragg_tick_sets=(),
            axes_labels=['2θ (degree)', 'Intensity (arb. units)'],
            title='Powder',
            residual_height_fraction=0.25,
            bragg_peaks_height_fraction=0.15,
            height=None,
        ),
    )

    fig = captured['fig']
    assert len(fig.data) == 3
    assert fig.layout.yaxis2.range[0] == pytest.approx(-1.0)
    assert fig.layout.yaxis2.range[1] == pytest.approx(1.0)
