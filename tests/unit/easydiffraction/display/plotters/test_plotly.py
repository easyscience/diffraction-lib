# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import numpy as np
import pytest


def test_module_import():
    import easydiffraction.display.plotters.plotly as MUT

    expected_module_name = 'easydiffraction.display.plotters.plotly'
    actual_module_name = MUT.__name__
    assert expected_module_name == actual_module_name


@pytest.mark.parametrize(
    'is_dark_mode',
    [False, True],
)
def test_get_layout_sets_title_axis_and_theme_colors(
    monkeypatch,
    is_dark_mode,
):
    import easydiffraction.display.plotters.plotly as pp

    if is_dark_mode:
        background_color = pp.DARK_BACKGROUND_COLOR
        axis_color = pp.DARK_AXIS_FRAME_COLOR
        grid_color = pp.DARK_INNER_TICK_GRID_COLOR
    else:
        background_color = pp.LIGHT_BACKGROUND_COLOR
        axis_color = pp.LIGHT_AXIS_FRAME_COLOR
        grid_color = pp.LIGHT_INNER_TICK_GRID_COLOR

    monkeypatch.setattr(
        pp.PlotlyPlotter,
        '_is_dark_mode',
        classmethod(lambda cls: is_dark_mode),
    )

    layout = pp.PlotlyPlotter._get_layout('Title', ['x axis', 'y axis'])

    assert layout.title.font.size == pp.TITLE_FONT_SIZE
    assert layout.xaxis.title.font.size == pp.AXIS_TITLE_FONT_SIZE
    assert layout.yaxis.title.font.size == pp.AXIS_TITLE_FONT_SIZE
    assert layout.paper_bgcolor == background_color
    assert layout.plot_bgcolor == background_color
    assert layout.xaxis.linecolor == axis_color
    assert layout.yaxis.linecolor == axis_color
    assert layout.xaxis.gridcolor == grid_color
    assert layout.yaxis.gridcolor == grid_color
    assert layout.xaxis.ticklabelstandoff == pp.X_AXIS_TICK_LABEL_STANDOFF
    assert layout.yaxis.ticklabelstandoff == pp.Y_AXIS_TICK_LABEL_STANDOFF


@pytest.mark.parametrize(
    ('is_dark_mode', 'background_color'),
    [
        (False, 'light-background'),
        (True, 'dark-background'),
    ],
)
def test_correlation_colorscale_uses_theme_background(
    monkeypatch,
    is_dark_mode,
    background_color,
):
    import easydiffraction.display.plotters.plotly as pp

    monkeypatch.setattr(
        pp.PlotlyPlotter,
        '_is_dark_mode',
        classmethod(lambda cls: is_dark_mode),
    )
    monkeypatch.setattr(
        pp.PlotlyPlotter,
        '_background_color',
        classmethod(lambda cls: background_color),
    )

    colorscale = pp.PlotlyPlotter._correlation_colorscale()

    assert colorscale == [
        (0.0, '#d73027'),
        (0.5, background_color),
        (1.0, '#4575b4'),
    ]


def test_get_trace_and_plot(monkeypatch):
    import easydiffraction.display.plotters.plotly as pp

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
        def to_html(fig, include_plotlyjs=None, full_html=None, config=None, post_script=None):
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

    x = [0, 1, 2]
    y = [1, 2, 3]
    trace = plotter._get_powder_trace(x, y, label='calc')
    assert hasattr(trace, 'kwargs')
    assert trace.kwargs['x'] == x
    assert trace.kwargs['y'] == y
    assert trace.kwargs['line']['width'] == pp.CALCULATED_LINE_WIDTH

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


