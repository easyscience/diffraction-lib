# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
Plotly plotting backend.

Provides an interactive plotting implementation using Plotly. In
notebooks, figures are displayed inline; in other environments a browser
renderer may be used depending on configuration.
"""

from __future__ import annotations

import base64
import json
import uuid
from dataclasses import dataclass

import darkdetect
import numpy as np
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots
from plotly.utils import PlotlyJSONEncoder

try:
    from IPython.display import HTML
    from IPython.display import display
except ImportError:
    display = None
    HTML = None

from easydiffraction.display.plotters.base import DEFAULT_HEIGHT
from easydiffraction.display.plotters.base import SERIES_CONFIG
from easydiffraction.display.plotters.base import BraggTickSet
from easydiffraction.display.plotters.base import PlotterBase
from easydiffraction.display.plotters.base import PowderMeasVsCalcSpec
from easydiffraction.display.theme import DARK_AXIS_FRAME_COLOR
from easydiffraction.display.theme import DARK_BACKGROUND_COLOR
from easydiffraction.display.theme import DARK_FOREGROUND_COLOR
from easydiffraction.display.theme import DARK_HOVER_BACKGROUND_COLOR
from easydiffraction.display.theme import DARK_INNER_TICK_GRID_COLOR
from easydiffraction.display.theme import DARK_LEGEND_BACKGROUND_COLOR
from easydiffraction.display.theme import LIGHT_AXIS_FRAME_COLOR
from easydiffraction.display.theme import LIGHT_BACKGROUND_COLOR
from easydiffraction.display.theme import LIGHT_FOREGROUND_COLOR
from easydiffraction.display.theme import LIGHT_HOVER_BACKGROUND_COLOR
from easydiffraction.display.theme import LIGHT_INNER_TICK_GRID_COLOR
from easydiffraction.display.theme import LIGHT_LEGEND_BACKGROUND_COLOR
from easydiffraction.display.theme import DisplayThemeColors
from easydiffraction.display.theme import display_theme_colors
from easydiffraction.display.theme import display_theme_colors_for_template
from easydiffraction.utils._vendored.theme_detect import is_dark
from easydiffraction.utils.environment import FigureEmbedMode
from easydiffraction.utils.environment import in_jupyter
from easydiffraction.utils.environment import in_pycharm
from easydiffraction.utils.environment import resolve_figure_embed_mode

DEFAULT_COLORS = {
    'meas': 'rgb(31, 119, 180)',
    'bkg': 'rgb(140, 140, 140)',
    'calc': 'rgb(214, 39, 40)',
    'posterior': 'rgb(214, 39, 40)',
    'resid': 'rgb(44, 160, 44)',
}

MEASURED_LINE_WIDTH = 2.0
BACKGROUND_LINE_WIDTH = 1.0
CALCULATED_LINE_WIDTH = 2.0
RESIDUAL_LINE_WIDTH = 2.0
MEASURED_MARKER_SIZE = 6
MEASURED_MARKER_LINE_WIDTH = 0
SINGLE_CRYSTAL_MARKER_LINE_WIDTH = 0.5
MEASURED_ERROR_BAR_THICKNESS = 0.5
MEASURED_ERROR_BAR_WIDTH = 2
# Single source for the y=x reference-line colour, shared with the
# report axis gray (report.style.REPORT_AXIS_RGB) and imported by
# report.fit_plot so the diagonal looks identical in the Plotly and
# pgfplots renderers.
DIAGONAL_LINE_RGB = (190, 199, 208)
DIAGONAL_LINE_COLOR = (
    f'rgb({DIAGONAL_LINE_RGB[0]}, {DIAGONAL_LINE_RGB[1]}, {DIAGONAL_LINE_RGB[2]})'
)
DIAGONAL_LINE_WIDTH = 0.5

BRAGG_TICK_COLORS = (
    'rgb(255, 127, 14)',
    'rgb(23, 190, 207)',
    'rgb(140, 140, 140)',
    'rgb(188, 189, 34)',
    'rgb(148, 103, 189)',
)

NICE_AXIS_FRACTIONS = (1.0, 2.0, 5.0, 10.0)
NICE_AXIS_FRACTION_THRESHOLDS = (1.5, 3.0, 7.0)
DISPLAY_TICK_FRACTIONS = (1.0, 2.0, 2.5, 4.0, 5.0, 7.5, 10.0)
PLOTLY_HEIGHT_PER_UNIT = 24
BRAGG_TICK_MARKER_SIZE = 12
BRAGG_TICK_MARKER_LINE_WIDTH = 1
BRAGG_TICK_SYMBOL_HEIGHT_SCALE = 1.4
MAIN_INTENSITY_RANGE_MARGIN_FRACTION = 0.05
COMPOSITE_VERTICAL_SPACING = 0.03
COMPOSITE_MARGIN_RIGHT = 30
COMPOSITE_MARGIN_TOP = 40
COMPOSITE_MARGIN_BOTTOM = 45
TITLE_FONT_SIZE = 14
AXIS_TITLE_FONT_SIZE = 12
X_AXIS_TICK_LABEL_STANDOFF = 5
Y_AXIS_TICK_LABEL_STANDOFF = 6
HOVER_LABEL_FONT_SIZE = 12
# Plotly has no hover-label padding, so a non-breaking space is baked
# into each template line to hold the text off the left and right frame.
# Vertical spacing is left to Plotly's own ~3px line box: a blank spacer
# line reserves a full content-line height, which inflates the bottom
# margin and cannot be tuned, so a single space keeps all four margins
# small and even.
HOVER_HORIZONTAL_PAD = '\u00a0'
PREDICTIVE_BAND_COLOR = 'rgba(214, 39, 40, 0.14)'
PREDICTIVE_BAND_EDGE_COLOR = 'rgba(214, 39, 40, 0.45)'
PREDICTIVE_DRAW_COLOR = 'rgba(140, 140, 140, 0.18)'
EXCLUDED_REGION_FILL_COLOR = 'rgba(120, 120, 120, 0.16)'
PREDICTIVE_DRAW_PLOT_CAP = 50
PREDICTIVE_DRAW_ARRAY_NDIM = 2
FIXED_ASPECT_WRAPPER_META_KEY = 'fixed_aspect_wrapper'
FIXED_ASPECT_WRAPPER_CLASS_NAME = 'ed-fixed-aspect-plotly-wrapper'
THEME_SYNC_META_KEY = 'ed_plotly_theme_sync'
THEME_SYNC_AXIS_FRAME_SHAPE_INDEXES_KEY = 'axis_frame_shape_indexes'
THEME_SYNC_CORRELATION_HEATMAP_KEY = 'correlation_heatmap'


def _typed_arrays_to_float32(value: object) -> object:
    """
    Recursively transcode float64 Plotly typed-array specs to float32.

    Plotly serializes numpy arrays as base64 typed-array specs
    (``{'dtype': 'f8', 'bdata': ...}``). For the docs display, float32
    (~7 significant figures) is visually lossless and halves the bulk
    data size. Scalars and small inline lists are left untouched.

    Parameters
    ----------
    value : object
        A figure dict, list, or leaf from ``fig.to_plotly_json()``.

    Returns
    -------
    object
        The same structure with float64 typed arrays downcast to float32.
    """
    if isinstance(value, dict):
        if value.get('dtype') == 'f8' and 'bdata' in value:
            downcast = np.frombuffer(
                base64.b64decode(value['bdata']),
                dtype='<f8',
            ).astype('<f4')
            return {
                **value,
                'dtype': 'f4',
                'bdata': base64.b64encode(downcast.tobytes()).decode('ascii'),
            }
        return {key: _typed_arrays_to_float32(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_typed_arrays_to_float32(item) for item in value]
    return value


def single_crystal_axis_range(
    x_calc: object,
    y_meas: object,
    y_meas_su: object,
) -> tuple[float, float]:
    """
    Return one shared (min, max) range for a single-crystal scatter.

    The range spans the calculated values and the measured values
    widened by their standard uncertainties, then pads both ends by
    ``MAIN_INTENSITY_RANGE_MARGIN_FRACTION``. Applying the same range to
    both axes keeps the y=x diagonal meaningful.

    Parameters
    ----------
    x_calc : object
        1D array-like of calculated values (x-axis).
    y_meas : object
        1D array-like of measured values (y-axis).
    y_meas_su : object
        1D array-like of measurement uncertainties, or None.

    Returns
    -------
    tuple[float, float]
        The padded ``(minimum, maximum)`` shared by both axes.
    """
    calc = [float(value) for value in x_calc]
    meas = [float(value) for value in y_meas]
    if y_meas_su is not None:
        su = [float(value) for value in y_meas_su]
        low = [value - error for value, error in zip(meas, su, strict=True)]
        high = [value + error for value, error in zip(meas, su, strict=True)]
    else:
        low = meas
        high = meas
    candidates_low = [*calc, *low]
    candidates_high = [*calc, *high]
    if not candidates_low or not candidates_high:
        return 0.0, 1.0
    minimum = min(candidates_low)
    maximum = max(candidates_high)
    margin = max(maximum - minimum, 0.0) * MAIN_INTENSITY_RANGE_MARGIN_FRACTION
    if margin <= 0.0:
        margin = 1.0
    return minimum - margin, maximum + margin


def single_crystal_tick_step(
    minimum: float,
    maximum: float,
    target_ticks: int = 6,
) -> float:
    """
    Return a 'nice' tick step covering ``[minimum, maximum]``.

    The raw step ``span / target_ticks`` is rounded to the nearest 1/2/5
    multiple of a power of ten (the classic axis-label rounding), so the
    ticks read as round numbers and the same step gives identical x and
    y ticks over a shared range. Combined with a tick origin of 0 this
    reproduces Plotly's own choice (e.g. a 500 step, not 750).

    Parameters
    ----------
    minimum : float
        Lower bound of the shared axis range.
    maximum : float
        Upper bound of the shared axis range.
    target_ticks : int, default=6
        Approximate number of tick intervals to aim for.

    Returns
    -------
    float
        The rounded tick step.
    """
    span = maximum - minimum
    if span <= 0.0 or target_ticks <= 0:
        return 1.0
    raw_step = span / target_ticks
    exponent = float(np.floor(np.log10(raw_step)))
    base = 10.0**exponent
    fraction = raw_step / base
    if fraction < NICE_AXIS_FRACTION_THRESHOLDS[0]:
        nice_fraction = 1.0
    elif fraction < NICE_AXIS_FRACTION_THRESHOLDS[1]:
        nice_fraction = 2.0
    elif fraction < NICE_AXIS_FRACTION_THRESHOLDS[2]:
        nice_fraction = 5.0
    else:
        nice_fraction = 10.0
    return nice_fraction * base


@dataclass(frozen=True)
class PowderCompositeRows:
    """Resolved row layout for the composite powder figure."""

    row_count: int
    row_heights: list[float]
    bragg_row: int | None
    residual_row: int | None


class PlotlyPlotter(PlotterBase):
    """Interactive plotter using Plotly for notebooks and browsers."""

    _supports_graphical_heatmap: bool = True

    def __init__(self) -> None:
        if hasattr(pio, 'templates'):
            pio.templates.default = self._default_template_name()
        if in_pycharm():
            pio.renderers.default = 'browser'

    @staticmethod
    def _is_dark_mode() -> bool:
        """
        Return whether the active plotting context should use dark mode.

        In Jupyter, prefer notebook dark-mode detection. Outside
        Jupyter, fall back to the system theme via ``darkdetect``.

        Returns
        -------
        bool
            ``True`` for dark mode, otherwise ``False``.
        """
        return is_dark() if in_jupyter() else darkdetect.isDark()

    @classmethod
    def _default_template_name(cls) -> str:
        """
        Return the Plotly template matching the active theme.

        In Jupyter, prefer notebook dark-mode detection. Outside
        Jupyter, fall back to the system theme via ``darkdetect``.

        Returns
        -------
        str
            Either ``'plotly_dark'`` or ``'plotly_white'``.
        """
        return 'plotly_dark' if cls._is_dark_mode() else 'plotly_white'

    @classmethod
    def _correlation_colorscale(cls) -> list[tuple[float, str]]:
        """
        Return a diverging colorscale for correlation heatmaps.

        The midpoint uses the active plot background so correlations
        fade from red-like negative values through the host surface to
        blue-like positive values.

        Returns
        -------
        list[tuple[float, str]]
            Plotly-compatible colorscale definition.
        """
        return cls._correlation_colorscale_for_background(cls._background_color())

    @staticmethod
    def _correlation_colorscale_for_background(
        background_color: str,
    ) -> list[tuple[float, str]]:
        """Return the correlation colorscale for a theme background."""
        return [
            (0.0, '#d73027'),
            (0.5, background_color),
            (1.0, '#4575b4'),
        ]

    @classmethod
    def _correlation_grid_color(cls) -> str:
        """
        Return the boundary-line color for correlation heatmaps.

        Returns
        -------
        str
            RGBA color string tuned for the active theme.
        """
        return cls._theme_colors().axis_frame

    @classmethod
    def _axis_frame_color(cls) -> str:
        """Return the shared axis-frame color for Plotly figures."""
        return cls._correlation_grid_color()

    @classmethod
    def _theme_colors(cls) -> DisplayThemeColors:
        """Return display theme colors for the active theme."""
        return display_theme_colors(is_dark_theme=cls._is_dark_mode())

    @classmethod
    def _background_color(cls) -> str:
        """Return the plot background color for the active theme."""
        return cls._theme_colors().background

    @classmethod
    def _inner_tick_grid_color(cls) -> str:
        """Return the inner tick-grid color for the active theme."""
        return cls._theme_colors().inner_tick_grid

    @classmethod
    def _legend_background_color(cls) -> str:
        """Return a half-transparent legend background color."""
        return cls._theme_colors().legend_background

    @classmethod
    def _hover_label_style(
        cls,
        theme_colors: DisplayThemeColors | None = None,
    ) -> dict:
        """
        Return the shared hover-label style for every Plotly figure.

        This is the single source of truth for tooltip framing. The
        border matches the Axes-rectangle (axis-frame) color and the
        background follows the active theme. Per-line text colors live
        in each trace's hover template, not here.

        Parameters
        ----------
        theme_colors : DisplayThemeColors | None, default=None
            Explicit theme colors; the active theme is used when
            omitted.

        Returns
        -------
        dict
            A Plotly ``hoverlabel`` style dictionary.
        """
        colors = theme_colors if theme_colors is not None else cls._theme_colors()
        return {
            'bgcolor': colors.hover_background,
            'bordercolor': colors.axis_frame,
            'font': {'color': colors.foreground, 'size': HOVER_LABEL_FONT_SIZE},
            'align': 'left',
        }

    @classmethod
    def _apply_hover_label_style(
        cls,
        fig: object,
        *,
        theme_colors: DisplayThemeColors | None = None,
    ) -> None:
        """Apply the shared hover-label style to a Plotly figure."""
        update_layout = getattr(fig, 'update_layout', None)
        if callable(update_layout):
            update_layout(hoverlabel=cls._hover_label_style(theme_colors))

    @staticmethod
    def _background_color_for_template(template: str) -> str | None:
        theme_colors = display_theme_colors_for_template(template)
        return theme_colors.background if theme_colors is not None else None

    @staticmethod
    def _axis_frame_color_for_template(template: str) -> str | None:
        theme_colors = display_theme_colors_for_template(template)
        return theme_colors.axis_frame if theme_colors is not None else None

    @staticmethod
    def _inner_tick_grid_color_for_template(template: str) -> str | None:
        theme_colors = display_theme_colors_for_template(template)
        return theme_colors.inner_tick_grid if theme_colors is not None else None

    @staticmethod
    def _legend_background_color_for_template(template: str) -> str | None:
        theme_colors = display_theme_colors_for_template(template)
        return theme_colors.legend_background if theme_colors is not None else None

    def plot_correlation_heatmap(
        self,
        corr_df: object,
        title: str,
        threshold: float | None,
        precision: int,
    ) -> None:
        """
        Render a Plotly heatmap for a correlation matrix.

        Parameters
        ----------
        corr_df : object
            Square correlation DataFrame.
        title : str
            Figure title.
        threshold : float | None
            Absolute-correlation cutoff used for value labels.
        precision : int
            Number of decimals to show in labels and hover text.
        """
        num_rows, num_cols = corr_df.shape
        x_edges = np.arange(num_cols + 1, dtype=float)
        y_edges = np.arange(num_rows + 1, dtype=float)
        x_centers = np.arange(num_cols, dtype=float) + 0.5
        y_centers = np.arange(num_rows, dtype=float) + 0.5
        grid_color = self._correlation_grid_color()

        heatmap = go.Heatmap(
            z=corr_df.to_numpy(),
            x=x_edges,
            y=y_edges,
            zmin=-1.0,
            zmax=1.0,
            zmid=0.0,
            colorscale=self._correlation_colorscale(),
            colorbar={
                'title': {'text': ''},
                'lenmode': 'fraction',
                'len': 1.0,
                'y': 0.5,
                'yanchor': 'middle',
            },
            hoverongaps=False,
            hovertemplate=f'%{{x}}<br>%{{y}}<br>correlation: %{{z:.{precision}f}}<extra></extra>',
        )
        label_trace = self._get_correlation_label_trace(
            corr_df,
            x_centers=x_centers,
            y_centers=y_centers,
            threshold=threshold,
            precision=precision,
        )

        shapes = [
            {
                'type': 'line',
                'x0': float(x_pos),
                'x1': float(x_pos),
                'y0': 0.0,
                'y1': float(num_rows),
                'xref': 'x',
                'yref': 'y',
                'layer': 'above',
                'line': {'color': grid_color, 'width': 1},
            }
            for x_pos in x_edges[1:-1]
        ]
        shapes.extend(
            {
                'type': 'line',
                'x0': 0.0,
                'x1': float(num_cols),
                'y0': float(y_pos),
                'y1': float(y_pos),
                'xref': 'x',
                'yref': 'y',
                'layer': 'above',
                'line': {'color': grid_color, 'width': 1},
            }
            for y_pos in y_edges[1:-1]
        )
        shapes.append({
            'type': 'rect',
            'x0': 0.0,
            'x1': 1.0,
            'y0': 0.0,
            'y1': 1.0,
            'xref': 'paper',
            'yref': 'paper',
            'layer': 'above',
            'line': {'color': grid_color, 'width': 1},
            'fillcolor': 'rgba(0, 0, 0, 0)',
        })

        layout = self._get_layout(
            title,
            ['Parameter', 'Parameter'],
            shapes=shapes,
        )
        traces = [heatmap]
        if label_trace is not None:
            traces.append(label_trace)
        fig = self._get_figure(traces, layout)
        self._apply_theme_sync_meta(
            fig,
            axis_frame_shape_indexes=range(len(shapes)),
            correlation_heatmap=True,
        )
        fig.update_xaxes(
            side='bottom',
            tickangle=-10,
            automargin=True,
            tickmode='array',
            tickvals=x_centers.tolist(),
            ticktext=corr_df.columns.tolist(),
            ticklabelstandoff=X_AXIS_TICK_LABEL_STANDOFF,
            range=[0.0, float(num_cols)],
            showgrid=False,
            showline=False,
            mirror=False,
            ticks='',
            layer='above traces',
        )
        fig.update_yaxes(
            autorange='reversed',
            automargin=True,
            tickmode='array',
            tickvals=y_centers.tolist(),
            ticktext=corr_df.index.tolist(),
            ticklabelstandoff=Y_AXIS_TICK_LABEL_STANDOFF,
            range=[float(num_rows), 0.0],
            showgrid=False,
            showline=False,
            mirror=False,
            ticks='',
            layer='above traces',
        )
        self._show_figure(fig)

    @classmethod
    def _correlation_label_color(cls) -> str:
        """
        Return the text color used for in-cell correlation labels.

        Returns
        -------
        str
            Hex color string.
        """
        return '#f5f5f5'

    @classmethod
    def _get_correlation_label_trace(
        cls,
        corr_df: object,
        x_centers: np.ndarray,
        y_centers: np.ndarray,
        threshold: float | None,
        precision: int,
    ) -> object | None:
        """
        Build a text trace for visible correlation values.

        Parameters
        ----------
        corr_df : object
            Correlation DataFrame to annotate.
        x_centers : np.ndarray
            Cell center x coordinates.
        y_centers : np.ndarray
            Cell center y coordinates.
        threshold : float | None
            Minimum absolute correlation required for a label.
        precision : int
            Number of decimals for rendered labels.

        Returns
        -------
        object | None
            Plotly text trace, or ``None`` when no labels should be
            shown.
        """
        values = corr_df.to_numpy()
        label_x = []
        label_y = []
        label_text = []

        for row_idx, row in enumerate(values):
            for col_idx, value in enumerate(row):
                if np.isnan(value):
                    continue
                if threshold is not None and threshold > 0 and abs(float(value)) < threshold:
                    continue
                label_x.append(float(x_centers[col_idx]))
                label_y.append(float(y_centers[row_idx]))
                label_text.append(f'{float(value):.{precision}f}')

        if not label_text:
            return None

        return go.Scatter(
            x=label_x,
            y=label_y,
            mode='text',
            text=label_text,
            textposition='middle center',
            textfont={'color': cls._correlation_label_color()},
            hoverinfo='skip',
            showlegend=False,
        )

    @classmethod
    def _get_powder_trace(
        cls,
        x: object,
        y: object,
        label: str,
        *,
        customdata: object | None = None,
        hovertemplate: str | None = None,
    ) -> object:
        """
        Create a Plotly trace for powder diffraction data.

        Parameters
        ----------
        x : object
            1D array-like of x-axis values.
        y : object
            1D array- like of y-axis values.
        label : str
            Series identifier (``'meas'``, ``'bkg'``, ``'calc'``, or
            ``'resid'``).
        customdata : object | None, default=None
            Optional per-point payload used by the hover template.
        hovertemplate : str | None, default=None
            Optional hover template overriding the default per-trace
            one.

        Returns
        -------
        object
            A configured :class:`plotly.graph_objects.Scatter` trace.
        """
        mode = SERIES_CONFIG[label]['mode']
        name = SERIES_CONFIG[label]['name']
        color = DEFAULT_COLORS[label]
        line_width = {
            'meas': MEASURED_LINE_WIDTH,
            'bkg': BACKGROUND_LINE_WIDTH,
            'calc': CALCULATED_LINE_WIDTH,
            'resid': RESIDUAL_LINE_WIDTH,
        }[label]
        line = {'color': color, 'width': line_width}
        marker = None
        if label == 'meas':
            marker = {
                'symbol': 'circle',
                'size': MEASURED_MARKER_SIZE,
                'line': {'width': MEASURED_MARKER_LINE_WIDTH},
                'color': color,
            }
        legend_rank = {
            'meas': 10,
            'bkg': 20,
            'calc': 30,
            'resid': 40,
        }[label]

        return go.Scatter(
            x=x,
            y=y,
            line=line,
            mode=mode,
            name=name,
            legendrank=legend_rank,
            marker=marker,
            customdata=customdata,
            hovertemplate=(
                hovertemplate
                if hovertemplate is not None
                else cls._format_hover_lines([
                    cls._hover_color_span(name, color),
                    cls._hover_color_span('x: %{x}', color),
                    cls._hover_color_span('y: %{y}', color),
                ])
            ),
        )

    @staticmethod
    def _hover_text_color(color: str) -> str:
        """Return a span-safe CSS color (no internal whitespace)."""
        return color.replace(' ', '')

    @classmethod
    def _hover_color_span(cls, text: str, color: str) -> str:
        """Wrap hover text in a span colored to match a trace."""
        return f'<span style="color:{cls._hover_text_color(color)}">{text}</span>'

    @classmethod
    def _format_hover_lines(
        cls,
        lines: list[str],
        *,
        extra: str = '<extra></extra>',
    ) -> str:
        """
        Join hover lines with the padding shared by every tooltip.

        Parameters
        ----------
        lines : list[str]
            Per-line hover content, already colored where needed.
        extra : str, default='<extra></extra>'
            Trailing Plotly hover directive (the secondary box).

        Returns
        -------
        str
            A hover-template body padded left and right; top and bottom
            spacing is supplied by Plotly's own line box.
        """
        padded = [f'{HOVER_HORIZONTAL_PAD}{line}{HOVER_HORIZONTAL_PAD}' for line in lines]
        return '<br>'.join(padded) + extra

    @staticmethod
    def _powder_meas_vs_calc_hover_data(plot_spec: PowderMeasVsCalcSpec) -> np.ndarray:
        """Return shared hover values for composite powder traces."""
        residual_values = (
            np.asarray(plot_spec.y_resid)
            if plot_spec.y_resid is not None
            else np.asarray(plot_spec.y_meas) - np.asarray(plot_spec.y_calc)
        )
        if plot_spec.y_bkg is None:
            return np.column_stack((
                np.asarray(plot_spec.y_meas),
                np.asarray(plot_spec.y_calc),
                residual_values,
            ))

        return np.column_stack((
            np.asarray(plot_spec.y_meas),
            np.asarray(plot_spec.y_bkg),
            np.asarray(plot_spec.y_calc),
            residual_values,
        ))

    @classmethod
    def _powder_meas_vs_calc_hover_template(
        cls,
        plot_spec: PowderMeasVsCalcSpec,
    ) -> str:
        """
        Return a shared hover template for composite powder traces.

        Each line is colored to match its curve and padded away from the
        tooltip frame through the shared hover formatter.
        """
        calc_label = plot_spec.y_calc_name or 'Icalc'
        if plot_spec.y_bkg is None:
            return cls._format_hover_lines([
                'x: %{x:,.2f}',
                cls._hover_color_span(
                    'Imeas: %{customdata[0]:,.2f}',
                    DEFAULT_COLORS['meas'],
                ),
                cls._hover_color_span(
                    f'{calc_label}: %{{customdata[1]:,.2f}}',
                    DEFAULT_COLORS['calc'],
                ),
                cls._hover_color_span(
                    f'Imeas - {calc_label}: %{{customdata[2]:,.2f}}',
                    DEFAULT_COLORS['resid'],
                ),
            ])

        return cls._format_hover_lines([
            'x: %{x:,.2f}',
            cls._hover_color_span(
                'Imeas: %{customdata[0]:,.2f}',
                DEFAULT_COLORS['meas'],
            ),
            cls._hover_color_span(
                'Ibkg: %{customdata[1]:,.2f}',
                DEFAULT_COLORS['bkg'],
            ),
            cls._hover_color_span(
                f'{calc_label}: %{{customdata[2]:,.2f}}',
                DEFAULT_COLORS['calc'],
            ),
            cls._hover_color_span(
                f'Imeas - {calc_label}: %{{customdata[3]:,.2f}}',
                DEFAULT_COLORS['resid'],
            ),
        ])

    @staticmethod
    def _get_single_crystal_trace(
        x_calc: object,
        y_meas: object,
        y_meas_su: object,
    ) -> object:
        """
        Create a Plotly trace for single crystal diffraction data.

        Parameters
        ----------
        x_calc : object
            1D array-like of calculated values (x-axis).
        y_meas : object
            1D array-like of measured values (y-axis).
        y_meas_su : object
            1D array-like of measurement uncertainties.

        Returns
        -------
        object
            A configured :class:`plotly.graph_objects.Scatter` trace
            with markers and error bars.
        """
        return go.Scatter(
            x=x_calc,
            y=y_meas,
            mode='markers',
            marker={
                'symbol': 'circle',
                'size': MEASURED_MARKER_SIZE,
                # Stroke colour matches the fill (like the pgfplots
                # PDF) so there is no contrasting ring around markers.
                'line': {
                    'width': SINGLE_CRYSTAL_MARKER_LINE_WIDTH,
                    'color': DEFAULT_COLORS['meas'],
                },
                'color': DEFAULT_COLORS['meas'],
            },
            error_y={
                'type': 'data',
                'array': y_meas_su,
                'visible': True,
                'color': DEFAULT_COLORS['meas'],
                'thickness': MEASURED_ERROR_BAR_THICKNESS,
                'width': MEASURED_ERROR_BAR_WIDTH,
            },
            hovertemplate='calc: %{x}<br>meas: %{y}<br><extra></extra>',
        )

    @staticmethod
    def _get_diagonal_shape(minimum: float, maximum: float) -> dict:
        """
        Create a y=x reference line in data coordinates.

        The line runs from ``(minimum, minimum)`` to ``(maximum,
        maximum)`` in axis (data) coordinates, so it tracks y=x
        regardless of the axis aspect ratio rather than the
        paper-rectangle diagonal.

        Parameters
        ----------
        minimum : float
            Lower bound of the shared axis range.
        maximum : float
            Upper bound of the shared axis range.

        Returns
        -------
        dict
            A dict configuring the diagonal line shape.
        """
        return {
            'type': 'line',
            'x0': minimum,
            'y0': minimum,
            'x1': maximum,
            'y1': maximum,
            'xref': 'x',
            'yref': 'y',
            'layer': 'below',
            'line': {'color': DIAGONAL_LINE_COLOR, 'width': DIAGONAL_LINE_WIDTH},
        }

    @staticmethod
    def _get_config() -> dict:
        """
        Return the Plotly figure configuration.

        Returns
        -------
        dict
            A dict with display and mode bar settings.
        """
        return {
            'displayModeBar': True,
            'displaylogo': False,
            'responsive': True,
            'modeBarButtonsToRemove': [
                'select2d',
                'lasso2d',
                'zoomIn2d',
                'zoomOut2d',
                'autoScale2d',
            ],
        }

    @staticmethod
    def _modebar_legend_toggle_post_script() -> str:
        """
        Return client-side code for a legend-toggle modebar button.
        """
        return r"""
