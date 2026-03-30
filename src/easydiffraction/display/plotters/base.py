# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Abstract base and shared constants for plotting backends."""

from abc import ABC
from abc import abstractmethod
from enum import Enum

import numpy as np

from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum

DEFAULT_HEIGHT = 25
DEFAULT_MIN = -np.inf
DEFAULT_MAX = np.inf


class XAxisType(str, Enum):
    """
    X-axis types for diffraction plots.

    Values match attribute names in data models for direct use with
    ``getattr(pattern, x_axis)``.
    """

    TWO_THETA = 'two_theta'
    TIME_OF_FLIGHT = 'time_of_flight'
    R = 'x'

    INTENSITY_CALC = 'intensity_calc'

    D_SPACING = 'd_spacing'
    SIN_THETA_OVER_LAMBDA = 'sin_theta_over_lambda'


# Map (SampleFormEnum, ScatteringTypeEnum, BeamModeEnum) to default
# x-axis type
DEFAULT_X_AXIS = {
    # Powder Bragg diffraction
    (
        SampleFormEnum.POWDER,
        ScatteringTypeEnum.BRAGG,
        BeamModeEnum.CONSTANT_WAVELENGTH,
    ): XAxisType.TWO_THETA,
    (
        SampleFormEnum.POWDER,
        ScatteringTypeEnum.BRAGG,
        BeamModeEnum.TIME_OF_FLIGHT,
    ): XAxisType.TIME_OF_FLIGHT,
    # Powder total scattering (PDF) — always r-space
    (
        SampleFormEnum.POWDER,
        ScatteringTypeEnum.TOTAL,
        BeamModeEnum.CONSTANT_WAVELENGTH,
    ): XAxisType.R,
    (
        SampleFormEnum.POWDER,
        ScatteringTypeEnum.TOTAL,
        BeamModeEnum.TIME_OF_FLIGHT,
    ): XAxisType.R,
    # Single crystal Bragg diffraction
    (
        SampleFormEnum.SINGLE_CRYSTAL,
        ScatteringTypeEnum.BRAGG,
        BeamModeEnum.CONSTANT_WAVELENGTH,
    ): XAxisType.INTENSITY_CALC,
    (
        SampleFormEnum.SINGLE_CRYSTAL,
        ScatteringTypeEnum.BRAGG,
        BeamModeEnum.TIME_OF_FLIGHT,
    ): XAxisType.INTENSITY_CALC,
}

DEFAULT_AXES_LABELS = {
    # Powder Bragg diffraction
    (
        SampleFormEnum.POWDER,
        ScatteringTypeEnum.BRAGG,
        XAxisType.TWO_THETA,
    ): [
        '2θ (degree)',
        'Intensity (arb. units)',
    ],
    (
        SampleFormEnum.POWDER,
        ScatteringTypeEnum.BRAGG,
        XAxisType.TIME_OF_FLIGHT,
    ): [
        'TOF (µs)',
        'Intensity (arb. units)',
    ],
    (
        SampleFormEnum.POWDER,
        ScatteringTypeEnum.BRAGG,
        XAxisType.D_SPACING,
    ): [
        'd (Å)',
        'Intensity (arb. units)',
    ],
    # Powder total scattering (PDF)
    (
        SampleFormEnum.POWDER,
        ScatteringTypeEnum.TOTAL,
        XAxisType.R,
    ): [
        'r (Å)',
        'G(r) (Å)',
    ],
    # Single crystal Bragg diffraction
    (
        SampleFormEnum.SINGLE_CRYSTAL,
        ScatteringTypeEnum.BRAGG,
        XAxisType.INTENSITY_CALC,
    ): [
        'I²calc',
        'I²meas',
    ],
    (
        SampleFormEnum.SINGLE_CRYSTAL,
        ScatteringTypeEnum.BRAGG,
        XAxisType.D_SPACING,
    ): [
        'd (Å)',
        'Intensity (arb. units)',
    ],
    (
        SampleFormEnum.SINGLE_CRYSTAL,
        ScatteringTypeEnum.BRAGG,
        XAxisType.SIN_THETA_OVER_LAMBDA,
    ): [
        'sin(θ)/λ (Å⁻¹)',
        'Intensity (arb. units)',
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
    """
    Abstract base for plotting backends.

    Implementations accept x values, multiple y-series, optional labels
    and render a plot to the chosen medium.

    Two main plot types are supported: - ``plot_powder``: Line plots for
    powder diffraction patterns   (intensity vs. 2θ/TOF/d-spacing). -
    ``plot_single_crystal``: Scatter plots comparing measured vs.
    calculated values (e.g., F²meas vs F²calc for single crystal).
    """

    @abstractmethod
    def plot_powder(
        self,
        x: object,
        y_series: object,
        labels: object,
        axes_labels: object,
        title: str,
        height: int | None,
    ) -> None:
        """
        Render a line plot for powder diffraction data.

        Suitable for powder diffraction data where intensity is plotted
        against an x-axis variable (2θ, TOF, d-spacing).

        Parameters
        ----------
        x : object
            1D array of x-axis values.
        y_series : object
            Sequence of y arrays to plot.
        labels : object
            Identifiers corresponding to y_series.
        axes_labels : object
            Pair of strings for the x and y titles.
        title : str
            Figure title.
        height : int | None
            Backend-specific height (text rows or pixels).
        """
        pass

    @abstractmethod
    def plot_single_crystal(
        self,
        x_calc: object,
        y_meas: object,
        y_meas_su: object,
        axes_labels: object,
        title: str,
        height: int | None,
    ) -> None:
        """
        Render a scatter plot for single crystal diffraction data.

        Suitable for single crystal diffraction data where measured
        values are plotted against calculated values with error bars.

        Parameters
        ----------
        x_calc : object
            1D array of calculated values (x-axis).
        y_meas : object
            1D array of measured values (y-axis).
        y_meas_su : object
            1D array of measurement uncertainties.
        axes_labels : object
            Pair of strings for the x and y titles.
        title : str
            Figure title.
        height : int | None
            Backend-specific height (text rows or pixels).
        """
        pass

    @abstractmethod
    def plot_scatter(
        self,
        x: object,
        y: object,
        sy: object,
        axes_labels: object,
        title: str,
        height: int | None,
    ) -> None:
        """
        Render a scatter plot with error bars.

        Parameters
        ----------
        x : object
            1-D array of x-axis values.
        y : object
            1-D array of y-axis values.
        sy : object
            1-D array of y uncertainties.
        axes_labels : object
            Pair of strings for x and y axis titles.
        title : str
            Figure title.
        height : int | None
            Backend-specific height (text rows or pixels).
        """
        pass