def test_show_figure_adds_legend_toggle_script_to_html_output(monkeypatch):
    import easydiffraction.display.plotters.plotly as pp

    monkeypatch.setattr(pp, 'in_pycharm', lambda: False)

    captured = {}

    class DummyFig:
        def update_xaxes(self, **kwargs):
            pass

        def update_yaxes(self, **kwargs):
            pass

        def show(self, **kwargs):
            captured['show_called'] = True

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
        def to_html(fig, include_plotlyjs=None, full_html=None, config=None, post_script=None):
            captured['config'] = config
            captured['post_script'] = post_script
            return '<div>plot</div>'

    def dummy_display(obj):
        captured['displayed_html'] = obj.html

    class DummyHTML:
        def __init__(self, html):
            self.html = html

    monkeypatch.setattr(pp, 'go', DummyGO)
    monkeypatch.setattr(pp, 'pio', DummyPIO)
    monkeypatch.setattr(pp, 'display', dummy_display)
    monkeypatch.setattr(pp, 'HTML', DummyHTML)

    plotter = pp.PlotlyPlotter()
    plotter.plot_powder(
        [0, 1, 2],
        y_series=[[1, 2, 3]],
        labels=['calc'],
        axes_labels=['x', 'y'],
        title='t',
        height=None,
    )

    assert captured.get('show_called') is not True
    assert captured['config']['displayModeBar'] is True
    assert captured['config']['displaylogo'] is False
    assert captured['config']['responsive'] is True
    assert 'data-jp-theme-light' in captured['post_script']
    assert 'data-md-color-scheme' in captured['post_script']
    assert 'graphDiv.dataset.edPlotlyTheme' in captured['post_script']
    assert f"background: '{pp.DARK_BACKGROUND_COLOR}'" in captured['post_script']
    assert f"background: '{pp.LIGHT_BACKGROUND_COLOR}'" in captured['post_script']
    assert f"axisFrame: '{pp.DARK_AXIS_FRAME_COLOR}'" in captured['post_script']
    assert f"axisFrame: '{pp.LIGHT_AXIS_FRAME_COLOR}'" in captured['post_script']
    assert f"innerTickGrid: '{pp.DARK_INNER_TICK_GRID_COLOR}'" in captured['post_script']
    assert f"innerTickGrid: '{pp.LIGHT_INNER_TICK_GRID_COLOR}'" in captured['post_script']
    assert f"hoverBackground: '{pp.DARK_HOVER_BACKGROUND_COLOR}'" in captured['post_script']
    assert f"legend: '{pp.DARK_LEGEND_BACKGROUND_COLOR}'" in captured['post_script']
    assert 'ed-plotly-modebar-theme-style' in captured['post_script']
    assert 'ed-plotly-themed-modebar' in captured['post_script']
    assert '--ed-plotly-modebar-icon-color' in captured['post_script']
    assert '--ed-plotly-modebar-icon-hover-opacity' in captured['post_script']
    assert 'const correlationColorscale = function (colors) {' in captured['post_script']
    assert 'const themeSync = meta.ed_plotly_theme_sync;' in captured['post_script']
    assert 'const applyAnnotationTheme = function (update, colors) {' in captured['post_script']
    assert 'const shapeIndexes = themeSync.axis_frame_shape_indexes;' in captured['post_script']
    assert 'if (themeSync.correlation_heatmap !== true) {' in captured['post_script']
    assert 'window.Plotly.restyle(' in captured['post_script']
    assert 'window.Plotly.relayout(graphDiv, update)' in captured['post_script']
    assert 'Promise.all(pending).then(function () {' in captured['post_script']
    assert 'window.Plotly.Plots.resize(graphDiv)' in captured['post_script']
    assert "document.addEventListener('visibilitychange'" in captured['post_script']
    assert "window.addEventListener('focus', scheduleResize);" in captured['post_script']
    assert 'new ResizeObserver(scheduleResize)' in captured['post_script']
    assert 'data-legend-toggle="true"' in captured['post_script']
    assert 'Toggle legend' in captured['post_script']
    assert 'graphDiv.dataset.legendVisible' in captured['post_script']
    assert 'const applyLegendVisibility = function (legendVisible) {' in captured['post_script']
    assert "legend.style.display = legendVisible ? 'inline' : 'none';" in captured['post_script']
    assert 'const readLegendVisibility = function () {' in captured['post_script']
    assert (
        "if (graphDiv.layout && typeof graphDiv.layout.showlegend === 'boolean')"
        in captured['post_script']
    )
    assert "legendButton.classList.toggle('active', legendVisible);" in captured['post_script']
    assert "graphDiv.on('plotly_relayout', function (eventData) {" in captured['post_script']
    assert 'legendButton.onclick = toggleLegend;' in captured['post_script']
    assert 'resolveLegendButtonFill(legendVisible ? 0.7 : 0.3)' in captured['post_script']
    assert "legendButtonGroup.className = 'modebar-group';" in captured['post_script']
    assert 'modebar.appendChild(legendButtonGroup);' in captured['post_script']
    assert 'legendButton.innerHTML' in captured['post_script']
    assert 'height="1em" width="1em"' in captured['post_script']
    assert captured['displayed_html'] == '<div>plot</div>'