const graphDiv = document.getElementById('{plot_id}');
if (!graphDiv) {
    return;
}

const parseColor = function (colorValue) {
    if (!colorValue) {
        return null;
    }

    const rgbMatch = colorValue.match(/^rgba?\(([^)]+)\)$/);
    if (rgbMatch) {
        const channels = rgbMatch[1].split(',').slice(0, 3).map((value) => Number(value.trim()));
        if (channels.every((value) => Number.isFinite(value))) {
            return {red: channels[0], green: channels[1], blue: channels[2]};
        }
    }

    const hexMatch = colorValue.match(/^#([0-9a-f]{3}|[0-9a-f]{6})$/i);
    if (!hexMatch) {
        return null;
    }

    const normalizedHex = hexMatch[1].length === 3
        ? hexMatch[1].split('').map((value) => value + value).join('')
        : hexMatch[1];
    return {
        red: Number.parseInt(normalizedHex.slice(0, 2), 16),
        green: Number.parseInt(normalizedHex.slice(2, 4), 16),
        blue: Number.parseInt(normalizedHex.slice(4, 6), 16),
    };
};

const resolveLegendButtonFill = function (opacity) {
    const referencePath = graphDiv.querySelector('.modebar-btn path');
    const referenceFill = referencePath ? window.getComputedStyle(referencePath).fill : null;
    const fontColor = graphDiv._fullLayout && graphDiv._fullLayout.font
        ? graphDiv._fullLayout.font.color
        : null;
    const parsedColor = (
        parseColor(referenceFill)
        || parseColor(fontColor)
        || {red: 68, green: 68, blue: 68}
    );
    return (
        'rgba('
        + parsedColor.red
        + ', '
        + parsedColor.green
        + ', '
        + parsedColor.blue
        + ', '
        + opacity
        + ')'
    );
};

