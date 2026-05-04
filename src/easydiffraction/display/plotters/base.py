# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Abstract base and shared constants for plotting backends."""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from enum import StrEnum

import numpy as np

from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum

DEFAULT_HEIGHT = 25
DEFAULT_MIN = -np.inf
DEFAULT_MAX = np.inf


@dataclass(frozen=True)
class BraggTickSet:
    """
    Bragg tick data for one linked phase row.

    The plotting facade converts experiment reflection-category data
    into this display-specific container so plotting backends stay
    decoupled from experiment datablock internals.
    """

    phase_id: str
    x: np.ndarray
    h: np.ndarray
    k: np.ndarray
    ell: np.ndarray
    f_squared_calc: np.ndarray
    f_calc: np.ndarray


@dataclass(frozen=True)
class PowderMeasVsCalcSpec:
    """
    Specification for one composite powder plot.

    The plotting facade assembles the measured, calculated, residual,
    and Bragg-tick data into this display-specific object before
    delegating to a backend.
    """

    x: np.ndarray
    y_meas: np.ndarray
    y_calc: np.ndarray
    y_resid: np.ndarray | None
    bragg_tick_sets: tuple[BraggTickSet, ...]
    axes_labels: list[str]
    title: str
    residual_height_fraction: float
    bragg_peaks_height_fraction: float
    height: int | None = None


class XAxisType(StrEnum):
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
        'TOF (μs)',
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

SERIES_CONFIG = {
    'calc': {
        'mode': 'lines',
        'name': 'Total calculated (Icalc)',
    },
    'meas': {
        'mode': 'lines+markers',
        'name': 'Measured (Imeas)',
    },
    'resid': {
        'mode': 'lines',
        'name': 'Residual (Imeas - Icalc)',
    },
}


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

    _supports_graphical_heatmap: bool = False

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

    @abstractmethod
    def plot_powder_meas_vs_calc(
        self,
        plot_spec: PowderMeasVsCalcSpec,
    ) -> None:
        """
        Render a composite powder plot with Bragg ticks and residual.

        Parameters
        ----------
        plot_spec : PowderMeasVsCalcSpec
            Composite powder-plot inputs and layout settings.
        """

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

    def plot_correlation_heatmap(
        self,
        corr_df: object,
        title: str,
        threshold: float | None,
        precision: int,
    ) -> None:
        """
        Render a graphical heatmap for a correlation matrix.

        The default implementation does nothing. Graphical backends
        (e.g. Plotly) override this method and set
        ``_supports_graphical_heatmap = True`` so the facade knows a
        heatmap was rendered.

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
        # Intentionally unused; accepted for API compatibility with
        # graphical backends that override this method.
        _ = self._supports_graphical_heatmap
        del corr_df, title, threshold, precision