def test_show_figure_skips_legend_toggle_script_without_legend(monkeypatch):
    import easydiffraction.display.plotters.plotly as pp

    monkeypatch.setattr(pp, 'in_pycharm', lambda: False)

    captured = {}

    class DummyTrace:
        def __init__(self, name=None, showlegend=None, visible=None):
            self.name = name
            self.showlegend = showlegend
            self.visible = visible

    class DummyFig:
        def __init__(self):
            self.data = [DummyTrace(name=None, showlegend=False)]
            self.layout = type('DummyLayout', (), {'showlegend': None})()

        def show(self, **kwargs):
            captured['show_called'] = True

    class DummyPIO:
        @staticmethod
        def to_html(fig, include_plotlyjs=None, full_html=None, config=None, post_script=None):
            captured['post_script'] = post_script
            return '<div>plot</div>'

    def dummy_display(obj):
        captured['displayed_html'] = obj.html

    class DummyHTML:
        def __init__(self, html):
            self.html = html

    monkeypatch.setattr(pp, 'pio', DummyPIO)
    monkeypatch.setattr(pp, 'display', dummy_display)
    monkeypatch.setattr(pp, 'HTML', DummyHTML)

    plotter = pp.PlotlyPlotter()
    plotter._show_figure(DummyFig())

    assert captured.get('show_called') is not True
    assert captured['post_script'] is not None
    assert 'data-jp-theme-light' in captured['post_script']
    assert 'data-legend-toggle="true"' not in captured['post_script']
    assert captured['displayed_html'] == '<div>plot</div>'


def test_show_figure_wraps_fixed_aspect_html(monkeypatch):
    import easydiffraction.display.plotters.plotly as pp

    monkeypatch.setattr(pp, 'in_pycharm', lambda: False)

    captured = {}

    class DummyLayout:
        def __init__(self):
            self.meta = {
                'fixed_aspect_wrapper': {
                    'aspect_ratio': '1 / 1',
                }
            }
            self.showlegend = False

    class DummyFig:
        def __init__(self):
            self.data = []
            self.layout = DummyLayout()

        def show(self, **kwargs):
            captured['show_called'] = True

    class DummyPIO:
        @staticmethod
        def to_html(fig, include_plotlyjs=None, full_html=None, config=None, post_script=None):
            captured['post_script'] = post_script
            return '<div>plot</div>'

    def dummy_display(obj):
        captured['displayed_html'] = obj.html

    class DummyHTML:
        def __init__(self, html):
            self.html = html

    monkeypatch.setattr(pp, 'pio', DummyPIO)
    monkeypatch.setattr(pp, 'display', dummy_display)
    monkeypatch.setattr(pp, 'HTML', DummyHTML)

    plotter = pp.PlotlyPlotter()
    plotter._show_figure(DummyFig())

    assert captured.get('show_called') is not True
    assert captured['post_script'] is not None
    assert 'data-jp-theme-light' in captured['post_script']
    assert 'aspect-ratio: 1 / 1;' in captured['displayed_html']
    assert 'ed-fixed-aspect-plotly-wrapper' in captured['displayed_html']
    assert '<div>plot</div>' in captured['displayed_html']


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
        def to_html(fig, include_plotlyjs=None, full_html=None, config=None, post_script=None):
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
    assert trace.kwargs['marker']['size'] == pp.MEASURED_MARKER_SIZE
    assert trace.kwargs['marker']['line']['color'] == pp.DEFAULT_COLORS['meas']
    assert trace.kwargs['error_y']['thickness'] == pp.MEASURED_ERROR_BAR_THICKNESS
    assert trace.kwargs['error_y']['width'] == pp.MEASURED_ERROR_BAR_WIDTH

    # Exercise _get_diagonal_shape (now a data-coordinate y=x line)
    shape = plotter._get_diagonal_shape(0.0, 10.0)
    assert shape['type'] == 'line'
    assert shape['xref'] == 'x'
    assert shape['yref'] == 'y'
    assert (shape['x0'], shape['y0']) == (0.0, 0.0)
    assert (shape['x1'], shape['y1']) == (10.0, 10.0)
    assert shape['line']['color'] == pp.DIAGONAL_LINE_COLOR
    assert shape['line']['width'] == pp.DIAGONAL_LINE_WIDTH

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