const updateLegendButtonAppearance = function (legendVisible) {
    const legendButton = graphDiv.querySelector('[data-legend-toggle="true"]');
    if (!legendButton) {
        return;
    }

    const legendIconPath = legendButton.querySelector('path');
    if (!legendIconPath) {
        return;
    }

    legendButton.classList.toggle('active', legendVisible);
    legendButton.setAttribute('aria-pressed', String(legendVisible));
    legendIconPath.setAttribute(
        'style',
        'fill: ' + resolveLegendButtonFill(legendVisible ? 0.7 : 0.3) + ';',
    );
};

const applyLegendVisibility = function (legendVisible) {
    const legend = graphDiv.querySelector('.legend');
    if (legend) {
        legend.style.display = legendVisible ? 'inline' : 'none';
        legend.style.visibility = legendVisible ? 'visible' : 'hidden';
        legend.style.pointerEvents = legendVisible ? '' : 'none';
    }

    if (graphDiv.layout) {
        graphDiv.layout.showlegend = legendVisible;
    }

    if (graphDiv._fullLayout) {
        graphDiv._fullLayout.showlegend = legendVisible;
    }
};

const readLegendVisibility = function () {
    if (graphDiv.dataset.legendVisible === 'true') {
        return true;
    }

    if (graphDiv.dataset.legendVisible === 'false') {
        return false;
    }

    const legend = graphDiv.querySelector('.legend');
    if (legend) {
        return (
            window.getComputedStyle(legend).display !== 'none'
            && window.getComputedStyle(legend).visibility !== 'hidden'
        );
    }

    if (graphDiv.layout && typeof graphDiv.layout.showlegend === 'boolean') {
        return graphDiv.layout.showlegend;
    }

    if (graphDiv._fullLayout && typeof graphDiv._fullLayout.showlegend === 'boolean') {
        return graphDiv._fullLayout.showlegend;
    }

    return true;
};

const syncLegendVisibility = function (legendVisible) {
    const resolvedLegendVisible = typeof legendVisible === 'boolean'
        ? legendVisible
        : readLegendVisibility();
    graphDiv.dataset.legendVisible = String(resolvedLegendVisible);
    applyLegendVisibility(resolvedLegendVisible);
    updateLegendButtonAppearance(resolvedLegendVisible);
    return resolvedLegendVisible;
};

const toggleLegend = function (event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }

    const currentValue = readLegendVisibility();
    const nextValue = !currentValue;
    syncLegendVisibility(nextValue);
};

const installLegendToggleButton = function () {
    const modebar = graphDiv.querySelector('.modebar');
    if (!modebar) {
        return;
    }

    if (!modebar.querySelector('.modebar-group')) {
        return;
    }

    let legendButton = modebar.querySelector('[data-legend-toggle="true"]');
    if (!legendButton) {
        const legendButtonGroup = document.createElement('div');
        legendButtonGroup.className = 'modebar-group';

        legendButton = document.createElement('a');
        legendButton.className = 'modebar-btn';
        legendButton.href = 'javascript:void(0)';
        legendButton.setAttribute('data-title', 'Toggle legend');
        legendButton.setAttribute('data-legend-toggle', 'true');
        legendButton.setAttribute('aria-label', 'Toggle legend');
        legendButton.setAttribute('role', 'button');
        legendButton.setAttribute('tabindex', '0');
        legendButton.innerHTML = [
            '<svg viewBox="0 0 1000 1000"'
            + ' class="icon" height="1em" width="1em"'
            + ' aria-hidden="true">',
            '<path d="M120 160H240V280H120z M120 440H240V560H120z '
            + 'M120 720H240V840H120z M320 200H880V240H320z '
            + 'M320 480H880V520H320z M320 760H880V800H320z"></path>',
            '</svg>',
        ].join('');

        legendButtonGroup.appendChild(legendButton);
        modebar.appendChild(legendButtonGroup);
    }

    legendButton.onclick = toggleLegend;
    legendButton.onkeydown = function (event) {
        if (event.key === 'Enter' || event.key === ' ') {
            toggleLegend(event);
        }
    };

    syncLegendVisibility();
};

