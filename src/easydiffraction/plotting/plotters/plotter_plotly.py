# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction Python Library contributors <https://github.com/easyscience/diffraction-lib>
# SPDX-License-Identifier: BSD-3-Clause

import darkdetect
import plotly.graph_objects as go
import plotly.io as pio

try:
    from IPython.display import display
except ImportError:
    display = None

from easydiffraction.utils.utils import is_pycharm

from .plotter_base import SERIES_CONFIG
from .plotter_base import PlotterBase

DEFAULT_COLORS = {
    'meas': 'rgb(31, 119, 180)',
    'calc': 'rgb(214, 39, 40)',
    'resid': 'rgb(44, 160, 44)',
}


class PlotlyPlotter(PlotterBase):
    pio.templates.default = 'plotly_dark' if darkdetect.isDark() else 'plotly_white'

    def _get_trace(self, x, y, label):
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

    def plot(
        self,
        x,
        y_series,
        labels,
        axes_labels,
        title,
        height=None,
    ):
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

        # Show the figure

        # Build a Figure for non-notebook environments and a FigureWidget for Jupyter.
        # In notebooks we display the FigureWidget's rich repr instead of calling `.show()`
        # to avoid the `application/vnd.plotly.v1+json` warning during book builds.

        if is_pycharm() or display is None:
            # PyCharm (or no IPython display available): use a regular Figure and show it
            fig = go.Figure(
                data=data,
                layout=layout,
            )
            fig.show(config=config)
        else:
            # Jupyter notebooks: use FigureWidget and let IPython render the repr
            fig_widget = go.FigureWidget(
                data=data,
                layout=layout,
            )
            display(fig_widget)