def test_single_crystal_axis_range_unions_calc_and_meas_with_uncertainty():
    import easydiffraction.display.plotters.plotly as pp

    minimum, maximum = pp.single_crystal_axis_range(
        x_calc=[2.0, 8.0],
        y_meas=[1.0, 10.0],
        y_meas_su=[0.5, 1.0],
    )
    # Spans meas-su minimum (0.5) to meas+su maximum (11.0); calc 2..8 is
    # inside. A 5% margin of the 10.5 span pads both ends symmetrically.
    assert minimum == pytest.approx(0.5 - 0.525)
    assert maximum == pytest.approx(11.0 + 0.525)


def test_single_crystal_axis_range_handles_missing_uncertainty():
    import easydiffraction.display.plotters.plotly as pp

    minimum, maximum = pp.single_crystal_axis_range(
        x_calc=[0.0, 4.0],
        y_meas=[1.0, 3.0],
        y_meas_su=None,
    )
    assert minimum < 0.0
    assert maximum > 4.0


def test_single_crystal_tick_step_rounds_to_nice_value():
    import easydiffraction.display.plotters.plotly as pp

    # Span 3000 over ~6 intervals -> raw 500 -> nice 500.
    assert pp.single_crystal_tick_step(0.0, 3000.0) == pytest.approx(500.0)
    # Padded heidi-like range (span just above the 500 threshold) rounds to
    # 500, not 750 (regression for the old round-up logic).
    assert pp.single_crystal_tick_step(-158.275, 2841.73) == pytest.approx(500.0)
    # Degenerate span falls back to 1.0.
    assert pp.single_crystal_tick_step(5.0, 5.0) == pytest.approx(1.0)


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
    assert 'phase-a' in trace.text[0]
    assert 'Miller indices: (1 0 1)' in trace.text[0]
    assert 'x: 1.50' in trace.text[0]


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
        y_meas_su=np.array([0.2, 0.3, 0.4]),
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
        axes_labels=['2θ (deg)', 'Intensity (arb. units)'],
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
    assert fig.layout.xaxis.ticklabelstandoff == pp.X_AXIS_TICK_LABEL_STANDOFF
    assert fig.layout.xaxis2.ticklabelstandoff == pp.X_AXIS_TICK_LABEL_STANDOFF
    assert fig.layout.xaxis3.ticklabelstandoff == pp.X_AXIS_TICK_LABEL_STANDOFF
    assert fig.layout.yaxis.ticklabelstandoff == pp.Y_AXIS_TICK_LABEL_STANDOFF
    assert fig.layout.yaxis2.ticklabelstandoff == pp.Y_AXIS_TICK_LABEL_STANDOFF
    assert fig.layout.yaxis3.ticklabelstandoff == pp.Y_AXIS_TICK_LABEL_STANDOFF
    assert fig.layout.yaxis3.scaleanchor == 'y'
    assert fig.layout.yaxis3.scaleratio == pytest.approx(1.0)

    plot_area_height = fig.layout.height - fig.layout.margin.t - fig.layout.margin.b
    main_height = fig.layout.yaxis.domain[1] - fig.layout.yaxis.domain[0]
    bragg_height = fig.layout.yaxis2.domain[1] - fig.layout.yaxis2.domain[0]
    residual_height = fig.layout.yaxis3.domain[1] - fig.layout.yaxis3.domain[0]
    assert residual_height == pytest.approx(main_height * 0.25)
    assert plot_area_height * bragg_height == pytest.approx(
        2 * pp.PlotlyPlotter._bragg_tick_symbol_height_pixels()
    )

    expected_hovertemplate = (
        'x: %{x:,.2f}<br>'
        'Imeas: %{customdata[0]:,.2f}<br>'
        'Icalc: %{customdata[1]:,.2f}<br>'
        'Imeas - Icalc: %{customdata[2]:,.2f}'
        '<extra></extra>'
    )
    meas_trace = next(trace for trace in fig.data if trace.name == 'Measured (Imeas)')
    calc_trace = next(trace for trace in fig.data if trace.name == 'Total calculated (Icalc)')
    residual_trace = next(trace for trace in fig.data if trace.name == 'Residual (Imeas - Icalc)')
    assert meas_trace.hovertemplate == expected_hovertemplate
    assert calc_trace.hovertemplate == expected_hovertemplate
    assert residual_trace.hovertemplate == expected_hovertemplate
    assert meas_trace.line.width == pp.MEASURED_LINE_WIDTH
    assert list(meas_trace.error_y.array) == pytest.approx([0.2, 0.3, 0.4])
    assert calc_trace.line.width == pp.CALCULATED_LINE_WIDTH
    assert residual_trace.line.width == pp.RESIDUAL_LINE_WIDTH
    assert list(meas_trace.customdata[0]) == pytest.approx([10.0, 9.0, 1.0])
    assert list(calc_trace.customdata[0]) == pytest.approx([10.0, 9.0, 1.0])
    assert list(residual_trace.customdata[0]) == pytest.approx([10.0, 9.0, 1.0])

    bragg_traces = [trace for trace in fig.data if trace.name.startswith('Bragg')]
    assert [trace.name for trace in bragg_traces] == [
        'Bragg peaks: phase-a',
        'Bragg peaks: phase-b',
    ]
    assert list(bragg_traces[0].y) == [1.0]
    assert list(bragg_traces[1].y) == [2.0]
    assert list(fig.layout.yaxis2.ticktext) == ['phase-a', 'phase-b']
    assert list(fig.layout.yaxis2.range) == [2.5, 0.5]
    assert fig.layout.yaxis2.title.text is None
    assert fig.layout.yaxis3.title.text is None
    assert fig.layout.yaxis3.zeroline is False
    assert fig.layout.xaxis3.title.text == '2θ (deg)'
    assert 'Miller indices: (1 0 1)' in bragg_traces[0].text[0]
    assert 'phase-a' in bragg_traces[0].text[0]


