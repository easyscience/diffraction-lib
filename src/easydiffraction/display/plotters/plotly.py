# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
Plotly plotting backend.

Provides an interactive plotting implementation using Plotly. In
notebooks, figures are displayed inline; in other environments a browser
renderer may be used depending on configuration.
"""

from __future__ import annotations

from dataclasses import dataclass

import darkdetect
import numpy as np
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots

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
from easydiffraction.utils._vendored.theme_detect import is_dark
from easydiffraction.utils.environment import in_jupyter
from easydiffraction.utils.environment import in_pycharm

DEFAULT_COLORS = {
    'meas': 'rgb(31, 119, 180)',
    'bkg': 'rgb(140, 140, 140)',
    'calc': 'rgb(214, 39, 40)',
    'resid': 'rgb(44, 160, 44)',
}

BRAGG_TICK_COLORS = (
    'rgb(255, 127, 14)',
    'rgb(23, 190, 207)',
    'rgb(140, 140, 140)',
    'rgb(188, 189, 34)',
    'rgb(148, 103, 189)',
)

NICE_AXIS_FRACTIONS = (1.0, 2.0, 5.0, 10.0)
DISPLAY_TICK_FRACTIONS = (1.0, 2.0, 2.5, 4.0, 5.0, 7.5, 10.0)
PLOTLY_HEIGHT_PER_UNIT = 24
BRAGG_TICK_MARKER_SIZE = 12
BRAGG_TICK_MARKER_LINE_WIDTH = 1
BRAGG_TICK_SYMBOL_HEIGHT_SCALE = 1.4
COMPOSITE_VERTICAL_SPACING = 0.03
COMPOSITE_MARGIN_RIGHT = 30
COMPOSITE_MARGIN_TOP = 40
COMPOSITE_MARGIN_BOTTOM = 45


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

        Dark mode uses black at zero correlation for lower visual
        prominence. Light mode uses white at zero correlation.

        Returns
        -------
        list[tuple[float, str]]
            Plotly-compatible colorscale definition.
        """
        if cls._is_dark_mode():
            return [
                (0.0, '#d73027'),
                (0.5, '#000000'),
                (1.0, '#4575b4'),
            ]
        return [
            (0.0, '#d73027'),
            (0.5, '#f7f7f7'),
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
        if cls._is_dark_mode():
            return 'rgba(110, 145, 190, 0.35)'
        return 'rgba(120, 140, 160, 0.28)'

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
            hovertemplate=f'x: %{{x}}<br>y: %{{y}}<br>corr: %{{z:.{precision}f}}<extra></extra>',
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
        fig.update_xaxes(
            side='bottom',
            tickangle=-10,
            automargin=True,
            tickmode='array',
            tickvals=x_centers.tolist(),
            ticktext=corr_df.columns.tolist(),
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
            ticklabelstandoff=8,
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

    @staticmethod
    def _get_powder_trace(
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
        line = {'color': color}
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
            customdata=customdata,
            hovertemplate=(
                hovertemplate
                if hovertemplate is not None
                else f'{name}<br>x: %{{x}}<br>y: %{{y}}<extra></extra>'
            ),
        )

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

    @staticmethod
    def _powder_meas_vs_calc_hover_template(plot_spec: PowderMeasVsCalcSpec) -> str:
        """
        Return a shared hover template for composite powder traces.
        """
        if plot_spec.y_bkg is None:
            return (
                'x: %{x:,.2f}<br>'
                'Imeas: %{customdata[0]:,.2f}<br>'
                'Icalc: %{customdata[1]:,.2f}<br>'
                'Imeas - Icalc: %{customdata[2]:,.2f}'
                '<extra></extra>'
            )

        return (
            'x: %{x:,.2f}<br>'
            'Imeas: %{customdata[0]:,.2f}<br>'
            'Ibkg: %{customdata[1]:,.2f}<br>'
            'Icalc: %{customdata[2]:,.2f}<br>'
            'Imeas - Icalc: %{customdata[3]:,.2f}'
            '<extra></extra>'
        )

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
                'size': 10,
                'line': {'width': 0.5},
                'color': DEFAULT_COLORS['meas'],
            },
            error_y={
                'type': 'data',
                'array': y_meas_su,
                'visible': True,
            },
            hovertemplate='calc: %{x}<br>meas: %{y}<br><extra></extra>',
        )

    @staticmethod
    def _get_diagonal_shape() -> dict:
        """
        Create a diagonal reference line shape.

        Returns a y=x diagonal line spanning the plot area using paper
        coordinates (0,0) to (1,1).

        Returns
        -------
        dict
            A dict configuring a diagonal line shape.
        """
        return {
            'type': 'line',
            'x0': 0,
            'y0': 0,
            'x1': 1,
            'y1': 1,
            'xref': 'paper',
            'yref': 'paper',
            'layer': 'below',
            'line': {'width': 0.5},
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
            'displaylogo': False,
            'modeBarButtonsToRemove': [
                'select2d',
                'lasso2d',
                'zoomIn2d',
                'zoomOut2d',
                'autoScale2d',
            ],
        }

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

        if in_pycharm() or display is None or HTML is None:
            fig.show(config=config)
        else:
            html_fig = pio.to_html(
                fig,
                include_plotlyjs='cdn',
                full_html=False,
                config=config,
            )
            display(HTML(html_fig))

    @staticmethod
    def _get_layout(
        title: str,
        axes_labels: object,
        shapes: list | None = None,
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

        Returns
        -------
        object
            A configured :class:`plotly.graph_objects.Layout`.
        """
        return go.Layout(
            margin={
                'autoexpand': True,
                'r': 30,
                't': 40,
                'b': 45,
            },
            title={
                'text': title,
            },
            legend={
                'xanchor': 'right',
                'x': 1.0,
                'yanchor': 'top',
                'y': 1.0,
            },
            xaxis={
                'title_text': axes_labels[0],
                'showline': True,
                'mirror': True,
                'zeroline': False,
            },
            yaxis={
                'title_text': axes_labels[1],
                'showline': True,
                'mirror': True,
                'zeroline': False,
            },
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
        self._show_figure(fig)

    @staticmethod
    def _get_bragg_tick_trace(
        tick_set: BraggTickSet,
        row_y: float,
        color: str,
    ) -> object:
        """
        Create a hover-capable Bragg tick trace for one linked phase.
        """
        y = np.full(tick_set.x.shape, row_y, dtype=float)
        hover_text = []
        for idx, x_value in enumerate(tick_set.x):
            index_h = int(tick_set.h[idx])
            index_k = int(tick_set.k[idx])
            index_l = int(tick_set.ell[idx])
            hover_text.append(
                f'{tick_set.phase_id}<br>'
                f'x: {float(x_value):,.2f}<br>'
                f'Miller indices: ({index_h} {index_k} {index_l})<br>'
                # f'F²cal:{float(tick_set.f_squared_calc[idx]):.6g}<br>'
                # f'Fcalc:{float(tick_set.f_calc[idx]):.6g}'
                '<extra></extra>'
            )

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
            hoverlabel={
                'font': {'color': 'white'},
                'bordercolor': 'white',
            },
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

        main_y_min = float(min(np.min(y_meas), np.min(y_calc)))
        main_y_max = float(max(np.max(y_meas), np.max(y_calc)))
        lower_limit = min(0.0, main_y_min)
        if main_y_max <= lower_limit:
            return lower_limit - 1.0, lower_limit + 1.0
        return lower_limit, main_y_max

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
        layout = self._get_powder_composite_rows(plot_spec)
        x_values = np.asarray(plot_spec.x)
        has_x_values = x_values.size > 0
        x_min = float(np.min(x_values)) if has_x_values else None
        x_max = float(np.max(x_values)) if has_x_values else None
        main_y_min, main_y_max = self._get_main_intensity_range(plot_spec)
        residual_limit = None
        hover_data = self._powder_meas_vs_calc_hover_data(plot_spec)
        hover_template = self._powder_meas_vs_calc_hover_template(plot_spec)

        fig = make_subplots(
            rows=layout.row_count,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=COMPOSITE_VERTICAL_SPACING,
            row_heights=layout.row_heights,
        )

        main_traces = (
            (
                ('meas', plot_spec.y_meas),
                ('bkg', plot_spec.y_bkg),
                ('calc', plot_spec.y_calc),
            )
            if plot_spec.y_bkg is not None
            else (
                ('meas', plot_spec.y_meas),
                ('calc', plot_spec.y_calc),
            )
        )
        for label, y_values in main_traces:
            fig.add_trace(
                self._get_powder_trace(
                    plot_spec.x,
                    y_values,
                    label,
                    customdata=hover_data,
                    hovertemplate=hover_template,
                ),
                row=1,
                col=1,
            )

        if layout.bragg_row is not None:
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

        if layout.residual_row is not None and plot_spec.y_resid is not None:
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

        fig.update_layout(
            height=self._composite_figure_height(plot_spec, layout),
            margin={
                'autoexpand': True,
                'r': COMPOSITE_MARGIN_RIGHT,
                't': COMPOSITE_MARGIN_TOP,
                'b': COMPOSITE_MARGIN_BOTTOM,
            },
            title={'text': plot_spec.title},
            legend={
                'xanchor': 'right',
                'x': 1.0,
                'yanchor': 'top',
                'y': 1.0,
            },
        )

        for row_idx in range(1, layout.row_count + 1):
            x_axis_kwargs = {
                'matches': 'x',
                'showline': True,
                'mirror': True,
                'zeroline': False,
                'tickformat': ',.6~g',
                'separatethousands': True,
            }
            if has_x_values:
                x_axis_kwargs['range'] = [x_min, x_max]
            fig.update_xaxes(row=row_idx, col=1, **x_axis_kwargs)
            fig.update_yaxes(
                showline=True,
                mirror=True,
                zeroline=False,
                tickformat=',.6~g',
                separatethousands=True,
                row=row_idx,
                col=1,
            )

        fig.update_xaxes(showticklabels=(layout.row_count == 1), row=1, col=1)
        fig.update_yaxes(
            title_text=plot_spec.axes_labels[1],
            range=[main_y_min, main_y_max],
            row=1,
            col=1,
        )

        if layout.bragg_row is not None:
            fig.update_yaxes(
                # title_text='Bragg peaks',
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

        if layout.residual_row is not None and plot_spec.y_resid is not None:
            residual_tick_limit = self._get_display_tick_limit(residual_limit)
            fig.update_yaxes(
                # title_text='Residual',
                range=[-residual_limit, residual_limit],
                tickmode='array',
                tickvals=[-residual_tick_limit, 0.0, residual_tick_limit],
                scaleanchor='y',
                scaleratio=1,
                zeroline=False,
                row=layout.residual_row,
                col=1,
            )
            fig.update_xaxes(title_text=plot_spec.axes_labels[0], row=layout.residual_row, col=1)
        else:
            terminal_row = layout.bragg_row if layout.bragg_row is not None else 1
            fig.update_xaxes(title_text=plot_spec.axes_labels[0], row=terminal_row, col=1)

        self._show_figure(fig)

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

        data = [
            self._get_single_crystal_trace(
                x_calc,
                y_meas,
                y_meas_su,
            )
        ]

        layout = self._get_layout(
            title,
            axes_labels,
            shapes=[self._get_diagonal_shape()],
        )

        fig = self._get_figure(data, layout)
        self._show_figure(fig)

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
