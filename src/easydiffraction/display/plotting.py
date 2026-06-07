# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
Plotting facade for measured and calculated patterns.

Uses the common :class:`RendererBase` so plotters and tablers share a
consistent configuration surface and engine handling.
"""

from __future__ import annotations

import pathlib
from dataclasses import dataclass
from enum import StrEnum

import numpy as np
import pandas as pd

from easydiffraction.analysis.enums import FitCorrelationSourceEnum
from easydiffraction.analysis.enums import FitResultKindEnum
from easydiffraction.analysis.fit_helpers.bayesian import PosteriorPredictiveSummary
from easydiffraction.analysis.fit_helpers.bayesian import posterior_predictive_cache_key
from easydiffraction.datablocks.experiment.item.base import intensity_category_for
from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum
from easydiffraction.display.base import RendererBase
from easydiffraction.display.base import RendererFactoryBase
from easydiffraction.display.plotters.ascii import AsciiPlotter
from easydiffraction.display.plotters.base import DEFAULT_AXES_LABELS
from easydiffraction.display.plotters.base import DEFAULT_HEIGHT
from easydiffraction.display.plotters.base import DEFAULT_MAX
from easydiffraction.display.plotters.base import DEFAULT_MIN
from easydiffraction.display.plotters.base import DEFAULT_RESIDUAL_HEIGHT_FRACTION
from easydiffraction.display.plotters.base import DEFAULT_X_AXIS
from easydiffraction.display.plotters.base import BraggTickSet
from easydiffraction.display.plotters.base import PowderMeasVsCalcSpec
from easydiffraction.display.plotters.base import XAxisType
from easydiffraction.display.plotters.plotly import (
    AXIS_TITLE_FONT_SIZE as PLOTLY_AXIS_TITLE_FONT_SIZE,
)
from easydiffraction.display.plotters.plotly import TITLE_FONT_SIZE as PLOTLY_TITLE_FONT_SIZE
from easydiffraction.display.plotters.plotly import PlotlyPlotter
from easydiffraction.display.tables import TableRenderer
from easydiffraction.utils.environment import in_jupyter
from easydiffraction.utils.logging import console
from easydiffraction.utils.logging import log
from easydiffraction.utils.utils import tof_to_d
from easydiffraction.utils.utils import twotheta_to_d


class PlotterEngineEnum(StrEnum):
    """Available plotting engine backends."""

    ASCII = 'asciichartpy'
    PLOTLY = 'plotly'

    @classmethod
    def default(cls) -> PlotterEngineEnum:
        """Select default engine based on environment."""
        if in_jupyter():
            log.debug('Setting default plotting engine to Plotly for Jupyter')
            return cls.PLOTLY
        log.debug('Setting default plotting engine to Asciichartpy for console')
        return cls.ASCII

    def description(self) -> str:
        """Human-readable description for UI listings."""
        if self is PlotterEngineEnum.ASCII:
            return 'Console ASCII line charts'
        if self is PlotterEngineEnum.PLOTLY:
            return 'Interactive browser-based graphing library'
        return ''


class PosteriorPairPlotStyleEnum(StrEnum):
    """Available posterior pair-plot rendering modes."""

    AUTO = 'auto'
    FAST = 'fast'
    FULL = 'full'


DEFAULT_CORRELATION_THRESHOLD: float | None = None
DEFAULT_CORRELATION_MAX_PARAMETERS = 6
EXPECTED_COVAR_NDIM = 2
DEFAULT_BRAGG_PEAKS_HEIGHT_FRACTION = 0.10
DEFAULT_RESID_HEIGHT = DEFAULT_RESIDUAL_HEIGHT_FRACTION
DEFAULT_BRAGG_ROW = DEFAULT_BRAGG_PEAKS_HEIGHT_FRACTION
DEFAULT_POSTERIOR_PREDICTIVE_DRAWS = 50
DEFAULT_POSTERIOR_PREDICTIVE_DRAW_PLOT_CAP = 50
FULL_POSTERIOR_PAIR_COVARIANCE_RANK = 2
POSTERIOR_FLATTENED_SAMPLE_NDIM = 2
MIN_POSTERIOR_PARAMETER_COUNT = 2
MIN_POSTERIOR_SAMPLE_COUNT = 2
PAIR_DENSITY_SURFACE_NDIM = 2
POSTERIOR_DENSITY_LINE_COLOR = 'rgb(99, 110, 250)'
POSTERIOR_DENSITY_FILL_COLOR = 'rgba(99, 110, 250, 0.22)'
POSTERIOR_PAIR_MARGINAL_DENSITY_LINE_COLOR = 'rgb(44, 160, 44)'
POSTERIOR_PAIR_MARGINAL_DENSITY_FILL_COLOR = 'rgba(44, 160, 44, 0.22)'
POSTERIOR_PAIR_MARGINAL_DENSITY_LINE_WIDTH = 1
POSTERIOR_HISTOGRAM_FILL_COLOR = 'rgba(120, 120, 120, 0.38)'
POSTERIOR_HISTOGRAM_LINE_COLOR = 'rgba(120, 120, 120, 0.24)'
POSTERIOR_INTERVAL_95_FILL_COLOR = 'rgba(214, 39, 40, 0.14)'
POSTERIOR_MEDIAN_LINE_COLOR = 'rgb(80, 80, 80)'
POSTERIOR_POINT_ESTIMATE_LINE_COLOR = 'rgb(214, 39, 40)'
POSTERIOR_POINT_ESTIMATE_TRACE_NAME = 'Best posterior sample'
POSTERIOR_POINT_ESTIMATE_LINE_DASH = 'dot'
POSTERIOR_PREDICTIVE_INTERVAL_TRACE_NAME = '95% credible interval'
POSTERIOR_DRAW_LINE_COLOR = 'rgba(140, 140, 140, 0.18)'
POSTERIOR_SCATTER_MARKER_COLOR = 'rgba(140, 140, 140, 0.20)'
POSTERIOR_CONTOUR_FILL_COLORSCALE = [
    [0.0, 'rgba(224, 233, 255, 0.62)'],
    [0.35, 'rgba(183, 203, 255, 0.70)'],
    [0.60, 'rgba(138, 169, 252, 0.78)'],
    [0.82, 'rgba(96, 131, 242, 0.84)'],
    [1.0, 'rgba(58, 86, 224, 0.90)'],
]
POSTERIOR_NEGATIVE_CONTOUR_FILL_COLORSCALE = [
    [0.0, 'rgba(255, 224, 224, 0.62)'],
    [0.35, 'rgba(250, 188, 188, 0.70)'],
    [0.60, 'rgba(245, 148, 148, 0.78)'],
    [0.82, 'rgba(237, 104, 104, 0.84)'],
    [1.0, 'rgba(215, 48, 39, 0.90)'],
]
POSTERIOR_CONTOUR_LINE_COLORSCALE = [
    [0.0, 'rgba(183, 203, 255, 0.94)'],
    [0.35, 'rgba(183, 203, 255, 0.94)'],
    [0.35, 'rgba(138, 169, 252, 0.95)'],
    [0.60, 'rgba(138, 169, 252, 0.95)'],
    [0.60, 'rgba(96, 131, 242, 0.96)'],
    [0.82, 'rgba(96, 131, 242, 0.96)'],
    [0.82, 'rgba(58, 86, 224, 0.98)'],
    [1.0, 'rgba(58, 86, 224, 0.98)'],
]
POSTERIOR_NEGATIVE_CONTOUR_LINE_COLORSCALE = [
    [0.0, 'rgba(250, 188, 188, 0.94)'],
    [0.35, 'rgba(250, 188, 188, 0.94)'],
    [0.35, 'rgba(245, 148, 148, 0.95)'],
    [0.60, 'rgba(245, 148, 148, 0.95)'],
    [0.60, 'rgba(237, 104, 104, 0.96)'],
    [0.82, 'rgba(237, 104, 104, 0.96)'],
    [0.82, 'rgba(215, 48, 39, 0.98)'],
    [1.0, 'rgba(215, 48, 39, 0.98)'],
]
POSTERIOR_PAIR_SCATTER_MAX_POINTS = 750  # keep embedded pair scatter small
POSTERIOR_PAIR_MAX_DENSITY_SAMPLES = 4000
POSTERIOR_PAIR_MIN_DENSITY_SAMPLES = 800
POSTERIOR_PAIR_TARGET_DENSITY_SAMPLE_BUDGET = 24000
POSTERIOR_PAIR_MAX_CONTOUR_GRID_SIZE = 96
POSTERIOR_PAIR_MIN_CONTOUR_GRID_SIZE = 56
POSTERIOR_PAIR_TARGET_CONTOUR_GRID_POINT_BUDGET = 73728
POSTERIOR_PAIR_AUTO_MAX_CONTOUR_PARAMETERS = 6
PAIR_PLOT_CELL_SIZE_PIXELS = 190
PAIR_PLOT_MIN_CELL_SIZE_PIXELS = 90
PAIR_PLOT_MIN_SIZE_PIXELS = 680
PAIR_PLOT_MARGIN_PIXELS = 120
PAIR_PLOT_ESTIMATED_CONTAINER_WIDTH_PIXELS = 980
PAIR_PLOT_SUBPLOT_SPACING = 0.01
POSTERIOR_PAIR_AXIS_LINE_WIDTH = 1.2
POSTERIOR_PAIR_AXIS_TITLE_FONT_SIZE = PLOTLY_AXIS_TITLE_FONT_SIZE
POSTERIOR_PAIR_TITLE_FONT_SIZE = PLOTLY_TITLE_FONT_SIZE
POSTERIOR_PAIR_Y_TITLE_XSHIFT_PIXELS = 16
POSTERIOR_PAIR_X_TITLE_YSHIFT_PIXELS = 10
SQUARE_MATRIX_TITLE_YSHIFT_PIXELS = 12
POSTERIOR_PAIR_GUIDE_LINE_COLOR = 'rgba(125, 140, 173, 0.18)'
SQUARE_MATRIX_FIXED_ASPECT_RATIO = '1 / 1'
SQUARE_MATRIX_FIXED_ASPECT_META_KEY = 'fixed_aspect_wrapper'
SQUARE_MATRIX_LEFT_MARGIN_PIXELS = 40
SQUARE_MATRIX_RIGHT_MARGIN_PIXELS = 24
SQUARE_MATRIX_TOP_MARGIN_PIXELS = 40
SQUARE_MATRIX_BOTTOM_MARGIN_PIXELS = 40
SQUARE_MATRIX_AXIS_TITLE_LINE_HEIGHT_PIXELS = 18
SQUARE_MATRIX_TITLE_LEFT_PADDING_PIXELS = 14
# Correlation-matrix cells are sized to roughly this many label-font
# characters; the factor approximates one glyph's width per font pixel
# for Plotly's default sans-serif axis labels.
CORRELATION_CELL_LABEL_CHAR_COUNT = 16
CORRELATION_LABEL_CHAR_WIDTH_FACTOR = 0.6
POSTERIOR_PAIR_SAMPLE_MARKER_SIZE = 6


@dataclass(frozen=True)
class _MeasVsCalcPlotOptions:
    """Internal options for a measured-vs-calculated plot request."""

    x_min: float | None = None
    x_max: float | None = None
    show_residual: bool | None = None
    show_background: bool | None = None
    show_bragg: bool | None = None
    show_excluded: bool = False
    x: object | None = None


@dataclass(frozen=True)
class _PowderMeasVsCalcSeries:
    """Filtered y-series for a composite powder plot."""

    y_meas: np.ndarray
    y_calc: np.ndarray
    y_meas_su: np.ndarray | None = None
    y_bkg: np.ndarray | None = None


@dataclass(frozen=True)
class _PosteriorDistributionContext:
    """Inputs needed to build a posterior distribution plot."""

    fit_results: object
    parameter_name: str
    values: np.ndarray
    label: str
    title: str
    summary: object | None


@dataclass(frozen=True)
class _PosteriorPairsContext:
    """Inputs needed to build a posterior pair plot."""

    fit_results: object
    parameter_names: list[str]
    labels: list[str]
    annotation_labels: list[str]
    title: str
    marginal_density_samples: np.ndarray
    density_samples: np.ndarray
    scatter_samples: np.ndarray
    show_contours: bool
    contour_grid_size: int
    axis_frame_color: str
    axis_ranges: list[tuple[float, float]]

    @property
    def n_parameters(self) -> int:
        """Return the number of plotted parameters."""
        return len(self.parameter_names)


@dataclass(frozen=True)
class _CorrelationHeatmapContext:
    """Inputs needed to build a correlation matrix plot."""

    corr_df: pd.DataFrame
    row_labels: list[str]
    col_labels: list[str]
    threshold: float | None
    precision: int

    @property
    def n_rows(self) -> int:
        """Return the number of displayed rows."""
        return self.corr_df.shape[0]

    @property
    def n_cols(self) -> int:
        """Return the number of displayed columns."""
        return self.corr_df.shape[1]


@dataclass(slots=True)
class _PosteriorPairsLegendState:
    """Legend-visibility state for posterior pair plots."""

    show_density: bool = True
    show_scatter: bool = True
    show_contour: bool = True


class Plotter(RendererBase):
    """User-facing plotting facade backed by concrete plotters."""

    # ------------------------------------------------------------------
    #  Private special methods
    # ------------------------------------------------------------------

    def __init__(self) -> None:
        super().__init__()
        # X-axis limits
        self._x_min = DEFAULT_MIN
        self._x_max = DEFAULT_MAX
        # Chart height
        self._height = DEFAULT_HEIGHT
        self._height_is_explicit = False
        # Back-reference to the owning Project (set via _set_project)
        self._project = None

    # ------------------------------------------------------------------
    #  Private class methods
    # ------------------------------------------------------------------

    def _set_project(self, project: object) -> None:
        """Wire the owning project for high-level plot methods."""
        self._project = project

    def _update_project_categories(self, expt_name: str) -> None:
        """Update all project categories before plotting."""
        for structure in self._project.structures:
            structure._update_categories()
        self._project.analysis._update_categories()
        experiment = self._project.experiments[expt_name]
        experiment._update_categories()

    @classmethod
    def _factory(cls) -> type[RendererFactoryBase]:  # type: ignore[override]
        return PlotterFactory

    @classmethod
    def _default_engine(cls) -> str:
        return PlotterEngineEnum.default().value

    # ------------------------------------------------------------------
    #  Private helper methods
    # ------------------------------------------------------------------

    def _auto_x_range_for_ascii(
        self,
        pattern: object,
        x_array: object,
        x_min: object,
        x_max: object,
    ) -> tuple:
        """
        For the ASCII engine, narrow the range around the tallest peak.

        Parameters
        ----------
        pattern : object
            Data pattern object (needs ``intensity_meas``).
        x_array : object
            Full x-axis array.
        x_min : object
            Current minimum (may be ``None``).
        x_max : object
            Current maximum (may be ``None``).

        Returns
        -------
        tuple
            Tuple of ``(x_min, x_max)``, possibly narrowed.
        """
        if (
            self._engine == 'asciichartpy'
            and x_min is None
            and x_max is None
            and AsciiPlotter._should_crop_to_peak_window(len(x_array))
        ):
            max_intensity_pos = int(np.argmax(pattern.intensity_meas))
            target_point_count = min(len(x_array), AsciiPlotter._chart_point_count())
            start = max(0, max_intensity_pos - target_point_count // 2)
            end = min(len(x_array) - 1, start + target_point_count - 1)
            start = max(0, end - target_point_count + 1)
            x_min = x_array[start]
            x_max = x_array[end]
        return x_min, x_max

    def _filtered_y_array(
        self,
        y_array: object,
        x_array: object,
        x_min: object,
        x_max: object,
    ) -> object:
        """
        Filter an array by the inclusive x-range limits.

        Parameters
        ----------
        y_array : object
            1D array-like of y values.
        x_array : object
            1D array-like of x values (same length as ``y_array``).
        x_min : object
            Minimum x limit (or ``None`` to use default).
        x_max : object
            Maximum x limit (or ``None`` to use default).

        Returns
        -------
        object
            Filtered ``y_array`` values where ``x_array`` lies within
            ``[x_min, x_max]``.
        """
        if x_min is None:
            x_min = self.x_min
        if x_max is None:
            x_max = self.x_max

        lower_bound = min(x_min, x_max)
        upper_bound = max(x_min, x_max)
        mask = (x_array >= lower_bound) & (x_array <= upper_bound)
        return y_array[mask]

    def _filtered_optional_y_array(
        self,
        y_array: object | None,
        x_array: object,
        x_min: object,
        x_max: object,
    ) -> object | None:
        """Filter an optional y-array by inclusive x-range limits."""
        if y_array is None:
            return None
        return self._filtered_y_array(y_array, x_array, x_min, x_max)

    @staticmethod
    def _get_axes_labels(
        sample_form: object,
        scattering_type: object,
        x_axis: object,
    ) -> list:
        """Look up axis labels for the experiment / x-axis."""
        return DEFAULT_AXES_LABELS[sample_form, scattering_type, x_axis]

    def _prepare_powder_context(
        self,
        pattern: object,
        expt_name: str,
        expt_type: object,
        x_min: object,
        x_max: object,
        x: object,
    ) -> dict | None:
        """
        Resolve axes, auto-range, and filter x-array.

        Parameters
        ----------
        pattern : object
            Data pattern object with intensity arrays.
        expt_name : str
            Experiment name for error messages.
        expt_type : object
            Experiment type with sample_form, scattering, and beam
            enums.
        x_min : object
            Optional minimum x-axis limit.
        x_max : object
            Optional maximum x-axis limit.
        x : object
            Explicit x-axis type or ``None``.

        Returns
        -------
        dict | None
            A dict with keys ``x_filtered``, ``x_array``, ``x_min``,
            ``x_max``, and ``axes_labels``; or ``None`` when the x-array
            is missing.
        """
        x_axis, x_name, sample_form, scattering_type, _ = self._resolve_x_axis(expt_type, x)

        # Get x-array from pattern
        x_raw = getattr(pattern, x_axis, None)
        if x_raw is None:
            log.error(f'No {x_name} data available for experiment {expt_name}')
            return None

        x_array = np.asarray(x_raw)

        # Auto-range for ASCII engine
        x_min, x_max = self._auto_x_range_for_ascii(pattern, x_array, x_min, x_max)

        # Filter x
        x_filtered = self._filtered_y_array(x_array, x_array, x_min, x_max)
        resolved_x_min = self.x_min if x_min is None else float(x_min)
        resolved_x_max = self.x_max if x_max is None else float(x_max)
        if x_filtered.size > 0:
            if x_min is None:
                resolved_x_min = float(np.min(x_filtered))
            if x_max is None:
                resolved_x_max = float(np.max(x_filtered))

        axes_labels = self._get_axes_labels(sample_form, scattering_type, x_axis)

        return {
            'x_filtered': x_filtered,
            'x_array': x_array,
            'x_min': resolved_x_min,
            'x_max': resolved_x_max,
            'x_axis': x_axis,
            'axes_labels': axes_labels,
        }

    @staticmethod
    def _resolve_x_axis(expt_type: object, x: object) -> tuple:
        """
        Determine the x-axis type from experiment metadata.

        Parameters
        ----------
        expt_type : object
            Experiment type with sample_form, scattering_type, and
            beam_mode enums.
        x : object
            Explicit x-axis type or ``None`` to auto-detect.

        Returns
        -------
        tuple
            Tuple of ``(x_axis, x_name, sample_form, scattering_type,
            beam_mode)``.
        """
        sample_form = expt_type.sample_form.value
        scattering_type = expt_type.scattering_type.value
        beam_mode = expt_type.beam_mode.value
        x_axis = DEFAULT_X_AXIS[sample_form, scattering_type, beam_mode] if x is None else x
        x_name = getattr(x_axis, 'value', x_axis)
        return x_axis, x_name, sample_form, scattering_type, beam_mode

    # ------------------------------------------------------------------
    #  Public properties
    # ------------------------------------------------------------------

    @property
    def x_min(self) -> float:
        """Minimum x-axis limit."""
        return self._x_min

    @x_min.setter
    def x_min(self, value: object) -> None:
        """
        Set the minimum x-axis limit.

        Parameters
        ----------
        value : object
            Minimum limit or ``None`` to reset to default.
        """
        if value is not None:
            self._x_min = value
        else:
            self._x_min = DEFAULT_MIN

    @property
    def x_max(self) -> float:
        """Maximum x-axis limit."""
        return self._x_max

    @x_max.setter
    def x_max(self, value: object) -> None:
        """
        Set the maximum x-axis limit.

        Parameters
        ----------
        value : object
            Maximum limit or ``None`` to reset to default.
        """
        if value is not None:
            self._x_max = value
        else:
            self._x_max = DEFAULT_MAX

    @property
    def height(self) -> int:
        """Plot height (rows for ASCII, pixels for Plotly)."""
        return self._height

    @height.setter
    def height(self, value: object) -> None:
        """
        Set plot height.

        Parameters
        ----------
        value : object
            Height value or ``None`` to reset to default.
        """
        if value is not None:
            self._height = value
            self._height_is_explicit = True
        else:
            self._height = DEFAULT_HEIGHT
            self._height_is_explicit = False

    def _composite_plot_height(self) -> int | None:
        """Return explicit composite height or backend default."""
        if self._height_is_explicit:
            return self._height
        return None

    # ------------------------------------------------------------------
    #  Public methods
    # ------------------------------------------------------------------

    def show_config(self) -> None:
        """Display the current plotting configuration."""
        headers = [
            ('Parameter', 'left'),
            ('Value', 'left'),
        ]
        rows = [
            ['Plotting engine', self.engine],
            ['x-axis limits', f'[{self.x_min}, {self.x_max}]'],
            ['Chart height', self.height],
        ]
        df = pd.DataFrame(rows, columns=pd.MultiIndex.from_tuples(headers))
        console.paragraph('Current plotter configuration')
        TableRenderer.get().render(df)

    def plot_meas(
        self,
        expt_name: str,
        x_min: float | None = None,
        x_max: float | None = None,
        x: object | None = None,
        *,
        show_excluded: bool = False,
    ) -> None:
        """
        Plot measured diffraction data for an experiment.

        Parameters
        ----------
        expt_name : str
            Name of the experiment to plot.
        x_min : float | None, default=None
            Lower bound for the x-axis range.
        x_max : float | None, default=None
            Upper bound for the x-axis range.
        x : object | None, default=None
            Optional explicit x-axis data to override stored values.
        show_excluded : bool, default=False
            Whether to show excluded fitting regions on supported plots.
        """
        self._update_project_categories(expt_name)
        experiment = self._project.experiments[expt_name]
        plot_options = _MeasVsCalcPlotOptions(
            x_min=x_min,
            x_max=x_max,
            show_excluded=show_excluded,
            x=x,
        )
        self._plot_meas_data(
            experiment,
            intensity_category_for(experiment),
            expt_name,
            experiment.type,
            plot_options,
        )

    def plot_calc(
        self,
        expt_name: str,
        x_min: float | None = None,
        x_max: float | None = None,
        x: object | None = None,
        *,
        show_excluded: bool = False,
    ) -> None:
        """
        Plot calculated diffraction pattern for an experiment.

        Parameters
        ----------
        expt_name : str
            Name of the experiment to plot.
        x_min : float | None, default=None
            Lower bound for the x-axis range.
        x_max : float | None, default=None
            Upper bound for the x-axis range.
        x : object | None, default=None
            Optional explicit x-axis data to override stored values.
        show_excluded : bool, default=False
            Whether to show excluded fitting regions on supported plots.
        """
        self._update_project_categories(expt_name)
        experiment = self._project.experiments[expt_name]
        plot_options = _MeasVsCalcPlotOptions(
            x_min=x_min,
            x_max=x_max,
            show_excluded=show_excluded,
            x=x,
        )
        self._plot_calc_data(
            experiment,
            intensity_category_for(experiment),
            expt_name,
            experiment.type,
            plot_options,
        )

    def plot_meas_vs_calc(
        self,
        expt_name: str,
        x_min: float | None = None,
        x_max: float | None = None,
        *,
        show_residual: bool | None = None,
        show_excluded: bool = False,
        x: object | None = None,
    ) -> None:
        """
        Plot measured vs calculated data for an experiment.

        Parameters
        ----------
        expt_name : str
            Name of the experiment to plot.
        x_min : float | None, default=None
            Lower bound for the x-axis range.
        x_max : float | None, default=None
            Upper bound for the x-axis range.
        show_residual : bool | None, default=None
            When ``None``, powder Bragg plots include the residual by
            default while other measured-vs-calculated plots keep the
            historical no-residual default.
        show_excluded : bool, default=False
            Whether to show excluded fitting regions on supported plots.
        x : object | None, default=None
            Optional explicit x-axis data to override stored values.
        """
        plot_options = _MeasVsCalcPlotOptions(
            x_min=x_min,
            x_max=x_max,
            show_residual=show_residual,
            show_excluded=show_excluded,
            x=x,
        )
        self._plot_meas_vs_calc_request(expt_name=expt_name, plot_options=plot_options)

    def plot_calc_comparison(
        self,
        *,
        expt_name: str,
        reference: np.ndarray,
        candidate: np.ndarray,
        reference_label: str,
        candidate_label: str,
        annotation_lines: tuple[str, ...] = (),
        title: str | None = None,
    ) -> None:
        """
        Overlay two calculated patterns with a residual panel.

        The reference is drawn as a solid line and the candidate as
        markers, both peak-normalised so they overlay regardless of
        engine scale. A residual panel and an optional metrics
        annotation are included; Bragg ticks and background are
        intentionally omitted.

        Parameters
        ----------
        expt_name : str
            Experiment supplying the x grid and axis labels.
        reference : np.ndarray
            Reference intensities, drawn as a solid line.
        candidate : np.ndarray
            Candidate intensities, drawn as markers.
        reference_label : str
            Legend name for the reference curve.
        candidate_label : str
            Legend name for the candidate curve.
        annotation_lines : tuple[str, ...], default=()
            Lines for the top-left metrics annotation.
        title : str | None, default=None
            Optional plot title.

        Raises
        ------
        ValueError
            If ``reference``, ``candidate``, and the experiment x grid
            do not all have the same length.
        """
        self._update_project_categories(expt_name)
        experiment = self._project.experiments[expt_name]
        x_axis, _, sample_form, scattering_type, _ = self._resolve_x_axis(experiment.type, None)
        axes_labels = self._get_axes_labels(sample_form, scattering_type, x_axis)
        x = np.asarray(intensity_category_for(experiment).x, dtype=float)
        reference = np.asarray(reference, dtype=float)
        candidate = np.asarray(candidate, dtype=float)
        if not reference.shape == candidate.shape == x.shape:
            msg = (
                f"reference, candidate, and the '{expt_name}' x grid must have "
                f'the same length (got {reference.shape}, {candidate.shape}, '
                f'{x.shape}).'
            )
            raise ValueError(msg)

        reference_norm = self._peak_normalized(reference)
        candidate_norm = self._peak_normalized(candidate)
        plot_spec = PowderMeasVsCalcSpec(
            x=x,
            y_meas=reference_norm,
            y_calc=candidate_norm,
            y_resid=reference_norm - candidate_norm,
            bragg_tick_sets=(),
            axes_labels=axes_labels,
            title=title or f"Calculated pattern comparison for 🔬 '{expt_name}'",
            residual_height_fraction=DEFAULT_RESID_HEIGHT,
            bragg_peaks_height_fraction=DEFAULT_BRAGG_ROW,
            height=self._composite_plot_height(),
            y_calc_name=candidate_label,
            y_meas_name=reference_label,
        )
        if self.engine == PlotterEngineEnum.PLOTLY.value:
            self._backend.build_and_show_calc_comparison(
                plot_spec=plot_spec,
                reference_label=reference_label,
                annotation_lines=annotation_lines,
            )
            return
        # Other engines (for example ASCII) render the base composite
        # without the styled overlay or metrics annotation.
        self._backend.plot_powder_meas_vs_calc(plot_spec=plot_spec)

    def plot_reflection_comparison(
        self,
        *,
        expt_name: str,
        reference: np.ndarray,
        candidate: np.ndarray,
        reference_label: str,
        candidate_label: str,
        annotation_lines: tuple[str, ...] = (),
        title: str | None = None,
    ) -> None:
        """
        Scatter a reference against a candidate per-reflection F².

        Peak-normalises both sets so they share one scale, then plots
        the reference on the x-axis and the candidate on the y-axis
        against a y=x reference line, with an optional metrics
        annotation. Intended for the single-crystal external-reference
        Verification pages.

        Parameters
        ----------
        expt_name : str
            Experiment supplying the plot context (single crystal).
        reference : np.ndarray
            Reference F² per reflection (for example FullProf F2cal).
        candidate : np.ndarray
            Candidate F² per reflection (for example an engine).
        reference_label : str
            Axis and hover name for the reference.
        candidate_label : str
            Axis and hover name for the candidate.
        annotation_lines : tuple[str, ...], default=()
            Lines for the top-left metrics annotation.
        title : str | None, default=None
            Optional plot title.

        Raises
        ------
        ValueError
            If ``reference`` and ``candidate`` differ in length.
        """
        self._update_project_categories(expt_name)
        reference = np.asarray(reference, dtype=float)
        candidate = np.asarray(candidate, dtype=float)
        if reference.shape != candidate.shape:
            msg = (
                f'reference and candidate must have the same length '
                f'(got {reference.shape}, {candidate.shape}).'
            )
            raise ValueError(msg)

        reference_norm = self._peak_normalized(reference)
        candidate_norm = self._peak_normalized(candidate)
        axes_labels = (
            f'{reference_label} F² (normalised)',
            f'{candidate_label} F² (normalised)',
        )
        plot_title = title or f"Reflection F² comparison for 🔬 '{expt_name}'"
        if self.engine == PlotterEngineEnum.PLOTLY.value:
            self._backend.build_and_show_reflection_comparison(
                x_reference=reference_norm,
                y_candidate=candidate_norm,
                axes_labels=axes_labels,
                reference_label=reference_label,
                candidate_label=candidate_label,
                title=plot_title,
                annotation_lines=annotation_lines,
            )
            return
        # Other engines (for example ASCII) render the base scatter
        # without the styled metrics annotation.
        self._backend.plot_single_crystal(
            x_calc=reference_norm,
            y_meas=candidate_norm,
            y_meas_su=np.zeros_like(candidate_norm),
            axes_labels=axes_labels,
            title=plot_title,
            height=self.height,
        )

    @staticmethod
    def _peak_normalized(values: np.ndarray) -> np.ndarray:
        """
        Scale a profile so its maximum equals 100 for overlay display.
        """
        peak = float(np.max(values))
        if not peak:
            return values
        return values / peak * 100.0

    def _plot_meas_vs_calc_request(
        self,
        *,
        expt_name: str,
        plot_options: _MeasVsCalcPlotOptions,
    ) -> None:
        """Render a measured-vs-calculated request from plot options."""
        self._update_project_categories(expt_name)
        experiment = self._project.experiments[expt_name]
        self._plot_meas_vs_calc_data(
            experiment=experiment,
            expt_name=expt_name,
            plot_options=plot_options,
        )

    def plot_param_series(
        self,
        param: object,
        versus: str | None = None,
    ) -> None:
        """
        Plot a parameter's value across sequential fit results.

        When a ``results.csv`` file exists in the project's
        ``analysis/`` directory, data is read from CSV.  Otherwise,
        falls back to in-memory parameter snapshots (produced by
        ``fit()`` in single mode).

        Parameters
        ----------
        param : object
            Descriptor whose ``unique_name`` or ``name`` identifies the
            values to plot.
        versus : str | None, default=None
            Persisted diffrn path (e.g.
            ``'diffrn.ambient_temperature'``) whose sequential-results
            column is used as the x-axis. When ``None``, the experiment
            sequence number is used instead.
        """
        column_names = self._series_column_names(param)
        if not column_names:
            log.warning('Series plot target does not expose a CSV column name.')
            return

        # Try CSV first (produced by fit_sequential or future fit)
        csv_path = None
        if self._project.info.path is not None:
            candidate = pathlib.Path(self._project.info.path) / 'analysis' / 'results.csv'
            if candidate.is_file():
                csv_path = str(candidate)

        if csv_path is not None:
            self._plot_param_series_from_csv(
                csv_path=csv_path,
                column_names=column_names,
                param_descriptor=param,
                versus_path=versus,
            )
        else:
            # Fallback: in-memory snapshots from fit() single mode
            self.plot_param_series_from_snapshots(
                column_names[0],
                versus,
                self._project.experiments,
                self._project.analysis._parameter_snapshots,
            )

    @staticmethod
    def _series_column_names(param: object) -> list[str]:
        """Return candidate CSV column names for one plotted series."""
        names: list[str] = []

        unique_name = getattr(param, 'unique_name', None)
        if isinstance(unique_name, str) and unique_name:
            names.append(unique_name)

        name = getattr(param, 'name', None)
        if isinstance(name, str) and name and name not in names:
            names.append(name)

        return names

    @staticmethod
    def _numeric_series_values(values: object) -> list[float]:
        """Return one CSV column normalized to numeric plot values."""
        series = pd.Series(values)
        if series.dtype == bool:
            return series.astype(float).tolist()

        normalized = series.replace({
            'True': 1.0,
            'False': 0.0,
            'true': 1.0,
            'false': 0.0,
        })
        return pd.to_numeric(normalized, errors='raise').tolist()

    def plot_all_param_series(
        self,
        versus: str | None = None,
    ) -> None:
        """
        Plot every fitted parameter across sequential fit results.

        Iterates the fitted parameters recorded in ``results.csv`` (or,
        when absent, in the in-memory parameter snapshots) and emits one
        ``plot_param_series`` plot per parameter.

        Parameters
        ----------
        versus : str | None, default=None
            Persisted diffrn path (e.g.
            ``'diffrn.ambient_temperature'``) whose sequential-results
            column is used as the x-axis. When ``None``, the experiment
            sequence number is used instead.
        """
        unique_names = self._collect_fitted_param_unique_names()
        if not unique_names:
            log.warning('No fitted parameters found to plot.')
            return

        descriptors_by_name = self._fitted_param_descriptors_by_unique_name()

        for unique_name in unique_names:
            descriptor = descriptors_by_name.get(unique_name)
            if descriptor is None:
                log.warning(f"Parameter '{unique_name}' not found in project; skipping plot.")
                continue
            self.plot_param_series(param=descriptor, versus=versus)

    def _collect_fitted_param_unique_names(self) -> list[str]:
        """
        Return fitted parameter unique names from CSV or snapshots.
        """
        from easydiffraction.analysis.sequential import _META_COLUMNS  # noqa: PLC0415

        meta = set(_META_COLUMNS)

        csv_path = None
        if self._project.info.path is not None:
            candidate = pathlib.Path(self._project.info.path) / 'analysis' / 'results.csv'
            if candidate.is_file():
                csv_path = str(candidate)

        if csv_path is not None:
            df = pd.read_csv(csv_path)
            return [
                column
                for column in df.columns
                if column not in meta
                and not column.startswith('diffrn.')
                and not column.endswith('.uncertainty')
            ]

        snapshots = self._project.analysis._parameter_snapshots
        if not snapshots:
            return []
        first_snapshot = next(iter(snapshots.values()))
        return list(first_snapshot.keys())

    def _fitted_param_descriptors_by_unique_name(self) -> dict[str, object]:
        """Return descriptor map keyed by ``unique_name``."""
        all_params = self._project.structures.parameters + self._project.experiments.parameters
        return {p.unique_name: p for p in all_params if hasattr(p, 'unique_name')}

    def _resolve_versus_descriptor_from_path(
        self,
        versus_path: str | None,
    ) -> object | None:
        """Return a template diffrn descriptor for a persisted path."""
        field_name = self._versus_field_name(versus_path)
        if field_name is None:
            return None

        project = getattr(self, '_project', None)
        if project is None or getattr(project, 'experiments', None) is None:
            return None

        experiment = next(iter(project.experiments.values()), None)
        if experiment is None:
            return None

        return self._resolve_diffrn_descriptor(experiment.diffrn, field_name)

    @staticmethod
    def _versus_field_name(versus_path: str | None) -> str | None:
        """Return the diffrn field name from a persisted path."""
        if versus_path is None:
            return None
        if versus_path.startswith('diffrn.'):
            return versus_path.removeprefix('diffrn.')
        return versus_path

    @classmethod
    def _versus_axis_label(
        cls,
        versus_path: str | None,
        descriptor: object | None,
    ) -> str:
        """Return the x-axis label for a persisted diffrn path."""
        if descriptor is not None:
            label = getattr(descriptor, 'description', None) or getattr(descriptor, 'name', None)
            units = getattr(descriptor, 'units', None)
            if label is not None and units:
                return f'{label} ({units})'
            if label is not None:
                return label

        field_name = cls._versus_field_name(versus_path)
        if field_name is None:
            return 'Experiment No.'
        return field_name.replace('_', ' ')

    def plot_param_correlations(
        self,
        threshold: float | None = DEFAULT_CORRELATION_THRESHOLD,
        precision: int = 2,
        *,
        max_parameters: int = DEFAULT_CORRELATION_MAX_PARAMETERS,
        show_diagonal: bool = True,
    ) -> None:
        """
        Plot the parameter correlation matrix from the latest fit.

        The matrix is taken from ``project.analysis.fit_results``. When
        the active engine is Plotly, an interactive heatmap is shown.
        Otherwise, a rounded correlation table is rendered.

        By default the lower triangle is shown with blank diagonal cells
        so the grid stays square, like posterior pair plots. Set
        ``show_diagonal=False`` to trim the empty outer row and column.

        Parameters
        ----------
        threshold : float | None, default=DEFAULT_CORRELATION_THRESHOLD
            Minimum absolute off-diagonal correlation required for a
            parameter to be shown. When omitted, an automatic cutoff is
            chosen so the displayed matrix stays at or below
            ``max_parameters x max_parameters`` when possible. Set to
            ``0`` to show the full matrix.
        precision : int, default=2
            Number of decimal places to show in the table fallback.
        max_parameters : int, default=DEFAULT_CORRELATION_MAX_PARAMETERS
            Maximum number of parameters to display when ``threshold``
            is omitted. Ignored when ``threshold`` is provided.
        show_diagonal : bool, default=True
            Whether to retain blank diagonal cells in the displayed
            lower-triangle matrix.
        """
        corr_df = self._get_param_correlation_dataframe()
        if corr_df is None:
            return

        corr_df, resolved_threshold = self._resolve_correlation_filter(
            corr_df,
            threshold=threshold,
            max_parameters=max_parameters,
        )
        if corr_df is None:
            return

        corr_df = self._mask_correlation_lower_triangle(corr_df)
        title = self._correlation_filtered_title(
            'Refined parameter correlation matrix',
            resolved_threshold,
        )

        is_graphical = self._backend._supports_graphical_heatmap
        display_corr_df, row_numbers, col_numbers = self._trim_correlation_display_dataframe(
            corr_df,
            preserve_all_rows=not is_graphical,
            show_diagonal=show_diagonal,
        )

        if is_graphical:
            self._plot_correlation_heatmap(
                display_corr_df,
                title,
                threshold=resolved_threshold,
                precision=precision,
            )
            return

        console.paragraph(title)
        TableRenderer.get().render(
            self._format_correlation_table_dataframe(
                display_corr_df,
                row_numbers=row_numbers,
                col_numbers=col_numbers,
                threshold=resolved_threshold,
                precision=precision,
            )
        )

    @classmethod
    def _resolve_correlation_filter(
        cls,
        corr_df: pd.DataFrame,
        *,
        threshold: float | None,
        max_parameters: int | None = DEFAULT_CORRELATION_MAX_PARAMETERS,
        min_parameters: int = 1,
    ) -> tuple[pd.DataFrame | None, float]:
        """Return a filtered matrix and effective threshold."""
        if threshold is not None:
            filtered_corr_df = cls._filter_correlation_dataframe(corr_df, threshold=threshold)
            return filtered_corr_df, float(threshold)
        if max_parameters is None:
            return corr_df, 0.0
        validated_max_parameters = cls._validated_max_parameter_count(
            max_parameters,
            minimum=min_parameters,
        )
        return cls._auto_filtered_correlation_dataframe(
            corr_df,
            max_parameters=validated_max_parameters,
            min_parameters=min_parameters,
        )

    @staticmethod
    def _validated_max_parameter_count(
        max_parameters: int,
        *,
        minimum: int,
    ) -> int:
        """Return a validated parameter-count limit."""
        if not isinstance(max_parameters, int) or isinstance(max_parameters, bool):
            msg = 'max_parameters must be an integer.'
            raise TypeError(msg)
        if max_parameters < minimum:
            msg = f'max_parameters must be at least {minimum}.'
            raise ValueError(msg)
        return max_parameters

    @staticmethod
    def _auto_filtered_correlation_dataframe(
        corr_df: pd.DataFrame,
        *,
        max_parameters: int,
        min_parameters: int = 1,
    ) -> tuple[pd.DataFrame, float]:
        """Return an auto-limited matrix for default display."""
        if corr_df.shape[0] <= max_parameters:
            return corr_df, 0.0

        abs_corr = np.abs(corr_df.to_numpy(copy=True))
        np.fill_diagonal(abs_corr, 0.0)
        positive_values = np.unique(abs_corr[abs_corr > 0.0])
        for candidate in np.sort(positive_values):
            keep_mask = (abs_corr >= candidate).any(axis=0)
            if min_parameters <= int(keep_mask.sum()) <= max_parameters:
                labels = corr_df.index[keep_mask]
                return corr_df.loc[labels, labels], float(candidate)

        if positive_values.size == 0:
            return corr_df.iloc[:max_parameters, :max_parameters], 0.0

        parameter_strength = np.max(abs_corr, axis=0)
        top_indices = np.argsort(-parameter_strength, kind='stable')[:max_parameters]
        top_indices.sort()
        labels = corr_df.index[top_indices]
        return corr_df.loc[labels, labels], 0.0

    @staticmethod
    def _correlation_filtered_title(base_title: str, threshold: float) -> str:
        """Return a plot title with a correlation cutoff."""
        if threshold <= 0:
            return base_title
        return f'{base_title} with |correlation| ≥ {threshold:.2f}'

    @staticmethod
    def _posterior_pair_title(multiplier: float | None) -> str:
        """
        Return the posterior pair title with its displayed bound scale.
        """
        if multiplier is None:
            return 'Posterior pair plot'
        return f'Posterior pair plot in ±{multiplier:g} × uncertainty region'  # noqa: RUF001

    @staticmethod
    def _posterior_pair_uncertainty_multiplier(
        fit_results: object,
        parameter_names: list[str],
    ) -> float | None:
        """
        Return a shared uncertainty-bound multiplier for a pair plot.
        """
        parameters_by_name = {
            getattr(parameter, 'unique_name', ''): parameter
            for parameter in fit_results.parameters
        }
        multiplier: float | None = None

        for parameter_name in parameter_names:
            parameter = parameters_by_name.get(parameter_name)
            if parameter is None:
                return None

            current = getattr(parameter, 'fit_bounds_uncertainty_multiplier', None)
            if current is None or not np.isfinite(float(current)):
                return None

            current_value = float(current)
            if multiplier is None:
                multiplier = current_value
                continue
            if not np.isclose(multiplier, current_value):
                return None

        return multiplier

    def plot_posterior_pairs(
        self,
        parameters: list[object] | None = None,
        style: PosteriorPairPlotStyleEnum | str = 'auto',
        *,
        threshold: float | None = DEFAULT_CORRELATION_THRESHOLD,
        max_parameters: int = DEFAULT_CORRELATION_MAX_PARAMETERS,
    ) -> None:
        """
        Plot posterior pair relationships for sampled parameters.

        Parameters
        ----------
        parameters : list[object] | None, default=None
            Optional subset of sampled parameters to include. When
            provided, ``threshold`` and ``max_parameters`` are ignored.
        style : PosteriorPairPlotStyleEnum | str, default='auto'
            Pair-plot rendering mode. Defaults to ``'auto'``. ``'auto'``
            keeps contours for compact plots and disables them for wide
            grids. ``'fast'`` always skips contours. ``'full'`` always
            renders contours.
        threshold : float | None, default=DEFAULT_CORRELATION_THRESHOLD
            Minimum absolute off-diagonal correlation required for a
            parameter to be auto-selected. When omitted, an automatic
            cutoff keeps the plot at or below ``max_parameters``
            parameters when possible. Set to ``0`` to show all sampled
            parameters.
        max_parameters : int, default=DEFAULT_CORRELATION_MAX_PARAMETERS
            Maximum number of parameters to auto-select when
            ``parameters`` is omitted and ``threshold`` is ``None``.
            Must be at least ``2``.
        """
        if self.engine != PlotterEngineEnum.PLOTLY.value:
            console.paragraph(self._posterior_pair_title(None))

        plot = self._build_posterior_pairs_plot(
            parameters=parameters,
            style=style,
            threshold=threshold,
            max_parameters=max_parameters,
        )
        if plot is None:
            return
        self._show_plot_figure(plot)

    def plot_param_distribution(
        self,
        param: object,
    ) -> None:
        """
        Plot the posterior distribution for one sampled parameter.

        Parameters
        ----------
        param : object
            Parameter descriptor or string identifier selecting the
            posterior to plot. Strings may be unique names or
            user-facing labels.
        """
        if self.engine == PlotterEngineEnum.ASCII.value:
            self._plot_ascii_param_distribution(param)
            return

        plot = self._build_param_distribution_plot(param)
        if plot is None:
            return
        self._show_plot_figure(plot)

    def plot_posterior_predictive(
        self,
        expt_name: str,
        style: str = 'band',
        x_min: float | None = None,
        x_max: float | None = None,
        *,
        show_residual: bool | None = None,
        show_excluded: bool = False,
        x: object | None = None,
    ) -> None:
        """
        Plot posterior predictive checks for supported experiments.

        Parameters
        ----------
        expt_name : str
            Experiment name to plot.
        style : str, default='band'
            ``'band'`` shows the 95% credible interval, ``'draws'``
            shows sampled predictive curves, and ``'band+draws'`` shows
            both together. ASCII powder plots fall back to measured and
            max-posterior lines without uncertainty bands or draws.
            Single-crystal plots currently render only the interval-
            based reflection check.
        x_min : float | None, default=None
            Lower bound for the x-axis range.
        x_max : float | None, default=None
            Upper bound for the x-axis range.
        show_residual : bool | None, default=None
            Whether to include the residual row in supported powder
            composite plots.
        show_excluded : bool, default=False
            Whether to show excluded fitting regions on supported plots.
        x : object | None, default=None
            Optional explicit x-axis data to override stored values.

        Raises
        ------
        ValueError
            If ``style`` is not one of ``'band'``, ``'draws'``, or
            ``'band+draws'``.
        """
        if style not in {'band', 'draws', 'band+draws'}:
            msg = "style must be 'band', 'draws', or 'band+draws'."
            raise ValueError(msg)

        plot_options = _MeasVsCalcPlotOptions(
            x_min=x_min,
            x_max=x_max,
            show_residual=show_residual,
            show_excluded=show_excluded,
            x=x,
        )

        self._plot_posterior_predictive_request(
            expt_name=expt_name,
            style=style,
            plot_options=plot_options,
        )

    def _plot_posterior_predictive_request(
        self,
        *,
        expt_name: str,
        style: str,
        plot_options: _MeasVsCalcPlotOptions,
    ) -> None:
        """Render a posterior predictive request from plot options."""
        if self._project is None:
            log.warning('Plotter is not attached to a project.')
            return

        self._update_project_categories(expt_name)
        experiment = self._project.experiments[expt_name]
        x_axis, _, sample_form, scattering_type, _ = self._resolve_x_axis(
            experiment.type,
            plot_options.x,
        )

        if sample_form == SampleFormEnum.SINGLE_CRYSTAL:
            if self.engine != PlotterEngineEnum.PLOTLY.value:
                log.warning(
                    'Single-crystal posterior predictive plots currently '
                    'require the Plotly backend.'
                )
                return
            self._plot_single_crystal_posterior_predictive(
                experiment=experiment,
                expt_name=expt_name,
                x_axis=x_axis,
                scattering_type=scattering_type,
                plot_options=plot_options,
                style=style,
            )
            return

        if sample_form != SampleFormEnum.POWDER:
            log.warning('Posterior predictive plots currently support powder experiments only.')
            return

        if scattering_type == ScatteringTypeEnum.BRAGG:
            self._plot_posterior_predictive_data(
                experiment=experiment,
                expt_name=expt_name,
                plot_options=plot_options,
                x_axis=x_axis,
                style=style,
            )
            return

        self._plot_non_bragg_posterior_predictive(
            experiment=experiment,
            expt_name=expt_name,
            plot_options=plot_options,
            x_axis=x_axis,
            sample_form=sample_form,
            scattering_type=scattering_type,
            style=style,
        )

    def _plot_single_crystal_posterior_predictive(
        self,
        *,
        experiment: object,
        expt_name: str,
        x_axis: object,
        scattering_type: object,
        plot_options: _MeasVsCalcPlotOptions,
        style: str,
    ) -> None:
        """Render a single-crystal posterior predictive scatter plot."""
        if scattering_type != ScatteringTypeEnum.BRAGG:
            log.warning(
                'Single-crystal posterior predictive plots currently support Bragg data only.'
            )
            return
        if x_axis not in {XAxisType.INTENSITY_CALC, 'intensity_calc'}:
            log.warning(
                'Single-crystal posterior predictive plots currently support '
                "x='intensity_calc' only."
            )
            return
        if plot_options.show_residual:
            log.warning(
                'Posterior predictive residuals are unavailable for '
                'single-crystal plots; ignoring show_residual=True.'
            )
        if style != 'band':
            log.warning(
                'Single-crystal posterior predictive plots currently support '
                'style="band" only; rendering the 95% credible interval.'
            )

        summary = self._get_or_build_posterior_predictive_summary(
            experiment=experiment,
            expt_name=expt_name,
            x_axis=x_axis,
            include_draws=False,
        )
        if summary is None:
            return

        pattern = intensity_category_for(experiment)
        y_meas_raw = getattr(pattern, 'intensity_meas', None)
        if y_meas_raw is None:
            log.warning(f'No measured data available for experiment {expt_name}.')
            return
        y_meas = np.asarray(y_meas_raw, dtype=float)
        if y_meas.shape != np.asarray(summary.best_sample_prediction).shape:
            log.warning(
                'Single-crystal posterior predictive values do not match the '
                'measured reflection array shape.'
            )
            return

        y_meas_su_raw = getattr(pattern, 'intensity_meas_su', None)
        if y_meas_su_raw is None:
            log.warning(f'No measurement uncertainties for experiment {expt_name}')
            y_meas_su = np.zeros_like(y_meas)
        else:
            y_meas_su = np.asarray(y_meas_su_raw, dtype=float)
            if y_meas_su.shape != y_meas.shape:
                log.warning(
                    'Single-crystal posterior predictive uncertainties do not '
                    'match the measured reflection array shape.'
                )
                return

        self._plot_single_crystal_posterior_predictive_summary(
            expt_name=expt_name,
            summary=summary,
            y_meas=y_meas,
            y_meas_su=y_meas_su,
            axes_labels=self._get_axes_labels(
                SampleFormEnum.SINGLE_CRYSTAL,
                ScatteringTypeEnum.BRAGG,
                XAxisType.INTENSITY_CALC,
            ),
        )

    def _plot_non_bragg_posterior_predictive(
        self,
        *,
        experiment: object,
        expt_name: str,
        plot_options: _MeasVsCalcPlotOptions,
        x_axis: object,
        sample_form: object,
        scattering_type: object,
        style: str,
    ) -> None:
        """Render non-Bragg posterior predictive summaries."""
        show_draws = self.engine == PlotterEngineEnum.PLOTLY.value and style in {
            'draws',
            'band+draws',
        }
        pattern = intensity_category_for(experiment)
        y_meas = getattr(pattern, 'intensity_meas', None)
        if y_meas is None:
            log.warning(f'No measured data available for experiment {expt_name}.')
            return

        ctx = self._prepare_powder_context(
            pattern,
            expt_name,
            experiment.type,
            plot_options.x_min,
            plot_options.x_max,
            plot_options.x,
        )
        if ctx is None:
            return

        if plot_options.show_residual:
            log.warning(
                'Posterior predictive residuals are unavailable for non-Bragg '
                'summary plots; ignoring show_residual=True.'
            )

        summary = self._get_or_build_posterior_predictive_summary(
            experiment=experiment,
            expt_name=expt_name,
            x_axis=x_axis,
            include_draws=show_draws,
        )
        if summary is None:
            return

        filtered_summary = self._filtered_posterior_predictive_summary(
            summary=summary,
            x_min=ctx['x_min'],
            x_max=ctx['x_max'],
            include_draws=show_draws,
        )
        if filtered_summary is None:
            log.warning(
                f'No posterior predictive data available within the requested x-range '
                f'for experiment {expt_name}.'
            )
            return

        filtered_y_meas = self._filtered_y_array(
            y_meas,
            ctx['x_array'],
            ctx['x_min'],
            ctx['x_max'],
        )
        excluded_ranges = (
            self._excluded_ranges(
                experiment=experiment,
                x_min=ctx['x_min'],
                x_max=ctx['x_max'],
            )
            if plot_options.show_excluded
            else ()
        )

        axes_labels = self._get_axes_labels(sample_form, scattering_type, x_axis)
        self._plot_posterior_predictive_summary(
            expt_name=expt_name,
            summary=filtered_summary,
            y_meas=filtered_y_meas,
            axes_labels=axes_labels,
            show_band=style in {'band', 'band+draws'},
            show_draws=style in {'draws', 'band+draws'},
            excluded_ranges=excluded_ranges,
        )

    @staticmethod
    def _filter_correlation_dataframe(
        corr_df: pd.DataFrame,
        threshold: float | None,
    ) -> pd.DataFrame | None:
        """
        Filter a correlation matrix to only strongly correlated params.

        Parameters
        ----------
        corr_df : pd.DataFrame
            Square correlation matrix.
        threshold : float | None
            Absolute-correlation cutoff. ``None`` or ``0`` keeps all
            parameters.

        Returns
        -------
        pd.DataFrame | None
            Filtered square matrix, or ``None`` if no off-diagonal
            correlations meet the cutoff.

        Raises
        ------
        ValueError
            If *threshold* is outside ``[0, 1]``.
        """
        if threshold is None or threshold <= 0:
            return corr_df
        if threshold > 1:
            msg = 'Correlation threshold must be between 0 and 1.'
            raise ValueError(msg)

        abs_corr = np.abs(corr_df.to_numpy(copy=True))
        np.fill_diagonal(abs_corr, 0.0)
        keep_mask = (abs_corr >= threshold).any(axis=0)

        if not keep_mask.any():
            log.warning(f'No parameter pairs with |correlation| >= {threshold:.2f} were found.')
            return None

        labels = corr_df.index[keep_mask]
        return corr_df.loc[labels, labels]

    @staticmethod
    def _mask_correlation_lower_triangle(
        corr_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Mask the upper triangle and diagonal of a correlation matrix.

        Only the lower triangle is kept, since the matrix is symmetric
        and diagonal values are always ``1``.

        Parameters
        ----------
        corr_df : pd.DataFrame
            Square correlation matrix.

        Returns
        -------
        pd.DataFrame
            Correlation matrix with upper triangle and diagonal masked.
        """
        masked_values = corr_df.to_numpy(copy=True)
        mask = np.triu(np.ones_like(masked_values, dtype=bool), k=0)
        masked_values[mask] = np.nan
        return pd.DataFrame(masked_values, index=corr_df.index, columns=corr_df.columns)

    @staticmethod
    def _trim_correlation_display_dataframe(
        corr_df: pd.DataFrame,
        *,
        preserve_all_rows: bool,
        show_diagonal: bool,
    ) -> tuple[pd.DataFrame, list[int], list[int]]:
        """
        Trim empty outer rows/columns from the lower-triangle view.

        For the lower triangle without diagonal, the last column and
        first row are always empty and can be trimmed.

        Parameters
        ----------
        corr_df : pd.DataFrame
            Masked correlation matrix.
        preserve_all_rows : bool
            Whether to keep the full row list so row labels continue to
            identify all numeric column headers in tabular output.
        show_diagonal : bool
            Whether blank diagonal cells should remain visible.

        Returns
        -------
        tuple[pd.DataFrame, list[int], list[int]]
            Display matrix plus 1-based parameter numbers for the kept
            rows and columns.
        """
        num_rows, num_cols = corr_df.shape
        row_numbers = list(range(1, num_rows + 1))
        col_numbers = list(range(1, num_cols + 1))

        if show_diagonal or min(num_rows, num_cols) <= 1:
            return corr_df, row_numbers, col_numbers

        if preserve_all_rows:
            return corr_df.iloc[:, :-1], row_numbers, col_numbers[:-1]
        return corr_df.iloc[1:, :-1], row_numbers[1:], col_numbers[:-1]

    def _get_param_correlation_dataframe(self) -> pd.DataFrame | None:
        """
        Return the correlation matrix for the latest fit.

        Returns
        -------
        pd.DataFrame | None
            Square correlation matrix labeled by parameter unique names,
            or ``None`` if unavailable.
        """
        fit_results = self._get_fit_result_for_correlation()
        if fit_results is None:
            return None

        corr_df = self._posterior_correlation_dataframe(fit_results)
        if corr_df is not None:
            return corr_df

        raw_result = self._raw_fit_result_for_correlation(fit_results)
        if raw_result is not None:
            corr_df = self._correlation_dataframe_from_engine_result(
                raw_result=raw_result,
                parameters=fit_results.parameters,
            )
            if corr_df is not None:
                return corr_df

        corr_df = self._correlation_dataframe_from_persisted_projection(fit_results)
        if corr_df is not None:
            return corr_df

        log.warning(
            'Correlation matrix is unavailable for this fit. '
            'Use a minimizer that returns covariance information or posterior samples.'
        )
        return None

    def _posterior_correlation_dataframe(
        self,
        fit_results: object,
    ) -> pd.DataFrame | None:
        """Return posterior-sample correlations when available."""
        posterior_samples = getattr(fit_results, 'posterior_samples', None)
        if posterior_samples is None:
            return None
        return self._correlation_from_posterior_samples(posterior_samples)

    @staticmethod
    def _raw_fit_result_for_correlation(fit_results: object) -> object | None:
        """Return raw fit results for correlation fallback."""
        raw_result = getattr(fit_results, 'result', None)
        if raw_result is None:
            raw_result = getattr(fit_results, 'engine_result', None)
        if raw_result is None:
            return None

        var_names = getattr(raw_result, 'var_names', None)
        if not var_names:
            return None
        return raw_result

    def _correlation_dataframe_from_persisted_projection(
        self,
        fit_results: object,
    ) -> pd.DataFrame | None:
        """
        Return correlations restored from persisted fit-state rows.
        """
        if self._project is None:
            return None

        analysis = self._project.analysis
        source_kind = (
            FitCorrelationSourceEnum.POSTERIOR.value
            if analysis.fit_result.result_kind.value == FitResultKindEnum.BAYESIAN.value
            else FitCorrelationSourceEnum.DETERMINISTIC.value
        )
        correlation_rows = [
            row
            for row in analysis.fit_parameter_correlations
            if row.source_kind.value == source_kind
        ]
        if not correlation_rows:
            return None

        parameter_names = [
            getattr(parameter, 'unique_name', '')
            for parameter in getattr(fit_results, 'parameters', [])
            if getattr(parameter, 'unique_name', None)
        ]
        if not parameter_names:
            parameter_names = [
                summary.unique_name
                for summary in getattr(fit_results, 'posterior_parameter_summaries', [])
            ]

        for row in correlation_rows:
            parameter_names.extend([row.param_unique_name_i.value, row.param_unique_name_j.value])
        parameter_names = list(dict.fromkeys(parameter_names))
        if len(parameter_names) < MIN_POSTERIOR_PARAMETER_COUNT:
            return None

        correlation_values = np.eye(len(parameter_names), dtype=float)
        corr_df = pd.DataFrame(
            correlation_values,
            index=parameter_names,
            columns=parameter_names,
        )
        wrote_any = False
        for row in correlation_rows:
            i_name = row.param_unique_name_i.value
            j_name = row.param_unique_name_j.value
            if i_name not in corr_df.index or j_name not in corr_df.index:
                continue
            corr_df.loc[i_name, j_name] = float(row.correlation.value)
            corr_df.loc[j_name, i_name] = float(row.correlation.value)
            wrote_any = True
        return corr_df if wrote_any else None

    def _correlation_dataframe_from_engine_result(
        self,
        *,
        raw_result: object,
        parameters: list[object],
    ) -> pd.DataFrame | None:
        """Return correlations derived from engine result fields."""
        covar = getattr(raw_result, 'covar', None)
        if covar is not None:
            return self._correlation_from_covariance(
                covar,
                getattr(raw_result, 'var_names', None),
                parameters,
            )
        return self._get_param_correlation_dataframe_from_engine_params(
            raw_result=raw_result,
            parameters=parameters,
        )

    def _build_posterior_pairs_plot(
        self,
        *,
        parameters: list[object] | None,
        style: PosteriorPairPlotStyleEnum | str = 'auto',
        threshold: float | None = DEFAULT_CORRELATION_THRESHOLD,
        max_parameters: int | None = None,
    ) -> object | None:
        """
        Build a Plotly posterior pair plot.

        Parameters
        ----------
        parameters : list[object] | None
            Optional subset of sampled parameters to include.
        style : PosteriorPairPlotStyleEnum | str, default='auto'
            Posterior pair-plot rendering mode. Defaults to ``'auto'``.
        threshold : float | None, default=DEFAULT_CORRELATION_THRESHOLD
            Absolute-correlation cutoff for auto-selected parameters.
        max_parameters : int | None, default=None
            Maximum number of auto-selected parameters. ``None`` keeps
            the full posterior parameter set.

        Returns
        -------
        object | None
            Plotly figure, or ``None`` when posterior plotting is
            unavailable.
        """
        context = self._posterior_pairs_context(
            parameters,
            style=style,
            threshold=threshold,
            max_parameters=max_parameters,
        )
        if context is None:
            return None

        make_subplots = __import__('plotly.subplots', fromlist=['make_subplots']).make_subplots
        subplot_title_annotations: list[dict[str, object]] = []
        subplot_border_shapes: list[dict[str, object]] = []
        legend_state = _PosteriorPairsLegendState()
        fig = make_subplots(
            rows=context.n_parameters,
            cols=context.n_parameters,
            shared_xaxes='columns',
            horizontal_spacing=PAIR_PLOT_SUBPLOT_SPACING,
            vertical_spacing=PAIR_PLOT_SUBPLOT_SPACING,
        )

        for row_index in range(context.n_parameters):
            for col_index in range(context.n_parameters):
                self._populate_posterior_pair_panel(
                    fig=fig,
                    context=context,
                    row_index=row_index,
                    col_index=col_index,
                    legend_state=legend_state,
                    subplot_title_annotations=subplot_title_annotations,
                    subplot_border_shapes=subplot_border_shapes,
                )

        self._finalize_posterior_pairs_figure(
            fig=fig,
            context=context,
            subplot_title_annotations=subplot_title_annotations,
            subplot_border_shapes=subplot_border_shapes,
        )
        return fig

    def _posterior_pairs_context(
        self,
        parameters: list[object] | None,
        *,
        style: PosteriorPairPlotStyleEnum | str = 'auto',
        threshold: float | None = DEFAULT_CORRELATION_THRESHOLD,
        max_parameters: int | None = None,
    ) -> _PosteriorPairsContext | None:
        """Return the resolved inputs for a posterior pair plot."""
        posterior_samples, fit_results = self._get_posterior_samples_and_fit_results()
        if posterior_samples is None or fit_results is None:
            return None

        plot_style = self._validated_posterior_pair_plot_style(style)

        parameter_names, resolved_threshold = self._resolved_posterior_pair_parameter_names(
            fit_results=fit_results,
            parameters=parameters,
            threshold=threshold,
            max_parameters=max_parameters,
        )
        if parameter_names is None:
            return None
        if len(parameter_names) < MIN_POSTERIOR_PARAMETER_COUNT:
            log.warning('Posterior pair plots require at least two sampled parameters.')
            return None

        selected_samples = self._selected_posterior_samples(posterior_samples, parameter_names)
        if selected_samples is None:
            return None

        n_parameters = len(parameter_names)
        show_contours = self._posterior_pair_show_contours(
            n_parameters=n_parameters,
            style=plot_style,
        )
        if plot_style is PosteriorPairPlotStyleEnum.AUTO and not show_contours:
            log.warning(
                'Posterior pair plot auto mode disabled contours for '
                f'{n_parameters} parameters. Use style="full" to force '
                'contours.'
            )

        density_samples = self._thin_posterior_samples(
            selected_samples,
            max_points=self._posterior_pair_density_max_points(n_parameters),
        )
        scatter_samples = self._thin_posterior_samples(
            selected_samples,
            max_points=POSTERIOR_PAIR_SCATTER_MAX_POINTS,
        )
        uncertainty_multiplier = self._posterior_pair_uncertainty_multiplier(
            fit_results,
            parameter_names,
        )

        return _PosteriorPairsContext(
            fit_results=fit_results,
            parameter_names=parameter_names,
            labels=self._posterior_plot_labels(fit_results, parameter_names),
            annotation_labels=self._square_matrix_axis_title_labels(parameter_names),
            title=self._correlation_filtered_title(
                self._posterior_pair_title(uncertainty_multiplier),
                resolved_threshold,
            ),
            marginal_density_samples=selected_samples,
            density_samples=density_samples,
            scatter_samples=scatter_samples,
            show_contours=show_contours,
            contour_grid_size=self._posterior_pair_contour_grid_size(n_parameters),
            axis_frame_color=self._plot_axis_frame_color(),
            axis_ranges=self._posterior_pair_axis_ranges(
                fit_results=fit_results,
                parameter_names=parameter_names,
                samples=selected_samples,
            ),
        )

    def _resolved_posterior_pair_parameter_names(
        self,
        *,
        fit_results: object,
        parameters: list[object] | None,
        threshold: float | None,
        max_parameters: int | None,
    ) -> tuple[list[str] | None, float]:
        """Return pair-plot names and the effective cutoff."""
        parameter_names = self._resolve_posterior_parameter_names(
            fit_results=fit_results,
            parameters=parameters,
        )
        if parameter_names is None:
            return None, 0.0
        if parameters is not None:
            return parameter_names, 0.0

        corr_df = self._posterior_correlation_dataframe(fit_results)
        if corr_df is None:
            return parameter_names, 0.0

        filtered_corr_df, resolved_threshold = self._resolve_correlation_filter(
            corr_df.loc[parameter_names, parameter_names],
            threshold=threshold,
            max_parameters=max_parameters,
            min_parameters=MIN_POSTERIOR_PARAMETER_COUNT,
        )
        if filtered_corr_df is None:
            return None, 0.0
        return list(filtered_corr_df.index), resolved_threshold

    def _posterior_pair_axis_ranges(
        self,
        *,
        fit_results: object,
        parameter_names: list[str],
        samples: np.ndarray,
    ) -> list[tuple[float, float]]:
        """Return per-parameter axis ranges for a pair plot."""
        axis_ranges: list[tuple[float, float]] = []
        for index, parameter_name in enumerate(parameter_names):
            lower_bound, upper_bound = self._posterior_parameter_bounds(
                fit_results=fit_results,
                parameter_name=parameter_name,
            )
            axis_ranges.append(
                self._posterior_axis_bounds(
                    samples[:, index],
                    lower_bound=lower_bound,
                    upper_bound=upper_bound,
                )
            )
        return axis_ranges

    def _populate_posterior_pair_panel(
        self,
        *,
        fig: object,
        context: _PosteriorPairsContext,
        row_index: int,
        col_index: int,
        legend_state: _PosteriorPairsLegendState,
        subplot_title_annotations: list[dict[str, object]],
        subplot_border_shapes: list[dict[str, object]],
    ) -> None:
        """Populate one panel in the posterior pair plot grid."""
        row = row_index + 1
        col = col_index + 1
        if col_index > row_index:
            self._hide_posterior_pair_panel(fig=fig, row=row, col=col)
            return

        if row_index == col_index:
            self._add_posterior_pair_diagonal(
                fig=fig,
                context=context,
                row=row,
                col=col,
                parameter_index=col_index,
                legend_state=legend_state,
            )
        else:
            self._add_posterior_pair_off_diagonal(
                fig=fig,
                context=context,
                row=row,
                col=col,
                row_index=row_index,
                col_index=col_index,
                legend_state=legend_state,
            )

        self._configure_posterior_pair_panel_axes(
            fig=fig,
            context=context,
            row=row,
            col=col,
            row_index=row_index,
            col_index=col_index,
        )
        self._collect_posterior_pair_panel_decorations(
            fig=fig,
            context=context,
            row_index=row_index,
            col_index=col_index,
            subplot_title_annotations=subplot_title_annotations,
            subplot_border_shapes=subplot_border_shapes,
        )

    @staticmethod
    def _hide_posterior_pair_panel(
        *,
        fig: object,
        row: int,
        col: int,
    ) -> None:
        """Hide an upper-triangle panel in the pair plot grid."""
        fig.update_xaxes(visible=False, row=row, col=col)
        fig.update_yaxes(visible=False, row=row, col=col)

    def _add_posterior_pair_diagonal(
        self,
        *,
        fig: object,
        context: _PosteriorPairsContext,
        row: int,
        col: int,
        parameter_index: int,
        legend_state: _PosteriorPairsLegendState,
    ) -> None:
        """Add the diagonal marginal-density panel."""
        go = __import__('plotly.graph_objects', fromlist=['Histogram'])
        density_values = context.marginal_density_samples[:, parameter_index]
        density_trace = self._posterior_density_trace(
            fit_results=context.fit_results,
            parameter_name=context.parameter_names[parameter_index],
            values=density_values,
            trace_name=context.labels[parameter_index],
        )
        if density_trace is None:
            fig.add_trace(
                go.Histogram(
                    x=density_values,
                    nbinsx=40,
                    histnorm='probability density',
                    marker={'color': POSTERIOR_PAIR_MARGINAL_DENSITY_LINE_COLOR},
                    showlegend=False,
                    hovertemplate=self._posterior_pair_density_hovertemplate(
                        context.parameter_names[parameter_index]
                    ),
                ),
                row=row,
                col=col,
            )
            return

        self._style_posterior_pair_marginal_density_trace(density_trace)
        density_trace.hovertemplate = self._posterior_pair_density_hovertemplate(
            context.parameter_names[parameter_index]
        )
        density_trace.name = 'Marginal density'
        density_trace.legendgroup = 'posterior-marginal-density'
        density_trace.showlegend = legend_state.show_density
        fig.add_trace(density_trace, row=row, col=col)
        legend_state.show_density = False
        y_axis_range = self._posterior_density_axis_range(np.asarray(density_trace.y))
        if y_axis_range is not None:
            fig.update_yaxes(range=list(y_axis_range), row=row, col=col)

    def _add_posterior_pair_off_diagonal(
        self,
        *,
        fig: object,
        context: _PosteriorPairsContext,
        row: int,
        col: int,
        row_index: int,
        col_index: int,
        legend_state: _PosteriorPairsLegendState,
    ) -> None:
        """Add one off-diagonal pair-relationship panel."""
        go = __import__('plotly.graph_objects', fromlist=['Scatter'])
        x_density_values = context.density_samples[:, col_index]
        y_density_values = context.density_samples[:, row_index]
        x_scatter_values = context.scatter_samples[:, col_index]
        y_scatter_values = context.scatter_samples[:, row_index]
        contour_traces = None
        if context.show_contours:
            contour_traces = self._posterior_contour_traces(
                fit_results=context.fit_results,
                x_parameter_name=context.parameter_names[col_index],
                y_parameter_name=context.parameter_names[row_index],
                x_values=x_density_values,
                y_values=y_density_values,
                grid_size=context.contour_grid_size,
            )
        sample_hovertemplate = self._posterior_pair_scatter_hovertemplate(
            x_parameter_name=context.parameter_names[col_index],
            y_parameter_name=context.parameter_names[row_index],
        )
        fig.add_trace(
            go.Scatter(
                x=x_scatter_values,
                y=y_scatter_values,
                mode='markers',
                marker={
                    'color': POSTERIOR_SCATTER_MARKER_COLOR,
                    'size': POSTERIOR_PAIR_SAMPLE_MARKER_SIZE,
                },
                name='Posterior samples',
                legendgroup='posterior-samples',
                showlegend=legend_state.show_scatter,
                hovertemplate=sample_hovertemplate,
                zorder=0,
            ),
            row=row,
            col=col,
        )
        legend_state.show_scatter = False
        if contour_traces is not None:
            contour_traces[0].name = 'Posterior contours'
            contour_traces[0].legendgroup = 'posterior-contours'
            contour_traces[0].showlegend = legend_state.show_contour
            contour_traces[1].legendgroup = 'posterior-contours'
            contour_traces[1].showlegend = False
            fig.add_trace(contour_traces[0], row=row, col=col)
            fig.add_trace(contour_traces[1], row=row, col=col)
            legend_state.show_contour = False

    @staticmethod
    def _configure_posterior_pair_panel_axes(
        *,
        fig: object,
        context: _PosteriorPairsContext,
        row: int,
        col: int,
        row_index: int,
        col_index: int,
    ) -> None:
        """Apply axis styling and labels to one pair-plot panel."""
        is_diagonal = row_index == col_index
        fig.update_xaxes(
            showline=True,
            mirror=True,
            range=list(context.axis_ranges[col_index]),
            zeroline=False,
            showgrid=False,
            layer='above traces',
            linecolor=context.axis_frame_color,
            linewidth=POSTERIOR_PAIR_AXIS_LINE_WIDTH,
            ticks='',
            ticklen=0,
            tickwidth=0,
            showticklabels=False,
            row=row,
            col=col,
        )
        fig.update_yaxes(
            showline=True,
            mirror=True,
            zeroline=False,
            showgrid=False,
            layer='above traces',
            linecolor=context.axis_frame_color,
            linewidth=POSTERIOR_PAIR_AXIS_LINE_WIDTH,
            ticks='',
            ticklen=0,
            tickwidth=0,
            showticklabels=False,
            row=row,
            col=col,
        )
        if not is_diagonal:
            fig.update_yaxes(range=list(context.axis_ranges[row_index]), row=row, col=col)
        if is_diagonal:
            fig.update_yaxes(
                title_text=None,
                row=row,
                col=col,
            )
        fig.update_xaxes(title_text=None, row=row, col=col)

    @staticmethod
    def _collect_posterior_pair_panel_decorations(
        *,
        fig: object,
        context: _PosteriorPairsContext,
        row_index: int,
        col_index: int,
        subplot_title_annotations: list[dict[str, object]],
        subplot_border_shapes: list[dict[str, object]],
    ) -> None:
        """Collect annotations and frame shapes for one pair panel."""
        row = row_index + 1
        col = col_index + 1
        subplot = fig.get_subplot(row, col)
        x_mid = 0.5 * (subplot.xaxis.domain[0] + subplot.xaxis.domain[1])
        y_mid = 0.5 * (subplot.yaxis.domain[0] + subplot.yaxis.domain[1])
        if col_index == 0:
            subplot_title_annotations.append({
                'x': subplot.xaxis.domain[0],
                'xref': 'paper',
                'xanchor': 'right',
                'xshift': -POSTERIOR_PAIR_Y_TITLE_XSHIFT_PIXELS,
                'y': 0.5 * (subplot.yaxis.domain[0] + subplot.yaxis.domain[1]),
                'yref': 'paper',
                'yanchor': 'middle',
                'text': context.annotation_labels[row_index],
                'align': 'center',
                'font': {'size': POSTERIOR_PAIR_AXIS_TITLE_FONT_SIZE},
                'textangle': -90,
                'showarrow': False,
            })
        if row_index == context.n_parameters - 1:
            subplot_title_annotations.append({
                'x': x_mid,
                'xref': 'paper',
                'xanchor': 'center',
                'y': subplot.yaxis.domain[0],
                'yref': 'paper',
                'yanchor': 'top',
                'yshift': -POSTERIOR_PAIR_X_TITLE_YSHIFT_PIXELS,
                'text': context.annotation_labels[col_index],
                'align': 'center',
                'font': {'size': POSTERIOR_PAIR_AXIS_TITLE_FONT_SIZE},
                'showarrow': False,
            })
        subplot_border_shapes.extend([
            {
                'type': 'line',
                'xref': 'paper',
                'yref': 'paper',
                'x0': x_mid,
                'x1': x_mid,
                'y0': subplot.yaxis.domain[0],
                'y1': subplot.yaxis.domain[1],
                'line': {
                    'color': POSTERIOR_PAIR_GUIDE_LINE_COLOR,
                    'width': 1,
                },
                'layer': 'above',
            },
            {
                'type': 'line',
                'xref': 'paper',
                'yref': 'paper',
                'x0': subplot.xaxis.domain[0],
                'x1': subplot.xaxis.domain[1],
                'y0': y_mid,
                'y1': y_mid,
                'line': {
                    'color': POSTERIOR_PAIR_GUIDE_LINE_COLOR,
                    'width': 1,
                },
                'layer': 'above',
            },
            {
                'type': 'rect',
                'xref': 'paper',
                'yref': 'paper',
                'x0': subplot.xaxis.domain[0],
                'x1': subplot.xaxis.domain[1],
                'y0': subplot.yaxis.domain[0],
                'y1': subplot.yaxis.domain[1],
                'line': {
                    'color': context.axis_frame_color,
                    'width': POSTERIOR_PAIR_AXIS_LINE_WIDTH,
                },
                'fillcolor': 'rgba(0, 0, 0, 0)',
                'layer': 'above',
            },
        ])

    @staticmethod
    def _square_matrix_title_annotation(
        title: str,
        annotation_labels: list[str],
    ) -> dict[str, object]:
        """Return a top-left title annotation for matrix plots."""
        return {
            'x': 0.0,
            'xref': 'paper',
            'xanchor': 'left',
            'xshift': -Plotter._square_matrix_title_left_shift(annotation_labels),
            'y': 1.0,
            'yref': 'paper',
            'yanchor': 'bottom',
            'yshift': SQUARE_MATRIX_TITLE_YSHIFT_PIXELS,
            'text': title,
            'font': {'size': POSTERIOR_PAIR_TITLE_FONT_SIZE},
            'showarrow': False,
        }

    @staticmethod
    def _posterior_pair_title_annotation(
        title: str,
        annotation_labels: list[str],
    ) -> dict[str, object]:
        """Return the outer title annotation for the pair plot."""
        return Plotter._square_matrix_title_annotation(
            title,
            annotation_labels,
        )

    @staticmethod
    def _square_matrix_title_left_shift(annotation_labels: list[str]) -> int:
        """Return the title shift relative to the shared left margin."""
        extra_margin = Plotter._square_matrix_extra_axis_title_margin(annotation_labels)
        return max(
            0,
            SQUARE_MATRIX_LEFT_MARGIN_PIXELS
            + extra_margin
            - SQUARE_MATRIX_TITLE_LEFT_PADDING_PIXELS,
        )

    @staticmethod
    def _square_matrix_gap_data_width(n_parameters: int) -> float:
        """Return the gap width matching pair-plot spacing."""
        if n_parameters <= 1:
            return 0.0

        denominator = 1.0 - PAIR_PLOT_SUBPLOT_SPACING * (n_parameters - 1)
        if denominator <= 0:
            return 0.0
        return PAIR_PLOT_SUBPLOT_SPACING * n_parameters / denominator

    @classmethod
    def _square_matrix_plot_extent(cls, n_parameters: int) -> float:
        """Return the inner plot extent for one square matrix plot."""
        gap_width = cls._square_matrix_gap_data_width(n_parameters)
        return float(n_parameters + max(0, n_parameters - 1) * gap_width)

    @classmethod
    def _square_matrix_target_plot_size_pixels(cls, n_parameters: int) -> float:
        """Return the target inner size for one square matrix plot."""
        cell_size = cls._posterior_pair_cell_size_pixels(
            n_parameters,
            available_width_pixels=PAIR_PLOT_ESTIMATED_CONTAINER_WIDTH_PIXELS,
        )
        return cell_size * cls._square_matrix_plot_extent(n_parameters)

    @staticmethod
    def _correlation_cell_size_pixels() -> int:
        """
        Return the correlation cell width in pixels (~16 label chars).
        """
        return round(
            CORRELATION_CELL_LABEL_CHAR_COUNT
            * CORRELATION_LABEL_CHAR_WIDTH_FACTOR
            * POSTERIOR_PAIR_AXIS_TITLE_FONT_SIZE
        )

    @classmethod
    def _square_matrix_layout_meta(
        cls,
        *,
        n_parameters: int,
        annotation_labels: list[str],
        cell_size_pixels: int | None = None,
        cap_width: bool = False,
    ) -> dict[str, object]:
        """Return wrapper metadata for square matrix plots."""
        margins = cls._square_matrix_layout_margin(annotation_labels)
        if cell_size_pixels is None:
            plot_size = cls._square_matrix_target_plot_size_pixels(n_parameters)
        else:
            plot_size = cell_size_pixels * cls._square_matrix_plot_extent(n_parameters)
        aspect_width = round(plot_size + int(margins['l']) + int(margins['r']))
        aspect_height = round(plot_size + int(margins['t']) + int(margins['b']))
        wrapper: dict[str, object] = {
            'aspect_ratio': f'{aspect_width} / {aspect_height}',
        }
        if cap_width:
            wrapper['max_width_pixels'] = aspect_width
        return {SQUARE_MATRIX_FIXED_ASPECT_META_KEY: wrapper}

    def _finalize_posterior_pairs_figure(
        self,
        *,
        fig: object,
        context: _PosteriorPairsContext,
        subplot_title_annotations: list[dict[str, object]],
        subplot_border_shapes: list[dict[str, object]],
    ) -> None:
        """Apply final layout settings to the posterior pair plot."""
        axis_frame_shape_indexes = [
            index
            for index, shape in enumerate(subplot_border_shapes)
            if shape.get('type') == 'rect'
        ]
        fig.update_layout(
            autosize=True,
            margin=self._square_matrix_layout_margin(context.annotation_labels),
            bargap=0.05,
            annotations=[
                self._posterior_pair_title_annotation(
                    context.title,
                    context.annotation_labels,
                ),
                *subplot_title_annotations,
            ],
            shapes=subplot_border_shapes,
            meta=self._square_matrix_layout_meta(
                n_parameters=context.n_parameters,
                annotation_labels=context.annotation_labels,
            ),
            legend={
                'bgcolor': 'rgba(0, 0, 0, 0)',
                'xanchor': 'right',
                'x': 0.995,
                'yanchor': 'top',
                'y': 0.995,
                'groupclick': 'togglegroup',
            },
        )
        PlotlyPlotter._apply_theme_sync_meta(
            fig,
            axis_frame_shape_indexes=axis_frame_shape_indexes,
        )

    @staticmethod
    def _square_matrix_layout_margin(annotation_labels: list[str]) -> dict[str, int | bool]:
        """Return outer margins sized for multiline matrix labels."""
        extra_margin = Plotter._square_matrix_extra_axis_title_margin(annotation_labels)
        return {
            'autoexpand': False,
            'l': SQUARE_MATRIX_LEFT_MARGIN_PIXELS + extra_margin,
            'r': SQUARE_MATRIX_RIGHT_MARGIN_PIXELS,
            't': SQUARE_MATRIX_TOP_MARGIN_PIXELS,
            'b': SQUARE_MATRIX_BOTTOM_MARGIN_PIXELS + extra_margin,
        }

    @staticmethod
    def _square_matrix_extra_axis_title_margin(annotation_labels: list[str]) -> int:
        """Return extra margin needed for multiline axis labels."""
        if not annotation_labels:
            return 0

        max_line_count = max(
            Plotter._square_matrix_axis_title_line_count(label) for label in annotation_labels
        )
        return max(0, max_line_count - 1) * SQUARE_MATRIX_AXIS_TITLE_LINE_HEIGHT_PIXELS

    @staticmethod
    def _square_matrix_axis_title_line_count(label: str) -> int:
        """Return the number of display lines in one axis title."""
        if not label:
            return 1
        return label.count('<br>') + 1

    @staticmethod
    def _posterior_pair_cell_size_pixels(
        n_parameters: int,
        *,
        available_width_pixels: float,
    ) -> int:
        """Return an estimated square cell size for a pair plot."""
        if n_parameters < 1:
            return PAIR_PLOT_CELL_SIZE_PIXELS

        plot_width = max(
            PAIR_PLOT_MIN_CELL_SIZE_PIXELS,
            available_width_pixels - PAIR_PLOT_MARGIN_PIXELS,
        )
        cell_size = plot_width / n_parameters
        return round(
            min(
                PAIR_PLOT_CELL_SIZE_PIXELS,
                max(PAIR_PLOT_MIN_CELL_SIZE_PIXELS, cell_size),
            )
        )

    @classmethod
    def _posterior_pair_figure_height_pixels(cls, n_parameters: int) -> int:
        """
        Return the initial figure height for a responsive pair plot.
        """
        cell_size = cls._posterior_pair_cell_size_pixels(
            n_parameters,
            available_width_pixels=PAIR_PLOT_ESTIMATED_CONTAINER_WIDTH_PIXELS,
        )
        return max(
            PAIR_PLOT_MIN_SIZE_PIXELS,
            cell_size * n_parameters + PAIR_PLOT_MARGIN_PIXELS,
        )

    @staticmethod
    def _posterior_pair_contour_panel_count(n_parameters: int) -> int:
        """Return the number of lower-triangle contour panels."""
        if n_parameters < MIN_POSTERIOR_PARAMETER_COUNT:
            return 1
        return n_parameters * (n_parameters - 1) // 2

    @classmethod
    def _posterior_pair_density_max_points(cls, n_parameters: int) -> int:
        """Return a KDE sample cap for interactive pair plots."""
        panel_count = cls._posterior_pair_contour_panel_count(n_parameters)
        estimated_limit = round(
            POSTERIOR_PAIR_TARGET_DENSITY_SAMPLE_BUDGET / panel_count,
        )
        return max(
            POSTERIOR_PAIR_MIN_DENSITY_SAMPLES,
            min(POSTERIOR_PAIR_MAX_DENSITY_SAMPLES, estimated_limit),
        )

    @classmethod
    def _posterior_pair_contour_grid_size(cls, n_parameters: int) -> int:
        """Return contour grid size for current pair-plot width."""
        panel_count = cls._posterior_pair_contour_panel_count(n_parameters)
        estimated_grid_size = round(
            np.sqrt(POSTERIOR_PAIR_TARGET_CONTOUR_GRID_POINT_BUDGET / panel_count),
        )
        return max(
            POSTERIOR_PAIR_MIN_CONTOUR_GRID_SIZE,
            min(POSTERIOR_PAIR_MAX_CONTOUR_GRID_SIZE, estimated_grid_size),
        )

    @staticmethod
    def _validated_posterior_pair_plot_style(
        style: PosteriorPairPlotStyleEnum | str,
    ) -> PosteriorPairPlotStyleEnum:
        """Return a validated posterior pair-plot rendering mode."""
        try:
            return PosteriorPairPlotStyleEnum(style)
        except ValueError as exc:
            supported_styles = ', '.join(item.value for item in PosteriorPairPlotStyleEnum)
            msg = f'style must be one of {supported_styles} for posterior pair plots.'
            raise ValueError(msg) from exc

    @staticmethod
    def _posterior_pair_show_contours(
        *,
        n_parameters: int,
        style: PosteriorPairPlotStyleEnum,
    ) -> bool:
        """Return whether contours should be rendered."""
        if style is PosteriorPairPlotStyleEnum.FULL:
            return True
        if style is PosteriorPairPlotStyleEnum.FAST:
            return False
        return n_parameters <= POSTERIOR_PAIR_AUTO_MAX_CONTOUR_PARAMETERS

    def _plot_axis_frame_color(self) -> str:
        """
        Return the shared axis-frame color for Plotly-backed plots.
        """
        axis_frame_color = getattr(self._backend, '_axis_frame_color', None)
        if callable(axis_frame_color):
            return axis_frame_color()
        return PlotlyPlotter._axis_frame_color()

    def _plot_legend_background_color(self) -> str:
        """Return the shared legend background for Plotly plots."""
        legend_background_color = getattr(self._backend, '_legend_background_color', None)
        if callable(legend_background_color):
            return legend_background_color()
        return PlotlyPlotter._legend_background_color()

    def _resolved_posterior_contour_surface(
        self,
        *,
        fit_results: object,
        x_parameter_name: str,
        y_parameter_name: str,
        x_values: np.ndarray,
        y_values: np.ndarray,
        grid_size: int,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray | None] | None:
        """Return cached or computed posterior contour surface data."""
        cached_surface = self._cached_posterior_pair_surface(
            x_parameter_name=x_parameter_name,
            y_parameter_name=y_parameter_name,
        )
        if cached_surface is not None:
            return cached_surface

        bounds = self._posterior_pair_bounds(
            fit_results=fit_results,
            x_parameter_name=x_parameter_name,
            y_parameter_name=y_parameter_name,
            x_values=x_values,
            y_values=y_values,
        )
        density_surface = self._posterior_pair_density_surface(
            x_values=x_values,
            y_values=y_values,
            x_bounds=bounds[0],
            y_bounds=bounds[1],
            grid_size=grid_size,
        )
        if density_surface is None:
            return None

        x_grid, y_grid, density = density_surface
        return x_grid, y_grid, density, None

    def _posterior_contour_traces(
        self,
        *,
        fit_results: object,
        x_parameter_name: str,
        y_parameter_name: str,
        x_values: np.ndarray,
        y_values: np.ndarray,
        grid_size: int,
    ) -> tuple[object, object] | None:
        """
        Return filled and line contour traces for posterior pair plots.
        """
        go = __import__('plotly.graph_objects', fromlist=['Contour'])

        surface = self._resolved_posterior_contour_surface(
            fit_results=fit_results,
            x_parameter_name=x_parameter_name,
            y_parameter_name=y_parameter_name,
            x_values=x_values,
            y_values=y_values,
            grid_size=grid_size,
        )
        if surface is None:
            return None

        x_grid, y_grid, density, contour_levels = surface

        fill_colorscale, line_colorscale = self._posterior_pair_contour_colorscales(
            x_values,
            y_values,
        )
        contour_start, contour_end, contour_size = self._posterior_contour_levels(
            density=density,
            contour_levels=contour_levels,
        )
        fill_density = np.array(density, copy=True)
        fill_density[fill_density < contour_start] = np.nan
        fill_trace = go.Contour(
            x=x_grid,
            y=y_grid,
            z=fill_density,
            contours={
                'coloring': 'fill',
                'showlabels': False,
                'showlines': False,
                'start': contour_start,
                'end': contour_end,
                'size': contour_size,
            },
            colorscale=fill_colorscale,
            zmin=contour_start,
            zmax=contour_end,
            connectgaps=False,
            hoverinfo='skip',
            showscale=False,
            showlegend=False,
            zorder=1,
        )
        line_trace = go.Contour(
            x=x_grid,
            y=y_grid,
            z=density,
            contours={
                'coloring': 'lines',
                'showlabels': False,
                'start': contour_start,
                'end': contour_end,
                'size': contour_size,
            },
            colorscale=line_colorscale,
            zmin=contour_start,
            zmax=contour_end,
            line={'width': 0.9},
            hoverinfo='skip',
            showscale=False,
            showlegend=False,
            zorder=2,
        )
        return fill_trace, line_trace

    def _cached_posterior_pair_surface(
        self,
        *,
        x_parameter_name: str,
        y_parameter_name: str,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray | None] | None:
        """
        Return a restored posterior pair-density surface when available.
        """
        if self._project is None:
            return None

        analysis = self._project.analysis
        sidecar_data = getattr(analysis, '_persisted_fit_state_sidecar', {})
        pair_caches = sidecar_data.get('pair_caches', {})
        for cache_data in pair_caches.values():
            cache_x = str(cache_data.get('param_unique_name_x', ''))
            cache_y = str(cache_data.get('param_unique_name_y', ''))
            if {cache_x, cache_y} != {x_parameter_name, y_parameter_name}:
                continue

            x_grid = np.asarray(cache_data.get('x'), dtype=float)
            y_grid = np.asarray(cache_data.get('y'), dtype=float)
            density = np.asarray(cache_data.get('density'), dtype=float)
            contour_levels = cache_data.get('contour_levels')
            if contour_levels is not None:
                contour_levels = np.asarray(contour_levels, dtype=float)

            if x_parameter_name != cache_x or y_parameter_name != cache_y:
                x_grid, y_grid = y_grid, x_grid
                if density.ndim == PAIR_DENSITY_SURFACE_NDIM:
                    density = density.T

            expected_shape = (y_grid.size, x_grid.size)
            if x_grid.ndim != 1 or y_grid.ndim != 1 or density.shape != expected_shape:
                log.warning(
                    'Persisted posterior pair cache is invalid for '
                    f'{x_parameter_name!r} and {y_parameter_name!r}.'
                )
                return None
            return x_grid, y_grid, density, contour_levels

        return None

    @staticmethod
    def _posterior_contour_levels(
        *,
        density: np.ndarray,
        contour_levels: np.ndarray | None,
    ) -> tuple[float, float, float]:
        """Return contour start, end, and step for pair density."""
        if contour_levels is not None and contour_levels.ndim == 1 and contour_levels.size > 0:
            finite_levels = contour_levels[np.isfinite(contour_levels)]
            if finite_levels.size > 0:
                start = float(finite_levels[0])
                end = float(finite_levels[-1])
                if finite_levels.size > 1:
                    size = float(np.min(np.diff(finite_levels)))
                else:
                    size = max(end - start, abs(end) * 0.15, 1e-6)
                if end > start and size > 0:
                    return start, end, size

        density_max = float(np.max(density))
        return (
            density_max * 0.20,
            density_max * 0.95,
            density_max * 0.15,
        )

    def _build_param_distribution_plot(
        self,
        param: object,
    ) -> object | None:
        """
        Build a Plotly posterior distribution plot for one parameter.

        Parameters
        ----------
        param : object
            Parameter descriptor to plot.

        Returns
        -------
        object | None
            Plotly figure, or ``None`` when posterior plotting is
            unavailable.
        """
        context = self._posterior_distribution_context(param)
        if context is None:
            return None

        go = __import__('plotly.graph_objects', fromlist=['Figure', 'Histogram'])
        fig, layout_factory = self._posterior_distribution_figure(
            go=go,
            title=context.title,
            label=context.label,
        )
        histogram_bin_edges = self._posterior_distribution_histogram_bin_edges(context.values)
        density_trace = self._posterior_density_trace(
            fit_results=context.fit_results,
            parameter_name=context.parameter_name,
            values=context.values,
            trace_name='Marginal density',
        )
        if density_trace is not None:
            self._style_posterior_pair_marginal_density_trace(density_trace)
            density_trace.hovertemplate = self._posterior_pair_density_hovertemplate(
                context.parameter_name
            )
        x_axis_range = self._posterior_distribution_x_axis_range(
            values=context.values,
            density_trace=density_trace,
            histogram_bin_edges=histogram_bin_edges,
        )
        y_axis_range = self._posterior_distribution_y_axis_range(
            values=context.values,
            density_trace=density_trace,
            histogram_bin_edges=histogram_bin_edges,
        )

        self._add_posterior_distribution_interval_traces(
            fig=fig,
            summary=context.summary,
            y_axis_range=y_axis_range,
        )
        self._add_posterior_distribution_histogram(
            fig=fig,
            go=go,
            values=context.values,
            histogram_bin_edges=histogram_bin_edges,
        )
        self._add_posterior_distribution_density_trace(fig=fig, density_trace=density_trace)
        self._add_posterior_distribution_reference_traces(
            fig=fig,
            summary=context.summary,
            values=context.values,
            y_axis_range=y_axis_range,
        )
        self._apply_posterior_distribution_layout(
            fig=fig,
            layout_factory=layout_factory,
            title=context.title,
            label=context.label,
            x_axis_range=x_axis_range,
            y_axis_range=y_axis_range,
        )
        panel_height = getattr(self._backend, '_single_main_panel_height_pixels', None)
        if callable(panel_height):
            fig.update_layout(height=panel_height(DEFAULT_RESID_HEIGHT))
        return fig

    def _plot_ascii_param_distribution(
        self,
        param: object,
    ) -> None:
        """Render one posterior marginal on the ASCII backend."""
        context = self._posterior_distribution_context(param)
        if context is None:
            return

        lower_bound, upper_bound = self._posterior_parameter_bounds(
            fit_results=context.fit_results,
            parameter_name=context.parameter_name,
        )
        density_curve = self._cached_posterior_density_curve(context.parameter_name)
        if density_curve is None:
            density_curve = self._posterior_density_curve(
                context.values,
                lower_bound=lower_bound,
                upper_bound=upper_bound,
            )
        if density_curve is None:
            log.warning(
                f'Posterior distribution is unavailable for parameter {context.parameter_name}.'
            )
            return

        grid, density = density_curve
        self._backend.plot_powder(
            x=grid,
            y_series=[density],
            labels=['density'],
            axes_labels=[context.label, 'Probability density'],
            title=context.title,
            height=self.height,
        )

    def _cached_posterior_density_curve(
        self,
        parameter_name: str,
    ) -> tuple[np.ndarray, np.ndarray] | None:
        """
        Return a restored posterior density curve for one parameter.
        """
        if self._project is None:
            return None

        sidecar_data = getattr(self._project.analysis, '_persisted_fit_state_sidecar', {})
        cache_data = sidecar_data.get('distribution_caches', {}).get(parameter_name)
        if cache_data is None:
            return None

        x_values = np.asarray(cache_data.get('x'), dtype=float)
        density_values = np.asarray(cache_data.get('density'), dtype=float)
        if x_values.ndim != 1 or density_values.shape != x_values.shape:
            log.warning(
                f'Persisted posterior distribution cache is invalid for {parameter_name!r}.'
            )
            return None
        return x_values, density_values

    def _posterior_distribution_context(
        self,
        param: object,
    ) -> _PosteriorDistributionContext | None:
        """Return the context for a posterior distribution plot."""
        fit_results = self._get_fit_result_for_correlation()
        if fit_results is None:
            return None

        posterior_samples = getattr(fit_results, 'posterior_samples', None)
        if posterior_samples is None:
            log.warning('Posterior samples are unavailable. Run a Bayesian fit first.')
            return None

        parameter_names = self._resolve_posterior_parameter_names(
            fit_results=fit_results,
            parameters=[param],
        )
        if parameter_names is None:
            return None

        parameter_name = parameter_names[0]
        samples = self._selected_posterior_samples(posterior_samples, [parameter_name])
        if samples is None:
            return None

        label = self._posterior_plot_labels(fit_results, [parameter_name])[0]
        return _PosteriorDistributionContext(
            fit_results=fit_results,
            parameter_name=parameter_name,
            values=samples[:, 0],
            label=label,
            title=f'Posterior distribution: {parameter_name}',
            summary=self._posterior_summary_by_name(fit_results).get(parameter_name),
        )

    def _posterior_distribution_figure(
        self,
        *,
        go: object,
        title: str,
        label: str,
    ) -> tuple[object, object | None]:
        """Return the figure and optional backend layout factory."""
        layout_factory = getattr(self._backend, '_get_layout', None)
        if callable(layout_factory):
            figure = go.Figure(layout=layout_factory(title, [label, 'Probability density']))
            return figure, layout_factory
        return go.Figure(), layout_factory

    def _posterior_distribution_y_axis_range(
        self,
        *,
        values: np.ndarray,
        density_trace: object | None,
        histogram_bin_edges: np.ndarray | None,
    ) -> tuple[float, float] | None:
        """Return the y-axis range for a posterior distribution plot."""
        density_sources = []
        histogram_density = self._posterior_distribution_histogram_density(
            values,
            histogram_bin_edges,
        )
        if histogram_density is not None:
            density_sources.append(histogram_density)
        if density_trace is not None:
            density_sources.append(np.asarray(density_trace.y, dtype=float))
        if not density_sources:
            return None
        return self._posterior_density_axis_range(np.concatenate(density_sources))

    @staticmethod
    def _posterior_distribution_x_axis_range(
        *,
        values: np.ndarray,
        density_trace: object | None,
        histogram_bin_edges: np.ndarray | None,
    ) -> tuple[float, float] | None:
        """Return the x-axis range for a posterior distribution plot."""
        if density_trace is not None:
            density_x = np.asarray(density_trace.x, dtype=float)
            return float(density_x[0]), float(density_x[-1])

        if histogram_bin_edges is not None:
            return (
                float(histogram_bin_edges[0]),
                float(histogram_bin_edges[-1]),
            )

        finite_values = np.asarray(values, dtype=float)
        finite_values = finite_values[np.isfinite(finite_values)]
        if finite_values.size == 0:
            return None
        return float(np.min(finite_values)), float(np.max(finite_values))

    @staticmethod
    def _posterior_distribution_histogram_bin_edges(values: np.ndarray) -> np.ndarray | None:
        """Return histogram bin edges used by the distribution plot."""
        finite_values = np.asarray(values, dtype=float)
        finite_values = finite_values[np.isfinite(finite_values)]
        if finite_values.size == 0:
            return None

        bin_edges = np.histogram_bin_edges(finite_values, bins='auto')
        if bin_edges.size >= MIN_POSTERIOR_SAMPLE_COUNT:
            return np.asarray(bin_edges, dtype=float)
        return None

    @staticmethod
    def _posterior_distribution_histogram_density(
        values: np.ndarray,
        histogram_bin_edges: np.ndarray | None,
    ) -> np.ndarray | None:
        """Return densities matching the rendered histogram bins."""
        if histogram_bin_edges is None:
            return None

        histogram_density, _ = np.histogram(
            np.asarray(values, dtype=float),
            bins=histogram_bin_edges,
            density=True,
        )
        return np.asarray(histogram_density, dtype=float)

    def _add_posterior_distribution_interval_traces(
        self,
        *,
        fig: object,
        summary: object | None,
        y_axis_range: tuple[float, float] | None,
    ) -> None:
        """Add credible-interval bands to the distribution plot."""
        if summary is None or y_axis_range is None:
            return

        fig.add_trace(
            self._posterior_interval_band_trace(
                x0=summary.interval_95[0],
                x1=summary.interval_95[1],
                y_axis_range=y_axis_range,
                trace_name='95% credible interval',
                color=POSTERIOR_INTERVAL_95_FILL_COLOR,
            )
        )

    @staticmethod
    def _add_posterior_distribution_histogram(
        *,
        fig: object,
        go: object,
        values: np.ndarray,
        histogram_bin_edges: np.ndarray | None,
    ) -> None:
        """Add the histogram trace for a posterior distribution plot."""
        marker = {
            'color': POSTERIOR_HISTOGRAM_FILL_COLOR,
            'line': {'color': POSTERIOR_HISTOGRAM_LINE_COLOR, 'width': 1},
        }
        densities = Plotter._posterior_distribution_histogram_density(
            values,
            histogram_bin_edges,
        )
        if densities is None or histogram_bin_edges is None:
            # Degenerate sample (no usable bins): let Plotly bin the few
            # raw values client-side; the embedded payload stays tiny.
            fig.add_trace(
                go.Histogram(
                    x=values,
                    histnorm='probability density',
                    marker=marker,
                    opacity=0.82,
                    name='Posterior histogram',
                    hovertemplate='sample=%{x:.4f}<br>density: %{y:.2f}<extra></extra>',
                )
            )
            return

        # Pre-bin server-side and emit a Bar trace so only the per-bin
        # densities ride in the page, not every raw posterior sample.
        # ``go.Histogram(x=values)`` serializes the full sample array
        # (hundreds of thousands of values per parameter), bloating the
        # docs page and stalling the "Loading plot…" skeleton paint.
        edges = np.asarray(histogram_bin_edges, dtype=float)
        bin_centers = (edges[:-1] + edges[1:]) / 2.0
        bin_widths = np.diff(edges)
        fig.add_trace(
            go.Bar(
                x=bin_centers,
                y=densities,
                width=bin_widths,
                marker=marker,
                opacity=0.82,
                name='Posterior histogram',
                hovertemplate='sample=%{x:.4f}<br>density: %{y:.2f}<extra></extra>',
            )
        )

    @staticmethod
    def _add_posterior_distribution_density_trace(
        *,
        fig: object,
        density_trace: object | None,
    ) -> None:
        """Add the KDE trace for a posterior distribution plot."""
        if density_trace is None:
            return

        density_trace.name = 'Marginal density'
        density_trace.showlegend = True
        fig.add_trace(density_trace)

    def _add_posterior_distribution_reference_traces(
        self,
        *,
        fig: object,
        summary: object | None,
        values: np.ndarray,
        y_axis_range: tuple[float, float] | None,
    ) -> None:
        """Add posterior median and MAP reference lines."""
        if y_axis_range is None:
            return

        fig.add_trace(
            self._posterior_reference_line_trace(
                x_value=float(np.median(values)),
                y_axis_range=y_axis_range,
                trace_name='Median',
                color=POSTERIOR_MEDIAN_LINE_COLOR,
                dash='dash',
            )
        )
        if summary is None:
            return

        fig.add_trace(
            self._posterior_reference_line_trace(
                x_value=summary.best_sample_value,
                y_axis_range=y_axis_range,
                trace_name=POSTERIOR_POINT_ESTIMATE_TRACE_NAME,
                color=POSTERIOR_POINT_ESTIMATE_LINE_COLOR,
                dash=POSTERIOR_POINT_ESTIMATE_LINE_DASH,
            )
        )

    @staticmethod
    def _apply_posterior_distribution_layout(
        *,
        fig: object,
        layout_factory: object | None,
        title: str,
        label: str,
        x_axis_range: tuple[float, float] | None,
        y_axis_range: tuple[float, float] | None,
    ) -> None:
        """Apply layout settings to the distribution plot."""
        if callable(layout_factory):
            fig.update_layout(
                title={
                    'text': title,
                    'font': {'size': POSTERIOR_PAIR_TITLE_FONT_SIZE},
                }
            )
        else:
            fig.update_layout(
                title={
                    'text': title,
                    'font': {'size': POSTERIOR_PAIR_TITLE_FONT_SIZE},
                },
                xaxis_title=label,
                yaxis_title='Probability density',
                legend={
                    'bgcolor': 'rgba(0, 0, 0, 0)',
                    'xanchor': 'right',
                    'x': 1.0,
                    'yanchor': 'top',
                    'y': 1.0,
                },
            )
            fig.update_xaxes(title_font={'size': POSTERIOR_PAIR_AXIS_TITLE_FONT_SIZE})
            fig.update_yaxes(title_font={'size': POSTERIOR_PAIR_AXIS_TITLE_FONT_SIZE})
        if x_axis_range is not None:
            fig.update_xaxes(range=list(x_axis_range))
        if y_axis_range is not None:
            fig.update_yaxes(range=list(y_axis_range))

    def _show_plot_figure(self, figure: object) -> None:
        """Display a figure through the active backend when possible."""
        show_figure = getattr(self._backend, '_show_figure', None)
        if callable(show_figure):
            show_figure(figure)
            return
        figure.show()

    @staticmethod
    def _style_posterior_pair_marginal_density_trace(density_trace: object) -> None:
        """Apply pair-plot-specific styling to a marginal KDE trace."""
        density_trace.line = {
            'color': POSTERIOR_PAIR_MARGINAL_DENSITY_LINE_COLOR,
            'width': POSTERIOR_PAIR_MARGINAL_DENSITY_LINE_WIDTH,
        }
        density_trace.fillcolor = POSTERIOR_PAIR_MARGINAL_DENSITY_FILL_COLOR

    @staticmethod
    def _posterior_pair_density_hovertemplate(parameter_name: str) -> str:
        """Return the hover template for a marginal density trace."""
        return f'{parameter_name}: %{{x:.4f}}<br>density: %{{y:.4f}}<extra></extra>'

    @staticmethod
    def _posterior_pair_scatter_hovertemplate(
        *,
        x_parameter_name: str,
        y_parameter_name: str,
    ) -> str:
        """Return the hover template for pair-plot sample points."""
        return f'{x_parameter_name}: %{{x:.4f}}<br>{y_parameter_name}: %{{y:.4f}}<extra></extra>'

    @staticmethod
    def _posterior_pair_correlation_value(
        x_values: np.ndarray,
        y_values: np.ndarray,
    ) -> float | None:
        """Return the sample correlation for one contour panel."""
        finite_mask = np.isfinite(x_values) & np.isfinite(y_values)
        if np.count_nonzero(finite_mask) < MIN_POSTERIOR_SAMPLE_COUNT:
            return None

        correlation_matrix = np.corrcoef(x_values[finite_mask], y_values[finite_mask])
        correlation_value = float(correlation_matrix[0, 1])
        if not np.isfinite(correlation_value):
            return None
        return correlation_value

    @staticmethod
    def _posterior_pair_contour_colorscales(
        x_values: np.ndarray,
        y_values: np.ndarray,
    ) -> tuple[list[list[float | str]], list[list[float | str]]]:
        """Return sign-aware contour palettes for one panel."""
        correlation_value = Plotter._posterior_pair_correlation_value(x_values, y_values)
        if correlation_value is not None and correlation_value < 0:
            return (
                POSTERIOR_NEGATIVE_CONTOUR_FILL_COLORSCALE,
                POSTERIOR_NEGATIVE_CONTOUR_LINE_COLORSCALE,
            )
        return POSTERIOR_CONTOUR_FILL_COLORSCALE, POSTERIOR_CONTOUR_LINE_COLORSCALE

    def _posterior_density_trace(
        self,
        *,
        fit_results: object,
        parameter_name: str,
        values: np.ndarray,
        trace_name: str,
    ) -> object | None:
        """Return a filled KDE trace for one posterior marginal."""
        go = __import__('plotly.graph_objects', fromlist=['Scatter'])

        lower_bound, upper_bound = self._posterior_parameter_bounds(
            fit_results=fit_results,
            parameter_name=parameter_name,
        )
        density_curve = self._cached_posterior_density_curve(parameter_name)
        if density_curve is None:
            density_curve = self._posterior_density_curve(
                values,
                lower_bound=lower_bound,
                upper_bound=upper_bound,
            )
        if density_curve is None:
            return None

        grid, density = density_curve
        return go.Scatter(
            x=grid,
            y=density,
            mode='lines',
            line={'color': POSTERIOR_DENSITY_LINE_COLOR, 'width': 2},
            fill='tozeroy',
            fillcolor=POSTERIOR_DENSITY_FILL_COLOR,
            name=trace_name,
            showlegend=False,
            hovertemplate='%{x:.4f}<br>density: %{y:.2f}<extra></extra>',
        )

    @staticmethod
    def _posterior_density_axis_range(
        density_values: np.ndarray,
    ) -> tuple[float, float] | None:
        """Return a padded y-axis range for posterior density plots."""
        data = np.asarray(density_values, dtype=float)
        data = data[np.isfinite(data)]
        if data.size == 0:
            return None

        data_min = float(np.min(data))
        data_max = float(np.max(data))
        data_range = data_max - data_min
        upper_padding = 0.08 * data_range if data_range > 0 else max(abs(data_max), 1.0) * 0.05
        if upper_padding == 0:
            upper_padding = 1e-6
        lower = min(0.0, data_min)
        return lower, data_max + upper_padding

    @staticmethod
    def _posterior_interval_band_trace(
        *,
        x0: float,
        x1: float,
        y_axis_range: tuple[float, float],
        trace_name: str,
        color: str,
    ) -> object:
        """Return a hideable credible-interval band trace."""
        go = __import__('plotly.graph_objects', fromlist=['Scatter'])

        return go.Scatter(
            x=[x0, x1, x1, x0, x0],
            y=[
                y_axis_range[0],
                y_axis_range[0],
                y_axis_range[1],
                y_axis_range[1],
                y_axis_range[0],
            ],
            mode='lines',
            fill='toself',
            fillcolor=color,
            line={'color': color, 'width': 0},
            name=trace_name,
            showlegend=True,
            hoverinfo='skip',
        )

    @staticmethod
    def _posterior_reference_line_trace(
        *,
        x_value: float,
        y_axis_range: tuple[float, float],
        trace_name: str,
        color: str,
        dash: str,
    ) -> object:
        """
        Return a named vertical reference line for posterior plots.
        """
        go = __import__('plotly.graph_objects', fromlist=['Scatter'])

        return go.Scatter(
            x=[x_value, x_value],
            y=[y_axis_range[0], y_axis_range[1]],
            mode='lines',
            line={'color': color, 'width': 2, 'dash': dash},
            name=trace_name,
            showlegend=True,
            hovertemplate=f'{trace_name}: %{{x:.4f}}<extra></extra>',
        )

    @staticmethod
    def _posterior_parameter_bounds(
        *,
        fit_results: object,
        parameter_name: str,
    ) -> tuple[float | None, float | None]:
        """Return finite fit bounds for a posterior parameter."""
        parameters_by_name = {
            getattr(parameter, 'unique_name', ''): parameter
            for parameter in fit_results.parameters
        }
        parameter = parameters_by_name.get(parameter_name)
        if parameter is None:
            return None, None

        lower_bound = getattr(parameter, 'fit_min', None)
        upper_bound = getattr(parameter, 'fit_max', None)
        lower = (
            float(lower_bound)
            if lower_bound is not None and np.isfinite(float(lower_bound))
            else None
        )
        upper = (
            float(upper_bound)
            if upper_bound is not None and np.isfinite(float(upper_bound))
            else None
        )
        return lower, upper

    @classmethod
    def _posterior_pair_bounds(
        cls,
        *,
        fit_results: object,
        x_parameter_name: str,
        y_parameter_name: str,
        x_values: np.ndarray,
        y_values: np.ndarray,
    ) -> tuple[tuple[float, float], tuple[float, float]]:
        """Return plotting bounds for a posterior pair panel."""
        x_lower, x_upper = cls._posterior_parameter_bounds(
            fit_results=fit_results,
            parameter_name=x_parameter_name,
        )
        y_lower, y_upper = cls._posterior_parameter_bounds(
            fit_results=fit_results,
            parameter_name=y_parameter_name,
        )
        return (
            cls._posterior_axis_bounds(x_values, lower_bound=x_lower, upper_bound=x_upper),
            cls._posterior_axis_bounds(y_values, lower_bound=y_lower, upper_bound=y_upper),
        )

    @staticmethod
    def _posterior_axis_bounds(
        values: np.ndarray,
        *,
        lower_bound: float | None,
        upper_bound: float | None,
    ) -> tuple[float, float]:
        """Return finite plotting bounds for one posterior axis."""
        data = np.asarray(values, dtype=float)
        data = data[np.isfinite(data)]
        data_min = float(np.min(data))
        data_max = float(np.max(data))
        data_range = data_max - data_min
        padding = 0.05 * data_range if data_range > 0 else max(abs(data_min), 1.0) * 0.05
        if padding == 0:
            padding = 1e-6

        resolved_lower = lower_bound if lower_bound is not None else data_min - padding
        resolved_upper = upper_bound if upper_bound is not None else data_max + padding
        return float(resolved_lower), float(resolved_upper)

    @classmethod
    def _posterior_density_curve(
        cls,
        values: np.ndarray,
        *,
        lower_bound: float | None,
        upper_bound: float | None,
        grid_size: int = 256,
    ) -> tuple[np.ndarray, np.ndarray] | None:
        """Estimate a boundary-aware posterior density curve."""
        gaussian_kde = __import__('scipy.stats', fromlist=['gaussian_kde']).gaussian_kde

        data = np.asarray(values, dtype=float)
        data = data[np.isfinite(data)]
        if data.size < MIN_POSTERIOR_SAMPLE_COUNT:
            return None

        data_min = float(np.min(data))
        data_max = float(np.max(data))
        data_range = data_max - data_min
        padding = 0.05 * data_range if data_range > 0 else max(abs(data_min), 1.0) * 0.05
        if padding == 0:
            padding = 1e-6

        grid_lower = lower_bound if lower_bound is not None else data_min - padding
        grid_upper = upper_bound if upper_bound is not None else data_max + padding
        if grid_upper <= grid_lower:
            return None

        grid = np.linspace(grid_lower, grid_upper, num=grid_size)
        if np.allclose(data, data[0]):
            bandwidth = max(abs(data[0]) * 0.01, 1e-6)
            density = np.exp(-0.5 * ((grid - data[0]) / bandwidth) ** 2)
            density /= bandwidth * np.sqrt(2.0 * np.pi)
        else:
            kde = gaussian_kde(data)
            density = cls._evaluate_reflected_1d_kde(
                kde,
                grid,
                lower_bound=lower_bound,
                upper_bound=upper_bound,
            )

        area = np.trapezoid(density, grid)
        if area <= 0:
            return None
        return grid, density / area

    @classmethod
    def _posterior_pair_density_surface(
        cls,
        *,
        x_values: np.ndarray,
        y_values: np.ndarray,
        x_bounds: tuple[float, float],
        y_bounds: tuple[float, float],
        grid_size: int = 96,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray] | None:
        """Estimate a 2D KDE surface for a posterior pair panel."""
        gaussian_kde = __import__('scipy.stats', fromlist=['gaussian_kde']).gaussian_kde

        x_data = np.asarray(x_values, dtype=float)
        y_data = np.asarray(y_values, dtype=float)
        mask = np.isfinite(x_data) & np.isfinite(y_data)
        x_data = x_data[mask]
        y_data = y_data[mask]
        if x_data.size < MIN_POSTERIOR_SAMPLE_COUNT or y_data.size < MIN_POSTERIOR_SAMPLE_COUNT:
            return None

        if np.allclose(x_data, x_data[0]) and np.allclose(y_data, y_data[0]):
            return None

        pair_data = np.vstack([x_data, y_data])
        covariance = np.cov(pair_data)
        if np.linalg.matrix_rank(covariance) < FULL_POSTERIOR_PAIR_COVARIANCE_RANK:
            return None

        x_grid = np.linspace(x_bounds[0], x_bounds[1], num=grid_size)
        y_grid = np.linspace(y_bounds[0], y_bounds[1], num=grid_size)
        mesh_x, mesh_y = np.meshgrid(x_grid, y_grid)
        try:
            density = cls._evaluate_reflected_2d_kde(
                gaussian_kde(pair_data),
                mesh_x=mesh_x,
                mesh_y=mesh_y,
                x_bounds=x_bounds,
                y_bounds=y_bounds,
            )
        except (np.linalg.LinAlgError, ValueError):
            return None
        if not np.any(np.isfinite(density)):
            return None
        return x_grid, y_grid, density

    @staticmethod
    def _reflection_positions_1d(
        values: np.ndarray,
        *,
        lower_bound: float | None,
        upper_bound: float | None,
    ) -> list[np.ndarray]:
        """Return mirrored positions for boundary-corrected KDEs."""
        reflected = [values]
        if lower_bound is not None:
            reflected.append(2.0 * lower_bound - values)
        if upper_bound is not None:
            reflected.append(2.0 * upper_bound - values)
        return reflected

    @classmethod
    def _evaluate_reflected_1d_kde(
        cls,
        kde: object,
        grid: np.ndarray,
        *,
        lower_bound: float | None,
        upper_bound: float | None,
    ) -> np.ndarray:
        """Evaluate a 1D KDE using mirrored-boundary correction."""
        density = np.zeros_like(grid, dtype=float)
        for reflected_grid in cls._reflection_positions_1d(
            grid,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
        ):
            density += np.asarray(kde(reflected_grid), dtype=float)
        return density

    @classmethod
    def _evaluate_reflected_2d_kde(
        cls,
        kde: object,
        *,
        mesh_x: np.ndarray,
        mesh_y: np.ndarray,
        x_bounds: tuple[float, float],
        y_bounds: tuple[float, float],
    ) -> np.ndarray:
        """Evaluate a 2D KDE using mirrored-boundary correction."""
        x_positions = cls._reflection_positions_1d(
            mesh_x.ravel(),
            lower_bound=x_bounds[0],
            upper_bound=x_bounds[1],
        )
        y_positions = cls._reflection_positions_1d(
            mesh_y.ravel(),
            lower_bound=y_bounds[0],
            upper_bound=y_bounds[1],
        )
        density = np.zeros(mesh_x.size, dtype=float)
        for reflected_x in x_positions:
            for reflected_y in y_positions:
                positions = np.vstack([reflected_x, reflected_y])
                density += np.asarray(kde(positions), dtype=float)
        return density.reshape(mesh_x.shape)

    def _get_or_build_posterior_predictive_summary(
        self,
        *,
        experiment: object,
        expt_name: str,
        x_axis: object,
        include_draws: bool = True,
    ) -> object | None:
        """Return a cached or built predictive summary."""
        fit_results = self._get_fit_result_for_correlation()
        if fit_results is None:
            return None

        posterior_predictive = getattr(fit_results, 'posterior_predictive', None)
        if posterior_predictive is None:
            return None

        x_axis_name = getattr(x_axis, 'value', x_axis)
        draw_cache_key = posterior_predictive_cache_key(
            expt_name,
            str(x_axis_name),
            include_draws=True,
        )
        band_cache_key = posterior_predictive_cache_key(
            expt_name,
            str(x_axis_name),
            include_draws=False,
        )
        cache_key = draw_cache_key if include_draws else band_cache_key
        summary = posterior_predictive.get(cache_key)
        if summary is None and not include_draws:
            summary = posterior_predictive.get(draw_cache_key)
        if summary is None:
            summary = posterior_predictive.get(expt_name)
            summary_x_axis = getattr(summary, 'x_axis_name', None)
            if summary is not None and str(summary_x_axis) != str(x_axis_name):
                summary = None
        if summary is not None:
            return summary

        posterior_samples = getattr(fit_results, 'posterior_samples', None)
        if posterior_samples is None:
            return None

        summary = self._build_posterior_predictive_summary(
            fit_results=fit_results,
            experiment=experiment,
            expt_name=expt_name,
            x_axis=x_axis,
            include_draws=include_draws,
        )
        if summary is None:
            return None

        posterior_predictive[cache_key] = summary
        return summary

    def _build_posterior_predictive_summary(
        self,
        *,
        fit_results: object,
        experiment: object,
        expt_name: str,
        x_axis: object,
        include_draws: bool = True,
    ) -> object | None:
        """Build posterior predictive summaries from posterior draws."""
        sampling_inputs = self._posterior_predictive_sampling_inputs(fit_results)
        if sampling_inputs is None:
            return None

        flattened_samples, parameter_names = sampling_inputs
        sampled_parameters = self._posterior_predictive_parameters(
            fit_results=fit_results,
            parameter_names=parameter_names,
        )
        if sampled_parameters is None:
            return None

        predictive_data = self._evaluate_posterior_predictive_draws(
            flattened_samples=flattened_samples,
            sampled_parameters=sampled_parameters,
            experiment=experiment,
            expt_name=expt_name,
            x_axis=x_axis,
        )
        if predictive_data is None:
            return None

        best_sample_prediction, x_values, predictive_draw_array = predictive_data
        lower_68, upper_68 = np.quantile(predictive_draw_array, [0.16, 0.84], axis=0)
        lower_95, upper_95 = np.quantile(predictive_draw_array, [0.025, 0.975], axis=0)
        x_axis_name = getattr(x_axis, 'value', x_axis)

        return PosteriorPredictiveSummary(
            experiment_name=expt_name,
            x_axis_name=str(x_axis_name),
            x=np.asarray(x_values, dtype=float),
            best_sample_prediction=np.asarray(best_sample_prediction, dtype=float),
            lower_95=np.asarray(lower_95, dtype=float),
            upper_95=np.asarray(upper_95, dtype=float),
            lower_68=np.asarray(lower_68, dtype=float),
            upper_68=np.asarray(upper_68, dtype=float),
            draws=predictive_draw_array if include_draws else None,
        )

    @staticmethod
    def _posterior_predictive_sampling_inputs(
        fit_results: object,
    ) -> tuple[np.ndarray, list[str]] | None:
        """Return predictive-sampling arrays and parameter names."""
        posterior_samples = getattr(fit_results, 'posterior_samples', None)
        if posterior_samples is None:
            return None

        flattened_samples = np.asarray(posterior_samples.flattened(), dtype=float)
        parameter_names = getattr(posterior_samples, 'parameter_names', None)
        if flattened_samples.ndim != POSTERIOR_FLATTENED_SAMPLE_NDIM or not parameter_names:
            log.warning('Posterior samples are unavailable for predictive summaries.')
            return None
        return flattened_samples, list(parameter_names)

    @staticmethod
    def _posterior_predictive_parameters(
        *,
        fit_results: object,
        parameter_names: list[str],
    ) -> list[object] | None:
        """Return fitted parameters in posterior sample order."""
        parameters_by_name = {
            getattr(parameter, 'unique_name', ''): parameter
            for parameter in fit_results.parameters
        }
        sampled_parameters: list[object] = []
        for name in parameter_names:
            parameter = parameters_by_name.get(name)
            if parameter is None:
                log.warning(
                    'Posterior predictive summaries require matching fitted parameters for '
                    f"'{name}'."
                )
                return None
            sampled_parameters.append(parameter)
        return sampled_parameters

    def _evaluate_posterior_predictive_draws(
        self,
        *,
        flattened_samples: np.ndarray,
        sampled_parameters: list[object],
        experiment: object,
        expt_name: str,
        x_axis: object,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray] | None:
        """Return best-sample and sampled predictive curves."""
        original_values = np.array(
            [parameter.value for parameter in sampled_parameters],
            dtype=float,
        )
        original_uncertainties = [parameter.uncertainty for parameter in sampled_parameters]
        draw_indices = self._posterior_predictive_draw_indices(flattened_samples.shape[0])

        try:
            evaluated = self._evaluate_posterior_predictive_draw_values(
                draw_indices=draw_indices,
                flattened_samples=flattened_samples,
                sampled_parameters=sampled_parameters,
                experiment=experiment,
                expt_name=expt_name,
                x_axis=x_axis,
                original_values=original_values,
            )
        finally:
            self._restore_posterior_predictive_parameters(
                sampled_parameters=sampled_parameters,
                original_values=original_values,
                original_uncertainties=original_uncertainties,
                expt_name=expt_name,
            )

        if evaluated is None:
            return None
        best_sample_prediction, x_values, predictive_draws = evaluated
        return (
            np.asarray(best_sample_prediction, dtype=float),
            np.asarray(x_values, dtype=float),
            np.asarray(predictive_draws, dtype=float),
        )

    def _evaluate_posterior_predictive_draw_values(
        self,
        *,
        draw_indices: np.ndarray,
        flattened_samples: np.ndarray,
        sampled_parameters: list[object],
        experiment: object,
        expt_name: str,
        x_axis: object,
        original_values: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray, list[np.ndarray]] | None:
        """Evaluate posterior predictive best sample and draw curves."""
        best_sample_prediction, x_values = self._evaluate_posterior_predictive_state(
            sampled_parameters=sampled_parameters,
            values=original_values,
            experiment=experiment,
            expt_name=expt_name,
            x_axis=x_axis,
        )
        if best_sample_prediction is None or x_values is None:
            return None

        predictive_draws: list[np.ndarray] = []
        for index in draw_indices:
            prediction, current_x = self._evaluate_posterior_predictive_state(
                sampled_parameters=sampled_parameters,
                values=flattened_samples[index],
                experiment=experiment,
                expt_name=expt_name,
                x_axis=x_axis,
            )
            if prediction is None or current_x is None:
                return None
            if (
                prediction.shape != best_sample_prediction.shape
                or current_x.shape != x_values.shape
            ):
                log.warning('Posterior predictive draws returned inconsistent array shapes.')
                return None
            predictive_draws.append(prediction)

        return best_sample_prediction, x_values, predictive_draws

    def _restore_posterior_predictive_parameters(
        self,
        *,
        sampled_parameters: list[object],
        original_values: np.ndarray,
        original_uncertainties: list[float | None],
        expt_name: str,
    ) -> None:
        """Restore parameter state after predictive sampling."""
        for parameter, value, uncertainty in zip(
            sampled_parameters,
            original_values,
            original_uncertainties,
            strict=True,
        ):
            parameter._set_value_from_minimizer(float(value))
            parameter.uncertainty = uncertainty
        self._update_project_categories(expt_name)

    def _evaluate_posterior_predictive_state(
        self,
        *,
        sampled_parameters: list[object],
        values: np.ndarray,
        experiment: object,
        expt_name: str,
        x_axis: object,
    ) -> tuple[np.ndarray | None, np.ndarray | None]:
        """Evaluate one posterior predictive state for an experiment."""
        for parameter, value in zip(sampled_parameters, values, strict=True):
            parameter._set_value_from_minimizer(float(value))

        self._update_project_categories(expt_name)
        pattern = intensity_category_for(experiment)
        x_name = getattr(x_axis, 'value', x_axis)
        x_values = getattr(pattern, x_name, None)
        y_calc = getattr(pattern, 'intensity_calc', None)
        if x_values is None or y_calc is None:
            log.warning(
                f'Posterior predictive data is unavailable for experiment {expt_name}. '
                'Ensure calculated intensities and the selected x axis are available.'
            )
            return None, None

        return np.asarray(y_calc, dtype=float), np.asarray(x_values, dtype=float)

    @staticmethod
    def _posterior_predictive_draw_indices(n_draws: int) -> np.ndarray:
        """
        Select evenly spaced posterior draws for predictive summaries.
        """
        if n_draws <= DEFAULT_POSTERIOR_PREDICTIVE_DRAWS:
            return np.arange(n_draws, dtype=int)

        return np.unique(
            np.linspace(
                0,
                n_draws - 1,
                num=DEFAULT_POSTERIOR_PREDICTIVE_DRAWS,
                dtype=int,
            )
        )

    def _get_posterior_samples_and_fit_results(
        self,
    ) -> tuple[object | None, object | None]:
        """Return posterior samples and fit results for plotting."""
        if self.engine != PlotterEngineEnum.PLOTLY.value:
            log.warning('Posterior plots currently require the Plotly plotting backend.')
            return None, None

        fit_results = self._get_fit_result_for_correlation()
        if fit_results is None:
            return None, None

        posterior_samples = getattr(fit_results, 'posterior_samples', None)
        if posterior_samples is None:
            log.warning('Posterior samples are unavailable. Run a Bayesian fit first.')
            return None, None

        return posterior_samples, fit_results

    def _plot_posterior_predictive_summary(
        self,
        *,
        expt_name: str,
        summary: object,
        y_meas: np.ndarray,
        axes_labels: list[str],
        show_band: bool,
        show_draws: bool,
        excluded_ranges: tuple[tuple[float, float], ...] = (),
    ) -> None:
        """
        Render posterior predictive summaries using the active backend.
        """
        if self.engine == PlotterEngineEnum.ASCII.value:
            self._plot_ascii_posterior_predictive_lines(
                expt_name=expt_name,
                x=np.asarray(summary.x, dtype=float),
                y_meas=np.asarray(y_meas, dtype=float),
                y_calc=np.asarray(summary.best_sample_prediction, dtype=float),
                axes_labels=axes_labels,
                excluded_ranges=excluded_ranges,
            )
            return

        go = __import__('plotly.graph_objects', fromlist=['Figure', 'Scatter'])
        axis_frame_color = self._plot_axis_frame_color()

        fig = go.Figure()
        if show_band:
            fig.add_trace(
                go.Scatter(
                    x=summary.x,
                    y=summary.lower_95,
                    mode='lines',
                    line={'color': 'rgba(0, 0, 0, 0)'},
                    hoverinfo='skip',
                    showlegend=False,
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=summary.x,
                    y=summary.upper_95,
                    mode='lines',
                    line={'color': 'rgba(0, 0, 0, 0)'},
                    fill='tonexty',
                    fillcolor=POSTERIOR_INTERVAL_95_FILL_COLOR,
                    name=POSTERIOR_PREDICTIVE_INTERVAL_TRACE_NAME,
                    hoverinfo='skip',
                    legendrank=30,
                )
            )

        if show_draws:
            draws = getattr(summary, 'draws', None)
            if draws is None:
                log.warning('Posterior predictive draws are unavailable for plotting.')
                return

            draw_cap = min(len(draws), DEFAULT_POSTERIOR_PREDICTIVE_DRAW_PLOT_CAP)
            for index in range(draw_cap):
                fig.add_trace(
                    go.Scatter(
                        x=summary.x,
                        y=draws[index],
                        mode='lines',
                        line={'color': POSTERIOR_DRAW_LINE_COLOR, 'width': 1},
                        name='Posterior draw' if index == 0 else None,
                        showlegend=index == 0,
                        legendrank=40,
                    )
                )

        fig.add_trace(
            go.Scatter(
                x=summary.x,
                y=y_meas,
                mode='lines+markers',
                line={'color': 'rgb(31, 119, 180)', 'width': 1.5},
                name='Measured',
                legendrank=10,
            )
        )
        fig.add_trace(
            go.Scatter(
                x=summary.x,
                y=summary.best_sample_prediction,
                mode='lines',
                line={
                    'color': POSTERIOR_POINT_ESTIMATE_LINE_COLOR,
                    'width': 2,
                    'dash': POSTERIOR_POINT_ESTIMATE_LINE_DASH,
                },
                name=POSTERIOR_POINT_ESTIMATE_TRACE_NAME,
                legendrank=20,
            )
        )
        for start, end in excluded_ranges:
            fig.add_vrect(
                x0=start,
                x1=end,
                fillcolor='rgba(120, 120, 120, 0.16)',
                opacity=1.0,
                line_width=0,
                layer='below',
            )
        fig.update_layout(
            title={
                'text': f"Posterior predictive for experiment 🔬 '{expt_name}'",
                'font': {'size': POSTERIOR_PAIR_TITLE_FONT_SIZE},
            },
            margin={
                'autoexpand': True,
                'r': 30,
                't': 40,
                'b': 45,
            },
            legend={
                'bgcolor': self._plot_legend_background_color(),
                'xanchor': 'right',
                'x': 0.99,
                'yanchor': 'top',
                'y': 0.99,
            },
            xaxis_title=axes_labels[0],
            yaxis_title=axes_labels[1],
        )
        fig.update_xaxes(
            title_font={'size': POSTERIOR_PAIR_AXIS_TITLE_FONT_SIZE},
            showline=True,
            linecolor=axis_frame_color,
            mirror=True,
            zeroline=False,
        )
        fig.update_yaxes(
            title_font={'size': POSTERIOR_PAIR_AXIS_TITLE_FONT_SIZE},
            showline=True,
            linecolor=axis_frame_color,
            mirror=True,
            zeroline=False,
        )
        self._show_plot_figure(fig)

    def _plot_ascii_posterior_predictive_lines(
        self,
        *,
        expt_name: str,
        x: np.ndarray,
        y_meas: np.ndarray,
        y_calc: np.ndarray,
        axes_labels: list[str],
        excluded_ranges: tuple[tuple[float, float], ...] = (),
    ) -> None:
        """Render posterior predictive lines on the ASCII backend."""
        self._backend.plot_powder(
            x=x,
            y_series=[y_meas, y_calc],
            labels=['meas', 'posterior'],
            axes_labels=axes_labels,
            title=f"Posterior predictive for experiment 🔬 '{expt_name}'",
            height=self.height,
            excluded_ranges=excluded_ranges,
        )

    def _plot_single_crystal_posterior_predictive_summary(
        self,
        *,
        expt_name: str,
        summary: PosteriorPredictiveSummary,
        y_meas: np.ndarray,
        y_meas_su: np.ndarray,
        axes_labels: list[str],
    ) -> None:
        """Render single-crystal posterior predictive checks."""
        if summary.lower_95 is None or summary.upper_95 is None:
            log.warning(
                'Single-crystal posterior predictive plots require 95% predictive intervals.'
            )
            return

        best_sample_prediction = np.asarray(summary.best_sample_prediction, dtype=float)
        lower_95 = np.asarray(summary.lower_95, dtype=float)
        upper_95 = np.asarray(summary.upper_95, dtype=float)
        if (
            lower_95.shape != best_sample_prediction.shape
            or upper_95.shape != best_sample_prediction.shape
        ):
            log.warning('Single-crystal posterior predictive interval arrays have invalid shapes.')
            return

        go = __import__('plotly.graph_objects', fromlist=['Figure'])
        trace = PlotlyPlotter._get_single_crystal_trace(
            x_calc=best_sample_prediction,
            y_meas=y_meas,
            y_meas_su=y_meas_su,
        )
        trace.error_x = {
            'type': 'data',
            'array': np.maximum(0.0, upper_95 - best_sample_prediction),
            'arrayminus': np.maximum(0.0, best_sample_prediction - lower_95),
            'visible': True,
        }
        trace.customdata = np.column_stack((lower_95, upper_95, y_meas_su))
        trace.hovertemplate = (
            'Predicted I²: %{x:,.2f}<br>'
            '95% credible interval: [%{customdata[0]:,.2f}, %{customdata[1]:,.2f}]<br>'
            'Measured I²: %{y:,.2f}<br>'
            'su(I²meas): %{customdata[2]:,.2f}<extra></extra>'
        )

        fig = go.Figure(
            data=[trace],
            layout=PlotlyPlotter._get_layout(
                f"Posterior predictive reflection check for experiment 🔬 '{expt_name}'",
                axes_labels,
                shapes=[PlotlyPlotter._get_diagonal_shape()],
            ),
        )
        self._show_plot_figure(fig)

    def _filtered_posterior_predictive_summary(
        self,
        *,
        summary: PosteriorPredictiveSummary,
        x_min: float,
        x_max: float,
        include_draws: bool,
    ) -> PosteriorPredictiveSummary | None:
        """Return a predictive summary filtered to an x-range."""
        x_filtered = self._filtered_y_array(summary.x, summary.x, x_min, x_max)
        if np.asarray(x_filtered).size == 0:
            return None

        draws = None
        if include_draws and summary.draws is not None:
            draws = np.asarray(
                [self._filtered_y_array(draw, summary.x, x_min, x_max) for draw in summary.draws],
                dtype=float,
            )

        return PosteriorPredictiveSummary(
            experiment_name=summary.experiment_name,
            x_axis_name=summary.x_axis_name,
            x=x_filtered,
            best_sample_prediction=self._filtered_y_array(
                summary.best_sample_prediction,
                summary.x,
                x_min,
                x_max,
            ),
            lower_95=(
                None
                if summary.lower_95 is None
                else self._filtered_y_array(summary.lower_95, summary.x, x_min, x_max)
            ),
            upper_95=(
                None
                if summary.upper_95 is None
                else self._filtered_y_array(summary.upper_95, summary.x, x_min, x_max)
            ),
            lower_68=(
                None
                if summary.lower_68 is None
                else self._filtered_y_array(summary.lower_68, summary.x, x_min, x_max)
            ),
            upper_68=(
                None
                if summary.upper_68 is None
                else self._filtered_y_array(summary.upper_68, summary.x, x_min, x_max)
            ),
            draws=draws,
        )

    def _plot_posterior_predictive_data(
        self,
        *,
        experiment: object,
        expt_name: str,
        plot_options: _MeasVsCalcPlotOptions,
        x_axis: object,
        style: str,
    ) -> None:
        """Render posterior predictive curves on the powder layout."""
        show_draws = self.engine == PlotterEngineEnum.PLOTLY.value and style in {
            'draws',
            'band+draws',
        }
        pattern = intensity_category_for(experiment)
        ctx = self._prepare_powder_context(
            pattern,
            expt_name,
            experiment.type,
            plot_options.x_min,
            plot_options.x_max,
            plot_options.x,
        )
        if ctx is None:
            return

        summary = self._get_or_build_posterior_predictive_summary(
            experiment=experiment,
            expt_name=expt_name,
            x_axis=x_axis,
            include_draws=show_draws,
        )
        if summary is None:
            return

        y_meas = self._filtered_y_array(
            pattern.intensity_meas,
            ctx['x_array'],
            ctx['x_min'],
            ctx['x_max'],
        )
        y_bkg = self._filtered_optional_y_array(
            getattr(pattern, 'intensity_bkg', None),
            ctx['x_array'],
            ctx['x_min'],
            ctx['x_max'],
        )
        if not self._show_background_enabled(plot_options, background_available=y_bkg is not None):
            y_bkg = None
        y_calc = self._filtered_y_array(
            summary.best_sample_prediction,
            summary.x,
            ctx['x_min'],
            ctx['x_max'],
        )
        excluded_ranges = (
            self._excluded_ranges(
                experiment=experiment,
                x_min=ctx['x_min'],
                x_max=ctx['x_max'],
            )
            if plot_options.show_excluded
            else ()
        )
        if self.engine == PlotterEngineEnum.ASCII.value:
            if plot_options.show_residual:
                log.warning(
                    'Posterior predictive residuals are unavailable for '
                    'ASCII summary plots; ignoring show_residual=True.'
                )
            self._plot_ascii_posterior_predictive_lines(
                expt_name=expt_name,
                x=np.asarray(ctx['x_filtered'], dtype=float),
                y_meas=np.asarray(y_meas, dtype=float),
                y_calc=np.asarray(y_calc, dtype=float),
                axes_labels=list(ctx['axes_labels']),
                excluded_ranges=excluded_ranges,
            )
            return

        y_resid = y_meas - y_calc if plot_options.show_residual is not False else None

        predictive_lower_95 = None
        predictive_upper_95 = None
        if style in {'band', 'band+draws'}:
            predictive_lower_95 = self._filtered_y_array(
                summary.lower_95,
                summary.x,
                ctx['x_min'],
                ctx['x_max'],
            )
            predictive_upper_95 = self._filtered_y_array(
                summary.upper_95,
                summary.x,
                ctx['x_min'],
                ctx['x_max'],
            )

        predictive_draws = None
        if show_draws:
            if summary.draws is None:
                log.warning('Posterior predictive draws are unavailable for plotting.')
                return
            predictive_draws = np.asarray(
                [
                    self._filtered_y_array(draw, summary.x, ctx['x_min'], ctx['x_max'])
                    for draw in summary.draws
                ],
                dtype=float,
            )

        if np.asarray(ctx['x_filtered']).size == 0 or not self._show_bragg_enabled(plot_options):
            bragg_tick_sets = ()
        else:
            bragg_tick_sets = self._extract_bragg_tick_sets(
                experiment=experiment,
                expt_name=expt_name,
                x_axis=ctx['x_axis'],
                x_min=ctx['x_min'],
                x_max=ctx['x_max'],
            )
        self._backend.plot_powder_meas_vs_calc(
            plot_spec=PowderMeasVsCalcSpec(
                x=ctx['x_filtered'],
                y_meas=y_meas,
                y_calc=y_calc,
                y_resid=y_resid,
                bragg_tick_sets=bragg_tick_sets,
                axes_labels=ctx['axes_labels'],
                title=f"Posterior predictive for experiment 🔬 '{expt_name}'",
                residual_height_fraction=DEFAULT_RESID_HEIGHT,
                bragg_peaks_height_fraction=DEFAULT_BRAGG_ROW,
                height=self._composite_plot_height(),
                y_bkg=y_bkg,
                predictive_lower_95=predictive_lower_95,
                predictive_upper_95=predictive_upper_95,
                predictive_draws=predictive_draws,
                y_calc_name=POSTERIOR_POINT_ESTIMATE_TRACE_NAME,
                y_calc_line_dash=POSTERIOR_POINT_ESTIMATE_LINE_DASH,
                excluded_ranges=excluded_ranges,
            )
        )

    @staticmethod
    def _resolve_posterior_parameter_names(
        *,
        fit_results: object,
        parameters: list[object] | None,
    ) -> list[str] | None:
        """
        Resolve posterior parameter names from descriptors.

        Parameters
        ----------
        fit_results : object
            Bayesian fit result exposing posterior samples.
        parameters : list[object] | None
            Optional parameter subset.

        Returns
        -------
        list[str] | None
            Posterior parameter names in plotting order, or ``None`` if
            the selection cannot be resolved.
        """
        posterior_samples = getattr(fit_results, 'posterior_samples', None)
        available_names = getattr(posterior_samples, 'parameter_names', None)
        if not available_names:
            log.warning('Posterior samples do not expose parameter names.')
            return None

        if parameters is None:
            return list(available_names)

        resolved_names: list[str] = []
        for parameter in parameters:
            resolved_name = Plotter._resolve_posterior_parameter_name(
                fit_results=fit_results,
                available_names=list(available_names),
                parameter=parameter,
            )
            if resolved_name is None:
                return None
            resolved_names.append(resolved_name)
        return resolved_names

    @staticmethod
    def _resolve_posterior_parameter_name(
        *,
        fit_results: object,
        available_names: list[str],
        parameter: object,
    ) -> str | None:
        """
        Resolve one posterior parameter selection into a unique name.
        """
        if isinstance(parameter, str):
            return Plotter._resolve_posterior_parameter_name_from_string(
                fit_results=fit_results,
                available_names=available_names,
                selection=parameter,
            )

        unique_name = getattr(parameter, 'unique_name', None)
        if unique_name is None:
            log.warning(
                'Posterior parameter selection expects parameter objects '
                'or strings matching a unique name or label.'
            )
            return None
        if unique_name not in available_names:
            log.warning(f'Posterior samples do not contain the selected parameter: {unique_name}')
            return None
        return str(unique_name)

    @staticmethod
    def _resolve_posterior_parameter_name_from_string(
        *,
        fit_results: object,
        available_names: list[str],
        selection: str,
    ) -> str | None:
        """Resolve a string posterior parameter selection."""
        stripped_selection = selection.strip()
        if not stripped_selection:
            log.warning('Posterior parameter selection cannot use an empty string.')
            return None
        if stripped_selection in available_names:
            return stripped_selection

        selection_candidates = Plotter._posterior_parameter_selection_candidates(
            fit_results=fit_results,
            available_names=available_names,
        )
        matching_names = [
            unique_name
            for unique_name, candidates in selection_candidates.items()
            if stripped_selection in candidates
        ]
        if len(matching_names) == 1:
            return matching_names[0]
        if len(matching_names) > 1:
            matches = ', '.join(matching_names)
            log.warning(
                f"Posterior parameter selection '{stripped_selection}' is ambiguous. "
                f'Matches: {matches}'
            )
            return None

        log.warning(
            f'Posterior samples do not contain the selected parameter or label: '
            f'{stripped_selection}'
        )
        return None

    @staticmethod
    def _posterior_parameter_selection_candidates(
        *,
        fit_results: object,
        available_names: list[str],
    ) -> dict[str, set[str]]:
        """
        Return string identifiers accepted for posterior selection.
        """
        parameters_by_name = {
            getattr(parameter, 'unique_name', ''): parameter
            for parameter in fit_results.parameters
        }
        summaries_by_name = Plotter._posterior_summary_by_name(fit_results)
        plot_labels = dict(
            zip(
                available_names,
                Plotter._posterior_plot_labels(fit_results, available_names),
                strict=True,
            )
        )
        candidates_by_name: dict[str, set[str]] = {}
        for unique_name in available_names:
            candidates = {unique_name}
            parameter = parameters_by_name.get(unique_name)
            if parameter is not None:
                parameter_name = getattr(parameter, 'name', None)
                if isinstance(parameter_name, str) and parameter_name.strip():
                    candidates.add(parameter_name.strip())

            summary = summaries_by_name.get(unique_name)
            summary_label = getattr(summary, 'display_name', None)
            if isinstance(summary_label, str) and summary_label.strip():
                candidates.add(summary_label.strip())

            plot_label = plot_labels.get(unique_name)
            if isinstance(plot_label, str) and plot_label.strip():
                candidates.add(plot_label.strip())

            candidates_by_name[unique_name] = candidates
        return candidates_by_name

    @staticmethod
    def _selected_posterior_samples(
        posterior_samples: object,
        parameter_names: list[str],
    ) -> np.ndarray | None:
        """Return flattened posterior samples in the selected order."""
        available_names = getattr(posterior_samples, 'parameter_names', None)
        if not available_names:
            return None

        name_to_index = {name: index for index, name in enumerate(available_names)}
        try:
            indices = [name_to_index[name] for name in parameter_names]
        except KeyError:
            return None

        flattened = np.asarray(posterior_samples.flattened(), dtype=float)
        if flattened.ndim != POSTERIOR_FLATTENED_SAMPLE_NDIM:
            return None
        return flattened[:, indices]

    @staticmethod
    def _thin_posterior_samples(
        samples: np.ndarray,
        *,
        max_points: int = 4000,
    ) -> np.ndarray:
        """Downsample posterior samples for interactive plotting."""
        if samples.shape[0] <= max_points:
            return samples

        indices = np.linspace(0, samples.shape[0] - 1, num=max_points, dtype=int)
        return samples[indices]

    @staticmethod
    def _posterior_plot_labels(
        fit_results: object,
        parameter_names: list[str],
    ) -> list[str]:
        """
        Return readable posterior plot labels for selected parameters.
        """
        parameters_by_name = {
            getattr(parameter, 'unique_name', ''): parameter
            for parameter in fit_results.parameters
        }
        labels: list[str] = []
        for parameter_name in parameter_names:
            parameter = parameters_by_name.get(parameter_name)
            if parameter is None:
                labels.append(parameter_name)
                continue

            entry_name = getattr(getattr(parameter, '_identity', None), 'category_entry_name', '')
            short_name = getattr(parameter, 'name', parameter_name)
            if entry_name:
                labels.append(f'{entry_name} {short_name}')
            else:
                labels.append(short_name)
        return labels

    @staticmethod
    def _square_matrix_axis_title_labels(
        parameter_names: list[str],
    ) -> list[str]:
        """Return compact multiline labels for square-matrix axes."""
        return [Plotter._square_matrix_axis_title_label(name) for name in parameter_names]

    @staticmethod
    def _square_matrix_axis_title_label(unique_name: str) -> str:
        """Return one compact multiline axis title."""
        normalized_name = unique_name.strip()
        if not normalized_name or '.' not in normalized_name:
            return normalized_name

        name_parts = [part.strip() for part in normalized_name.split('.') if part.strip()]
        if not name_parts:
            return normalized_name

        return '<br>'.join([*(f'{part}.' for part in name_parts[:-1]), name_parts[-1]])

    @staticmethod
    def _posterior_summary_by_name(
        fit_results: object,
    ) -> dict[str, object]:
        """Return posterior summaries keyed by unique parameter name."""
        summaries = getattr(fit_results, 'posterior_parameter_summaries', [])
        return {summary.unique_name: summary for summary in summaries}

    def _get_fit_result_for_correlation(
        self,
    ) -> object | None:
        """
        Validate and return the fit result for correlation.

        Returns
        -------
        object | None
            Fit result object when available, or ``None`` otherwise.
        """
        if self._project is None:
            log.warning('Plotter is not attached to a project.')
            return None

        fit_results = getattr(self._project.analysis, 'fit_results', None)
        if fit_results is None:
            log.warning('No fit results available. Run fit() first.')
            return None
        return fit_results

    @staticmethod
    def _correlation_from_posterior_samples(
        posterior_samples: object,
    ) -> pd.DataFrame | None:
        """
        Convert posterior samples into a correlation DataFrame.

        Parameters
        ----------
        posterior_samples : object
            Posterior sample container exposing ``flattened()`` and
            ``parameter_names``.

        Returns
        -------
        pd.DataFrame | None
            Correlation matrix labeled by posterior parameter names, or
            ``None`` if the sample array is invalid.
        """
        parameter_names = getattr(posterior_samples, 'parameter_names', None)
        if not parameter_names:
            log.warning('Posterior samples do not expose parameter names.')
            return None

        flattened = np.asarray(posterior_samples.flattened(), dtype=float)
        if flattened.ndim != POSTERIOR_FLATTENED_SAMPLE_NDIM or flattened.shape[1] != len(
            parameter_names
        ):
            log.warning('Posterior sample array has an invalid shape for correlations.')
            return None
        if flattened.shape[0] < MIN_POSTERIOR_SAMPLE_COUNT:
            log.warning('At least two posterior draws are required for correlations.')
            return None

        corr = np.corrcoef(flattened, rowvar=False)
        corr = np.nan_to_num(corr, nan=0.0, posinf=0.0, neginf=0.0)
        np.fill_diagonal(corr, 1.0)
        return pd.DataFrame(corr, index=parameter_names, columns=parameter_names)

    @staticmethod
    def _correlation_from_covariance(
        covar: object,
        var_names: list[str],
        parameters: list[object],
    ) -> pd.DataFrame | None:
        """
        Convert a covariance matrix to a correlation DataFrame.

        Parameters
        ----------
        covar : object
            Raw covariance matrix from the fit result.
        var_names : list[str]
            Minimizer variable names.
        parameters : list[object]
            Fitted parameter descriptors.

        Returns
        -------
        pd.DataFrame | None
            Correlation matrix, or ``None`` if the covariance is
            invalid.
        """
        covar_array = np.asarray(covar, dtype=float)
        if covar_array.ndim != EXPECTED_COVAR_NDIM or covar_array.shape[0] != covar_array.shape[1]:
            log.warning('Fit result returned an invalid covariance matrix.')
            return None
        if covar_array.shape[0] != len(var_names):
            log.warning('Covariance matrix size does not match the fitted parameter list.')
            return None

        sigma = np.sqrt(np.diag(covar_array))
        with np.errstate(divide='ignore', invalid='ignore'):
            corr = covar_array / np.outer(sigma, sigma)
        corr = np.nan_to_num(corr, nan=0.0, posinf=0.0, neginf=0.0)
        np.fill_diagonal(corr, 1.0)

        labels = Plotter._get_correlation_labels(parameters, var_names)
        return pd.DataFrame(corr, index=labels, columns=labels)

    @staticmethod
    def _get_correlation_labels(
        parameters: list[object],
        var_names: list[str],
    ) -> list[str]:
        """
        Map minimizer variable names to readable parameter labels.

        Parameters
        ----------
        parameters : list[object]
            Fitted parameter descriptors.
        var_names : list[str]
            Minimizer variable names from the engine result.

        Returns
        -------
        list[str]
            Labels for the correlation matrix axes.
        """
        labels_by_uid = {
            getattr(param, '_minimizer_uid', ''): getattr(
                param, 'unique_name', getattr(param, 'name', '')
            )
            for param in parameters
        }
        return [labels_by_uid.get(name, name) for name in var_names]

    def _get_param_correlation_dataframe_from_engine_params(
        self,
        raw_result: object,
        parameters: list[object],
    ) -> pd.DataFrame | None:
        """
        Reconstruct a correlation matrix from engine parameter metadata.

        This is a fallback for backends that populate per-parameter
        correlation coefficients but do not expose a covariance matrix.

        Parameters
        ----------
        raw_result : object
            Backend-specific fit result.
        parameters : list[object]
            Fitted parameter descriptors.

        Returns
        -------
        pd.DataFrame | None
            Correlation matrix labeled by readable parameter names, or
            ``None`` if no correlation coefficients are available.
        """
        engine_params = getattr(raw_result, 'params', None)
        var_names = getattr(raw_result, 'var_names', None)
        if engine_params is None or not var_names:
            return None

        corr = np.eye(len(var_names), dtype=float)
        indices = {name: idx for idx, name in enumerate(var_names)}
        found_corr = False

        for name, idx in indices.items():
            engine_param = engine_params.get(name)
            param_corr = getattr(engine_param, 'correl', None)
            if not param_corr:
                continue

            for other_name, value in param_corr.items():
                other_idx = indices.get(other_name)
                if other_idx is None:
                    continue
                corr_value = float(value)
                corr[idx, other_idx] = corr_value
                corr[other_idx, idx] = corr_value
                found_corr = True

        if not found_corr:
            return None

        labels = self._get_correlation_labels(parameters, var_names)
        return pd.DataFrame(corr, index=labels, columns=labels)

    def _plot_correlation_heatmap(
        self,
        corr_df: pd.DataFrame,
        title: str,
        threshold: float | None,
        precision: int,
    ) -> None:
        """
        Delegate correlation heatmap rendering to the backend.

        Parameters
        ----------
        corr_df : pd.DataFrame
            Square correlation matrix.
        title : str
            Figure title.
        threshold : float | None
            Absolute-correlation cutoff used for value labels.
        precision : int
            Number of decimals to show in plot labels and hover text.
        """
        figure = self._build_correlation_heatmap_plot(
            corr_df,
            title,
            threshold=threshold,
            precision=precision,
        )
        self._show_plot_figure(figure)

    def _build_correlation_heatmap_plot(
        self,
        corr_df: pd.DataFrame,
        title: str,
        *,
        threshold: float | None,
        precision: int,
    ) -> object:
        """Build a compact pair-plot-style correlation heatmap."""
        go = __import__('plotly.graph_objects', fromlist=['Figure', 'Heatmap'])
        context = _CorrelationHeatmapContext(
            corr_df=corr_df,
            row_labels=self._square_matrix_axis_title_labels(corr_df.index.tolist()),
            col_labels=self._square_matrix_axis_title_labels(corr_df.columns.tolist()),
            threshold=threshold,
            precision=precision,
        )
        plot_extent = self._square_matrix_plot_extent(context.n_cols)
        x_edges = self._correlation_heatmap_edges(context.n_cols)
        y_edges = self._correlation_heatmap_edges(context.n_rows)
        x_centers = self._correlation_heatmap_centers(context.n_cols)
        y_centers = self._correlation_heatmap_centers(context.n_rows)

        heatmap = go.Heatmap(
            z=self._correlation_heatmap_values(context.corr_df),
            x=x_edges,
            y=y_edges,
            customdata=self._correlation_heatmap_customdata(context.corr_df),
            zmin=-1.0,
            zmax=1.0,
            zmid=0.0,
            colorscale=self._plot_correlation_colorscale(),
            showscale=False,
            hoverongaps=False,
            hovertemplate=(
                '%{customdata[0]}<br>'
                '%{customdata[1]}<br>'
                f'correlation: %{{z:.{context.precision}f}}<extra></extra>'
            ),
        )
        label_trace = PlotlyPlotter._get_correlation_label_trace(
            context.corr_df,
            x_centers=x_centers,
            y_centers=y_centers,
            threshold=context.threshold,
            precision=context.precision,
        )
        traces = [heatmap]
        if label_trace is not None:
            traces.append(label_trace)
        fig = go.Figure(data=traces)
        shapes = self._correlation_heatmap_grid_shapes(context)

        fig.update_layout(
            autosize=True,
            margin=self._square_matrix_layout_margin([
                *context.row_labels,
                *context.col_labels,
            ]),
            annotations=self._correlation_heatmap_annotations(
                title=title,
                context=context,
                plot_extent=plot_extent,
                x_centers=x_centers,
                y_centers=y_centers,
            ),
            shapes=shapes,
            meta=self._square_matrix_layout_meta(
                n_parameters=context.n_cols,
                annotation_labels=[*context.row_labels, *context.col_labels],
                cell_size_pixels=self._correlation_cell_size_pixels(),
                cap_width=True,
            ),
            showlegend=False,
        )
        fig.update_xaxes(
            range=[0.0, plot_extent],
            showline=False,
            mirror=False,
            zeroline=False,
            showgrid=False,
            ticks='',
            ticklen=0,
            tickwidth=0,
            showticklabels=False,
            title_text=None,
            layer='above traces',
            constrain='domain',
        )
        fig.update_yaxes(
            range=[plot_extent, 0.0],
            showline=False,
            mirror=False,
            zeroline=False,
            showgrid=False,
            ticks='',
            ticklen=0,
            tickwidth=0,
            showticklabels=False,
            title_text=None,
            layer='above traces',
            constrain='domain',
            scaleanchor='x',
            scaleratio=1,
        )
        PlotlyPlotter._apply_theme_sync_meta(
            fig,
            axis_frame_shape_indexes=range(len(shapes)),
            correlation_heatmap=True,
        )
        return fig

    @classmethod
    def _correlation_heatmap_edges(cls, n_parameters: int) -> np.ndarray:
        """Return expanded heatmap edges with pair-plot-like gaps."""
        if n_parameters <= 0:
            return np.asarray([0.0], dtype=float)

        gap_width = cls._square_matrix_gap_data_width(n_parameters)
        if np.isclose(gap_width, 0.0):
            return np.arange(n_parameters + 1, dtype=float)

        widths = [1.0 if index % 2 == 0 else gap_width for index in range(2 * n_parameters - 1)]
        return np.concatenate(([0.0], np.cumsum(np.asarray(widths, dtype=float))))

    @classmethod
    def _correlation_heatmap_centers(cls, n_parameters: int) -> np.ndarray:
        """Return visible-cell centers for a gapped heatmap."""
        gap_width = cls._square_matrix_gap_data_width(n_parameters)
        return np.arange(n_parameters, dtype=float) * (1.0 + gap_width) + 0.5

    @staticmethod
    def _correlation_heatmap_values(corr_df: pd.DataFrame) -> np.ndarray:
        """Return a gapped heatmap array for correlation cells."""
        n_rows, n_cols = corr_df.shape
        expanded = np.full((2 * n_rows - 1, 2 * n_cols - 1), np.nan, dtype=float)
        expanded[0::2, 0::2] = corr_df.to_numpy(dtype=float)
        return expanded

    @staticmethod
    def _correlation_heatmap_customdata(
        corr_df: pd.DataFrame,
    ) -> np.ndarray:
        """Return hover labels for a correlation heatmap."""
        n_rows, n_cols = corr_df.shape
        expanded = np.empty((2 * n_rows - 1, 2 * n_cols - 1, 2), dtype=object)
        expanded[..., 0] = ''
        expanded[..., 1] = ''
        for row_index, row_label in enumerate(corr_df.index):
            for col_index, col_label in enumerate(corr_df.columns):
                expanded[2 * row_index, 2 * col_index, 0] = str(col_label)
                expanded[2 * row_index, 2 * col_index, 1] = str(row_label)
        return expanded

    def _correlation_heatmap_annotations(
        self,
        *,
        title: str,
        context: _CorrelationHeatmapContext,
        plot_extent: float,
        x_centers: np.ndarray,
        y_centers: np.ndarray,
    ) -> list[dict[str, object]]:
        """Return pair-plot-like title and axis annotations."""
        annotations = [
            self._square_matrix_title_annotation(
                title,
                [*context.row_labels, *context.col_labels],
            )
        ]
        for row_index, row_label in enumerate(context.row_labels):
            annotations.append({
                'x': 0.0,
                'xref': 'paper',
                'xanchor': 'right',
                'xshift': -POSTERIOR_PAIR_Y_TITLE_XSHIFT_PIXELS,
                'y': 1.0 - (float(y_centers[row_index]) / plot_extent),
                'yref': 'paper',
                'yanchor': 'middle',
                'text': row_label,
                'align': 'center',
                'font': {'size': POSTERIOR_PAIR_AXIS_TITLE_FONT_SIZE},
                'textangle': -90,
                'showarrow': False,
            })
        for col_index, col_label in enumerate(context.col_labels):
            annotations.append({
                'x': float(x_centers[col_index]) / plot_extent,
                'xref': 'paper',
                'xanchor': 'center',
                'y': 0.0,
                'yref': 'paper',
                'yanchor': 'top',
                'yshift': -POSTERIOR_PAIR_X_TITLE_YSHIFT_PIXELS,
                'text': col_label,
                'align': 'center',
                'font': {'size': POSTERIOR_PAIR_AXIS_TITLE_FONT_SIZE},
                'showarrow': False,
            })
        return annotations

    def _correlation_heatmap_grid_shapes(
        self,
        context: _CorrelationHeatmapContext,
    ) -> list[dict[str, object]]:
        """Return per-cell borders for the visible lower triangle."""
        axis_frame_color = self._plot_axis_frame_color()
        gap_width = self._square_matrix_gap_data_width(context.n_cols)
        return [
            {
                'type': 'rect',
                'xref': 'x',
                'yref': 'y',
                'x0': float(col_index * (1.0 + gap_width)),
                'x1': float(col_index * (1.0 + gap_width) + 1.0),
                'y0': float(row_index * (1.0 + gap_width)),
                'y1': float(row_index * (1.0 + gap_width) + 1.0),
                'layer': 'above',
                'line': {
                    'color': axis_frame_color,
                    'width': POSTERIOR_PAIR_AXIS_LINE_WIDTH,
                },
                'fillcolor': 'rgba(0, 0, 0, 0)',
            }
            for row_index in range(context.n_rows)
            for col_index in range(context.n_cols)
            if col_index <= row_index
        ]

    def _populate_correlation_heatmap_panel(
        self,
        *,
        fig: object,
        context: _CorrelationHeatmapContext,
        row_index: int,
        col_index: int,
        subplot_title_annotations: list[dict[str, object]],
        subplot_border_shapes: list[dict[str, object]],
    ) -> None:
        """Populate one panel in the correlation-matrix grid."""
        row = row_index + 1
        col = col_index + 1
        if col_index > row_index:
            self._hide_posterior_pair_panel(fig=fig, row=row, col=col)
            return

        value = context.corr_df.iat[row_index, col_index]
        if not pd.isna(value):
            self._add_correlation_heatmap_value_panel(
                fig=fig,
                context=context,
                row_index=row_index,
                col_index=col_index,
                value=float(value),
            )

        self._configure_correlation_heatmap_panel_axes(fig=fig, row=row, col=col)
        self._collect_correlation_heatmap_panel_decorations(
            fig=fig,
            context=context,
            row_index=row_index,
            col_index=col_index,
            subplot_title_annotations=subplot_title_annotations,
            subplot_border_shapes=subplot_border_shapes,
        )

    def _add_correlation_heatmap_value_panel(
        self,
        *,
        fig: object,
        context: _CorrelationHeatmapContext,
        row_index: int,
        col_index: int,
        value: float,
    ) -> None:
        """Add one colored cell and optional text label."""
        go = __import__('plotly.graph_objects', fromlist=['Heatmap'])
        row = row_index + 1
        col = col_index + 1
        hovertemplate = (
            f'{context.corr_df.columns[col_index]}<br>'
            f'{context.corr_df.index[row_index]}<br>'
            f'correlation: %{{z:.{context.precision}f}}<extra></extra>'
        )
        fig.add_trace(
            go.Heatmap(
                z=[[value]],
                x=[0.0, 1.0],
                y=[0.0, 1.0],
                zmin=-1.0,
                zmax=1.0,
                zmid=0.0,
                colorscale=self._plot_correlation_colorscale(),
                showscale=False,
                hoverongaps=False,
                hovertemplate=hovertemplate,
            ),
            row=row,
            col=col,
        )

        if (
            context.threshold is not None
            and context.threshold > 0
            and abs(value) < context.threshold
        ):
            return

        fig.add_trace(
            go.Scatter(
                x=[0.5],
                y=[0.5],
                mode='text',
                text=[f'{value:.{context.precision}f}'],
                textposition='middle center',
                textfont={'color': PlotlyPlotter._correlation_label_color()},
                hoverinfo='skip',
                showlegend=False,
            ),
            row=row,
            col=col,
        )

    @staticmethod
    def _configure_correlation_heatmap_panel_axes(
        *,
        fig: object,
        row: int,
        col: int,
    ) -> None:
        """Hide ticks and titles for one correlation-matrix panel."""
        fig.update_xaxes(
            range=[0.0, 1.0],
            showline=False,
            mirror=False,
            zeroline=False,
            showgrid=False,
            ticks='',
            ticklen=0,
            tickwidth=0,
            showticklabels=False,
            title_text=None,
            layer='above traces',
            row=row,
            col=col,
        )
        fig.update_yaxes(
            range=[1.0, 0.0],
            showline=False,
            mirror=False,
            zeroline=False,
            showgrid=False,
            ticks='',
            ticklen=0,
            tickwidth=0,
            showticklabels=False,
            title_text=None,
            layer='above traces',
            row=row,
            col=col,
        )

    def _collect_correlation_heatmap_panel_decorations(
        self,
        *,
        fig: object,
        context: _CorrelationHeatmapContext,
        row_index: int,
        col_index: int,
        subplot_title_annotations: list[dict[str, object]],
        subplot_border_shapes: list[dict[str, object]],
    ) -> None:
        """Collect labels and frames for one correlation cell."""
        row = row_index + 1
        col = col_index + 1
        subplot = fig.get_subplot(row, col)
        x_mid = 0.5 * (subplot.xaxis.domain[0] + subplot.xaxis.domain[1])
        y_mid = 0.5 * (subplot.yaxis.domain[0] + subplot.yaxis.domain[1])

        if col_index == 0:
            subplot_title_annotations.append({
                'x': subplot.xaxis.domain[0],
                'xref': 'paper',
                'xanchor': 'right',
                'xshift': -POSTERIOR_PAIR_Y_TITLE_XSHIFT_PIXELS,
                'y': y_mid,
                'yref': 'paper',
                'yanchor': 'middle',
                'text': context.row_labels[row_index],
                'align': 'center',
                'font': {'size': POSTERIOR_PAIR_AXIS_TITLE_FONT_SIZE},
                'textangle': -90,
                'showarrow': False,
            })
        if row_index == context.n_rows - 1:
            subplot_title_annotations.append({
                'x': x_mid,
                'xref': 'paper',
                'xanchor': 'center',
                'y': subplot.yaxis.domain[0],
                'yref': 'paper',
                'yanchor': 'top',
                'yshift': -POSTERIOR_PAIR_X_TITLE_YSHIFT_PIXELS,
                'text': context.col_labels[col_index],
                'align': 'center',
                'font': {'size': POSTERIOR_PAIR_AXIS_TITLE_FONT_SIZE},
                'showarrow': False,
            })

        subplot_border_shapes.append({
            'type': 'rect',
            'xref': 'paper',
            'yref': 'paper',
            'x0': subplot.xaxis.domain[0],
            'x1': subplot.xaxis.domain[1],
            'y0': subplot.yaxis.domain[0],
            'y1': subplot.yaxis.domain[1],
            'line': {
                'color': self._plot_axis_frame_color(),
                'width': POSTERIOR_PAIR_AXIS_LINE_WIDTH,
            },
            'fillcolor': 'rgba(0, 0, 0, 0)',
            'layer': 'above',
        })

    def _plot_correlation_colorscale(self) -> list[tuple[float, str]]:
        """Return the active correlation colorscale."""
        correlation_colorscale = getattr(self._backend, '_correlation_colorscale', None)
        if callable(correlation_colorscale):
            return correlation_colorscale()
        return PlotlyPlotter._correlation_colorscale()

    @staticmethod
    def _format_correlation_table_dataframe(
        corr_df: pd.DataFrame,
        row_numbers: list[int],
        col_numbers: list[int],
        threshold: float | None,
        precision: int,
    ) -> pd.DataFrame:
        """
        Format a correlation matrix for TableRenderer.

        Parameters
        ----------
        corr_df : pd.DataFrame
            Correlation matrix labeled by parameter name.
        row_numbers : list[int]
            1-based parameter numbers for displayed rows.
        col_numbers : list[int]
            1-based parameter numbers for displayed columns.
        threshold : float | None
            Absolute-correlation cutoff used to blank low-magnitude
            cells in the rendered table. ``None`` or ``0`` keeps all
            non-masked values.
        precision : int
            Number of decimals to show in the rendered values.

        Returns
        -------
        pd.DataFrame
            DataFrame with MultiIndex columns and default numeric index,
            suitable for :class:`TableRenderer`. Correlation columns use
            1-based numeric headers so they line up with the numbered
            parameter rows in terminal output.
        """
        rounded = corr_df.round(precision)
        cell_width = max(
            len(str(max(col_numbers, default=0))),
            len(f'{-1.0:.{precision}f}'),
        )
        headers = [('parameter', 'left')]
        headers.extend((str(index).rjust(cell_width), 'right') for index in col_numbers)

        rows = []
        for label, values in rounded.iterrows():
            row_values = []
            for value in values.tolist():
                should_blank = pd.isna(value) or (
                    threshold is not None and threshold > 0 and abs(float(value)) < threshold
                )
                if should_blank:
                    row_values.append('')
                else:
                    fval = float(value)
                    text = f'{fval:>{cell_width}.{precision}f}'
                    if fval < 0:
                        text = f'[red]{text}[/red]'
                    elif fval > 0:
                        text = f'[blue]{text}[/blue]'
                    row_values.append(text)
            rows.append([label, *row_values])

        df = pd.DataFrame(rows, columns=pd.MultiIndex.from_tuples(headers))
        df.index = pd.Index([row_number - 1 for row_number in row_numbers])
        return df

    def _plot_meas_data(
        self,
        experiment: object,
        pattern: object,
        expt_name: str,
        expt_type: object,
        plot_options: _MeasVsCalcPlotOptions,
    ) -> None:
        """
        Plot measured pattern using the current engine.

        Parameters
        ----------
        experiment : object
            Experiment object used for excluded-range extraction.
        pattern : object
            Object with x-axis arrays (``two_theta``,
            ``time_of_flight``, ``d_spacing``) and ``meas`` array.
        expt_name : str
            Experiment name for the title.
        expt_type : object
            Experiment type with scattering/beam enums.
        plot_options : _MeasVsCalcPlotOptions
            X-range, excluded-region, and x-axis selection options.
        """
        ctx = self._prepare_powder_context(
            pattern,
            expt_name,
            expt_type,
            plot_options.x_min,
            plot_options.x_max,
            plot_options.x,
        )
        if ctx is None:
            return

        if pattern.intensity_meas is None:
            log.error(f'No measured data available for experiment {expt_name}')
            return
        y_meas = self._filtered_y_array(
            pattern.intensity_meas, ctx['x_array'], ctx['x_min'], ctx['x_max']
        )
        excluded_ranges = (
            self._excluded_ranges(
                experiment=experiment,
                x_min=ctx['x_min'],
                x_max=ctx['x_max'],
            )
            if plot_options.show_excluded
            else ()
        )

        self._backend.plot_powder(
            x=ctx['x_filtered'],
            y_series=[y_meas],
            labels=['meas'],
            axes_labels=ctx['axes_labels'],
            title=f"Diffraction pattern for experiment 🔬 '{expt_name}'",
            height=self.height,
            excluded_ranges=excluded_ranges,
        )

    def _plot_calc_data(
        self,
        experiment: object,
        pattern: object,
        expt_name: str,
        expt_type: object,
        plot_options: _MeasVsCalcPlotOptions,
    ) -> None:
        """
        Plot calculated pattern using the current engine.

        Parameters
        ----------
        experiment : object
            Experiment object used for excluded-range extraction.
        pattern : object
            Object with x-axis arrays (``two_theta``,
            ``time_of_flight``, ``d_spacing``) and ``calc`` array.
        expt_name : str
            Experiment name for the title.
        expt_type : object
            Experiment type with scattering/beam enums.
        plot_options : _MeasVsCalcPlotOptions
            X-range, excluded-region, and x-axis selection options.
        """
        ctx = self._prepare_powder_context(
            pattern,
            expt_name,
            expt_type,
            plot_options.x_min,
            plot_options.x_max,
            plot_options.x,
        )
        if ctx is None:
            return

        if pattern.intensity_calc is None:
            log.error(f'No calculated data available for experiment {expt_name}')
            return
        y_calc = self._filtered_y_array(
            pattern.intensity_calc, ctx['x_array'], ctx['x_min'], ctx['x_max']
        )
        excluded_ranges = (
            self._excluded_ranges(
                experiment=experiment,
                x_min=ctx['x_min'],
                x_max=ctx['x_max'],
            )
            if plot_options.show_excluded
            else ()
        )

        self._backend.plot_powder(
            x=ctx['x_filtered'],
            y_series=[y_calc],
            labels=['calc'],
            axes_labels=ctx['axes_labels'],
            title=f"Diffraction pattern for experiment 🔬 '{expt_name}'",
            height=self.height,
            excluded_ranges=excluded_ranges,
        )

    def _powder_meas_vs_calc_series(
        self,
        pattern: object,
        ctx: dict[str, object],
        plot_options: _MeasVsCalcPlotOptions,
    ) -> _PowderMeasVsCalcSeries:
        """Return filtered measured/calculated powder series."""
        y_meas = self._filtered_y_array(
            pattern.intensity_meas, ctx['x_array'], ctx['x_min'], ctx['x_max']
        )
        y_calc = self._filtered_y_array(
            pattern.intensity_calc, ctx['x_array'], ctx['x_min'], ctx['x_max']
        )
        y_meas_su = self._optional_filtered_y_array(
            getattr(pattern, 'intensity_meas_su', None),
            ctx,
        )
        y_bkg = self._optional_filtered_y_array(
            getattr(pattern, 'intensity_bkg', None),
            ctx,
        )
        if not self._show_background_enabled(
            plot_options,
            background_available=y_bkg is not None,
        ):
            y_bkg = None
        return _PowderMeasVsCalcSeries(
            y_meas=y_meas,
            y_calc=y_calc,
            y_meas_su=y_meas_su,
            y_bkg=y_bkg,
        )

    def _optional_filtered_y_array(
        self,
        values: object | None,
        ctx: dict[str, object],
    ) -> np.ndarray | None:
        """Return filtered optional y values."""
        if values is None:
            return None
        return self._filtered_y_array(
            values,
            ctx['x_array'],
            ctx['x_min'],
            ctx['x_max'],
        )

    def _plot_meas_vs_calc_data(
        self,
        experiment: object,
        expt_name: str,
        plot_options: _MeasVsCalcPlotOptions,
    ) -> None:
        """
        Plot measured and calculated series and optional residual.

        Supports both powder and single crystal data with a unified API.

        For powder diffraction: - x='two_theta', 'time_of_flight', or
        'd_spacing' - Auto-detected from beam mode if not specified

        For single crystal diffraction: - x='intensity_calc' (default):
        scatter plot - x='d_spacing' or 'sin_theta_over_lambda': line
        plot

        Parameters
        ----------
        experiment : object
            Experiment instance with an intensity category and
            ``.type``.
        expt_name : str
            Experiment name for the title.
        plot_options : _MeasVsCalcPlotOptions
            X-range, residual, and x-axis selection options.
        """
        pattern = intensity_category_for(experiment)
        expt_type = experiment.type

        x_axis, _, sample_form, scattering_type, _ = self._resolve_x_axis(
            expt_type,
            plot_options.x,
        )

        # Validate required data (before x-array check, matching
        # original behavior for plot_meas_vs_calc)
        if pattern.intensity_meas is None:
            log.error(f'No measured data available for experiment {expt_name}')
            return
        if pattern.intensity_calc is None:
            log.error(f'No calculated data available for experiment {expt_name}')
            return

        title = f"Diffraction pattern for experiment 🔬 '{expt_name}'"

        # Single crystal scatter plot (I²calc vs I²meas)
        if x_axis in {XAxisType.INTENSITY_CALC, 'intensity_calc'}:
            self._plot_single_crystal_meas_vs_calc(
                pattern=pattern,
                expt_name=expt_name,
                sample_form=sample_form,
                scattering_type=scattering_type,
                x_axis=x_axis,
                title=title,
            )
            return

        # Line plot (PD or SC with d_spacing/sin_theta_over_lambda)
        ctx = self._prepare_powder_context(
            pattern,
            expt_name,
            expt_type,
            plot_options.x_min,
            plot_options.x_max,
            plot_options.x,
        )
        if ctx is None:
            return

        powder_series = self._powder_meas_vs_calc_series(pattern, ctx, plot_options)
        excluded_ranges = (
            self._excluded_ranges(
                experiment=experiment,
                x_min=ctx['x_min'],
                x_max=ctx['x_max'],
            )
            if plot_options.show_excluded
            else ()
        )

        if sample_form == SampleFormEnum.POWDER and scattering_type == ScatteringTypeEnum.BRAGG:
            self._plot_powder_bragg_meas_vs_calc(
                experiment=experiment,
                expt_name=expt_name,
                ctx=ctx,
                series=powder_series,
                plot_options=plot_options,
                title=title,
                excluded_ranges=excluded_ranges,
            )
            return

        self._plot_line_meas_vs_calc(
            ctx=ctx,
            y_meas=powder_series.y_meas,
            y_calc=powder_series.y_calc,
            show_residual=False
            if plot_options.show_residual is None
            else plot_options.show_residual,
            title=title,
            excluded_ranges=excluded_ranges,
        )

    def _plot_single_crystal_meas_vs_calc(
        self,
        pattern: object,
        expt_name: str,
        sample_form: SampleFormEnum,
        scattering_type: ScatteringTypeEnum,
        x_axis: XAxisType | str,
        title: str,
    ) -> None:
        """
        Render the single-crystal measured-vs-calculated scatter plot.
        """
        axes_labels = self._get_axes_labels(sample_form, scattering_type, x_axis)
        if pattern.intensity_meas_su is None:
            log.warning(f'No measurement uncertainties for experiment {expt_name}')
            meas_su = np.zeros_like(pattern.intensity_meas)
        else:
            meas_su = pattern.intensity_meas_su

        self._backend.plot_single_crystal(
            x_calc=pattern.intensity_calc,
            y_meas=pattern.intensity_meas,
            y_meas_su=meas_su,
            axes_labels=axes_labels,
            title=title,
            height=self.height,
        )

    def _plot_powder_bragg_meas_vs_calc(
        self,
        experiment: object,
        expt_name: str,
        ctx: dict[str, object],
        series: _PowderMeasVsCalcSeries,
        plot_options: _MeasVsCalcPlotOptions,
        title: str,
        excluded_ranges: tuple[tuple[float, float], ...],
    ) -> None:
        """
        Render the composite powder Bragg measured-vs-calculated plot.
        """
        show_residual = True if plot_options.show_residual is None else plot_options.show_residual
        y_resid = series.y_meas - series.y_calc if show_residual else None
        if np.asarray(ctx['x_filtered']).size == 0 or not self._show_bragg_enabled(plot_options):
            bragg_tick_sets = ()
        else:
            bragg_tick_sets = self._extract_bragg_tick_sets(
                experiment=experiment,
                expt_name=expt_name,
                x_axis=ctx['x_axis'],
                x_min=ctx['x_min'],
                x_max=ctx['x_max'],
            )

        plot_spec = PowderMeasVsCalcSpec(
            x=ctx['x_filtered'],
            y_meas=series.y_meas,
            y_calc=series.y_calc,
            y_resid=y_resid,
            bragg_tick_sets=bragg_tick_sets,
            axes_labels=ctx['axes_labels'],
            title=title,
            residual_height_fraction=DEFAULT_RESID_HEIGHT,
            bragg_peaks_height_fraction=DEFAULT_BRAGG_ROW,
            height=self._composite_plot_height(),
            y_bkg=series.y_bkg,
            excluded_ranges=excluded_ranges,
            y_meas_su=series.y_meas_su,
        )
        self._backend.plot_powder_meas_vs_calc(plot_spec=plot_spec)

    @staticmethod
    def _show_background_enabled(
        plot_options: object,
        *,
        background_available: bool,
    ) -> bool:
        """Return whether the background curve should be shown."""
        show_background = getattr(plot_options, 'show_background', None)
        if show_background is None:
            return background_available
        return show_background and background_available

    @staticmethod
    def _show_bragg_enabled(plot_options: object) -> bool:
        """Return whether Bragg reflection rows should be shown."""
        show_bragg = getattr(plot_options, 'show_bragg', None)
        if show_bragg is None:
            return True
        return show_bragg

    def _plot_line_meas_vs_calc(
        self,
        ctx: dict[str, object],
        y_meas: np.ndarray,
        y_calc: np.ndarray,
        *,
        show_residual: bool,
        title: str,
        excluded_ranges: tuple[tuple[float, float], ...] = (),
    ) -> None:
        """
        Render the non-composite line version of measured-vs-calculated.
        """
        y_series = [y_meas, y_calc]
        y_labels = ['meas', 'calc']
        if show_residual:
            y_series.append(y_meas - y_calc)
            y_labels.append('resid')

        self._backend.plot_powder(
            x=ctx['x_filtered'],
            y_series=y_series,
            labels=y_labels,
            axes_labels=ctx['axes_labels'],
            title=title,
            height=self.height,
            excluded_ranges=excluded_ranges,
        )

    @staticmethod
    def _excluded_ranges(
        *,
        experiment: object,
        x_min: float | None,
        x_max: float | None,
    ) -> tuple[tuple[float, float], ...]:
        """Return excluded x-ranges clipped to the current view."""
        excluded_regions = getattr(experiment, 'excluded_regions', None)
        if excluded_regions is None:
            return ()

        clipped_ranges: list[tuple[float, float]] = []
        lower_bound = -np.inf if x_min is None else float(x_min)
        upper_bound = np.inf if x_max is None else float(x_max)

        for region in excluded_regions:
            start = float(region.start.value)
            end = float(region.end.value)
            clipped_start = max(start, lower_bound)
            clipped_end = min(end, upper_bound)
            if clipped_start > clipped_end:
                continue
            clipped_ranges.append((clipped_start, clipped_end))

        return tuple(clipped_ranges)

    @staticmethod
    def _extract_bragg_tick_sets(
        experiment: object,
        expt_name: str,
        x_axis: object,
        x_min: float | None,
        x_max: float | None,
    ) -> tuple[BraggTickSet, ...]:
        """
        Convert experiment reflection data into Bragg tick display rows.
        """
        refln = getattr(experiment, 'refln', None)
        if refln is None:
            return ()

        x_values = Plotter._bragg_tick_x_values(
            refln=refln,
            experiment=experiment,
            expt_name=expt_name,
            x_axis=x_axis,
        )
        arrays = Plotter._bragg_tick_arrays(refln=refln, expt_name=expt_name)
        if x_values is None or arrays is None:
            return ()

        arrays['x'] = np.asarray(x_values)
        if arrays['x'].size == 0:
            return ()

        mask = Plotter._bragg_tick_mask(arrays['x'], x_min=x_min, x_max=x_max)
        if not np.any(mask):
            return ()

        return Plotter._group_bragg_tick_sets(arrays=arrays, mask=mask)

    @staticmethod
    def _bragg_tick_x_values(
        *,
        refln: object,
        experiment: object,
        expt_name: str,
        x_axis: object,
    ) -> object | None:
        x_name = getattr(x_axis, 'value', x_axis)
        if x_name == XAxisType.D_SPACING:
            return Plotter._bragg_tick_d_spacing(refln=refln, experiment=experiment)
        if x_name == XAxisType.TWO_THETA:
            return Plotter._bragg_tick_attr(refln, x_name, expt_name)
        if x_name == XAxisType.TIME_OF_FLIGHT:
            return Plotter._bragg_tick_attr(refln, x_name, expt_name)

        log.warning(
            f"Unsupported Bragg tick x axis '{x_name}' for experiment '{expt_name}'. "
            'Skipping the Bragg subplot.',
        )
        return None

    @staticmethod
    def _bragg_tick_attr(
        refln: object,
        name: str,
        expt_name: str,
    ) -> object | None:
        value = getattr(refln, name, None)
        if value is not None:
            return value

        log.warning(
            f"Experiment '{expt_name}' reflection data does not expose '{name}'. "
            'Skipping the Bragg subplot.',
        )
        return None

    @staticmethod
    def _bragg_tick_arrays(
        *,
        refln: object,
        expt_name: str,
    ) -> dict[str, np.ndarray] | None:
        arrays: dict[str, np.ndarray] = {}
        for name in (
            'phase_id',
            'index_h',
            'index_k',
            'index_l',
            'f_squared_calc',
            'f_calc',
        ):
            value = getattr(refln, name, None)
            if value is None:
                log.warning(
                    f"Experiment '{expt_name}' reflection data is missing '{name}'. "
                    'Skipping the Bragg subplot.',
                )
                return None
            arrays[name] = np.asarray(value)
        return arrays

    @staticmethod
    def _bragg_tick_mask(
        x_values: np.ndarray,
        *,
        x_min: float | None,
        x_max: float | None,
    ) -> np.ndarray:
        lower_bound = DEFAULT_MIN if x_min is None else min(x_min, x_max)
        upper_bound = DEFAULT_MAX if x_max is None else max(x_min, x_max)
        return (x_values >= lower_bound) & (x_values <= upper_bound)

    @staticmethod
    def _group_bragg_tick_sets(
        *,
        arrays: dict[str, np.ndarray],
        mask: np.ndarray,
    ) -> tuple[BraggTickSet, ...]:
        phase_ids = arrays['phase_id'][mask]
        unique_phase_ids = []
        for raw_phase_id in phase_ids:
            if not any(
                np.array_equal(raw_phase_id, existing_phase_id)
                for existing_phase_id in unique_phase_ids
            ):
                unique_phase_ids.append(raw_phase_id)

        tick_sets = []
        for raw_phase_id in unique_phase_ids:
            phase_mask = mask & (arrays['phase_id'] == raw_phase_id)
            tick_sets.append(
                BraggTickSet(
                    phase_id=str(raw_phase_id),
                    x=arrays['x'][phase_mask],
                    h=arrays['index_h'][phase_mask],
                    k=arrays['index_k'][phase_mask],
                    ell=arrays['index_l'][phase_mask],
                    f_squared_calc=arrays['f_squared_calc'][phase_mask],
                    f_calc=arrays['f_calc'][phase_mask],
                )
            )

        return tuple(tick_sets)

    @staticmethod
    def _bragg_tick_d_spacing(
        *,
        refln: object,
        experiment: object,
    ) -> object:
        """
        Resolve Bragg tick d-spacing in the plotted coordinate system.
        """
        if hasattr(refln, 'two_theta'):
            return twotheta_to_d(
                refln.two_theta,
                experiment.instrument.setup_wavelength.value,
            )
        if hasattr(refln, 'time_of_flight'):
            return tof_to_d(
                refln.time_of_flight,
                experiment.instrument.calib_d_to_tof_offset.value,
                experiment.instrument.calib_d_to_tof_linear.value,
                experiment.instrument.calib_d_to_tof_quad.value,
            )
        return refln.d_spacing

    def _plot_param_series_from_csv(
        self,
        csv_path: str,
        column_names: str | list[str],
        param_descriptor: object,
        versus_path: str | None = None,
    ) -> None:
        """
        Plot a parameter's value across sequential fit results.

        Reads data from the CSV file at *csv_path*.  The y-axis values
        come from the first matching column named in *column_names*,
        with uncertainties from ``{column_name}.uncertainty``. When
        *versus_path* is provided, the x-axis uses the corresponding
        ``diffrn.*`` CSV column; otherwise the row index is used.

        Axis labels use the live parameter descriptor and, when
        available, a template diffrn descriptor resolved from
        *versus_path*.

        Parameters
        ----------
        csv_path : str
            Path to the ``results.csv`` file.
        column_names : str | list[str]
            Candidate CSV column keys to plot.
        param_descriptor : object
            The live parameter descriptor (for axis label / units).
        versus_path : str | None, default=None
            Persisted diffrn path whose matching CSV column provides the
            x-axis values. ``None`` uses row index.
        """
        df = pd.read_csv(csv_path)

        column_candidates = [column_names] if isinstance(column_names, str) else column_names

        column_name = next((name for name in column_candidates if name in df.columns), None)
        if column_name is None:
            log.warning(
                f"Parameter '{column_candidates[0]}' not found in CSV columns. "
                f'Available: {list(df.columns)}'
            )
            return

        y = self._numeric_series_values(df[column_name])
        uncert_col = f'{column_name}.uncertainty'
        sy = (
            self._numeric_series_values(df[uncert_col])
            if uncert_col in df.columns
            else [0.0] * len(y)
        )

        # X-axis: diffrn column or row index
        diffrn_col = versus_path
        versus_descriptor = self._resolve_versus_descriptor_from_path(versus_path)

        if diffrn_col and diffrn_col in df.columns:
            x = pd.to_numeric(df[diffrn_col], errors='coerce').tolist()
            x_label = self._versus_axis_label(versus_path, versus_descriptor)
        else:
            x = list(range(1, len(y) + 1))
            x_label = 'Experiment No.'

        # Y-axis label from descriptor
        param_units = (
            param_descriptor.resolve_display_units('gui')
            if hasattr(param_descriptor, 'resolve_display_units')
            else getattr(param_descriptor, 'units', '')
        )
        y_label = f'Parameter value ({param_units})' if param_units else 'Parameter value'

        title = f"Parameter '{column_name}' across fit results"

        self._backend.plot_scatter(
            x=x,
            y=y,
            sy=sy,
            axes_labels=[x_label, y_label],
            title=title,
            height=self.height,
        )

    def plot_param_series_from_snapshots(
        self,
        unique_name: str,
        versus_path: str | None,
        experiments: object,
        parameter_snapshots: dict[str, dict[str, dict]],
    ) -> None:
        """
        Plot a parameter's value from in-memory snapshots.

        This is a backward-compatibility method used when no CSV file is
        available (e.g. after ``fit()`` in single mode, before PR 13
        adds CSV output to the existing fit loop).

        Parameters
        ----------
        unique_name : str
            Unique name of the parameter to plot.
        versus_path : str | None
            Persisted diffrn path for the x-axis.
        experiments : object
            Experiments collection for accessing diffrn conditions.
        parameter_snapshots : dict[str, dict[str, dict]]
            Per-experiment parameter value snapshots.
        """
        x = []
        y = []
        sy = []
        axes_labels = []
        title = ''

        for idx, expt_name in enumerate(parameter_snapshots, start=1):
            experiment = experiments[expt_name]
            diffrn = experiment.diffrn

            x_axis_param = self._resolve_diffrn_descriptor(
                diffrn,
                self._versus_field_name(versus_path),
            )

            if x_axis_param is not None and x_axis_param.value is not None:
                value = x_axis_param.value
            else:
                value = idx
            x.append(value)

            param_data = parameter_snapshots[expt_name][unique_name]
            y.append(param_data['value'])
            sy.append(param_data['uncertainty'])

            if x_axis_param is not None:
                axes_labels = [
                    self._versus_axis_label(versus_path, x_axis_param),
                    f'Parameter value ({param_data["units"]})',
                ]
            else:
                axes_labels = [
                    'Experiment No.',
                    f'Parameter value ({param_data["units"]})',
                ]

            title = f"Parameter '{unique_name}' across fit results"

        self._backend.plot_scatter(
            x=x,
            y=y,
            sy=sy,
            axes_labels=axes_labels,
            title=title,
            height=self.height,
        )

    @staticmethod
    def _resolve_diffrn_descriptor(
        diffrn: object,
        name: str | None,
    ) -> object | None:
        """
        Return the diffrn descriptor matching *name*, or ``None``.

        Parameters
        ----------
        diffrn : object
            The diffrn category of an experiment.
        name : str | None
            Descriptor name (e.g. ``'ambient_temperature'``).

        Returns
        -------
        object | None
            The matching ``NumericDescriptor``, or ``None`` when *name*
            is ``None`` or unrecognised.
        """
        if name is None:
            return None
        if name == 'ambient_temperature':
            return diffrn.ambient_temperature
        if name == 'ambient_pressure':
            return diffrn.ambient_pressure
        if name == 'ambient_magnetic_field':
            return diffrn.ambient_magnetic_field
        if name == 'ambient_electric_field':
            return diffrn.ambient_electric_field
        return None


class PlotterFactory(RendererFactoryBase):
    """Factory for plotter implementations."""

    @classmethod
    def _registry(cls) -> dict:
        return {
            PlotterEngineEnum.ASCII.value: {
                'description': PlotterEngineEnum.ASCII.description(),
                'class': AsciiPlotter,
            },
            PlotterEngineEnum.PLOTLY.value: {
                'description': PlotterEngineEnum.PLOTLY.description(),
                'class': PlotlyPlotter,
            },
        }
