# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
Plotting facade for measured and calculated patterns.

Uses the common :class:`RendererBase` so plotters and tablers share a
consistent configuration surface and engine handling.
"""

from enum import Enum

import numpy as np
import pandas as pd

from easydiffraction.display.base import RendererBase
from easydiffraction.display.base import RendererFactoryBase
from easydiffraction.display.plotters.ascii import AsciiPlotter
from easydiffraction.display.plotters.base import DEFAULT_AXES_LABELS
from easydiffraction.display.plotters.base import DEFAULT_HEIGHT
from easydiffraction.display.plotters.base import DEFAULT_MAX
from easydiffraction.display.plotters.base import DEFAULT_MIN
from easydiffraction.display.plotters.base import DEFAULT_X_AXIS
from easydiffraction.display.plotters.base import XAxisType
from easydiffraction.display.plotters.plotly import PlotlyPlotter
from easydiffraction.display.tables import TableRenderer
from easydiffraction.utils.environment import in_jupyter
from easydiffraction.utils.logging import console
from easydiffraction.utils.logging import log


class PlotterEngineEnum(str, Enum):
    """Available plotting engine backends."""

    ASCII = 'asciichartpy'
    PLOTLY = 'plotly'

    @classmethod
    def default(cls) -> 'PlotterEngineEnum':
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
        elif self is PlotterEngineEnum.PLOTLY:
            return 'Interactive browser-based graphing library'
        return ''


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
        self.height = DEFAULT_HEIGHT

    # ------------------------------------------------------------------
    #  Private class methods
    # ------------------------------------------------------------------

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
        if self._engine == 'asciichartpy' and (x_min is None or x_max is None):
            max_intensity_pos = np.argmax(pattern.intensity_meas)
            half_range = 50
            start = max(0, max_intensity_pos - half_range)
            end = min(len(x_array) - 1, max_intensity_pos + half_range)
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

        mask = (x_array >= x_min) & (x_array <= x_max)
        filtered_y_array = y_array[mask]

        return filtered_y_array

    def _get_axes_labels(
        self,
        sample_form: object,
        scattering_type: object,
        x_axis: object,
    ) -> list:
        """Look up axis labels for the experiment / x-axis."""
        return DEFAULT_AXES_LABELS[(sample_form, scattering_type, x_axis)]

    def _prepare_powder_data(
        self,
        pattern: object,
        expt_name: str,
        expt_type: object,
        x_min: object,
        x_max: object,
        x: object,
        need_meas: bool = False,
        need_calc: bool = False,
        show_residual: bool = False,
    ) -> dict | None:
        """
        Validate, resolve axes, auto-range, and filter arrays.

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
        need_meas : bool, default=False
            Whether ``intensity_meas`` is required.
        need_calc : bool, default=False
            Whether ``intensity_calc`` is required.
        show_residual : bool, default=False
            If ``True``, compute meas − calc residual.

        Returns
        -------
        dict | None
            A dict with keys ``x_filtered``, ``y_series``, ``y_labels``,
            ``axes_labels``, and ``x_axis``; or ``None`` when a required
            array is missing.
        """
        x_axis, x_name, sample_form, scattering_type, _ = self._resolve_x_axis(expt_type, x)

        # Get x-array from pattern
        x_array = getattr(pattern, x_axis, None)
        if x_array is None:
            log.error(f'No {x_name} data available for experiment {expt_name}')
            return None

        # Validate required intensities
        if need_meas and pattern.intensity_meas is None:
            log.error(f'No measured data available for experiment {expt_name}')
            return None
        if need_calc and pattern.intensity_calc is None:
            log.error(f'No calculated data available for experiment {expt_name}')
            return None

        # Auto-range for ASCII engine
        x_min, x_max = self._auto_x_range_for_ascii(pattern, x_array, x_min, x_max)

        # Filter x
        x_filtered = self._filtered_y_array(x_array, x_array, x_min, x_max)

        # Filter y arrays and build series / labels
        y_series = []
        y_labels = []

        y_meas = None
        if need_meas:
            y_meas = self._filtered_y_array(pattern.intensity_meas, x_array, x_min, x_max)
            y_series.append(y_meas)
            y_labels.append('meas')

        y_calc = None
        if need_calc:
            y_calc = self._filtered_y_array(pattern.intensity_calc, x_array, x_min, x_max)
            y_series.append(y_calc)
            y_labels.append('calc')

        if show_residual and y_meas is not None and y_calc is not None:
            y_resid = y_meas - y_calc
            y_series.append(y_resid)
            y_labels.append('resid')

        axes_labels = self._get_axes_labels(sample_form, scattering_type, x_axis)

        return {
            'x_filtered': x_filtered,
            'y_series': y_series,
            'y_labels': y_labels,
            'axes_labels': axes_labels,
            'x_axis': x_axis,
        }

    def _resolve_x_axis(self, expt_type: object, x: object) -> tuple:
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
        x_axis = DEFAULT_X_AXIS[(sample_form, scattering_type, beam_mode)] if x is None else x
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
        else:
            self._height = DEFAULT_HEIGHT

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
        pattern: object,
        expt_name: str,
        expt_type: object,
        x_min: object = None,
        x_max: object = None,
        x: object = None,
    ) -> None:
        """
        Plot measured pattern using the current engine.

        Parameters
        ----------
        pattern : object
            Object with x-axis arrays (``two_theta``,
            ``time_of_flight``, ``d_spacing``) and ``meas`` array.
        expt_name : str
            Experiment name for the title.
        expt_type : object
            Experiment type with scattering/beam enums.
        x_min : object, default=None
            Optional minimum x-axis limit.
        x_max : object, default=None
            Optional maximum x-axis limit.
        x : object, default=None
            X-axis type (``'two_theta'``, ``'time_of_flight'``, or
            ``'d_spacing'``). If ``None``, auto-detected from beam mode.
        """
        ctx = self._prepare_powder_data(
            pattern,
            expt_name,
            expt_type,
            x_min,
            x_max,
            x,
            need_meas=True,
        )
        if ctx is None:
            return

        self._backend.plot_powder(
            x=ctx['x_filtered'],
            y_series=ctx['y_series'],
            labels=ctx['y_labels'],
            axes_labels=ctx['axes_labels'],
            title=f"Measured data for experiment 🔬 '{expt_name}'",
            height=self.height,
        )

    def plot_calc(
        self,
        pattern: object,
        expt_name: str,
        expt_type: object,
        x_min: object = None,
        x_max: object = None,
        x: object = None,
    ) -> None:
        """
        Plot calculated pattern using the current engine.

        Parameters
        ----------
        pattern : object
            Object with x-axis arrays (``two_theta``,
            ``time_of_flight``, ``d_spacing``) and ``calc`` array.
        expt_name : str
            Experiment name for the title.
        expt_type : object
            Experiment type with scattering/beam enums.
        x_min : object, default=None
            Optional minimum x-axis limit.
        x_max : object, default=None
            Optional maximum x-axis limit.
        x : object, default=None
            X-axis type (``'two_theta'``, ``'time_of_flight'``, or
            ``'d_spacing'``). If ``None``, auto-detected from beam mode.
        """
        ctx = self._prepare_powder_data(
            pattern,
            expt_name,
            expt_type,
            x_min,
            x_max,
            x,
            need_calc=True,
        )
        if ctx is None:
            return

        self._backend.plot_powder(
            x=ctx['x_filtered'],
            y_series=ctx['y_series'],
            labels=ctx['y_labels'],
            axes_labels=ctx['axes_labels'],
            title=f"Calculated data for experiment 🔬 '{expt_name}'",
            height=self.height,
        )

    def plot_meas_vs_calc(
        self,
        pattern: object,
        expt_name: str,
        expt_type: object,
        x_min: object = None,
        x_max: object = None,
        show_residual: bool = False,
        x: object = None,
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
        pattern : object
            Data pattern object with meas/calc arrays.
        expt_name : str
            Experiment name for the title.
        expt_type : object
            Experiment type with sample_form, scattering, and beam
            enums.
        x_min : object, default=None
            Optional minimum x-axis limit.
        x_max : object, default=None
            Optional maximum x-axis limit.
        show_residual : bool, default=False
            If ``True``, add residual series (powder only).
        x : object, default=None
            X-axis type. If ``None``, auto-detected from sample form and
            beam mode.
        """
        x_axis, _, sample_form, scattering_type, _ = self._resolve_x_axis(expt_type, x)

        # Validate required data (before x-array check, matching
        # original behavior for plot_meas_vs_calc)
        if pattern.intensity_meas is None:
            log.error(f'No measured data available for experiment {expt_name}')
            return
        if pattern.intensity_calc is None:
            log.error(f'No calculated data available for experiment {expt_name}')
            return

        title = f"Measured vs Calculated data for experiment 🔬 '{expt_name}'"

        # Single crystal scatter plot (I²calc vs I²meas)
        if x_axis == XAxisType.INTENSITY_CALC or x_axis == 'intensity_calc':
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
                title=f"Measured vs Calculated data for experiment 🔬 '{expt_name}'",
                height=self.height,
            )
            return

        # Line plot (PD or SC with d_spacing/sin_theta_over_lambda)
        # TODO: Rename from _prepare_powder_data as it also supports
        #  single crystal line plots
        ctx = self._prepare_powder_data(
            pattern,
            expt_name,
            expt_type,
            x_min,
            x_max,
            x,
            need_meas=True,
            need_calc=True,
            show_residual=show_residual,
        )
        if ctx is None:
            return

        self._backend.plot_powder(
            x=ctx['x_filtered'],
            y_series=ctx['y_series'],
            labels=ctx['y_labels'],
            axes_labels=ctx['axes_labels'],
            title=title,
            height=self.height,
        )


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
