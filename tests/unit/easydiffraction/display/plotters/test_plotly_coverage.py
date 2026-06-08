# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Supplementary coverage tests for the Plotly plotting backend.

These exercise behavior and edge paths not covered by the primary
``test_plotly.py``: the correlation heatmap, the fixed-aspect wrapper
metadata, the templated ``serialize_html`` branch, excluded-region
shading, nice-axis rounding, the predictive draws/band handling, and the
small numeric edge cases in the shared axis-range helpers.
"""

import base64

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pytest
from plotly.subplots import make_subplots


def test_init_uses_browser_renderer_in_pycharm(monkeypatch):
    """The browser renderer is forced when running inside PyCharm."""
    import easydiffraction.display.plotters.plotly as pp

    monkeypatch.setattr(pp, 'in_pycharm', lambda: True)

    captured = {}

    class DummyRenderers:
        default = None

    class DummyTemplates:
        default = None

    monkeypatch.setattr(pp.pio, 'renderers', DummyRenderers, raising=False)
    monkeypatch.setattr(pp.pio, 'templates', DummyTemplates, raising=False)

    def fake_default_template_name(cls):
        captured['template'] = 'plotly_white'
        return 'plotly_white'

    monkeypatch.setattr(
        pp.PlotlyPlotter,
        '_default_template_name',
        classmethod(fake_default_template_name),
    )

    pp.PlotlyPlotter()

    assert DummyRenderers.default == 'browser'
    assert DummyTemplates.default == 'plotly_white'


@pytest.mark.parametrize(
    'in_jupyter_value',
    [False, True],
)
def test_is_dark_mode_uses_jupyter_or_system_detection(monkeypatch, in_jupyter_value):
    """Dark-mode detection prefers notebook state, else the OS theme."""
    import easydiffraction.display.plotters.plotly as pp

    monkeypatch.setattr(pp, 'in_jupyter', lambda: in_jupyter_value)
    monkeypatch.setattr(pp, 'is_dark', lambda: True)
    monkeypatch.setattr(pp.darkdetect, 'isDark', lambda: False)

    # In Jupyter the notebook detector (True) wins; otherwise the system
    # detector (False) is consulted.
    assert pp.PlotlyPlotter._is_dark_mode() is in_jupyter_value


def test_single_crystal_axis_range_returns_unit_range_for_empty_inputs():
    import easydiffraction.display.plotters.plotly as pp

    minimum, maximum = pp.single_crystal_axis_range(
        x_calc=[],
        y_meas=[],
        y_meas_su=None,
    )
    assert (minimum, maximum) == (0.0, 1.0)


def test_single_crystal_axis_range_uses_unit_margin_for_degenerate_span():
    import easydiffraction.display.plotters.plotly as pp

    # A flat span (calc == meas, no uncertainty) has zero raw margin, so
    # the helper pads by one unit on each side instead.
    minimum, maximum = pp.single_crystal_axis_range(
        x_calc=[5.0],
        y_meas=[5.0],
        y_meas_su=None,
    )
    assert minimum == pytest.approx(4.0)
    assert maximum == pytest.approx(6.0)


@pytest.mark.parametrize(
    ('span', 'expected_step'),
    [
        # raw_step = span / 6, then rounded to the nearest 1/2/5 decade.
        (12.0, 2.0),  # raw 2.0 -> nice 2.0
        (24.0, 5.0),  # raw 4.0 -> nice 5.0
        (54.0, 10.0),  # raw 9.0 -> nice 10.0
    ],
)
def test_single_crystal_tick_step_selects_each_nice_fraction(span, expected_step):
    import easydiffraction.display.plotters.plotly as pp

    assert pp.single_crystal_tick_step(0.0, span) == pytest.approx(expected_step)


def test_single_crystal_tick_step_handles_nonpositive_target():
    import easydiffraction.display.plotters.plotly as pp

    assert pp.single_crystal_tick_step(0.0, 100.0, target_ticks=0) == pytest.approx(1.0)


@pytest.mark.parametrize(
    ('raw_limit', 'expected'),
    [
        (0.0, 1.0),  # non-positive falls back to 1.0
        (0.7, 1.0),  # fraction 0.7 -> first nice fraction 1.0
        (1.5, 2.0),  # fraction 1.5 -> 2.0
        (4.0, 5.0),  # fraction 4.0 -> 5.0
        (60.0, 100.0),  # fraction 6.0 -> 10.0 * base(10) = 100
    ],
)
def test_nice_axis_limit_rounds_up_to_readable_values(raw_limit, expected):
    import easydiffraction.display.plotters.plotly as pp

    assert pp.PlotlyPlotter._nice_axis_limit(raw_limit) == pytest.approx(expected)


@pytest.mark.parametrize(
    ('raw_limit', 'expected'),
    [
        (0.0, 1.0),  # non-positive falls back to 1.0
        (3.0, 2.5),  # largest display fraction <= 3.0
        (9.0, 7.5),  # largest display fraction <= 9.0
        (1.0, 1.0),  # exactly the smallest fraction
        (0.4, 0.4),  # fraction 4.0 of base 0.1 -> 4.0 * 0.1
    ],
)
def test_get_display_tick_limit_rounds_down_within_limit(raw_limit, expected):
    import easydiffraction.display.plotters.plotly as pp

    assert pp.PlotlyPlotter._get_display_tick_limit(raw_limit) == pytest.approx(expected)


def test_predictive_draw_array_rejects_wrong_shape_and_empty():
    import easydiffraction.display.plotters.plotly as pp

    assert pp.PlotlyPlotter._predictive_draw_array(None) is None
    # 1D is not the required 2D draw layout.
    assert pp.PlotlyPlotter._predictive_draw_array(np.array([1.0, 2.0, 3.0])) is None
    # Empty 2D array is rejected too.
    assert pp.PlotlyPlotter._predictive_draw_array(np.empty((0, 3))) is None

    valid = np.array([[1.0, 2.0], [3.0, 4.0]])
    result = pp.PlotlyPlotter._predictive_draw_array(valid)
    assert result is not None
    assert np.array_equal(result, valid)


def test_get_residual_limit_returns_unit_without_residuals():
    import easydiffraction.display.plotters.plotly as pp
    from easydiffraction.display.plotters.base import PowderMeasVsCalcSpec

    plot_spec = PowderMeasVsCalcSpec(
        x=np.array([1.0, 2.0]),
        y_meas=np.array([1.0, 2.0]),
        y_calc=np.array([1.0, 2.0]),
        y_resid=None,
        bragg_tick_sets=(),
        axes_labels=['x', 'y'],
        title='t',
        residual_height_fraction=0.25,
        bragg_peaks_height_fraction=0.1,
        height=None,
    )
    assert pp.PlotlyPlotter._get_residual_limit(plot_spec) == pytest.approx(1.0)


def test_get_residual_limit_returns_unit_for_empty_series():
    import easydiffraction.display.plotters.plotly as pp
    from easydiffraction.display.plotters.base import PowderMeasVsCalcSpec

    plot_spec = PowderMeasVsCalcSpec(
        x=np.array([], dtype=float),
        y_meas=np.array([], dtype=float),
        y_calc=np.array([], dtype=float),
        y_resid=np.array([], dtype=float),
        bragg_tick_sets=(),
        axes_labels=['x', 'y'],
        title='t',
        residual_height_fraction=0.25,
        bragg_peaks_height_fraction=0.1,
        height=None,
    )
    assert pp.PlotlyPlotter._get_residual_limit(plot_spec) == pytest.approx(1.0)


def test_get_main_intensity_range_returns_unit_for_empty_series():
    import easydiffraction.display.plotters.plotly as pp
    from easydiffraction.display.plotters.base import PowderMeasVsCalcSpec

    plot_spec = PowderMeasVsCalcSpec(
        x=np.array([], dtype=float),
        y_meas=np.array([], dtype=float),
        y_calc=np.array([], dtype=float),
        y_resid=None,
        bragg_tick_sets=(),
        axes_labels=['x', 'y'],
        title='t',
        residual_height_fraction=0.25,
        bragg_peaks_height_fraction=0.1,
        height=None,
    )
    assert pp.PlotlyPlotter._get_main_intensity_range(plot_spec) == (0.0, 1.0)


def test_main_intensity_series_includes_predictive_bounds_and_draws():
    import easydiffraction.display.plotters.plotly as pp
    from easydiffraction.display.plotters.base import PowderMeasVsCalcSpec

    plot_spec = PowderMeasVsCalcSpec(
        x=np.array([1.0, 2.0]),
        y_meas=np.array([10.0, 12.0]),
        y_calc=np.array([9.0, 11.0]),
        y_resid=None,
        bragg_tick_sets=(),
        axes_labels=['x', 'y'],
        title='t',
        residual_height_fraction=0.25,
        bragg_peaks_height_fraction=0.1,
        height=None,
        y_bkg=np.array([1.0, 1.0]),
        predictive_lower_95=np.array([8.0, 9.0]),
        predictive_upper_95=np.array([13.0, 14.0]),
        predictive_draws=np.array([[7.0, 8.0], [9.0, 10.0]]),
    )

    series = pp.PlotlyPlotter._main_intensity_series(
        plot_spec,
        y_meas=np.asarray(plot_spec.y_meas),
        y_calc=np.asarray(plot_spec.y_calc),
    )
    flat_min = min(float(np.min(part)) for part in series)
    flat_max = max(float(np.max(part)) for part in series)
    # Predictive draws (min 7) and upper band (max 14) widen the range.
    assert flat_min == pytest.approx(1.0)
    assert flat_max == pytest.approx(14.0)


def test_append_non_empty_series_skips_none_and_empty():
    import easydiffraction.display.plotters.plotly as pp

    collected = []
    pp.PlotlyPlotter._append_non_empty_series(collected, None)
    pp.PlotlyPlotter._append_non_empty_series(collected, np.array([], dtype=float))
    assert collected == []

    pp.PlotlyPlotter._append_non_empty_series(collected, np.array([1.0, 2.0]))
    assert len(collected) == 1
    assert np.array_equal(collected[0], np.array([1.0, 2.0]))


def test_add_predictive_draw_traces_caps_and_labels_first_only():
    import easydiffraction.display.plotters.plotly as pp
    from easydiffraction.display.plotters.base import PowderMeasVsCalcSpec

    draw_count = pp.PREDICTIVE_DRAW_PLOT_CAP + 5
    plot_spec = PowderMeasVsCalcSpec(
        x=np.array([1.0, 2.0, 3.0]),
        y_meas=np.array([10.0, 12.0, 11.0]),
        y_calc=np.array([9.0, 11.0, 10.5]),
        y_resid=None,
        bragg_tick_sets=(),
        axes_labels=['x', 'y'],
        title='t',
        residual_height_fraction=0.25,
        bragg_peaks_height_fraction=0.1,
        height=None,
        predictive_draws=np.ones((draw_count, 3)),
    )

    # Draw traces are placed on row=1/col=1, so a subplot grid is needed.
    fig = make_subplots(rows=1, cols=1)
    plotter = pp.PlotlyPlotter()
    plotter._add_predictive_draw_traces(fig=fig, plot_spec=plot_spec)

    # Draw traces are capped at PREDICTIVE_DRAW_PLOT_CAP.
    assert len(fig.data) == pp.PREDICTIVE_DRAW_PLOT_CAP
    # Only the first draw carries a legend entry.
    assert fig.data[0].name == 'Posterior draw'
    assert fig.data[0].showlegend is True
    assert fig.data[1].showlegend is False
    assert fig.data[1].name is None


def test_predictive_draws_widen_main_range_in_built_figure(monkeypatch):
    import easydiffraction.display.plotters.plotly as pp
    from easydiffraction.display.plotters.base import PowderMeasVsCalcSpec

    plot_spec = PowderMeasVsCalcSpec(
        x=np.array([1.0, 2.0, 3.0]),
        y_meas=np.array([10.0, 12.0, 11.0]),
        y_calc=np.array([9.0, 11.0, 10.5]),
        y_resid=np.array([1.0, 1.0, 0.5]),
        bragg_tick_sets=(),
        axes_labels=['2θ (deg)', 'Intensity (arb. units)'],
        title='Powder',
        residual_height_fraction=0.25,
        bragg_peaks_height_fraction=0.1,
        height=None,
        predictive_draws=np.array([[100.0, 100.0, 100.0]]),
    )

    plotter = pp.PlotlyPlotter()
    fig = plotter.build_powder_meas_vs_calc_figure(plot_spec=plot_spec)

    # A single posterior-draw trace is added on the main row...
    draw_traces = [trace for trace in fig.data if trace.name == 'Posterior draw']
    assert len(draw_traces) == 1
    # ...and it pushes the main y-range up to include 100.
    assert fig.layout.yaxis.range[1] > 100.0


def test_get_residual_limit_falls_back_to_nice_axis_limit():
    import easydiffraction.display.plotters.plotly as pp
    from easydiffraction.display.plotters.base import PowderMeasVsCalcSpec

    # A flat main intensity (meas == calc) yields a zero scale-matched
    # half range, forcing the nice-axis-limit fallback on the residuals.
    plot_spec = PowderMeasVsCalcSpec(
        x=np.array([1.0, 2.0, 3.0]),
        y_meas=np.array([5.0, 5.0, 5.0]),
        y_calc=np.array([5.0, 5.0, 5.0]),
        y_resid=np.array([0.0, 0.0, 0.0]),
        bragg_tick_sets=(),
        axes_labels=['x', 'y'],
        title='t',
        residual_height_fraction=0.0,
        bragg_peaks_height_fraction=0.1,
        height=None,
    )
    # max abs residual is 0 -> _nice_axis_limit(0.0) -> 1.0
    assert pp.PlotlyPlotter._get_residual_limit(plot_spec) == pytest.approx(1.0)


def test_plot_powder_shades_excluded_regions(monkeypatch):
    import easydiffraction.display.plotters.plotly as pp

    captured = {}

    def fake_show_figure(self, fig):
        captured['fig'] = fig

    monkeypatch.setattr(pp.PlotlyPlotter, '_show_figure', fake_show_figure)

    plotter = pp.PlotlyPlotter()
    plotter.plot_powder(
        np.array([0.0, 1.0, 2.0, 3.0, 4.0]),
        y_series=[np.array([1.0, 2.0, 3.0, 2.0, 1.0])],
        labels=['calc'],
        axes_labels=['x', 'y'],
        title='t',
        height=None,
        excluded_ranges=((1.0, 2.0), (3.0, 3.5)),
    )

    fig = captured['fig']
    rects = [
        shape
        for shape in fig.layout.shapes
        if shape.type == 'rect' and shape.fillcolor == pp.EXCLUDED_REGION_FILL_COLOR
    ]
    assert len(rects) == 2
    assert {(rect.x0, rect.x1) for rect in rects} == {(1.0, 2.0), (3.0, 3.5)}
    # The shaded regions sit behind the data.
    assert all(rect.layer == 'below' for rect in rects)


def test_plot_correlation_heatmap_builds_heatmap_labels_and_frame(monkeypatch):
    import easydiffraction.display.plotters.plotly as pp

    captured = {}

    def fake_show_figure(self, fig):
        captured['fig'] = fig

    monkeypatch.setattr(pp.PlotlyPlotter, '_show_figure', fake_show_figure)

    corr_df = pd.DataFrame(
        [
            [1.0, 0.8, 0.1],
            [0.8, 1.0, -0.9],
            [0.1, -0.9, 1.0],
        ],
        columns=['alpha', 'beta', 'gamma'],
        index=['alpha', 'beta', 'gamma'],
    )

    plotter = pp.PlotlyPlotter()
    plotter.plot_correlation_heatmap(
        corr_df,
        title='Correlations',
        threshold=0.5,
        precision=2,
    )

    fig = captured['fig']
    heatmap = next(trace for trace in fig.data if trace.type == 'heatmap')
    label_trace = next(trace for trace in fig.data if trace.type == 'scatter')

    assert heatmap.zmin == -1.0
    assert heatmap.zmax == 1.0
    assert 'correlation: %{z:.2f}' in heatmap.hovertemplate

    # Only off-diagonal cells at/above the threshold are labelled: the
    # three diagonal 1.0 values, the two 0.8 pairs, and the two -0.9
    # pairs survive; the 0.1 pair is below threshold and dropped.
    assert '0.10' not in label_trace.text
    assert '0.80' in label_trace.text
    assert '-0.90' in label_trace.text
    assert label_trace.mode == 'text'

    # Axis tick labels come from the DataFrame headers.
    assert list(fig.layout.xaxis.ticktext) == ['alpha', 'beta', 'gamma']
    assert list(fig.layout.yaxis.ticktext) == ['alpha', 'beta', 'gamma']
    assert fig.layout.yaxis.autorange == 'reversed'

    # The frame rect plus internal separators are emitted as shapes, and
    # the figure is flagged as a correlation heatmap for live theme sync.
    rect_shapes = [shape for shape in fig.layout.shapes if shape.type == 'rect']
    assert len(rect_shapes) == 1
    assert fig.layout.meta[pp.THEME_SYNC_META_KEY][pp.THEME_SYNC_CORRELATION_HEATMAP_KEY] is True
    assert pp.PlotlyPlotter._figure_is_correlation_heatmap(fig) is True


def test_plot_correlation_heatmap_without_threshold_labels_every_cell(monkeypatch):
    import easydiffraction.display.plotters.plotly as pp

    captured = {}

    def fake_show_figure(self, fig):
        captured['fig'] = fig

    monkeypatch.setattr(pp.PlotlyPlotter, '_show_figure', fake_show_figure)

    corr_df = pd.DataFrame(
        [[1.0, 0.05], [0.05, 1.0]],
        columns=['a', 'b'],
        index=['a', 'b'],
    )

    plotter = pp.PlotlyPlotter()
    plotter.plot_correlation_heatmap(
        corr_df,
        title='Correlations',
        threshold=None,
        precision=3,
    )

    fig = captured['fig']
    label_trace = next(trace for trace in fig.data if trace.type == 'scatter')
    # With no threshold, every finite cell (4 of them) is labelled.
    assert len(label_trace.text) == 4
    assert '0.050' in label_trace.text


def test_get_correlation_label_trace_returns_none_when_all_filtered():
    import easydiffraction.display.plotters.plotly as pp

    corr_df = pd.DataFrame(
        [[float('nan'), 0.1], [0.1, float('nan')]],
        columns=['a', 'b'],
        index=['a', 'b'],
    )

    trace = pp.PlotlyPlotter._get_correlation_label_trace(
        corr_df,
        x_centers=np.array([0.5, 1.5]),
        y_centers=np.array([0.5, 1.5]),
        threshold=0.5,
        precision=2,
    )
    # NaN cells are skipped and the 0.1 cells fall below the threshold,
    # so there is nothing to annotate.
    assert trace is None


def test_correlation_label_color_is_light():
    import easydiffraction.display.plotters.plotly as pp

    assert pp.PlotlyPlotter._correlation_label_color() == '#f5f5f5'


def test_apply_theme_sync_meta_merges_indexes_and_skips_invalid():
    import easydiffraction.display.plotters.plotly as pp

    fig = go.Figure()
    truthy_bool = True
    pp.PlotlyPlotter._apply_theme_sync_meta(
        fig,
        axis_frame_shape_indexes=[0, 2, -1, truthy_bool, 5],
        correlation_heatmap=True,
    )

    theme_sync = fig.layout.meta[pp.THEME_SYNC_META_KEY]
    # Negative indexes and booleans are filtered out; valid ints remain.
    assert theme_sync[pp.THEME_SYNC_AXIS_FRAME_SHAPE_INDEXES_KEY] == [0, 2, 5]
    assert theme_sync[pp.THEME_SYNC_CORRELATION_HEATMAP_KEY] is True


def test_apply_theme_sync_meta_no_op_without_payload():
    import easydiffraction.display.plotters.plotly as pp

    fig = go.Figure()
    pp.PlotlyPlotter._apply_theme_sync_meta(
        fig,
        axis_frame_shape_indexes=(),
        correlation_heatmap=False,
    )
    # Nothing to store, so no theme-sync metadata is written.
    meta = pp.PlotlyPlotter._figure_meta(fig)
    assert meta is None or pp.THEME_SYNC_META_KEY not in meta


def test_ed_theme_sync_payload_reports_indexes_and_heatmap_flag():
    import easydiffraction.display.plotters.plotly as pp

    fig = go.Figure()
    pp.PlotlyPlotter._apply_theme_sync_meta(
        fig,
        axis_frame_shape_indexes=[0, 1],
        correlation_heatmap=True,
    )
    payload = pp.PlotlyPlotter._ed_theme_sync_payload(fig)
    assert payload['axisFrameShapeIndexes'] == [0, 1]
    assert payload['correlationHeatmap'] is True


def test_ed_theme_sync_payload_empty_without_metadata():
    import easydiffraction.display.plotters.plotly as pp

    fig = go.Figure()
    assert pp.PlotlyPlotter._ed_theme_sync_payload(fig) == {}


def test_figure_meta_returns_none_for_layoutless_object():
    import easydiffraction.display.plotters.plotly as pp

    class NoLayout:
        layout = None

    assert pp.PlotlyPlotter._figure_meta(NoLayout()) is None


def test_figure_meta_reads_meta_from_layout_kwargs():
    import easydiffraction.display.plotters.plotly as pp

    class Layout:
        meta = None
        kwargs = {'meta': {'flag': 1}}

    class Fig:
        layout = Layout()

    assert pp.PlotlyPlotter._figure_meta(Fig()) == {'flag': 1}


def test_figure_is_correlation_heatmap_false_without_meta():
    import easydiffraction.display.plotters.plotly as pp

    assert pp.PlotlyPlotter._figure_is_correlation_heatmap(go.Figure()) is False


def test_fixed_aspect_wrapper_aspect_ratio_variants():
    import easydiffraction.display.plotters.plotly as pp

    # No meta at all.
    assert pp.PlotlyPlotter._fixed_aspect_wrapper_aspect_ratio(go.Figure()) is None

    # Wrapper present but the aspect ratio is blank after stripping.
    blank = go.Figure()
    blank.update_layout(meta={pp.FIXED_ASPECT_WRAPPER_META_KEY: {'aspect_ratio': '   '}})
    assert pp.PlotlyPlotter._fixed_aspect_wrapper_aspect_ratio(blank) is None

    # Wrapper present but not a dict.
    not_dict = go.Figure()
    not_dict.update_layout(meta={pp.FIXED_ASPECT_WRAPPER_META_KEY: 'nope'})
    assert pp.PlotlyPlotter._fixed_aspect_wrapper_aspect_ratio(not_dict) is None

    # Valid aspect ratio is stripped and returned.
    valid = go.Figure()
    valid.update_layout(meta={pp.FIXED_ASPECT_WRAPPER_META_KEY: {'aspect_ratio': ' 16 / 9 '}})
    assert pp.PlotlyPlotter._fixed_aspect_wrapper_aspect_ratio(valid) == '16 / 9'


def test_fixed_aspect_wrapper_max_width_variants():
    import easydiffraction.display.plotters.plotly as pp

    # No meta -> None.
    assert pp.PlotlyPlotter._fixed_aspect_wrapper_max_width(go.Figure()) is None

    # Non-positive width is rejected.
    zero = go.Figure()
    zero.update_layout(meta={pp.FIXED_ASPECT_WRAPPER_META_KEY: {'max_width_pixels': 0}})
    assert pp.PlotlyPlotter._fixed_aspect_wrapper_max_width(zero) is None

    # A positive float is coerced to int.
    sized = go.Figure()
    sized.update_layout(meta={pp.FIXED_ASPECT_WRAPPER_META_KEY: {'max_width_pixels': 640.0}})
    assert pp.PlotlyPlotter._fixed_aspect_wrapper_max_width(sized) == 640


def test_wrap_html_figure_emits_max_width_when_requested():
    import easydiffraction.display.plotters.plotly as pp

    fig = go.Figure()
    fig.update_layout(
        meta={
            pp.FIXED_ASPECT_WRAPPER_META_KEY: {
                'aspect_ratio': '1 / 1',
                'max_width_pixels': 480,
            }
        }
    )

    wrapped = pp.PlotlyPlotter._wrap_html_figure(fig, '<div>plot</div>')
    assert 'max-width: 480px;' in wrapped
    assert 'aspect-ratio: 1 / 1;' in wrapped
    assert pp.FIXED_ASPECT_WRAPPER_CLASS_NAME in wrapped
    assert '<div>plot</div>' in wrapped


def test_wrap_html_figure_is_passthrough_without_aspect_ratio():
    import easydiffraction.display.plotters.plotly as pp

    assert pp.PlotlyPlotter._wrap_html_figure(go.Figure(), '<div>x</div>') == '<div>x</div>'


def test_figure_height_uses_explicit_layout_height():
    import easydiffraction.display.plotters.plotly as pp

    fig = go.Figure()
    fig.update_layout(height=512)
    assert pp.PlotlyPlotter._figure_height(fig) == 512


def test_figure_height_falls_back_to_default_pixels():
    import easydiffraction.display.plotters.plotly as pp

    # A height-less figure converts the unit-count default to pixels.
    assert pp.PlotlyPlotter._figure_height(go.Figure()) == (
        pp.DEFAULT_HEIGHT * pp.PLOTLY_HEIGHT_PER_UNIT
    )


@pytest.mark.parametrize(
    'template',
    ['plotly_white', 'plotly_dark'],
)
def test_template_color_helpers_resolve_known_templates(template):
    import easydiffraction.display.plotters.plotly as pp

    assert pp.PlotlyPlotter._background_color_for_template(template) is not None
    assert pp.PlotlyPlotter._axis_frame_color_for_template(template) is not None
    assert pp.PlotlyPlotter._inner_tick_grid_color_for_template(template) is not None
    assert pp.PlotlyPlotter._legend_background_color_for_template(template) is not None


def test_template_color_helpers_return_none_for_unknown_template():
    import easydiffraction.display.plotters.plotly as pp

    assert pp.PlotlyPlotter._background_color_for_template('mystery') is None
    assert pp.PlotlyPlotter._axis_frame_color_for_template('mystery') is None
    assert pp.PlotlyPlotter._inner_tick_grid_color_for_template('mystery') is None
    assert pp.PlotlyPlotter._legend_background_color_for_template('mystery') is None


def test_serialize_html_force_template_applies_template_and_colors():
    import easydiffraction.display.plotters.plotly as pp

    fig = go.Figure(go.Scatter(x=[0.0, 1.0], y=[0.0, 1.0]))
    html = pp.PlotlyPlotter.serialize_html(
        fig,
        include_plotlyjs=False,
        force_template='plotly_dark',
    )

    # The forced template is applied to the figure layout...
    assert fig.layout.template is not None
    # ...the dark background is baked into the plot area...
    assert fig.layout.plot_bgcolor == pp.DARK_BACKGROUND_COLOR
    # ...and an eager (non-shared) HTML body is produced.
    assert 'plotly-graph-div' in html or 'newPlot' in html


def test_serialize_html_force_template_honors_explicit_axis_and_grid_colors():
    import easydiffraction.display.plotters.plotly as pp

    fig = go.Figure(go.Scatter(x=[0.0, 1.0], y=[0.0, 1.0]))
    pp.PlotlyPlotter.serialize_html(
        fig,
        include_plotlyjs=False,
        force_template='plotly_white',
        axis_frame_color='rgb(1, 2, 3)',
        grid_color='rgb(4, 5, 6)',
    )

    assert fig.layout.xaxis.linecolor == 'rgb(1, 2, 3)'
    assert fig.layout.yaxis.linecolor == 'rgb(1, 2, 3)'
    assert fig.layout.xaxis.gridcolor == 'rgb(4, 5, 6)'
    assert fig.layout.yaxis.gridcolor == 'rgb(4, 5, 6)'


def test_serialize_html_shared_embeds_theme_sync_for_heatmap(monkeypatch):
    import easydiffraction.display.plotters.plotly as pp
    from easydiffraction.utils.environment import FigureEmbedMode

    captured = {}

    def fake_show_figure(self, fig):
        captured['fig'] = fig

    monkeypatch.setattr(pp.PlotlyPlotter, '_show_figure', fake_show_figure)

    corr_df = pd.DataFrame(
        [[1.0, 0.7], [0.7, 1.0]],
        columns=['a', 'b'],
        index=['a', 'b'],
    )
    plotter = pp.PlotlyPlotter()
    plotter.plot_correlation_heatmap(corr_df, title='t', threshold=0.5, precision=2)
    fig = captured['fig']

    html = pp.PlotlyPlotter.serialize_html(
        fig,
        include_plotlyjs=False,
        mode=FigureEmbedMode.SHARED,
    )
    # The lazy placeholder carries the correlation-heatmap theme-sync
    # flag so the shared loader can re-theme the heatmap colorscale.
    assert 'correlationHeatmap' in html
    assert 'ed-figure-spec' in html


def test_serialize_html_shared_downcasts_via_figure_height(monkeypatch):
    import easydiffraction.display.plotters.plotly as pp
    from easydiffraction.utils.environment import FigureEmbedMode

    fig = go.Figure(go.Scatter(x=np.arange(5.0), y=np.arange(5.0)))
    fig.update_layout(height=321)

    html = pp.PlotlyPlotter.serialize_html(
        fig,
        include_plotlyjs=False,
        mode=FigureEmbedMode.SHARED,
    )
    # The skeleton reserves the figure's explicit pixel height.
    assert 'height: 321px' in html


def test_typed_arrays_to_float32_recurses_through_lists():
    import easydiffraction.display.plotters.plotly as pp

    values = np.arange(4, dtype='<f8')
    spec = {
        'dtype': 'f8',
        'bdata': base64.b64encode(values.tobytes()).decode('ascii'),
        'shape': '4',
    }
    payload = [spec, {'nested': [spec]}, 'scalar', 7]

    result = pp._typed_arrays_to_float32(payload)
    assert result[0]['dtype'] == 'f4'
    assert result[1]['nested'][0]['dtype'] == 'f4'
    assert result[2] == 'scalar'
    assert result[3] == 7


def test_show_figure_uses_native_show_in_pycharm(monkeypatch):
    import easydiffraction.display.plotters.plotly as pp

    monkeypatch.setattr(pp, 'in_pycharm', lambda: True)

    captured = {}

    class DummyFig:
        layout = None
        data = ()

        def update_layout(self, **kwargs):
            captured.setdefault('layout_updates', []).append(kwargs)

        def show(self, config=None):
            captured['config'] = config

    plotter = pp.PlotlyPlotter()
    plotter._show_figure(DummyFig())

    # In PyCharm the native renderer is used, not the inline HTML path.
    assert captured['config'] == pp.PlotlyPlotter._get_config()


def test_has_visible_legend_reads_named_traces_and_layout_flag():
    import easydiffraction.display.plotters.plotly as pp

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[0], y=[0], name='Measured'))
    assert pp.PlotlyPlotter._has_visible_legend(fig) is True

    fig.update_layout(showlegend=False)
    assert pp.PlotlyPlotter._has_visible_legend(fig) is False

    hidden = go.Figure()
    hidden.add_trace(go.Scatter(x=[0], y=[0], name='hidden', visible=False))
    assert pp.PlotlyPlotter._has_visible_legend(hidden) is False


def test_packaged_asset_reads_runtime_and_loader():
    import easydiffraction.display.plotters.plotly as pp

    runtime = pp._packaged_asset(pp._PLOTLY_RUNTIME_ASSET)
    loader = pp._packaged_asset(pp._FIGURE_LOADER_ASSET)
    assert 'Plotly' in runtime  # the self-hosted runtime bundle
    assert 'edFigures' in loader  # the shared figure loader


def test_live_runtime_bootstrap_injects_once_per_session(monkeypatch):
    import easydiffraction.display.plotters.plotly as pp

    monkeypatch.setattr(pp.PlotlyPlotter, '_live_runtime_injected', False)
    first = pp.PlotlyPlotter._live_runtime_bootstrap_js()
    second = pp.PlotlyPlotter._live_runtime_bootstrap_js()
    # First call carries the runtime + loader JS; later calls are empty.
    assert 'Plotly' in first
    assert 'edFigures' in first
    assert second == ''


def test_show_figure_live_emits_single_output_with_render(monkeypatch):
    import easydiffraction.display.plotters.plotly as pp

    monkeypatch.setattr(pp, 'in_pycharm', lambda: False)
    monkeypatch.setattr(pp, 'resolve_figure_embed_mode', lambda: pp.FigureEmbedMode.INLINE)
    monkeypatch.setattr(pp.PlotlyPlotter, '_live_runtime_injected', False)
    captured = []
    monkeypatch.setattr(pp, 'display', captured.append)
    monkeypatch.setattr(pp, 'HTML', lambda value: value)

    fig = go.Figure(data=[go.Scatter(x=[1, 2, 3], y=[4, 5, 6], name='t')])
    fig.update_layout(height=400)
    plotter = pp.PlotlyPlotter()

    plotter._show_figure(fig)
    # A single HTML output: target div + one render script, carrying the
    # one-time inlined runtime on the first figure.
    assert len(captured) == 1
    first = captured[0]
    assert 'ed-figure-target' in first
    assert first.count('</script>') == 1  # exactly one render script element
    assert 'renderSpec' in first
    assert 'Plotly' in first

    captured.clear()
    plotter._show_figure(go.Figure())
    second = captured[0]
    # Later figures reference the already-injected runtime, not re-embed.
    assert 'renderSpec' in second
    assert 'Plotly' not in second
    assert len(second) < len(first)
