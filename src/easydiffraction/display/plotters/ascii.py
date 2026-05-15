# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
ASCII plotting backend.

Renders compact line charts in the terminal using ``asciichartpy``. This
backend is well suited for quick feedback in CLI environments and keeps
a consistent API with other plotters.
"""

from __future__ import annotations

import shutil

import asciichartpy
import numpy as np

from easydiffraction.display.plotters.base import DEFAULT_HEIGHT
from easydiffraction.display.plotters.base import SERIES_CONFIG
from easydiffraction.display.plotters.base import PlotterBase
from easydiffraction.display.plotters.base import PowderMeasVsCalcSpec
from easydiffraction.utils.logging import console

DEFAULT_COLORS = {
    'meas': asciichartpy.blue,
    'calc': asciichartpy.red,
    'posterior': asciichartpy.red,
    'density': asciichartpy.green,
    'resid': asciichartpy.green,
}
ASCII_CHART_OFFSET = 3
ASCII_CHART_LEFT_PADDING = 15
ASCII_CHART_FALLBACK_POINT_COUNT = 80
ASCII_CHART_MIN_POINT_COUNT = 2


class AsciiPlotter(PlotterBase):
    """Terminal-based plotter using ASCII art."""

    @staticmethod
    def _chart_point_count() -> int:
        """Return the number of points that fit the current terminal."""
        fallback_columns = (
            ASCII_CHART_FALLBACK_POINT_COUNT + ASCII_CHART_OFFSET + ASCII_CHART_LEFT_PADDING
        )
        columns = shutil.get_terminal_size(fallback=(fallback_columns, DEFAULT_HEIGHT)).columns
        return max(
            ASCII_CHART_MIN_POINT_COUNT,
            columns - ASCII_CHART_OFFSET - ASCII_CHART_LEFT_PADDING,
        )

    @classmethod
    def _resample_series_for_chart(
        cls,
        y_series: object,
    ) -> list[list[float]]:
        """Return y-series resampled to the available chart width."""
        target_point_count = cls._chart_point_count()
        resampled_series: list[list[float]] = []
        for series in y_series:
            series_array = np.ravel(np.asarray(series, dtype=float))
            if (
                series_array.size <= target_point_count
                or series_array.size < ASCII_CHART_MIN_POINT_COUNT
            ):
                resampled_series.append(series_array.tolist())
                continue

            source_positions = np.linspace(0.0, 1.0, series_array.size)
            target_positions = np.linspace(0.0, 1.0, target_point_count)
            resampled_series.append(
                np.interp(target_positions, source_positions, series_array).tolist()
            )
        return resampled_series

    @staticmethod
    def _get_legend_item(label: str) -> str:
        """
        Return a colored legend entry for a given series label.

        The legend uses a colored line matching the series color and the
        human-readable name from :data:`SERIES_CONFIG`.

        Parameters
        ----------
        label : str
            Series identifier (e.g., ``'meas'``).

        Returns
        -------
        str
            A formatted legend string with color escapes.
        """
        color_start = DEFAULT_COLORS[label]
        color_end = asciichartpy.reset
        line = '────'
        name = SERIES_CONFIG[label]['name']
        return f'{color_start}{line}{color_end} {name}'

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
        against an x-axis variable (2θ, TOF, d-spacing). Uses ASCII
        characters for terminal display.

        Parameters
        ----------
        x : object
            1D array-like of x values (only used for range display).
        y_series : object
            Sequence of y arrays to plot.
        labels : object
            Series identifiers corresponding to y_series.
        axes_labels : object
            Ignored; kept for API compatibility.
        title : str
            Figure title printed above the chart.
        height : int | None, default=None
            Number of text rows to allocate for the chart.
        excluded_ranges : tuple[tuple[float, float], ...], default=()
            Excluded x-ranges to print below the selected x-range.
        """
        # Intentionally unused; kept for a consistent display API
        del axes_labels
        legend = '\n'.join([self._get_legend_item(label) for label in labels])

        if height is None:
            height = DEFAULT_HEIGHT
        colors = [DEFAULT_COLORS[label] for label in labels]
        config = {
            'height': height,
            'colors': colors,
            'offset': ASCII_CHART_OFFSET,
        }
        y_series = self._resample_series_for_chart(y_series)

        chart = asciichartpy.plot(y_series, config)

        console.paragraph(f'{title}')  # TODO: f''?
        console.print(
            f'Displaying data for selected x-range from {x[0]} to {x[-1]} ({len(x)} points)'
        )
        if excluded_ranges:
            formatted_ranges = ', '.join(
                f'[{start:,.2f}, {end:,.2f}]' for start, end in excluded_ranges
            )
            console.print(f'Excluded regions: {formatted_ranges}')
        console.print(f'Legend:\n{legend}')

        padded = '\n'.join(' ' + line for line in chart.splitlines())

        print(padded)

    def plot_powder_meas_vs_calc(
        self,
        plot_spec: PowderMeasVsCalcSpec,
    ) -> None:
        """
        Render a composite powder plot in the terminal.

        The ASCII backend falls back to the existing single-chart view
        for measured, calculated, and residual series. Bragg tick rows
        are announced but not rendered graphically.
        """
        y_series = [plot_spec.y_meas, plot_spec.y_calc]
        labels = ['meas', 'calc']
        if plot_spec.y_resid is not None:
            y_series.append(plot_spec.y_resid)
            labels.append('resid')

        self.plot_powder(
            x=plot_spec.x,
            y_series=y_series,
            labels=labels,
            axes_labels=plot_spec.axes_labels,
            title=plot_spec.title,
            height=plot_spec.height,
            excluded_ranges=plot_spec.excluded_ranges,
        )
        if plot_spec.predictive_lower_95 is not None and plot_spec.predictive_upper_95 is not None:
            console.print('Posterior predictive bands are available with the Plotly engine only.')
        if plot_spec.bragg_tick_sets:
            console.print('Bragg peak subplot rows are available with the Plotly engine only.')

    @staticmethod
    def plot_single_crystal(
        x_calc: object,
        y_meas: object,
        y_meas_su: object,
        axes_labels: object,
        title: str,
        height: int | None = None,
    ) -> None:
        """
        Render a scatter plot for single crystal diffraction data.

        Creates an ASCII scatter plot showing measured vs calculated
        values with a diagonal reference line.

        Parameters
        ----------
        x_calc : object
            1D array-like of calculated values (x-axis).
        y_meas : object
            1D array-like of measured values (y-axis).
        y_meas_su : object
            1D array-like of measurement uncertainties (ignored in ASCII
            mode).
        axes_labels : object
            Pair of strings for the x and y titles.
        title : str
            Figure title.
        height : int | None, default=None
            Number of text rows for the chart (default: 15).
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

    @staticmethod
    def plot_scatter(
        x: object,
        y: object,
        sy: object,
        axes_labels: object,
        title: str,
        height: int | None = None,
    ) -> None:
        """Render a scatter plot with error bars in ASCII."""
        _ = x, sy  # ASCII backend does not use x ticks or error bars

        if height is None:
            height = DEFAULT_HEIGHT

        config = {'height': height, 'colors': [asciichartpy.blue]}
        chart = asciichartpy.plot([list(y)], config)

        console.paragraph(f'{title}')
        console.print(f'{axes_labels[1]} vs {axes_labels[0]}')
        padded = '\n'.join(' ' + line for line in chart.splitlines())
        print(padded)
