# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
Plotly plotting backend.

Provides an interactive plotting implementation using Plotly. In
notebooks, figures are displayed inline; in other environments a browser
renderer may be used depending on configuration.
"""

from __future__ import annotations

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

from easydiffraction.display.plotters.base import SERIES_CONFIG
from easydiffraction.display.plotters.base import BraggTickSet
from easydiffraction.display.plotters.base import PlotterBase
from easydiffraction.utils._vendored.theme_detect import is_dark
from easydiffraction.utils.environment import in_jupyter
from easydiffraction.utils.environment import in_pycharm

DEFAULT_COLORS = {
    'meas': 'rgb(31, 119, 180)',
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
            Series identifier (``'meas'``, ``'calc'``, or ``'resid'``).

        Returns
        -------
        object
            A configured :class:`plotly.graph_objects.Scatter` trace.
        """
        mode = SERIES_CONFIG[label]['mode']
        name = SERIES_CONFIG[label]['name']
        color = DEFAULT_COLORS[label]
        line = {'color': color}

        return go.Scatter(
            x=x,
            y=y,
            line=line,
            mode=mode,
            name=name,
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
        """Create a hover-capable Bragg tick trace for one structure."""
        y = np.full(tick_set.x.shape, row_y, dtype=float)
        peak_ids = tick_set.peak_id
        hover_text = []
        for idx, x_value in enumerate(tick_set.x):
            peak_line = ''
            if peak_ids is not None:
                peak_value = str(peak_ids[idx])
                if peak_value:
                    peak_line = f'peak: {peak_value}<br>'
            hover_text.append(
                f'structure: {tick_set.structure_id}<br>'
                f'{peak_line}'
                f'hkl: ({int(tick_set.h[idx])} {int(tick_set.k[idx])} {int(tick_set.l[idx])})<br>'
                f'x: {float(x_value):.6g}<br>'
                f'intensity: {float(tick_set.intensity[idx]):.6g}<extra></extra>'
            )

        return go.Scatter(
            x=tick_set.x,
            y=y,
            mode='markers',
            marker={
                'symbol': 'line-ns-open',
                'size': 18,
                'line': {'color': color, 'width': 2},
                'color': color,
            },
            name=f'Bragg ({tick_set.structure_id})',
            text=hover_text,
            hovertemplate='%{text}',
            showlegend=False,
        )

    @staticmethod
    def _nice_axis_limit(raw_limit: float) -> float:
        """Round a positive axis limit up to a readable value."""
        if raw_limit <= 0:
            return 1.0

        exponent = float(np.floor(np.log10(raw_limit)))
        base = 10.0**exponent
        fraction = raw_limit / base

        if fraction <= 1.0:
            nice_fraction = 1.0
        elif fraction <= 2.0:
            nice_fraction = 2.0
        elif fraction <= 5.0:
            nice_fraction = 5.0
        else:
            nice_fraction = 10.0

        return nice_fraction * base

    def plot_powder_meas_vs_calc(
        self,
        x: np.ndarray,
        y_meas: np.ndarray,
        y_calc: np.ndarray,
        y_resid: np.ndarray | None,
        bragg_tick_sets: tuple[BraggTickSet, ...],
        axes_labels: list[str],
        title: str,
        residual_height_fraction: float,
        bragg_peaks_height_fraction: float,
        height: int | None = None,
    ) -> None:
        """
        Render a three-row powder plot with Bragg ticks and residual.

        The main row shows measured and calculated intensities. The
        middle row shows one Bragg tick row per structure or phase. The
        bottom row shows the residual when requested.
        """
        del height

        has_residual = y_resid is not None
        row_count = 3 if has_residual else 2
        row_heights = [1.0, bragg_peaks_height_fraction]
        if has_residual:
            row_heights.append(residual_height_fraction)
        x_min = float(np.min(x))
        x_max = float(np.max(x))
        total_height = sum(row_heights)
        normalized_row_heights = [row_height / total_height for row_height in row_heights]

        fig = make_subplots(
            rows=row_count,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.04,
            row_heights=normalized_row_heights,
        )

        fig.add_trace(self._get_powder_trace(x, y_meas, 'meas'), row=1, col=1)
        fig.add_trace(self._get_powder_trace(x, y_calc, 'calc'), row=1, col=1)

        for idx, tick_set in enumerate(bragg_tick_sets):
            color = BRAGG_TICK_COLORS[idx % len(BRAGG_TICK_COLORS)]
            fig.add_trace(
                self._get_bragg_tick_trace(
                    tick_set=tick_set,
                    row_y=float(idx + 1),
                    color=color,
                ),
                row=2,
                col=1,
            )

        if has_residual:
            fig.add_trace(self._get_powder_trace(x, y_resid, 'resid'), row=3, col=1)

            main_y_min = float(min(np.min(y_meas), np.min(y_calc)))
            main_y_max = float(max(np.max(y_meas), np.max(y_calc)))
            main_y_range = max(main_y_max - main_y_min, 0.0)
            scale_matched_half_range = 0.5 * main_y_range * residual_height_fraction
            residual_half_range = max(scale_matched_half_range, float(np.max(np.abs(y_resid))))
            residual_limit = self._nice_axis_limit(residual_half_range)

        fig.update_layout(
            margin={
                'autoexpand': True,
                'r': 30,
                't': 40,
                'b': 45,
            },
            title={'text': title},
            legend={
                'xanchor': 'right',
                'x': 1.0,
                'yanchor': 'top',
                'y': 1.0,
            },
        )

        for row_idx in range(1, row_count + 1):
            fig.update_xaxes(
                matches='x',
                range=[x_min, x_max],
                showline=True,
                mirror=True,
                zeroline=False,
                tickformat=',.6~g',
                separatethousands=True,
                row=row_idx,
                col=1,
            )
            fig.update_yaxes(
                showline=True,
                mirror=True,
                zeroline=False,
                tickformat=',.6~g',
                separatethousands=True,
                row=row_idx,
                col=1,
            )

        fig.update_xaxes(showticklabels=False, row=1, col=1)
        fig.update_yaxes(title_text=axes_labels[1], row=1, col=1)

        if bragg_tick_sets:
            fig.update_yaxes(
                title_text='Bragg peaks',
                tickmode='array',
                tickvals=[float(idx + 1) for idx in range(len(bragg_tick_sets))],
                ticktext=[tick_set.structure_id for tick_set in bragg_tick_sets],
                range=[0.5, float(len(bragg_tick_sets)) + 0.5],
                showgrid=False,
                row=2,
                col=1,
            )
        else:
            fig.update_yaxes(
                title_text='Bragg peaks',
                showticklabels=False,
                range=[0.5, 1.5],
                showgrid=False,
                row=2,
                col=1,
            )
        fig.update_xaxes(showticklabels=not has_residual, row=2, col=1)

        if has_residual:
            fig.update_yaxes(
                title_text='Residual',
                range=[-residual_limit, residual_limit],
                tickmode='array',
                tickvals=[-residual_limit, 0.0, residual_limit],
                zeroline=False,
                row=3,
                col=1,
            )
            fig.update_xaxes(title_text=axes_labels[0], row=3, col=1)
        else:
            fig.update_xaxes(title_text=axes_labels[0], row=2, col=1)

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
            hovertemplate='x: %{x}<br>y: %{y}<br><extra></extra>',
        )

        layout = self._get_layout(
            title,
            axes_labels,
        )

        fig = self._get_figure(trace, layout)
        self._show_figure(fig)
