# SPDX-FileCopyrightText: 2021-2026 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Plotly plotting backend.

Provides an interactive plotting implementation using Plotly. In
notebooks, figures are displayed inline; in other environments a browser
renderer may be used depending on configuration.
"""

import darkdetect
import plotly.graph_objects as go
import plotly.io as pio

try:
    from IPython.display import HTML
    from IPython.display import display
except ImportError:
    display = None
    HTML = None

from easydiffraction.display.plotters.base import SERIES_CONFIG
from easydiffraction.display.plotters.base import PlotterBase
from easydiffraction.utils.environment import in_pycharm

DEFAULT_COLORS = {
    'meas': 'rgb(31, 119, 180)',
    'calc': 'rgb(214, 39, 40)',
    'resid': 'rgb(44, 160, 44)',
}


class PlotlyPlotter(PlotterBase):
    """Interactive plotter using Plotly for notebooks and browsers."""

    pio.templates.default = 'plotly_dark' if darkdetect.isDark() else 'plotly_white'
    if in_pycharm():
        pio.renderers.default = 'browser'

    def _get_trace(self, x, y, label):
        """Create a Plotly trace for a single data series.

        Args:
            x: 1D array-like of x-axis values.
            y: 1D array-like of y-axis values.
            label: Series identifier (``'meas'``, ``'calc'``, or
                ``'resid'``).

        Returns:
            A configured :class:`plotly.graph_objects.Scatter` trace.
        """
        mode = SERIES_CONFIG[label]['mode']
        name = SERIES_CONFIG[label]['name']
        color = DEFAULT_COLORS[label]
        line = {'color': color}

        trace = go.Scatter(
            x=x,
            y=y,
            line=line,
            mode=mode,
            name=name,
        )

        return trace

    def plot_pattern(
        self,
        x,
        y_series,
        labels,
        axes_labels,
        title,
        height=None,
    ):
        """Render an interactive Plotly line plot for pattern data.

        Suitable for powder diffraction data where intensity is plotted
        against an x-axis variable (2θ, TOF, d-spacing).

        Args:
            x: 1D array-like of x-axis values.
            y_series: Sequence of y arrays to plot.
            labels: Series identifiers corresponding to y_series.
            axes_labels: Pair of strings for the x and y titles.
            title: Figure title.
            height: Ignored; Plotly auto-sizes based on renderer.
        """
        # Intentionally unused; accepted for API compatibility
        del height

        data = []
        for idx, y in enumerate(y_series):
            label = labels[idx]
            trace = self._get_trace(x, y, label)
            data.append(trace)

        layout = go.Layout(
            margin=dict(
                autoexpand=True,
                r=30,
                t=40,
                b=45,
            ),
            title=dict(
                text=title,
            ),
            legend=dict(
                xanchor='right',
                x=1.0,
                yanchor='top',
                y=1.0,
            ),
            xaxis=dict(
                title_text=axes_labels[0],
                showline=True,
                mirror=True,
                zeroline=False,
            ),
            yaxis=dict(
                title_text=axes_labels[1],
                showline=True,
                mirror=True,
                zeroline=False,
            ),
        )

        config = dict(
            displaylogo=False,
            modeBarButtonsToRemove=[
                'select2d',
                'lasso2d',
                'zoomIn2d',
                'zoomOut2d',
                'autoScale2d',
            ],
        )

        fig = go.Figure(
            data=data,
            layout=layout,
        )

        # Format the axes ticks.
        # Keeps decimals for small numbers; groups thousands for large
        # ones
        fig.update_xaxes(tickformat=',.6~g', separatethousands=True)
        fig.update_yaxes(tickformat=',.6~g', separatethousands=True)

        # Show the figure
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

    def plot_scatter_comparison(
        self,
        x_calc,
        y_meas,
        y_meas_su,
        axes_labels,
        title,
        height=None,
    ):
        """Render a scatter comparison plot.

        Suitable for single crystal data where measured values are
        plotted against calculated values with error bars and a
        diagonal reference line.

        Args:
            x_calc: 1D array-like of calculated values (x-axis).
            y_meas: 1D array-like of measured values (y-axis).
            y_meas_su: 1D array-like of measurement uncertainties.
            axes_labels: Pair of strings for the x and y titles.
            title: Figure title.
            height: Ignored; Plotly auto-sizes based on renderer.
        """
        # Intentionally unused; accepted for API compatibility
        del height

        # Determine axis limits
        vmin = float(min(y_meas.min(), x_calc.min()))
        vmax = float(max(y_meas.max(), x_calc.max()))

        # Update limits with some padding
        pad = 0.05 * (vmax - vmin) if vmax > vmin else 1.0
        vmin -= pad
        vmax += pad

        # Create data trace
        data = [
            go.Scatter(
                x=x_calc,
                y=y_meas,
                mode='markers',
                marker=dict(
                    symbol='circle',
                    size=10,
                    line=dict(
                        width=0.5,
                        # color=DEFAULT_COLORS['meas'],
                    ),
                    color=DEFAULT_COLORS['meas'],
                ),
                error_y=dict(
                    type='data',
                    array=y_meas_su,
                    visible=True,
                ),
                hovertemplate=('calc: %{x}<br>meas: %{y}<br><extra></extra>'),
            )
        ]

        # Setup layout
        layout = go.Layout(
            margin=dict(
                autoexpand=True,
                r=30,
                t=40,
                b=45,
            ),
            title=dict(
                text=title,
            ),
            legend=dict(
                xanchor='right',
                x=1.0,
                yanchor='top',
                y=1.0,
            ),
            xaxis=dict(
                title_text=axes_labels[0],
                showline=True,
                mirror=True,
                zeroline=False,
                range=[vmin, vmax],
                # scaleanchor="y", # make 1 unit on x == 1 unit on y
            ),
            yaxis=dict(
                title_text=axes_labels[1],
                showline=True,
                mirror=True,
                zeroline=False,
                range=[vmin, vmax],
                # constrain="domain", # helps keep the plot square-ish
            ),
            shapes=[
                dict(
                    type='line',
                    x0=vmin,
                    y0=vmin,
                    x1=vmax,
                    y1=vmax,
                    xref='x',
                    yref='y',
                    layer='below',  # diagonal behind points
                    line=dict(
                        width=0.5,
                        # dash='dash',
                    ),
                )
            ],
        )

        # Setup config
        config = dict(
            displaylogo=False,
            modeBarButtonsToRemove=[
                'select2d',
                'lasso2d',
                'zoomIn2d',
                'zoomOut2d',
                'autoScale2d',
            ],
        )

        # Create figure
        fig = go.Figure(
            data=data,
            layout=layout,
        )

        # Format the axes ticks.
        # Keeps decimals for small numbers; groups thousands for large
        # ones
        fig.update_xaxes(tickformat=',.6~g', separatethousands=True)
        fig.update_yaxes(tickformat=',.6~g', separatethousands=True)

        # Show the figure
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