def test_plot_powder_meas_vs_calc_adds_background_curve(monkeypatch):
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
        ),
        axes_labels=['2θ (deg)', 'Intensity (arb. units)'],
        title='Powder',
        residual_height_fraction=0.25,
        bragg_peaks_height_fraction=0.10,
        height=None,
        y_bkg=np.array([1.5, 1.5, 1.5]),
    )

    plotter = pp.PlotlyPlotter()
    plotter.plot_powder_meas_vs_calc(plot_spec=plot_spec)

    fig = captured['fig']
    assert len(fig.data) == 5
    assert [trace.name for trace in fig.data[:3]] == [
        'Measured (Imeas)',
        'Background (Ibkg)',
        'Total calculated (Icalc)',
    ]
    background_trace = next(trace for trace in fig.data if trace.name == 'Background (Ibkg)')
    meas_trace = next(trace for trace in fig.data if trace.name == 'Measured (Imeas)')
    calc_trace = next(trace for trace in fig.data if trace.name == 'Total calculated (Icalc)')
    residual_trace = next(trace for trace in fig.data if trace.name == 'Residual (Imeas - Icalc)')
    assert list(background_trace.y) == pytest.approx([1.5, 1.5, 1.5])
    assert background_trace.mode == 'lines'
    assert background_trace.line.color == pp.DEFAULT_COLORS['bkg']
    assert background_trace.line.width == pp.BACKGROUND_LINE_WIDTH
    raw_min = 1.5
    raw_max = 12.0
    raw_range = raw_max - raw_min
    margin = raw_range * pp.MAIN_INTENSITY_RANGE_MARGIN_FRACTION
    assert fig.layout.yaxis.range[0] == pytest.approx(raw_min - margin)
    assert fig.layout.yaxis.range[1] == pytest.approx(raw_max + margin)
    assert meas_trace.legendrank < background_trace.legendrank < calc_trace.legendrank
    assert residual_trace.legendrank > calc_trace.legendrank
    for trace in (meas_trace, background_trace, calc_trace, residual_trace):
        assert 'Ibkg: %{customdata[1]' in trace.hovertemplate
        assert list(trace.customdata[0]) == pytest.approx([10.0, 1.5, 9.0, 1.0])


