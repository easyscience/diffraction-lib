# SPDX-FileCopyrightText: 2021-2026 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""ASCII plotting backend.

Renders compact line charts in the terminal using
``asciichartpy``. This backend is well suited for quick feedback in
CLI environments and keeps a consistent API with other plotters.
"""

import asciichartpy
import numpy as np

from easydiffraction.display.plotters.base import DEFAULT_HEIGHT
from easydiffraction.display.plotters.base import SERIES_CONFIG
from easydiffraction.display.plotters.base import PlotterBase
from easydiffraction.utils.logging import console

DEFAULT_COLORS = {
    'meas': asciichartpy.blue,
    'calc': asciichartpy.red,
    'resid': asciichartpy.green,
}


class AsciiPlotter(PlotterBase):
    """Terminal-based plotter using ASCII art."""

    def _get_legend_item(self, label):
        """Return a colored legend entry for a given series label.

        The legend uses a colored line matching the series color and
        the human-readable name from :data:`SERIES_CONFIG`.

        Args:
            label: Series identifier (e.g., ``'meas'``).

        Returns:
            A formatted legend string with color escapes.
        """
        color_start = DEFAULT_COLORS[label]
        color_end = asciichartpy.reset
        line = '────'
        name = SERIES_CONFIG[label]['name']
        item = f'{color_start}{line}{color_end} {name}'
        return item

    def plot_pattern(
        self,
        x,
        y_series,
        labels,
        axes_labels,
        title,
        height=None,
    ):
        """Render a compact ASCII line chart in the terminal.

        Suitable for powder diffraction data where intensity is plotted
        against an x-axis variable (2θ, TOF, d-spacing).

        Args:
            x: 1D array-like of x values (only used for range
                display).
            y_series: Sequence of y arrays to plot.
            labels: Series identifiers corresponding to y_series.
            axes_labels: Ignored; kept for API compatibility.
            title: Figure title printed above the chart.
            height: Number of text rows to allocate for the chart.
        """
        # Intentionally unused; kept for a consistent display API
        del axes_labels
        legend = '\n'.join([self._get_legend_item(label) for label in labels])

        if height is None:
            height = DEFAULT_HEIGHT
        colors = [DEFAULT_COLORS[label] for label in labels]
        config = {'height': height, 'colors': colors}
        y_series = [y.tolist() for y in y_series]

        chart = asciichartpy.plot(y_series, config)

        console.paragraph(f'{title}')  # TODO: f''?
        console.print(
            f'Displaying data for selected x-range from {x[0]} to {x[-1]} ({len(x)} points)'
        )
        console.print(f'Legend:\n{legend}')

        padded = '\n'.join(' ' + line for line in chart.splitlines())

        print(padded)

    def plot_scatter_comparison(
        self,
        x_calc,
        y_meas,
        y_meas_su,
        axes_labels,
        title,
        height=None,
    ):
        """Render a scatter comparison plot in the terminal.

        Creates an ASCII scatter plot showing measured vs calculated
        values with a diagonal reference line.

        Args:
            x_calc: 1D array-like of calculated values (x-axis).
            y_meas: 1D array-like of measured values (y-axis).
            y_meas_su: 1D array-like of measurement uncertainties
                (ignored in ASCII mode).
            axes_labels: Pair of strings for the x and y titles.
            title: Figure title.
            height: Number of text rows for the chart (default: 15).
        """
        # Intentionally unused; ASCII scatter doesn't show error bars
        del y_meas_su

        if height is None:
            height = DEFAULT_HEIGHT
        width = 60  # TODO: Make width configurable

        # Determine axis limits
        vmin = float(min(np.min(y_meas), np.min(x_calc)))
        vmax = float(max(np.max(y_meas), np.max(x_calc)))
        pad = 0.05 * (vmax - vmin) if vmax > vmin else 1.0
        vmin -= pad
        vmax += pad

        # Create empty grid
        grid = [[' ' for _ in range(width)] for _ in range(height)]

        # Draw diagonal line (calc == meas)
        for i in range(min(width, height)):
            row = height - 1 - int(i * height / width)
            col = i
            if 0 <= row < height and 0 <= col < width:
                grid[row][col] = '·'

        # Plot data points
        for xv, yv in zip(x_calc, y_meas, strict=False):
            col = int((xv - vmin) / (vmax - vmin) * (width - 1))
            row = height - 1 - int((yv - vmin) / (vmax - vmin) * (height - 1))
            if 0 <= row < height and 0 <= col < width:
                grid[row][col] = '●'

        # Build chart string with axes
        chart_lines = []
        for row in grid:
            label = '│'
            chart_lines.append(label + ''.join(row))

        # X-axis
        x_axis = '└' + '─' * width

        # Print output
        console.paragraph(f'{title}')
        console.print(f'{axes_labels[1]}')
        for line in chart_lines:
            print(f'  {line}')
        print(f'  {x_axis}')
        console.print(f'{" " * (width - 3)}{axes_labels[0]}')
