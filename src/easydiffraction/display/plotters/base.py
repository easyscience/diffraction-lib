# SPDX-FileCopyrightText: 2021-2026 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Abstract base and shared constants for plotting backends."""

from abc import ABC
from abc import abstractmethod

import numpy as np

from easydiffraction.experiments.experiment.enums import BeamModeEnum
from easydiffraction.experiments.experiment.enums import ScatteringTypeEnum

DEFAULT_HEIGHT = 25
DEFAULT_MIN = -np.inf
DEFAULT_MAX = np.inf

DEFAULT_AXES_LABELS = {
    (ScatteringTypeEnum.BRAGG, BeamModeEnum.CONSTANT_WAVELENGTH): [
        '2θ (degree)',
        'Intensity (arb. units)',
    ],
    (ScatteringTypeEnum.BRAGG, BeamModeEnum.TIME_OF_FLIGHT): [
        'TOF (µs)',
        'Intensity (arb. units)',
    ],
    (ScatteringTypeEnum.BRAGG, 'd-spacing'): [
        'd (Å)',
        'Intensity (arb. units)',
    ],
    (ScatteringTypeEnum.TOTAL, BeamModeEnum.CONSTANT_WAVELENGTH): [
        'r (Å)',
        'G(r) (Å)',
    ],
    (ScatteringTypeEnum.TOTAL, BeamModeEnum.TIME_OF_FLIGHT): [
        'r (Å)',
        'G(r) (Å)',
    ],
}

SERIES_CONFIG = dict(
    calc=dict(
        mode='lines',
        name='Total calculated (Icalc)',
    ),
    meas=dict(
        mode='lines+markers',
        name='Measured (Imeas)',
    ),
    resid=dict(
        mode='lines',
        name='Residual (Imeas - Icalc)',
    ),
)


class PlotterBase(ABC):
    """Abstract base for plotting backends.

    Implementations accept x values, multiple y-series, optional labels
    and render a plot to the chosen medium.

    Two main plot types are supported:
    - ``plot_pattern``: Line plots for powder diffraction patterns
      (intensity vs. 2θ/TOF/d-spacing).
    - ``plot_scatter_comparison``: Scatter plots comparing measured vs.
      calculated values (e.g., F²meas vs F²calc for single crystal).
    """

    @abstractmethod
    def plot_pattern(
        self,
        x,
        y_series,
        labels,
        axes_labels,
        title,
        height,
    ):
        """Render a pattern line plot.

        Suitable for powder diffraction data where intensity is plotted
        against an x-axis variable (2θ, TOF, d-spacing).

        Args:
            x: 1D array of x-axis values.
            y_series: Sequence of y arrays to plot.
            labels: Identifiers corresponding to y_series.
            axes_labels: Pair of strings for the x and y titles.
            title: Figure title.
            height: Backend-specific height (text rows or pixels).
        """
        pass

    @abstractmethod
    def plot_scatter_comparison(
        self,
        x_calc,
        y_meas,
        y_meas_su,
        axes_labels,
        title,
        height,
    ):
        """Render a scatter comparison plot.

        Suitable for single crystal data where measured values are
        plotted against calculated values with error bars.

        Args:
            x_calc: 1D array of calculated values (x-axis).
            y_meas: 1D array of measured values (y-axis).
            y_meas_su: 1D array of measurement uncertainties.
            axes_labels: Pair of strings for the x and y titles.
            title: Figure title.
            height: Backend-specific height (text rows or pixels).
        """
        pass

    def plot(
        self,
        x,
        y_series,
        labels,
        axes_labels,
        title,
        height,
    ):
        """Render a pattern plot (backward-compatible alias).

        .. deprecated::
            Use :meth:`plot_pattern` instead.

        Args:
            x: 1D array of x-axis values.
            y_series: Sequence of y arrays to plot.
            labels: Identifiers corresponding to y_series.
            axes_labels: Pair of strings for the x and y titles.
            title: Figure title.
            height: Backend-specific height (text rows or pixels).
        """
        return self.plot_pattern(x, y_series, labels, axes_labels, title, height)