def test_get_main_intensity_range_uses_unit_padding_for_flat_series():
    from easydiffraction.display.plotters.base import PowderMeasVsCalcSpec
    from easydiffraction.display.plotters.plotly import PlotlyPlotter

    plot_spec = PowderMeasVsCalcSpec(
        x=np.array([1.0]),
        y_meas=np.array([5.0]),
        y_calc=np.array([5.0]),
        y_resid=None,
        bragg_tick_sets=(),
        axes_labels=['2θ (deg)', 'Intensity (arb. units)'],
        title='Powder',
        residual_height_fraction=0.25,
        bragg_peaks_height_fraction=0.10,
        height=None,
        y_bkg=np.array([5.0]),
    )

    assert PlotlyPlotter._get_main_intensity_range(plot_spec) == pytest.approx((4.0, 6.0))


def test_bragg_row_height_pixels_scale_linearly_with_phase_count():
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
        axes_labels=['2θ (deg)', 'Intensity (arb. units)'],
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

    symbol_height = PlotlyPlotter._bragg_tick_symbol_height_pixels()
    single_height = PlotlyPlotter._bragg_row_height_pixels(single_phase)
    two_phase_height = PlotlyPlotter._bragg_row_height_pixels(two_phase)
    assert single_height == pytest.approx(symbol_height)
    assert two_phase_height == pytest.approx(2 * symbol_height)


def test_plot_powder_meas_vs_calc_grows_total_height_for_many_phases(monkeypatch):
    import easydiffraction.display.plotters.plotly as pp

    from easydiffraction.display.plotters.base import BraggTickSet
    from easydiffraction.display.plotters.base import PowderMeasVsCalcSpec

    captured = {}

    def fake_show_figure(self, fig):
        captured.setdefault('figures', []).append(fig)

    monkeypatch.setattr(pp.PlotlyPlotter, '_show_figure', fake_show_figure)

    def plot_spec(phase_count: int) -> PowderMeasVsCalcSpec:
        bragg_tick_sets = tuple(
            BraggTickSet(
                phase_id=f'phase-{idx}',
                x=np.array([1.0 + idx]),
                h=np.array([idx + 1]),
                k=np.array([0]),
                ell=np.array([1]),
                f_squared_calc=np.array([100.0 - idx]),
                f_calc=np.array([10.0 - 0.1 * idx]),
            )
            for idx in range(phase_count)
        )
        return PowderMeasVsCalcSpec(
            x=np.array([1.0, 2.0, 3.0]),
            y_meas=np.array([10.0, 12.0, 11.0]),
            y_calc=np.array([9.0, 11.0, 10.5]),
            y_resid=np.array([1.0, 1.0, 0.5]),
            bragg_tick_sets=bragg_tick_sets,
            axes_labels=['2θ (deg)', 'Intensity (arb. units)'],
            title='Powder',
            residual_height_fraction=0.25,
            bragg_peaks_height_fraction=0.10,
            height=None,
        )

    plotter = pp.PlotlyPlotter()
    plotter.plot_powder_meas_vs_calc(plot_spec=plot_spec(1))
    plotter.plot_powder_meas_vs_calc(plot_spec=plot_spec(10))

    single_fig, multi_fig = captured['figures']

    def row_height_pixels(fig, axis_name: str) -> float:
        axis = getattr(fig.layout, axis_name)
        plot_area_height = fig.layout.height - fig.layout.margin.t - fig.layout.margin.b
        return plot_area_height * (axis.domain[1] - axis.domain[0])

    assert multi_fig.layout.height > single_fig.layout.height
    assert row_height_pixels(multi_fig, 'yaxis') == pytest.approx(
        row_height_pixels(single_fig, 'yaxis')
    )
    assert row_height_pixels(multi_fig, 'yaxis3') == pytest.approx(
        row_height_pixels(single_fig, 'yaxis3')
    )
    assert row_height_pixels(multi_fig, 'yaxis2') == pytest.approx(
        row_height_pixels(single_fig, 'yaxis2') * 10
    )