if (graphDiv.on) {
    graphDiv.on('plotly_afterplot', installLegendToggleButton);
    graphDiv.on('plotly_relayout', function (eventData) {
        if (eventData && typeof eventData.showlegend === 'boolean') {
            syncLegendVisibility(eventData.showlegend);
            return;
        }

        syncLegendVisibility();
    });
}
syncLegendVisibility();
window.requestAnimationFrame(installLegendToggleButton);
"""

    @staticmethod
    def _theme_sync_post_script() -> str:
        """
        Return client-side code for host dark/light theme changes.
        """
        script = r"""
const graphDiv = document.getElementById('{plot_id}');
if (!graphDiv || !window.Plotly) {
    return;
}

const hostTheme = function () {
    const materialScheme = (
        (document.body && document.body.getAttribute('data-md-color-scheme'))
        || (
            document.documentElement
            && document.documentElement.getAttribute('data-md-color-scheme')
        )
    );
    if (materialScheme === 'slate') {
        return 'dark';
    }
    if (materialScheme === 'default') {
        return 'light';
    }

    const jupyterThemeLight = (
        (document.body && document.body.getAttribute('data-jp-theme-light'))
        || (
            document.documentElement
            && document.documentElement.getAttribute('data-jp-theme-light')
        )
    );
    if (jupyterThemeLight === 'false') {
        return 'dark';
    }
    if (jupyterThemeLight === 'true') {
        return 'light';
    }
    return 'light';
};

const themeColors = function (theme) {
    if (theme === 'dark') {
        return {
            background: '__DARK_BACKGROUND_COLOR__',
            foreground: '__DARK_FOREGROUND_COLOR__',
            axisFrame: '__DARK_AXIS_FRAME_COLOR__',
            innerTickGrid: '__DARK_INNER_TICK_GRID_COLOR__',
            hoverBackground: '__DARK_HOVER_BACKGROUND_COLOR__',
            legend: '__DARK_LEGEND_BACKGROUND_COLOR__',
        };
    }
    return {
        background: '__LIGHT_BACKGROUND_COLOR__',
        foreground: '__LIGHT_FOREGROUND_COLOR__',
        axisFrame: '__LIGHT_AXIS_FRAME_COLOR__',
        innerTickGrid: '__LIGHT_INNER_TICK_GRID_COLOR__',
        hoverBackground: '__LIGHT_HOVER_BACKGROUND_COLOR__',
        legend: '__LIGHT_LEGEND_BACKGROUND_COLOR__',
    };
};

const correlationColorscale = function (colors) {
    return [
        [0.0, '#d73027'],
        [0.5, colors.background],
        [1.0, '#4575b4'],
    ];
};

const themeSyncMeta = function () {
    const meta = (
        (graphDiv.layout && graphDiv.layout.meta)
        || (graphDiv._fullLayout && graphDiv._fullLayout.meta)
    );
    if (!meta || typeof meta !== 'object') {
        return {};
    }
    const themeSync = meta.__THEME_SYNC_META_KEY__;
    if (!themeSync || typeof themeSync !== 'object') {
        return {};
    }
    return themeSync;
};

const axisNames = function () {
    const names = new Set(['xaxis', 'yaxis']);
    [graphDiv.layout, graphDiv._fullLayout].forEach(function (layout) {
        if (!layout) {
            return;
        }
        Object.keys(layout).forEach(function (key) {
            if (/^[xyz]axis[0-9]*$/.test(key)) {
                names.add(key);
            }
        });
    });
    return names;
};

const applyAnnotationTheme = function (update, colors) {
    const annotations = (
        (graphDiv.layout && graphDiv.layout.annotations)
        || (graphDiv._fullLayout && graphDiv._fullLayout.annotations)
        || []
    );
    for (let index = 0; index < annotations.length; index += 1) {
        update['annotations[' + index + '].font.color'] = colors.foreground;
    }
};

const applyAxisFrameShapeTheme = function (update, colors, themeSync) {
    const shapeIndexes = themeSync.__THEME_SYNC_AXIS_FRAME_SHAPE_INDEXES_KEY__;
    if (!Array.isArray(shapeIndexes)) {
        return;
    }
    shapeIndexes.forEach(function (shapeIndex) {
        if (!Number.isInteger(shapeIndex) || shapeIndex < 0) {
            return;
        }
        update['shapes[' + shapeIndex + '].line.color'] = colors.axisFrame;
    });
};

const correlationHeatmapTraceIndexes = function (themeSync) {
    if (themeSync.__THEME_SYNC_CORRELATION_HEATMAP_KEY__ !== true) {
        return [];
    }
    const traces = graphDiv.data || [];
    const indexes = [];
    traces.forEach(function (trace, index) {
        if (trace && trace.type === 'heatmap') {
            indexes.push(index);
        }
    });
    return indexes;
};

const restyleCorrelationHeatmaps = function (colors, themeSync) {
    const colorscale = correlationColorscale(colors);
    return correlationHeatmapTraceIndexes(themeSync).map(function (traceIndex) {
        return window.Plotly.restyle(
            graphDiv,
            {colorscale: [colorscale]},
            [traceIndex],
        );
    });
};

const installModebarThemeStyle = function () {
    const styleId = 'ed-plotly-modebar-theme-style';
    if (document.getElementById(styleId)) {
        return;
    }

    const style = document.createElement('style');
    style.id = styleId;
    style.textContent = [
        '.plotly-graph-div.ed-plotly-themed-modebar .modebar-btn path {',
        '    fill: var(--ed-plotly-modebar-icon-color) !important;',
        '    opacity: var(--ed-plotly-modebar-icon-opacity) !important;',
        '}',
        '.plotly-graph-div.ed-plotly-themed-modebar .modebar-btn:hover path,',
        '.plotly-graph-div.ed-plotly-themed-modebar .modebar-btn.active path {',
        '    fill: var(--ed-plotly-modebar-icon-color) !important;',
        '    opacity: var(--ed-plotly-modebar-icon-hover-opacity) !important;',
        '}',
    ].join('\n');
    document.head.appendChild(style);
};

const applyModebarTheme = function (theme, colors) {
    installModebarThemeStyle();
    graphDiv.classList.add('ed-plotly-themed-modebar');
    graphDiv.style.setProperty('--ed-plotly-modebar-icon-color', colors.foreground);
    graphDiv.style.setProperty(
        '--ed-plotly-modebar-icon-opacity',
        theme === 'dark' ? '0.62' : '0.42',
    );
    graphDiv.style.setProperty(
        '--ed-plotly-modebar-icon-hover-opacity',
        theme === 'dark' ? '0.95' : '0.85',
    );
};

const applyTheme = function () {
    const theme = hostTheme();
    const colors = themeColors(theme);
    const syncMeta = themeSyncMeta();
    applyModebarTheme(theme, colors);

    if (graphDiv.dataset.edPlotlyTheme === theme) {
        return;
    }
    graphDiv.dataset.edPlotlyTheme = theme;

    const update = {
        paper_bgcolor: colors.background,
        plot_bgcolor: colors.background,
        'modebar.bgcolor': colors.background,
        'font.color': colors.foreground,
        'title.font.color': colors.foreground,
        'legend.bgcolor': colors.legend,
        'legend.font.color': colors.foreground,
        'hoverlabel.bgcolor': colors.hoverBackground,
        'hoverlabel.bordercolor': colors.axisFrame,
        'hoverlabel.font.color': colors.foreground,
    };

    axisNames().forEach(function (axisName) {
        update[axisName + '.color'] = colors.foreground;
        update[axisName + '.gridcolor'] = colors.innerTickGrid;
        update[axisName + '.linecolor'] = colors.axisFrame;
        update[axisName + '.zerolinecolor'] = colors.innerTickGrid;
        update[axisName + '.title.font.color'] = colors.foreground;
        update[axisName + '.tickfont.color'] = colors.foreground;
    });
    applyAnnotationTheme(update, colors);
    applyAxisFrameShapeTheme(update, colors, syncMeta);

    try {
        const result = window.Plotly.relayout(graphDiv, update);
        const restyleResults = restyleCorrelationHeatmaps(colors, syncMeta);
        const pending = [result].concat(restyleResults).filter(function (item) {
            return item && typeof item.then === 'function';
        });
        if (pending.length > 0) {
            Promise.all(pending).then(function () {
                window.Plotly.redraw(graphDiv);
            });
        } else {
            window.Plotly.redraw(graphDiv);
        }
    } catch (_error) {
        // Keep theme switching from breaking interaction with the figure.
    }
};

if (graphDiv.on) {
    graphDiv.on('plotly_afterplot', applyTheme);
}

if (window.MutationObserver) {
    const themeObserver = new MutationObserver(function () {
        graphDiv.dataset.edPlotlyTheme = '';
        applyTheme();
    });
    const attributeFilter = [
        'data-md-color-scheme',
        'data-jp-theme-light',
        'data-jp-theme-name',
    ];
    themeObserver.observe(document.documentElement, {
        attributes: true,
        attributeFilter: attributeFilter,
    });
    if (document.body) {
        themeObserver.observe(document.body, {
            attributes: true,
            attributeFilter: attributeFilter,
        });
    }
}

applyTheme();
"""
        return (
            script
            .replace('__THEME_SYNC_META_KEY__', THEME_SYNC_META_KEY)
            .replace(
                '__THEME_SYNC_AXIS_FRAME_SHAPE_INDEXES_KEY__',
                THEME_SYNC_AXIS_FRAME_SHAPE_INDEXES_KEY,
            )
            .replace(
                '__THEME_SYNC_CORRELATION_HEATMAP_KEY__',
                THEME_SYNC_CORRELATION_HEATMAP_KEY,
            )
            .replace('__DARK_BACKGROUND_COLOR__', DARK_BACKGROUND_COLOR)
            .replace('__DARK_FOREGROUND_COLOR__', DARK_FOREGROUND_COLOR)
            .replace('__DARK_AXIS_FRAME_COLOR__', DARK_AXIS_FRAME_COLOR)
            .replace('__DARK_INNER_TICK_GRID_COLOR__', DARK_INNER_TICK_GRID_COLOR)
            .replace('__DARK_HOVER_BACKGROUND_COLOR__', DARK_HOVER_BACKGROUND_COLOR)
            .replace('__DARK_LEGEND_BACKGROUND_COLOR__', DARK_LEGEND_BACKGROUND_COLOR)
            .replace('__LIGHT_BACKGROUND_COLOR__', LIGHT_BACKGROUND_COLOR)
            .replace('__LIGHT_FOREGROUND_COLOR__', LIGHT_FOREGROUND_COLOR)
            .replace('__LIGHT_AXIS_FRAME_COLOR__', LIGHT_AXIS_FRAME_COLOR)
            .replace('__LIGHT_INNER_TICK_GRID_COLOR__', LIGHT_INNER_TICK_GRID_COLOR)
            .replace('__LIGHT_HOVER_BACKGROUND_COLOR__', LIGHT_HOVER_BACKGROUND_COLOR)
            .replace('__LIGHT_LEGEND_BACKGROUND_COLOR__', LIGHT_LEGEND_BACKGROUND_COLOR)
        )

    @staticmethod
    def _resize_sync_post_script() -> str:
        """
        Return client-side code to resize hidden-tab Plotly outputs.
        """
        return r"""
