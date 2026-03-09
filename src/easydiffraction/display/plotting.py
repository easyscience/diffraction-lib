# SPDX-FileCopyrightText: 2021-2026 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Plotting facade for measured and calculated patterns.

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

    def __init__(self):
        super().__init__()
        # X-axis limits
        self._x_min = DEFAULT_MIN
        self._x_max = DEFAULT_MAX
        # Chart height
        self.height = DEFAULT_HEIGHT

    @classmethod
    def _factory(cls) -> type[RendererFactoryBase]:  # type: ignore[override]
        return PlotterFactory

    @classmethod
    def _default_engine(cls) -> str:
        return PlotterEngineEnum.default().value

    def show_config(self):
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

    @property
    def x_min(self):
        """Minimum x-axis limit."""
        return self._x_min

    @x_min.setter
    def x_min(self, value):
        """Set the minimum x-axis limit.

        Args:
            value: Minimum limit or ``None`` to reset to default.
        """
        if value is not None:
            self._x_min = value
        else:
            self._x_min = DEFAULT_MIN

    @property
    def x_max(self):
        """Maximum x-axis limit."""
        return self._x_max

    @x_max.setter
    def x_max(self, value):
        """Set the maximum x-axis limit.

        Args:
            value: Maximum limit or ``None`` to reset to default.
        """
        if value is not None:
            self._x_max = value
        else:
            self._x_max = DEFAULT_MAX

    @property
    def height(self):
        """Plot height (rows for ASCII, pixels for Plotly)."""
        return self._height

    @height.setter
    def height(self, value):
        """Set plot height.

        Args:
            value: Height value or ``None`` to reset to default.
        """
        if value is not None:
            self._height = value
        else:
            self._height = DEFAULT_HEIGHT

    # TODO: Extract common code from
    #  plot_meas, plot_calc and plot_meas_vs_calc
    def plot_meas(
        self,
        pattern,
        expt_name,
        expt_type,
        x_min=None,
        x_max=None,
        x=None,
    ):
        """Plot measured pattern using the current engine.

        Args:
            pattern: Object with x-axis arrays (``two_theta``,
                ``time_of_flight``, ``d_spacing``) and ``meas`` array.
            expt_name: Experiment name for the title.
            expt_type: Experiment type with scattering/beam enums.
            x_min: Optional minimum x-axis limit.
            x_max: Optional maximum x-axis limit.
            x: X-axis type (``'two_theta'``, ``'time_of_flight'``, or
                ``'d_spacing'``). If ``None``, auto-detected from
                beam mode.
        """
        # Determine x-axis type
        sample_form = expt_type.sample_form.value
        beam_mode = expt_type.beam_mode.value
        x_axis = DEFAULT_X_AXIS[(sample_form, beam_mode)] if x is None else x

        # Get attribute name for error messages
        # (works for both enum and string)
        x_name = getattr(x_axis, 'value', x_axis)

        # Get x-array from pattern
        x_array = getattr(pattern, x_axis, None)
        if x_array is None:
            log.error(f'No {x_name} data available for experiment {expt_name}')
            return
        if pattern.meas is None:
            log.error(f'No measured data available for experiment {expt_name}')
            return

        # For asciichartpy, if x_min or x_max is not provided, center
        # around the maximum intensity peak
        if self._engine == 'asciichartpy' and (x_min is None or x_max is None):
            max_intensity_pos = np.argmax(pattern.meas)
            half_range = 50
            start = max(0, max_intensity_pos - half_range)
            end = min(len(x_array) - 1, max_intensity_pos + half_range)
            x_min = x_array[start]
            x_max = x_array[end]

        # Filter x, y_meas, and y_calc based on x_min and x_max
        x = self._filtered_y_array(
            y_array=x_array,
            x_array=x_array,
            x_min=x_min,
            x_max=x_max,
        )
        y_meas = self._filtered_y_array(
            y_array=pattern.meas,
            x_array=x_array,
            x_min=x_min,
            x_max=x_max,
        )

        y_series = [y_meas]
        y_labels = ['meas']

        axes_labels = DEFAULT_AXES_LABELS[
            (
                expt_type.sample_form.value,
                expt_type.scattering_type.value,
                x_axis,
            )
        ]

        # TODO: Before, it was self._plotter.plot. Check what is better.
        self._backend.plot_powder(
            x=x,
            y_series=y_series,
            labels=y_labels,
            axes_labels=axes_labels,
            title=f"Measured data for experiment 🔬 '{expt_name}'",
            height=self.height,
        )

    # TODO: Extract common code from
    #  plot_meas, plot_calc and plot_meas_vs_calc
    def plot_calc(
        self,
        pattern,
        expt_name,
        expt_type,
        x_min=None,
        x_max=None,
        x=None,
    ):
        """Plot calculated pattern using the current engine.

        Args:
            pattern: Object with x-axis arrays (``two_theta``,
                ``time_of_flight``, ``d_spacing``) and ``calc`` array.
            expt_name: Experiment name for the title.
            expt_type: Experiment type with scattering/beam enums.
            x_min: Optional minimum x-axis limit.
            x_max: Optional maximum x-axis limit.
            x: X-axis type (``'two_theta'``, ``'time_of_flight'``, or
                ``'d_spacing'``). If ``None``, auto-detected from
                beam mode.
        """
        # Determine x-axis type
        sample_form = expt_type.sample_form.value
        beam_mode = expt_type.beam_mode.value
        x_axis = DEFAULT_X_AXIS[(sample_form, beam_mode)] if x is None else x

        # Get attribute name for error messages
        # (works for both enum and string)
        x_name = getattr(x_axis, 'value', x_axis)

        # Get x-array from pattern
        x_array = getattr(pattern, x_axis, None)
        if x_array is None:
            log.error(f'No {x_name} data available for experiment {expt_name}')
            return
        if pattern.calc is None:
            log.error(f'No calculated data available for experiment {expt_name}')
            return

        # For asciichartpy, if x_min or x_max is not provided, center
        # around the maximum intensity peak
        if self._engine == 'asciichartpy' and (x_min is None or x_max is None):
            max_intensity_pos = np.argmax(pattern.meas)
            half_range = 50
            start = max(0, max_intensity_pos - half_range)
            end = min(len(x_array) - 1, max_intensity_pos + half_range)
            x_min = x_array[start]
            x_max = x_array[end]

        # Filter x, y_meas, and y_calc based on x_min and x_max
        x = self._filtered_y_array(
            y_array=x_array,
            x_array=x_array,
            x_min=x_min,
            x_max=x_max,
        )
        y_calc = self._filtered_y_array(
            y_array=pattern.calc,
            x_array=x_array,
            x_min=x_min,
            x_max=x_max,
        )

        y_series = [y_calc]
        y_labels = ['calc']

        axes_labels = DEFAULT_AXES_LABELS[
            (
                expt_type.sample_form.value,
                expt_type.scattering_type.value,
                x_axis,
            )
        ]

        self._backend.plot_powder(
            x=x,
            y_series=y_series,
            labels=y_labels,
            axes_labels=axes_labels,
            title=f"Calculated data for experiment 🔬 '{expt_name}'",
            height=self.height,
        )

    # TODO: Extract common code from
    #  plot_meas, plot_calc and plot_meas_vs_calc
    def plot_meas_vs_calc(
        self,
        pattern,
        expt_name,
        expt_type,
        x_min=None,
        x_max=None,
        show_residual=False,
        x=None,
    ):
        """Plot measured and calculated series and optional residual.

        Supports both powder and single crystal data with a unified API.

        For powder diffraction:
            - x='two_theta', 'time_of_flight', or 'd_spacing'
            - Auto-detected from beam mode if not specified

        For single crystal diffraction:
            - x='intensity_calc' (default): scatter plot
            - x='d_spacing' or 'sin_theta_over_lambda': line plot

        Args:
            pattern: Data pattern object with meas/calc arrays.
            expt_name: Experiment name for the title.
            expt_type: Experiment type with sample_form,
                scattering, and beam enums.
            x_min: Optional minimum x-axis limit.
            x_max: Optional maximum x-axis limit.
            show_residual: If ``True``, add residual series
                (powder only).
            x: X-axis type. If ``None``, auto-detected from sample form
                and beam mode.
        """
        # Determine x-axis type from sample form and beam mode
        sample_form = expt_type.sample_form.value
        beam_mode = expt_type.beam_mode.value
        x_axis = DEFAULT_X_AXIS[(sample_form, beam_mode)] if x is None else x

        # Get attribute name for error messages
        # (works for both enum and string)
        x_name = getattr(x_axis, 'value', x_axis)

        # Validate required data
        if pattern.meas is None:
            log.error(f'No measured data available for experiment {expt_name}')
            return
        if pattern.calc is None:
            log.error(f'No calculated data available for experiment {expt_name}')
            return

        # Get axes labels
        axes_labels = DEFAULT_AXES_LABELS[
            (
                sample_form,
                expt_type.scattering_type.value,
                x_axis,
            )
        ]

        title = f"Measured vs Calculated data for experiment 🔬 '{expt_name}'"

        # Single crystal scatter plot (I²calc vs I²meas)
        if x_axis == XAxisType.INTENSITY_CALC or x_axis == 'intensity_calc':
            if pattern.meas_su is None:
                log.warning(f'No measurement uncertainties for experiment {expt_name}')
                meas_su = np.zeros_like(pattern.meas)
            else:
                meas_su = pattern.meas_su

            self._backend.plot_single_crystal(
                x_calc=pattern.calc,
                y_meas=pattern.meas,
                y_meas_su=meas_su,
                axes_labels=axes_labels,
                title=title,
                height=self.height,
            )
            return

        # Line plot (powder or SC with d_spacing/sin_theta_over_lambda)
        x_array = getattr(pattern, x_axis, None)
        if x_array is None:
            log.error(f'No {x_name} data available for experiment {expt_name}')
            return

        # For asciichartpy, if x_min or x_max is not provided, center
        # around the maximum intensity peak
        if self._engine == 'asciichartpy' and (x_min is None or x_max is None):
            max_intensity_pos = np.argmax(pattern.meas)
            half_range = 50
            start = max(0, max_intensity_pos - half_range)
            end = min(len(x_array) - 1, max_intensity_pos + half_range)
            x_min = x_array[start]
            x_max = x_array[end]

        # Filter x, y_meas, and y_calc based on x_min and x_max
        x = self._filtered_y_array(
            y_array=x_array,
            x_array=x_array,
            x_min=x_min,
            x_max=x_max,
        )
        y_meas = self._filtered_y_array(
            y_array=pattern.meas,
            x_array=x_array,
            x_min=x_min,
            x_max=x_max,
        )
        y_calc = self._filtered_y_array(
            y_array=pattern.calc,
            x_array=x_array,
            x_min=x_min,
            x_max=x_max,
        )

        y_series = [y_meas, y_calc]
        y_labels = ['meas', 'calc']

        if show_residual:
            y_resid = y_meas - y_calc
            y_series.append(y_resid)
            y_labels.append('resid')

        self._backend.plot_powder(
            x=x,
            y_series=y_series,
            labels=y_labels,
            axes_labels=axes_labels,
            title=title,
            height=self.height,
        )

    def _filtered_y_array(
        self,
        y_array,
        x_array,
        x_min,
        x_max,
    ):
        """Filter an array by the inclusive x-range limits.

        Args:
            y_array: 1D array-like of y values.
            x_array: 1D array-like of x values (same length as
                ``y_array``).
            x_min: Minimum x limit (or ``None`` to use default).
            x_max: Maximum x limit (or ``None`` to use default).

        Returns:
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