def test_plot_powder_meas_vs_calc_uses_explicit_plotly_height_as_pixels(monkeypatch):
    import easydiffraction.display.plotters.plotly as pp

    from easydiffraction.display.plotters.base import BraggTickSet
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
            y_resid=None,
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
            axes_labels=['2θ (deg)', 'Intensity (arb. units)'],
            title='Powder',
            residual_height_fraction=0.25,
            bragg_peaks_height_fraction=0.10,
            height=800,
        ),
    )

    assert captured['fig'].layout.height == 800


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
            axes_labels=['2θ (deg)', 'Intensity (arb. units)'],
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
    assert fig.layout.xaxis2.title.text == '2θ (deg)'
    assert fig.layout.title.font.size == pp.TITLE_FONT_SIZE
    assert fig.layout.yaxis.title.font.size == pp.AXIS_TITLE_FONT_SIZE
    assert fig.layout.xaxis2.title.font.size == pp.AXIS_TITLE_FONT_SIZE
    assert [trace.name for trace in fig.data] == [
        'Measured (Imeas)',
        'Total calculated (Icalc)',
        'Residual (Imeas - Icalc)',
    ]


def test_plot_powder_meas_vs_calc_styles_predictive_max_posterior_and_band(monkeypatch):
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
            axes_labels=['2θ (deg)', 'Intensity (arb. units)'],
            title='Powder',
            residual_height_fraction=0.25,
            bragg_peaks_height_fraction=0.15,
            height=None,
            predictive_lower_95=np.array([8.0, 9.0, 10.0]),
            predictive_upper_95=np.array([10.0, 11.0, 12.0]),
            y_calc_name='Best posterior sample',
            y_calc_line_dash='dot',
        ),
    )

    fig = captured['fig']
    predictive_band_trace = next(
        trace for trace in fig.data if trace.name == '95% credible interval'
    )
    max_posterior_trace = next(
        trace for trace in fig.data if trace.name == 'Best posterior sample'
    )
    residual_trace = next(trace for trace in fig.data if trace.name == 'Residual (Imeas - Icalc)')

    assert predictive_band_trace.fillcolor == pp.PREDICTIVE_BAND_COLOR
    assert predictive_band_trace.legendrank == 35
    assert max_posterior_trace.line.dash == 'dot'
    assert predictive_band_trace.legendrank < residual_trace.legendrank


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
            axes_labels=['2θ (deg)', 'Intensity (arb. units)'],
            title='Powder',
            residual_height_fraction=0.25,
            bragg_peaks_height_fraction=0.15,
            height=None,
        ),
    )

    fig = captured['fig']
    raw_min = 180.0
    raw_max = 3600.0
    raw_range = raw_max - raw_min
    margin = raw_range * pp.MAIN_INTENSITY_RANGE_MARGIN_FRACTION
    expected_main_min = raw_min - margin
    expected_main_max = raw_max + margin
    expected_limit = 0.5 * (expected_main_max - expected_main_min) * 0.25
    assert fig.layout.yaxis2.scaleanchor == 'y'
    assert fig.layout.yaxis2.scaleratio == pytest.approx(1.0)
    assert fig.layout.yaxis.range[0] == pytest.approx(expected_main_min)
    assert fig.layout.yaxis.range[1] == pytest.approx(expected_main_max)
    assert fig.layout.yaxis2.range[0] == pytest.approx(-expected_limit)
    assert fig.layout.yaxis2.range[1] == pytest.approx(expected_limit)
    plot_area_height = fig.layout.height - fig.layout.margin.t - fig.layout.margin.b
    main_pixels = plot_area_height * (fig.layout.yaxis.domain[1] - fig.layout.yaxis.domain[0])
    residual_pixels = plot_area_height * (
        fig.layout.yaxis2.domain[1] - fig.layout.yaxis2.domain[0]
    )
    main_units_per_pixel = (fig.layout.yaxis.range[1] - fig.layout.yaxis.range[0]) / main_pixels
    residual_units_per_pixel = (
        fig.layout.yaxis2.range[1] - fig.layout.yaxis2.range[0]
    ) / residual_pixels
    assert residual_units_per_pixel == pytest.approx(main_units_per_pixel)
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
            axes_labels=['2θ (deg)', 'Intensity (arb. units)'],
            title='Powder',
            residual_height_fraction=0.25,
            bragg_peaks_height_fraction=0.15,
            height=None,
        ),
    )

    fig = captured['fig']
    raw_min = 180.0
    raw_max = 3600.0
    raw_range = raw_max - raw_min
    margin = raw_range * pp.MAIN_INTENSITY_RANGE_MARGIN_FRACTION
    expected_limit = 0.5 * ((raw_max + margin) - (raw_min - margin)) * 0.25
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
            axes_labels=['2θ (deg)', 'Intensity (arb. units)'],
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