const graphDiv = document.getElementById('{plot_id}');
if (!graphDiv || !window.Plotly || !window.Plotly.Plots) {
    return;
}

let pendingResize = false;
const resizePlot = function () {
    if (pendingResize) {
        return;
    }
    pendingResize = true;
    window.requestAnimationFrame(function () {
        pendingResize = false;
        if (!graphDiv.isConnected || graphDiv.offsetParent === null) {
            return;
        }
        window.Plotly.Plots.resize(graphDiv);
    });
};

const scheduleResize = function () {
    resizePlot();
    window.setTimeout(resizePlot, 50);
    window.setTimeout(resizePlot, 250);
};

if (window.ResizeObserver) {
    const resizeObserver = new ResizeObserver(scheduleResize);
    resizeObserver.observe(graphDiv);
    if (graphDiv.parentElement) {
        resizeObserver.observe(graphDiv.parentElement);
    }
}

document.addEventListener('visibilitychange', function () {
    if (!document.hidden) {
        scheduleResize();
    }
});
window.addEventListener('focus', scheduleResize);
window.addEventListener('pageshow', scheduleResize);
scheduleResize();
"""

    @classmethod
    def _html_post_script(cls, fig: object) -> str | None:
        """Return concatenated HTML post scripts for a Plotly figure."""
        scripts: list[str] = [
            cls._theme_sync_post_script(),
            cls._resize_sync_post_script(),
        ]
        if cls._has_visible_legend(fig):
            scripts.append(cls._modebar_legend_toggle_post_script())
        return '\n'.join(cls._scoped_html_post_script(script) for script in scripts)

    @staticmethod
    def _scoped_html_post_script(script: str) -> str:
        """
        Return one HTML post script wrapped in its own block scope.
        """
        return '{\n' + script.strip() + '\n}'

    @staticmethod
    def _figure_meta(fig: object) -> dict[str, object] | None:
        """Return figure layout metadata when available."""
        layout = getattr(fig, 'layout', None)
        if layout is None:
            return None

        meta = getattr(layout, 'meta', None)
        if isinstance(meta, dict):
            return meta

        layout_kwargs = getattr(layout, 'kwargs', None)
        if isinstance(layout_kwargs, dict):
            meta = layout_kwargs.get('meta')
            if isinstance(meta, dict):
                return meta
        return None

    @classmethod
    def _apply_theme_sync_meta(
        cls,
        fig: object,
        *,
        axis_frame_shape_indexes: object = (),
        correlation_heatmap: bool = False,
    ) -> None:
        """Store figure-specific live theme-sync metadata."""
        meta = cls._figure_meta(fig)
        updated_meta = dict(meta) if isinstance(meta, dict) else {}

        theme_sync = updated_meta.get(THEME_SYNC_META_KEY)
        updated_theme_sync = dict(theme_sync) if isinstance(theme_sync, dict) else {}

        indexes = [
            int(index)
            for index in axis_frame_shape_indexes
            if isinstance(index, int) and not isinstance(index, bool) and index >= 0
        ]
        if indexes:
            updated_theme_sync[THEME_SYNC_AXIS_FRAME_SHAPE_INDEXES_KEY] = indexes
        if correlation_heatmap:
            updated_theme_sync[THEME_SYNC_CORRELATION_HEATMAP_KEY] = True

        if not updated_theme_sync:
            return

        updated_meta[THEME_SYNC_META_KEY] = updated_theme_sync
        update_layout = getattr(fig, 'update_layout', None)
        if callable(update_layout):
            update_layout(meta=updated_meta)

    @classmethod
    def _fixed_aspect_wrapper_aspect_ratio(cls, fig: object) -> str | None:
        """Return the fixed aspect ratio requested for inline HTML."""
        meta = cls._figure_meta(fig)
        if not isinstance(meta, dict):
            return None

        wrapper = meta.get(FIXED_ASPECT_WRAPPER_META_KEY)
        if not isinstance(wrapper, dict):
            return None

        aspect_ratio = wrapper.get('aspect_ratio')
        if not isinstance(aspect_ratio, str):
            return None

        aspect_ratio = aspect_ratio.strip()
        if not aspect_ratio:
            return None
        return aspect_ratio

    @classmethod
    def _fixed_aspect_wrapper_max_width(cls, fig: object) -> int | None:
        """
        Return the max wrapper width in pixels, if one was requested.
        """
        meta = cls._figure_meta(fig)
        if not isinstance(meta, dict):
            return None

        wrapper = meta.get(FIXED_ASPECT_WRAPPER_META_KEY)
        if not isinstance(wrapper, dict):
            return None

        max_width = wrapper.get('max_width_pixels')
        if not isinstance(max_width, (int, float)) or isinstance(max_width, bool):
            return None
        if max_width <= 0:
            return None
        return int(max_width)

    @classmethod
    def _wrap_html_figure(cls, fig: object, html_fig: str) -> str:
        """Wrap inline Plotly HTML in a fixed-aspect container."""
        aspect_ratio = cls._fixed_aspect_wrapper_aspect_ratio(fig)
        if aspect_ratio is None:
            return html_fig

        max_width = cls._fixed_aspect_wrapper_max_width(fig)
        max_width_css = f'    max-width: {max_width}px;\n' if max_width is not None else ''

        return (
            '<style>\n'
            f'.{FIXED_ASPECT_WRAPPER_CLASS_NAME} {{\n'
            '    width: 100%;\n'
            f'{max_width_css}'
            f'    aspect-ratio: {aspect_ratio};\n'
            '}\n\n'
            f'.{FIXED_ASPECT_WRAPPER_CLASS_NAME} > div,\n'
            f'.{FIXED_ASPECT_WRAPPER_CLASS_NAME} .plotly-graph-div,\n'
            f'.{FIXED_ASPECT_WRAPPER_CLASS_NAME} .js-plotly-plot,\n'
            f'.{FIXED_ASPECT_WRAPPER_CLASS_NAME} .plotly,\n'
            f'.{FIXED_ASPECT_WRAPPER_CLASS_NAME} .plot-container,\n'
            f'.{FIXED_ASPECT_WRAPPER_CLASS_NAME} .svg-container {{\n'
            '    display: block;\n'
            '    width: 100% !important;\n'
            '    height: 100% !important;\n'
            '}\n'
            '</style>\n\n'
            f'<div class="{FIXED_ASPECT_WRAPPER_CLASS_NAME}">\n'
            f'{html_fig}\n'
            '</div>'
        )

    @staticmethod
    def _get_figure(
        data: object,
        layout: object,
    ) -> object:
        """
        Create and configure a Plotly figure.

        Parameters
        ----------
        data : object
            List of traces to include in the figure.
        layout : object
            Layout configuration dict.

        Returns
        -------
        object
            A configured :class:`plotly.graph_objects.Figure`.
        """
        fig = go.Figure(data=data, layout=layout)
        # Format axis ticks:
        # decimals for small numbers, grouped thousands for large
        fig.update_xaxes(tickformat=',.6~g', separatethousands=True)
        fig.update_yaxes(tickformat=',.6~g', separatethousands=True)
        return fig

    @staticmethod
    def _has_visible_legend(fig: object) -> bool:
        """Return whether a figure exposes at least one legend entry."""

        def _trace_value(trace: object, field_name: str) -> object:
            value = getattr(trace, field_name, None)
            if value is not None:
                return value

            trace_kwargs = getattr(trace, 'kwargs', None)
            if isinstance(trace_kwargs, dict):
                return trace_kwargs.get(field_name)

            return None

        layout = getattr(fig, 'layout', None)
        layout_showlegend = getattr(layout, 'showlegend', None)
        if layout_showlegend is False:
            return False

        for trace in getattr(fig, 'data', ()):
            if _trace_value(trace, 'visible') is False:
                continue
            if _trace_value(trace, 'showlegend') is False:
                continue
            if _trace_value(trace, 'name'):
                return True

        return False

    def _show_figure(
        self,
        fig: object,
    ) -> None:
        """
        Display a Plotly figure.

        Renders the figure using the appropriate method for the current
        environment (browser for PyCharm, inline HTML for Jupyter).

        Parameters
        ----------
        fig : object
            A :class:`plotly.graph_objects.Figure` to display.
        """
        config = self._get_config()
        self._apply_background_color(fig)
        self._apply_hover_label_style(fig)

        if in_pycharm() or display is None or HTML is None:
            fig.show(config=config)
            return

        # Docs notebook execution sets SHARED so the baked cell HTML is a
        # lazy placeholder; live Jupyter stays INLINE (eager, runtime via
        # the CDN as before).
        if resolve_figure_embed_mode() is FigureEmbedMode.SHARED:
            html_fig = self.serialize_html(
                fig,
                include_plotlyjs=False,
                mode=FigureEmbedMode.SHARED,
            )
        else:
            html_fig = self.serialize_html(
                fig,
                include_plotlyjs='cdn',
                mode=FigureEmbedMode.INLINE,
            )
        display(HTML(html_fig))

    @staticmethod
    def _ed_theme_payload() -> dict:
        """Return light and dark theme colors for the shared loader."""
        return {
            'light': {
                'background': LIGHT_BACKGROUND_COLOR,
                'foreground': LIGHT_FOREGROUND_COLOR,
                'axisFrame': LIGHT_AXIS_FRAME_COLOR,
                'innerTickGrid': LIGHT_INNER_TICK_GRID_COLOR,
                'hoverBackground': LIGHT_HOVER_BACKGROUND_COLOR,
                'legend': LIGHT_LEGEND_BACKGROUND_COLOR,
            },
            'dark': {
                'background': DARK_BACKGROUND_COLOR,
                'foreground': DARK_FOREGROUND_COLOR,
                'axisFrame': DARK_AXIS_FRAME_COLOR,
                'innerTickGrid': DARK_INNER_TICK_GRID_COLOR,
                'hoverBackground': DARK_HOVER_BACKGROUND_COLOR,
                'legend': DARK_LEGEND_BACKGROUND_COLOR,
            },
        }

    @classmethod
    def _ed_theme_sync_payload(cls, fig: object) -> dict:
        """Return live theme-sync metadata for the shared loader."""
        meta = cls._figure_meta(fig)
        theme_sync = meta.get(THEME_SYNC_META_KEY) if isinstance(meta, dict) else None
        if not isinstance(theme_sync, dict):
            return {}
        payload: dict = {}
        indexes = theme_sync.get(THEME_SYNC_AXIS_FRAME_SHAPE_INDEXES_KEY)
        if isinstance(indexes, list):
            payload['axisFrameShapeIndexes'] = indexes
        if theme_sync.get(THEME_SYNC_CORRELATION_HEATMAP_KEY):
            payload['correlationHeatmap'] = True
        return payload

    @staticmethod
    def _figure_height(fig: object) -> int:
        """Return the figure height in pixels for the loading skeleton."""
        layout = getattr(fig, 'layout', None)
        height = getattr(layout, 'height', None) if layout is not None else None
        if isinstance(height, (int, float)) and not isinstance(height, bool) and height > 0:
            return int(height)
        return DEFAULT_HEIGHT

    @classmethod
    def _serialize_html_shared(cls, fig: object) -> str:
        """
        Serialize a figure as a lazy SHARED-mode placeholder.

        Emits a skeleton plus the figure spec as ``application/json`` for
        the shared ``ed-figures.js`` loader to render on demand. No Plotly
        bundle or per-figure post-script is embedded; the runtime loads
        once per page and the loader owns theme-sync, resize, and legend.
        Bulk float64 arrays are downcast to float32 (visually lossless,
        ~7 significant figures) to roughly halve the embedded data.

        Parameters
        ----------
        fig : object
            Plotly figure to serialize.

        Returns
        -------
        str
            Placeholder HTML carrying the figure spec.
        """
        figure_dict = _typed_arrays_to_float32(fig.to_plotly_json())
        spec = {
            'data': figure_dict.get('data', []),
            'layout': figure_dict.get('layout', {}),
            'config': cls._get_config(),
            'edTheme': cls._ed_theme_payload(),
            'edThemeSync': cls._ed_theme_sync_payload(fig),
            'edHasLegend': cls._has_visible_legend(fig),
        }
        # Escape '<' so the JSON cannot terminate the <script> element.
        spec_json = json.dumps(spec, cls=PlotlyJSONEncoder).replace('<', '\\u003c')
        plot_id = f'ed-fig-{uuid.uuid4().hex}'
        height = cls._figure_height(fig)
        html_fig = (
            '<div class="ed-figure" data-ed-figure="plotly">'
            f'<div class="ed-figure-skeleton" style="height: {height}px">'
            'Loading plot…</div>'
            f'<div class="ed-figure-target" id="{plot_id}" '
            f'style="min-height: {height}px"></div>'
            '<script type="application/json" class="ed-figure-spec">'
            f'{spec_json}</script>'
            '</div>'
        )
        return cls._wrap_html_figure(fig, html_fig)

    @classmethod
    def serialize_html(
        cls,
        fig: object,
        *,
        include_plotlyjs: bool | str,
        mode: FigureEmbedMode = FigureEmbedMode.STANDALONE,
        force_template: str | None = None,
        axis_frame_color: str | None = None,
        grid_color: str | None = None,
    ) -> str:
        """
        Serialize a Plotly figure with EasyDiffraction controls.

        Parameters
        ----------
        fig : object
            Plotly figure to serialize.
        include_plotlyjs : bool | str
            Plotly JavaScript inclusion mode passed to Plotly.
        mode : FigureEmbedMode, default=STANDALONE
            Embedding mode. ``SHARED`` emits a lazy placeholder for the
            docs loader; ``INLINE``/``STANDALONE`` serialize eagerly.
        force_template : str | None, default=None
            Optional template name applied before serialization.
        axis_frame_color : str | None, default=None
            Optional explicit axis-frame color.
        grid_color : str | None, default=None
            Optional explicit major-grid color.

        Returns
        -------
        str
            Inline HTML containing the figure and helper scripts.
        """
        if mode is FigureEmbedMode.SHARED:
            return cls._serialize_html_shared(fig)
        background_color = None
        if force_template is not None:
            fig.update_layout(template=force_template)
            background_color = cls._background_color_for_template(force_template)
            resolved_axis_color = axis_frame_color
            if resolved_axis_color is None:
                resolved_axis_color = cls._axis_frame_color_for_template(force_template)
            if resolved_axis_color is not None:
                fig.update_xaxes(linecolor=resolved_axis_color)
                fig.update_yaxes(linecolor=resolved_axis_color)
            resolved_grid_color = grid_color
            if resolved_grid_color is None:
                resolved_grid_color = cls._inner_tick_grid_color_for_template(
                    force_template,
                )
            if resolved_grid_color is not None:
                fig.update_xaxes(
                    gridcolor=resolved_grid_color,
                    zerolinecolor=resolved_grid_color,
                )
                fig.update_yaxes(
                    gridcolor=resolved_grid_color,
                    zerolinecolor=resolved_grid_color,
                )
            legend_bgcolor = cls._legend_background_color_for_template(force_template)
            if legend_bgcolor is not None:
                fig.update_layout(legend={'bgcolor': legend_bgcolor})
        cls._apply_background_color(fig, background_color=background_color)
        hover_theme_colors = (
            display_theme_colors_for_template(force_template)
            if force_template is not None
            else None
        )
        cls._apply_hover_label_style(fig, theme_colors=hover_theme_colors)
        html_fig = pio.to_html(
            fig,
            include_plotlyjs=include_plotlyjs,
            full_html=False,
            config=cls._get_config(),
            post_script=cls._html_post_script(fig),
        )
        return cls._wrap_html_figure(fig, html_fig)

    @classmethod
    def _apply_background_color(
        cls,
        fig: object,
        *,
        background_color: str | None = None,
    ) -> None:
        """Apply the theme background to Plotly paper and plot areas."""
        update_layout = getattr(fig, 'update_layout', None)
        if callable(update_layout):
            resolved_background = background_color
            if resolved_background is None:
                resolved_background = cls._background_color()
            update_layout(
                paper_bgcolor=resolved_background,
                plot_bgcolor=resolved_background,
            )

    @classmethod
    def _get_layout(
        cls,
        title: str,
        axes_labels: object,
        shapes: list | None = None,
        *,
        axis_range: tuple[float, float] | None = None,
        axis_dtick: float | None = None,
    ) -> object:
        """
        Create a Plotly layout configuration.

        Parameters
        ----------
        title : str
            Figure title.
        axes_labels : object
            Pair of strings for the x and y titles.
        shapes : list | None, default=None
            Optional list of shape dicts to overlay on the plot.
        axis_range : tuple[float, float] | None, default=None
            When given, the same explicit range applied to both axes.
        axis_dtick : float | None, default=None
            When given, the same tick step applied to both axes, so the
            x and y ticks match.

        Returns
        -------
        object
            A configured :class:`plotly.graph_objects.Layout`.
        """
        xaxis = {
            'title': {
                'text': axes_labels[0],
                'font': {'size': AXIS_TITLE_FONT_SIZE},
            },
            'showline': True,
            'linecolor': cls._axis_frame_color(),
            'gridcolor': cls._inner_tick_grid_color(),
            'mirror': True,
            'ticklabelstandoff': X_AXIS_TICK_LABEL_STANDOFF,
            'zeroline': False,
            'zerolinecolor': cls._inner_tick_grid_color(),
        }
        yaxis = {
            'title': {
                'text': axes_labels[1],
                'font': {'size': AXIS_TITLE_FONT_SIZE},
            },
            'showline': True,
            'linecolor': cls._axis_frame_color(),
            'gridcolor': cls._inner_tick_grid_color(),
            'mirror': True,
            'ticklabelstandoff': Y_AXIS_TICK_LABEL_STANDOFF,
            'zeroline': False,
            'zerolinecolor': cls._inner_tick_grid_color(),
        }
        if axis_range is not None:
            for axis in (xaxis, yaxis):
                axis['range'] = list(axis_range)
        if axis_dtick is not None:
            for axis in (xaxis, yaxis):
                # Anchor ticks at 0 so they read as round numbers
                # (0, 500, 1000, ...) instead of at the padded minimum.
                axis['tick0'] = 0
                axis['dtick'] = axis_dtick
        return go.Layout(
            margin={
                'autoexpand': True,
                'r': 30,
                't': 40,
                'b': 45,
            },
            title={
                'text': title,
                'font': {'size': TITLE_FONT_SIZE},
            },
            paper_bgcolor=cls._background_color(),
            plot_bgcolor=cls._background_color(),
            legend={
                'bgcolor': cls._legend_background_color(),
                'xanchor': 'right',
                'x': 1.0,
                'yanchor': 'top',
                'y': 1.0,
            },
            xaxis=xaxis,
            yaxis=yaxis,
            shapes=shapes,
        )

    def plot_powder(
        self,
        x: object,
        y_series: object,
        labels: object,
        axes_labels: object,
        title: str,
        height: int | None = None,
        excluded_ranges: tuple[tuple[float, float], ...] = (),
    ) -> None:
        """
        Render a line plot for powder diffraction data.

        Suitable for powder diffraction data where intensity is plotted
        against an x-axis variable (2θ, TOF, d-spacing).

        Parameters
        ----------
        x : object
            1D array-like of x-axis values.
        y_series : object
            Sequence of y arrays to plot.
        labels : object
            Series identifiers corresponding to y_series.
        axes_labels : object
            Pair of strings for the x and y titles.
        title : str
            Figure title.
        height : int | None, default=None
            Ignored; Plotly auto-sizes based on renderer.
        excluded_ranges : tuple[tuple[float, float], ...], default=()
            Excluded x-ranges to shade on the figure.
        """
        # Intentionally unused; accepted for API compatibility
        del height

        data = []
        for idx, y in enumerate(y_series):
            label = labels[idx]
            trace = self._get_powder_trace(x, y, label)
            data.append(trace)

        layout = self._get_layout(
            title,
            axes_labels,
        )

        fig = self._get_figure(data, layout)
        self._add_excluded_region_vrects(fig=fig, excluded_ranges=excluded_ranges)
        self._show_figure(fig)

    @staticmethod
    def _add_excluded_region_vrects(
        *,
        fig: object,
        excluded_ranges: tuple[tuple[float, float], ...],
        row: object | None = None,
        col: int | None = None,
    ) -> None:
        """Shade excluded x-ranges on a Plotly figure."""
        for start, end in excluded_ranges:
            add_kwargs = {
                'x0': start,
                'x1': end,
                'fillcolor': EXCLUDED_REGION_FILL_COLOR,
                'opacity': 1.0,
                'line_width': 0,
                'layer': 'below',
            }
            if row is not None:
                add_kwargs['row'] = row
            if col is not None:
                add_kwargs['col'] = col
            fig.add_vrect(**add_kwargs)

    @classmethod
    def _get_bragg_tick_trace(
        cls,
        tick_set: BraggTickSet,
        row_y: float,
        color: str,
    ) -> object:
        """
        Create a hover-capable Bragg tick trace for one linked phase.

        Only the Miller-index line is colored to match the phase tick
        marker; the phase name and x line use the default tooltip text
        color, and all lines share the padding and themed frame used by
        every other tooltip.
        """
        y = np.full(tick_set.x.shape, row_y, dtype=float)
        hover_text = []
        for idx, x_value in enumerate(tick_set.x):
            index_h = int(tick_set.h[idx])
            index_k = int(tick_set.k[idx])
            index_l = int(tick_set.ell[idx])
            lines = [
                tick_set.phase_id,
                f'x: {float(x_value):,.2f}',
                cls._hover_color_span(
                    f'Miller indices: ({index_h} {index_k} {index_l})',
                    color,
                ),
                # f'F²cal: {float(tick_set.f_squared_calc[idx]):.6g}',
                # f'Fcalc: {float(tick_set.f_calc[idx]):.6g}',
            ]
            hover_text.append(cls._format_hover_lines(lines))

        return go.Scatter(
            x=tick_set.x,
            y=y,
            mode='markers',
            marker={
                'symbol': 'line-ns-open',
                'size': BRAGG_TICK_MARKER_SIZE,
                'line': {'width': BRAGG_TICK_MARKER_LINE_WIDTH},
                'color': color,
            },
            name=f'Bragg peaks: {tick_set.phase_id}',
            text=hover_text,
            hovertemplate='%{text}',
        )

    @staticmethod
    def _nice_axis_limit(raw_limit: float) -> float:
        """Round a positive axis limit up to a readable value."""
        if raw_limit <= 0:
            return 1.0

        exponent = float(np.floor(np.log10(raw_limit)))
        base = 10.0**exponent
        fraction = raw_limit / base

        for nice_fraction in NICE_AXIS_FRACTIONS:
            if fraction <= nice_fraction:
                return nice_fraction * base
        return NICE_AXIS_FRACTIONS[-1] * base

    @staticmethod
    def _get_display_tick_limit(raw_limit: float) -> float:
        """Return a rounded positive tick limit within ``raw_limit``."""
        if raw_limit <= 0:
            return 1.0

        exponent = float(np.floor(np.log10(raw_limit)))
        base = 10.0**exponent
        fraction = raw_limit / base

        for nice_fraction in reversed(DISPLAY_TICK_FRACTIONS):
            if fraction >= nice_fraction:
                return nice_fraction * base
        return DISPLAY_TICK_FRACTIONS[0] * base

    @staticmethod
    def _base_composite_height_pixels(plot_spec: PowderMeasVsCalcSpec) -> float:
        """Return the baseline figure height for a single-phase plot."""
        if plot_spec.height is None:
            return float(DEFAULT_HEIGHT * PLOTLY_HEIGHT_PER_UNIT)
        return float(plot_spec.height)

    @staticmethod
    def _composite_plot_area_height(full_height: float) -> float:
        """
        Return the drawable plot area height after vertical margins.
        """
        return max(full_height - COMPOSITE_MARGIN_TOP - COMPOSITE_MARGIN_BOTTOM, 1.0)

    @staticmethod
    def _subplot_available_height_fraction(row_count: int) -> float:
        """
        Return the fraction of plot height available for subplot rows.
        """
        return 1.0 - COMPOSITE_VERTICAL_SPACING * max(row_count - 1, 0)

    @staticmethod
    def _bragg_tick_symbol_height_pixels() -> float:
        """Return rendered pixel height for one Bragg tick marker."""
        return (
            BRAGG_TICK_MARKER_SIZE * BRAGG_TICK_SYMBOL_HEIGHT_SCALE + BRAGG_TICK_MARKER_LINE_WIDTH
        )

    @staticmethod
    def _bragg_row_height_pixels(plot_spec: PowderMeasVsCalcSpec) -> float:
        """
        Return the exact Bragg-row pixel height for the current phases.
        """
        return float(
            len(plot_spec.bragg_tick_sets) * PlotlyPlotter._bragg_tick_symbol_height_pixels()
        )

    @classmethod
    def _baseline_non_bragg_row_heights(
        cls,
        plot_spec: PowderMeasVsCalcSpec,
        row_count: int,
        *,
        has_bragg_ticks: bool,
        has_residual: bool,
    ) -> tuple[float, float | None]:
        """Return baseline main and residual row heights in pixels."""
        baseline_height = cls._base_composite_height_pixels(plot_spec)
        plot_area_height = cls._composite_plot_area_height(baseline_height)
        available_row_pixels = plot_area_height * cls._subplot_available_height_fraction(row_count)
        baseline_bragg_pixels = float(
            cls._bragg_tick_symbol_height_pixels() if has_bragg_ticks else 0
        )
        non_bragg_pixels = max(available_row_pixels - baseline_bragg_pixels, 1.0)

        if not has_residual:
            return non_bragg_pixels, None

        main_pixels = non_bragg_pixels / (1.0 + plot_spec.residual_height_fraction)
        residual_pixels = main_pixels * plot_spec.residual_height_fraction
        return main_pixels, residual_pixels

    @staticmethod
    def _get_powder_composite_rows(plot_spec: PowderMeasVsCalcSpec) -> PowderCompositeRows:
        """Resolve subplot rows for the composite powder figure."""
        has_bragg_ticks = bool(plot_spec.bragg_tick_sets)
        has_residual = plot_spec.y_resid is not None
        row_count = 1 + int(has_bragg_ticks) + int(has_residual)
        main_row_height, residual_row_height = PlotlyPlotter._baseline_non_bragg_row_heights(
            plot_spec=plot_spec,
            row_count=row_count,
            has_bragg_ticks=has_bragg_ticks,
            has_residual=has_residual,
        )
        row_heights = [main_row_height]
        bragg_row = None
        residual_row = None
        next_row = 2

        if has_bragg_ticks:
            bragg_row = next_row
            next_row += 1
            row_heights.append(PlotlyPlotter._bragg_row_height_pixels(plot_spec))
        if has_residual:
            residual_row = next_row
            row_heights.append(residual_row_height if residual_row_height is not None else 1.0)

        return PowderCompositeRows(
            row_count=row_count,
            row_heights=row_heights,
            bragg_row=bragg_row,
            residual_row=residual_row,
        )

    @classmethod
    def _composite_figure_height(
        cls,
        plot_spec: PowderMeasVsCalcSpec,
        layout: PowderCompositeRows,
    ) -> float:
        """Return figure height for Bragg row growth."""
        base_pixels = cls._base_composite_height_pixels(plot_spec)
        phase_count = len(plot_spec.bragg_tick_sets)
        if phase_count <= 1:
            return base_pixels

        added_bragg_pixels = float((phase_count - 1) * cls._bragg_tick_symbol_height_pixels())
        growth_pixels = added_bragg_pixels / cls._subplot_available_height_fraction(
            layout.row_count
        )
        return base_pixels + growth_pixels

    @classmethod
    def _get_main_intensity_range(cls, plot_spec: PowderMeasVsCalcSpec) -> tuple[float, float]:
        """
        Return an explicit y-range for the main powder intensity row.
        """
        y_meas = np.asarray(plot_spec.y_meas)
        y_calc = np.asarray(plot_spec.y_calc)
        if min(y_meas.size, y_calc.size) == 0:
            return 0.0, 1.0

        main_series = cls._main_intensity_series(plot_spec, y_meas=y_meas, y_calc=y_calc)

        main_y_min = float(min(np.min(series) for series in main_series))
        main_y_max = float(max(np.max(series) for series in main_series))
        main_y_range = main_y_max - main_y_min
        if main_y_range > 0.0:
            main_y_margin = main_y_range * MAIN_INTENSITY_RANGE_MARGIN_FRACTION
            return main_y_min - main_y_margin, main_y_max + main_y_margin

        return main_y_min - 1.0, main_y_max + 1.0

    @classmethod
    def _main_intensity_series(
        cls,
        plot_spec: PowderMeasVsCalcSpec,
        *,
        y_meas: np.ndarray,
        y_calc: np.ndarray,
    ) -> list[np.ndarray]:
        main_series = [y_meas, y_calc]
        for values in (
            plot_spec.y_bkg,
            plot_spec.predictive_lower_95,
            plot_spec.predictive_upper_95,
        ):
            cls._append_non_empty_series(main_series, values)

        predictive_draws = cls._predictive_draw_array(plot_spec.predictive_draws)
        if predictive_draws is not None:
            main_series.extend(predictive_draws)
        return main_series

    @staticmethod
    def _append_non_empty_series(
        main_series: list[np.ndarray],
        values: np.ndarray | None,
    ) -> None:
        if values is None:
            return

        array = np.asarray(values)
        if array.size > 0:
            main_series.append(array)

    @staticmethod
    def _predictive_draw_array(values: object | None) -> np.ndarray | None:
        if values is None:
            return None

        predictive_draws = np.asarray(values)
        if predictive_draws.ndim != PREDICTIVE_DRAW_ARRAY_NDIM or predictive_draws.size == 0:
            return None
        return predictive_draws

    @classmethod
    def _get_residual_limit(cls, plot_spec: PowderMeasVsCalcSpec) -> float:
        """Return a symmetric residual limit matched to the main row."""
        if plot_spec.y_resid is None:
            return 1.0

        y_meas = np.asarray(plot_spec.y_meas)
        y_calc = np.asarray(plot_spec.y_calc)
        y_resid = np.asarray(plot_spec.y_resid)
        if min(y_meas.size, y_calc.size, y_resid.size) == 0:
            return 1.0

        main_y_min, main_y_max = cls._get_main_intensity_range(plot_spec)
        main_y_range = max(main_y_max - main_y_min, 0.0)
        scale_matched_half_range = 0.5 * main_y_range * plot_spec.residual_height_fraction
        if scale_matched_half_range > 0.0:
            return scale_matched_half_range

        return cls._nice_axis_limit(float(np.max(np.abs(y_resid))))

    @staticmethod
    def _composite_x_range(x_values: np.ndarray) -> tuple[float | None, float | None]:
        """Return the explicit x-range for the composite powder plot."""
        if x_values.size == 0:
            return None, None
        return float(np.min(x_values)), float(np.max(x_values))

    def plot_powder_meas_vs_calc(
        self,
        plot_spec: PowderMeasVsCalcSpec,
    ) -> None:
        """
        Render a composite powder plot with optional Bragg ticks.

        The main row shows measured and calculated intensities. The
        Bragg row is added only when tick data is available. The
        residual row is added only when residual data is requested.
        """
        fig = self.build_powder_meas_vs_calc_figure(plot_spec=plot_spec)
        self._show_figure(fig)

    def build_powder_meas_vs_calc_figure(
        self,
        plot_spec: PowderMeasVsCalcSpec,
    ) -> object:
        """
        Build a composite powder Plotly figure without displaying it.

        Parameters
        ----------
        plot_spec : PowderMeasVsCalcSpec
            Composite powder-plot inputs and layout settings.

        Returns
        -------
        object
            Configured :class:`plotly.graph_objects.Figure`.
        """
        layout = self._get_powder_composite_rows(plot_spec)
        x_min, x_max = self._composite_x_range(np.asarray(plot_spec.x))
        main_y_min, main_y_max = self._get_main_intensity_range(plot_spec)
        hover_data = self._powder_meas_vs_calc_hover_data(plot_spec)
        hover_template = self._powder_meas_vs_calc_hover_template(plot_spec)
        fig = self._create_powder_composite_figure(layout)
        self._add_predictive_band_traces(fig=fig, plot_spec=plot_spec)
        self._add_main_intensity_traces(
            fig=fig,
            plot_spec=plot_spec,
            hover_data=hover_data,
            hover_template=hover_template,
        )
        self._add_predictive_draw_traces(fig=fig, plot_spec=plot_spec)
        self._add_bragg_tick_traces(fig=fig, plot_spec=plot_spec, layout=layout)
        residual_limit = self._add_residual_trace(
            fig=fig,
            plot_spec=plot_spec,
            layout=layout,
            hover_data=hover_data,
            hover_template=hover_template,
        )
        self._add_excluded_region_vrects(
            fig=fig,
            excluded_ranges=plot_spec.excluded_ranges,
            row='all',
            col=1,
        )
        self._configure_powder_composite_layout(fig=fig, plot_spec=plot_spec, layout=layout)
        self._configure_powder_composite_axes(
            fig=fig,
            plot_spec=plot_spec,
            layout=layout,
            x_range=(x_min, x_max),
            main_y_range=(main_y_min, main_y_max),
            residual_limit=residual_limit,
        )

        return fig

    @staticmethod
    def _create_powder_composite_figure(layout: PowderCompositeRows) -> object:
        return make_subplots(
            rows=layout.row_count,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=COMPOSITE_VERTICAL_SPACING,
            row_heights=layout.row_heights,
        )

    def _add_predictive_band_traces(
        self,
        *,
        fig: object,
        plot_spec: PowderMeasVsCalcSpec,
    ) -> None:
        if plot_spec.predictive_lower_95 is None or plot_spec.predictive_upper_95 is None:
            return

        lower_trace, upper_trace = self._get_predictive_band_traces(
            x=plot_spec.x,
            lower=plot_spec.predictive_lower_95,
            upper=plot_spec.predictive_upper_95,
        )
        fig.add_trace(lower_trace, row=1, col=1)
        fig.add_trace(upper_trace, row=1, col=1)

    def _add_main_intensity_traces(
        self,
        *,
        fig: object,
        plot_spec: PowderMeasVsCalcSpec,
        hover_data: object,
        hover_template: str,
    ) -> None:
        meas_trace = self._get_powder_trace(
            plot_spec.x,
            plot_spec.y_meas,
            'meas',
            customdata=hover_data,
            hovertemplate=hover_template,
        )
        if plot_spec.y_meas_su is not None:
            meas_trace.error_y = {
                'type': 'data',
                'array': plot_spec.y_meas_su,
                'visible': True,
                'color': DEFAULT_COLORS['meas'],
                'thickness': MEASURED_ERROR_BAR_THICKNESS,
                'width': MEASURED_ERROR_BAR_WIDTH,
            }
        fig.add_trace(meas_trace, row=1, col=1)

        if plot_spec.y_bkg is not None:
            bkg_trace = self._get_powder_trace(
                plot_spec.x,
                plot_spec.y_bkg,
                'bkg',
                customdata=hover_data,
                hovertemplate=hover_template,
            )
            fig.add_trace(bkg_trace, row=1, col=1)

        calc_trace = self._get_powder_trace(
            plot_spec.x,
            plot_spec.y_calc,
            'calc',
            customdata=hover_data,
            hovertemplate=hover_template,
        )
        if plot_spec.y_calc_name is not None:
            calc_trace.name = plot_spec.y_calc_name
        if plot_spec.y_calc_line_dash is not None:
            calc_trace.line.dash = plot_spec.y_calc_line_dash
        fig.add_trace(calc_trace, row=1, col=1)

    def _add_predictive_draw_traces(
        self,
        *,
        fig: object,
        plot_spec: PowderMeasVsCalcSpec,
    ) -> None:
        predictive_draws = self._predictive_draw_array(plot_spec.predictive_draws)
        if predictive_draws is None:
            return

        draw_cap = min(predictive_draws.shape[0], PREDICTIVE_DRAW_PLOT_CAP)
        for index in range(draw_cap):
            fig.add_trace(
                go.Scatter(
                    x=plot_spec.x,
                    y=predictive_draws[index],
                    mode='lines',
                    line={'color': PREDICTIVE_DRAW_COLOR, 'width': 1},
                    name='Posterior draw' if index == 0 else None,
                    showlegend=index == 0,
                    hovertemplate=(
                        'Posterior draw<br>x: %{x:,.2f}<br>y: %{y:,.2f}<extra></extra>'
                    ),
                ),
                row=1,
                col=1,
            )

    def _add_bragg_tick_traces(
        self,
        *,
        fig: object,
        plot_spec: PowderMeasVsCalcSpec,
        layout: PowderCompositeRows,
    ) -> None:
        if layout.bragg_row is None:
            return

        for idx, tick_set in enumerate(plot_spec.bragg_tick_sets):
            color = BRAGG_TICK_COLORS[idx % len(BRAGG_TICK_COLORS)]
            fig.add_trace(
                self._get_bragg_tick_trace(
                    tick_set=tick_set,
                    row_y=float(idx + 1),
                    color=color,
                ),
                row=layout.bragg_row,
                col=1,
            )

    def _add_residual_trace(
        self,
        *,
        fig: object,
        plot_spec: PowderMeasVsCalcSpec,
        layout: PowderCompositeRows,
        hover_data: object,
        hover_template: str,
    ) -> float | None:
        if layout.residual_row is None or plot_spec.y_resid is None:
            return None

        residual_limit = self._get_residual_limit(plot_spec)
        fig.add_trace(
            self._get_powder_trace(
                plot_spec.x,
                plot_spec.y_resid,
                'resid',
                customdata=hover_data,
                hovertemplate=hover_template,
            ),
            row=layout.residual_row,
            col=1,
        )
        return residual_limit

    def _configure_powder_composite_layout(
        self,
        *,
        fig: object,
        plot_spec: PowderMeasVsCalcSpec,
        layout: PowderCompositeRows,
    ) -> None:
        fig.update_layout(
            height=self._composite_figure_height(plot_spec, layout),
            margin={
                'autoexpand': True,
                'r': COMPOSITE_MARGIN_RIGHT,
                't': COMPOSITE_MARGIN_TOP,
                'b': COMPOSITE_MARGIN_BOTTOM,
            },
            title={
                'text': plot_spec.title,
                'font': {'size': TITLE_FONT_SIZE},
            },
            legend={
                'bgcolor': self._legend_background_color(),
                'xanchor': 'right',
                'x': 1.0,
                'yanchor': 'top',
                'y': 1.0,
            },
        )

    def _configure_powder_composite_axes(
        self,
        *,
        fig: object,
        plot_spec: PowderMeasVsCalcSpec,
        layout: PowderCompositeRows,
        x_range: tuple[float | None, float | None],
        main_y_range: tuple[float, float],
        residual_limit: float | None,
    ) -> None:
        self._configure_shared_composite_axes(
            fig=fig,
            row_count=layout.row_count,
            x_min=x_range[0],
            x_max=x_range[1],
        )
        fig.update_xaxes(showticklabels=(layout.row_count == 1), row=1, col=1)
        fig.update_yaxes(
            title_text=plot_spec.axes_labels[1],
            title_font={'size': AXIS_TITLE_FONT_SIZE},
            range=list(main_y_range),
            row=1,
            col=1,
        )

        if layout.bragg_row is not None:
            self._configure_bragg_axes(fig=fig, plot_spec=plot_spec, layout=layout)
        if layout.residual_row is not None and residual_limit is not None:
            self._configure_residual_axes(
                fig=fig,
                plot_spec=plot_spec,
                layout=layout,
                residual_limit=residual_limit,
            )
            return

        terminal_row = layout.bragg_row if layout.bragg_row is not None else 1
        fig.update_xaxes(
            title_text=plot_spec.axes_labels[0],
            title_font={'size': AXIS_TITLE_FONT_SIZE},
            row=terminal_row,
            col=1,
        )

    def _configure_shared_composite_axes(
        self,
        *,
        fig: object,
        row_count: int,
        x_min: float | None,
        x_max: float | None,
    ) -> None:
        axis_frame_color = self._axis_frame_color()
        for row_idx in range(1, row_count + 1):
            x_axis_kwargs = {
                'matches': 'x',
                'showline': True,
                'linecolor': axis_frame_color,
                'mirror': True,
                'zeroline': False,
                'tickformat': ',.6~g',
                'ticklabelstandoff': X_AXIS_TICK_LABEL_STANDOFF,
                'separatethousands': True,
            }
            if x_min is not None and x_max is not None:
                x_axis_kwargs['range'] = [x_min, x_max]
            fig.update_xaxes(row=row_idx, col=1, **x_axis_kwargs)
            fig.update_yaxes(
                showline=True,
                linecolor=axis_frame_color,
                mirror=True,
                zeroline=False,
                tickformat=',.6~g',
                ticklabelstandoff=Y_AXIS_TICK_LABEL_STANDOFF,
                separatethousands=True,
                row=row_idx,
                col=1,
            )

    @staticmethod
    def _configure_bragg_axes(
        *,
        fig: object,
        plot_spec: PowderMeasVsCalcSpec,
        layout: PowderCompositeRows,
    ) -> None:
        fig.update_yaxes(
            tickmode='array',
            tickvals=[float(idx + 1) for idx in range(len(plot_spec.bragg_tick_sets))],
            ticktext=[tick_set.phase_id for tick_set in plot_spec.bragg_tick_sets],
            range=[float(len(plot_spec.bragg_tick_sets)) + 0.5, 0.5],
            showgrid=False,
            row=layout.bragg_row,
            col=1,
        )
        fig.update_xaxes(
            showticklabels=layout.residual_row is None,
            row=layout.bragg_row,
            col=1,
        )

    def _configure_residual_axes(
        self,
        *,
        fig: object,
        plot_spec: PowderMeasVsCalcSpec,
        layout: PowderCompositeRows,
        residual_limit: float,
    ) -> None:
        residual_tick_limit = self._get_display_tick_limit(residual_limit)
        fig.update_yaxes(
            range=[-residual_limit, residual_limit],
            tickmode='array',
            tickvals=[-residual_tick_limit, 0.0, residual_tick_limit],
            scaleanchor='y',
            scaleratio=1,
            zeroline=False,
            row=layout.residual_row,
            col=1,
        )
        fig.update_xaxes(
            title_text=plot_spec.axes_labels[0],
            title_font={'size': AXIS_TITLE_FONT_SIZE},
            row=layout.residual_row,
            col=1,
        )

    @staticmethod
    def _get_predictive_band_traces(
        *,
        x: np.ndarray,
        lower: np.ndarray,
        upper: np.ndarray,
    ) -> tuple[go.Scatter, go.Scatter]:
        """
        Return Plotly traces for a filled predictive interval band.
        """
        lower_trace = go.Scatter(
            x=x,
            y=lower,
            mode='lines',
            line={'color': PREDICTIVE_BAND_EDGE_COLOR, 'width': 1},
            hoverinfo='skip',
            showlegend=False,
            legendgroup='predictive_band',
        )
        upper_trace = go.Scatter(
            x=x,
            y=upper,
            mode='lines',
            line={'color': PREDICTIVE_BAND_EDGE_COLOR, 'width': 1},
            fill='tonexty',
            fillcolor=PREDICTIVE_BAND_COLOR,
            name='95% credible interval',
            hoverinfo='skip',
            legendgroup='predictive_band',
            legendrank=35,
        )
        return lower_trace, upper_trace

    def plot_single_crystal(
        self,
        x_calc: object,
        y_meas: object,
        y_meas_su: object,
        axes_labels: object,
        title: str,
        height: int | None = None,
    ) -> None:
        """
        Render a scatter plot for single crystal diffraction data.

        Suitable for single crystal diffraction data where measured
        values are plotted against calculated values with error bars and
        a diagonal reference line.

        Parameters
        ----------
        x_calc : object
            1D array-like of calculated values (x-axis).
        y_meas : object
            1D array-like of measured values (y-axis).
        y_meas_su : object
            1D array-like of measurement uncertainties.
        axes_labels : object
            Pair of strings for the x and y titles.
        title : str
            Figure title.
        height : int | None, default=None
            Ignored; Plotly auto-sizes based on renderer.
        """
        # Intentionally unused; accepted for API compatibility
        del height

        fig = self.build_single_crystal_figure(
            x_calc=x_calc,
            y_meas=y_meas,
            y_meas_su=y_meas_su,
            axes_labels=axes_labels,
            title=title,
        )
        self._show_figure(fig)

    def build_single_crystal_figure(
        self,
        *,
        x_calc: object,
        y_meas: object,
        y_meas_su: object,
        axes_labels: object,
        title: str,
    ) -> object:
        """
        Build a single-crystal Plotly figure without displaying it.

        Parameters
        ----------
        x_calc : object
            1D array-like of calculated values (x-axis).
        y_meas : object
            1D array-like of measured values (y-axis).
        y_meas_su : object
            1D array-like of measurement uncertainties.
        axes_labels : object
            Pair of strings for the x and y titles.
        title : str
            Figure title.

        Returns
        -------
        object
            Configured :class:`plotly.graph_objects.Figure`.
        """
        data = [
            self._get_single_crystal_trace(
                x_calc,
                y_meas,
                y_meas_su,
            )
        ]

        axis_min, axis_max = single_crystal_axis_range(x_calc, y_meas, y_meas_su)
        tick_step = single_crystal_tick_step(axis_min, axis_max)
        layout = self._get_layout(
            title,
            axes_labels,
            shapes=[self._get_diagonal_shape(axis_min, axis_max)],
            axis_range=(axis_min, axis_max),
            axis_dtick=tick_step,
        )

        return self._get_figure(data, layout)

    def plot_scatter(
        self,
        x: object,
        y: object,
        sy: object,
        axes_labels: object,
        title: str,
        height: int | None = None,
    ) -> None:
        """Render a scatter plot with error bars via Plotly."""
        _ = height  # not used by Plotly backend

        trace = go.Scatter(
            x=x,
            y=y,
            mode='markers+lines',
            marker={
                'symbol': 'circle',
                'size': 10,
                'line': {'width': 0.5},
                'color': DEFAULT_COLORS['meas'],
            },
            line={
                'width': 1,
                'color': DEFAULT_COLORS['meas'],
            },
            error_y={
                'type': 'data',
                'array': sy,
                'visible': True,
            },
            hovertemplate='x: %{x:,.2f}<br>y: %{y:,.2f}<br><extra></extra>',
        )

        layout = self._get_layout(
            title,
            axes_labels,
        )

        fig = self._get_figure(trace, layout)
        self._show_figure(fig)
