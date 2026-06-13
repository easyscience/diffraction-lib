# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Time-of-flight powder data range (time-of-flight bounds and step)."""

from __future__ import annotations

import numpy as np

from easydiffraction.core.display_handler import DisplayHandler
from easydiffraction.core.metadata import Compatibility
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import RangeValidator
from easydiffraction.core.variable import NumericDescriptor
from easydiffraction.datablocks.experiment.categories.data_range.base import DEFAULT_D_SPACING_MAX
from easydiffraction.datablocks.experiment.categories.data_range.base import DEFAULT_D_SPACING_MIN
from easydiffraction.datablocks.experiment.categories.data_range.base import DEFAULT_NUM_POINTS
from easydiffraction.datablocks.experiment.categories.data_range.base import DataRangeBase
from easydiffraction.datablocks.experiment.categories.data_range.factory import DataRangeFactory
from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum
from easydiffraction.io.cif.handler import CifHandler
from easydiffraction.utils.utils import tof_to_d


@DataRangeFactory.register
class TofPdDataRange(DataRangeBase):
    """
    Time-of-flight powder calculation range.

    Stores the time-of-flight window
    (``time_of_flight_min``/``time_of_flight_max``) and the profile step
    (``time_of_flight_inc``). Unset bounds default to ``NaN`` and are
    filled by projecting the default d-spacing window through the
    instrument TOF calibration.
    """

    type_info = TypeInfo(
        tag='tof-pd',
        description='TOF powder calculation range',
    )
    compatibility = Compatibility(
        scattering_type=frozenset({ScatteringTypeEnum.BRAGG}),
        beam_mode=frozenset({BeamModeEnum.TIME_OF_FLIGHT}),
        sample_form=frozenset({SampleFormEnum.POWDER}),
    )

    def __init__(self) -> None:
        """Initialize the time-of-flight powder data range."""
        super().__init__()

        self._time_of_flight_min = NumericDescriptor(
            name='time_of_flight_min',
            description='Lower time-of-flight bound of the calculation range',
            units='microseconds',
            display_handler=DisplayHandler(
                display_name='TOF min',
                display_units='μs',
                latex_name=r'$\mathrm{TOF}_{\min}$',
                latex_units=r'$\mu\mathrm{s}$',
            ),
            value_spec=AttributeSpec(
                default=np.nan,
                validator=RangeValidator(ge=0),
            ),
            cif_handler=CifHandler(
                names=['_data_range.time_of_flight_min'],
                import_names=['_pd_meas.time_of_flight_range_min'],
                iucr_name='_pd_meas.time_of_flight_range_min',
            ),
        )
        self._time_of_flight_max = NumericDescriptor(
            name='time_of_flight_max',
            description='Upper time-of-flight bound of the calculation range',
            units='microseconds',
            display_handler=DisplayHandler(
                display_name='TOF max',
                display_units='μs',
                latex_name=r'$\mathrm{TOF}_{\max}$',
                latex_units=r'$\mu\mathrm{s}$',
            ),
            value_spec=AttributeSpec(
                default=np.nan,
                validator=RangeValidator(ge=0),
            ),
            cif_handler=CifHandler(
                names=['_data_range.time_of_flight_max'],
                import_names=['_pd_meas.time_of_flight_range_max'],
                iucr_name='_pd_meas.time_of_flight_range_max',
            ),
        )
        self._time_of_flight_inc = NumericDescriptor(
            name='time_of_flight_inc',
            description='Time-of-flight step between calculation points',
            units='microseconds',
            display_handler=DisplayHandler(
                display_name='TOF step',
                display_units='μs',
                latex_name=r'$\mathrm{TOF}_{\mathrm{inc}}$',
                latex_units=r'$\mu\mathrm{s}$',
            ),
            value_spec=AttributeSpec(
                default=np.nan,
                validator=RangeValidator(gt=0),
            ),
            cif_handler=CifHandler(
                names=['_data_range.time_of_flight_inc'],
                import_names=['_pd_meas.time_of_flight_range_inc'],
                iucr_name='_pd_meas.time_of_flight_range_inc',
            ),
        )

    # ------------------------------------------------------------------
    #  Defaults projection
    # ------------------------------------------------------------------

    def _tof_calibration(self) -> tuple[float, float, float] | None:
        """
        Return ``(offset, linear, quadratic)`` calibration, or None.
        """
        instrument = self._instrument()
        if instrument is None:
            return None
        return (
            instrument.calib_d_to_tof_offset.value,
            instrument.calib_d_to_tof_linear.value,
            instrument.calib_d_to_tof_quadratic.value,
        )

    @staticmethod
    def _tof_from_d(
        d_spacing: float,
        offset: float,
        linear: float,
        quadratic: float,
    ) -> float:
        """
        Return time-of-flight (μs) for a d-spacing.

        ``TOF = c0+c1·d+c2·d²``.
        """
        return float(offset + linear * d_spacing + quadratic * d_spacing**2)

    def _ensure_default_range(self) -> None:
        """
        Project the default d window onto unset TOF bounds and step.
        """
        calibration = self._tof_calibration()
        if calibration is None:
            return
        offset, linear, quadratic = calibration
        if np.isnan(self._time_of_flight_min.value):
            self._time_of_flight_min._value = self._tof_from_d(
                DEFAULT_D_SPACING_MIN, offset, linear, quadratic
            )
        if np.isnan(self._time_of_flight_max.value):
            self._time_of_flight_max._value = self._tof_from_d(
                DEFAULT_D_SPACING_MAX, offset, linear, quadratic
            )
        if np.isnan(self._time_of_flight_inc.value):
            span = self._time_of_flight_max.value - self._time_of_flight_min.value
            self._time_of_flight_inc._value = span / (DEFAULT_NUM_POINTS - 1)

    # ------------------------------------------------------------------
    #  Stored axis (time-of-flight)
    # ------------------------------------------------------------------

    def _stored_axis(self) -> tuple[float, float, float]:
        """
        Return stored ``(min, max, inc)`` after projecting defaults.
        """
        return (
            self._time_of_flight_min.value,
            self._time_of_flight_max.value,
            self._time_of_flight_inc.value,
        )

    @property
    def time_of_flight_min(self) -> NumericDescriptor:
        """
        Lower time-of-flight bound of the calculation range (μs).

        Reading this property returns the underlying
        ``NumericDescriptor`` object, synced to the effective
        (measured-derived or stored/default) value.
        """
        self._time_of_flight_min._value = self._effective_axis()[0]
        return self._time_of_flight_min

    @time_of_flight_min.setter
    def time_of_flight_min(self, value: float) -> None:
        """Set the lower time-of-flight bound (μs)."""
        self._raise_if_measured()
        self._time_of_flight_min.value = value
        self._invalidate_generated_grid()

    @property
    def time_of_flight_max(self) -> NumericDescriptor:
        """
        Upper time-of-flight bound of the calculation range (μs).

        Reading this property returns the underlying
        ``NumericDescriptor`` object, synced to the effective value.
        """
        self._time_of_flight_max._value = self._effective_axis()[1]
        return self._time_of_flight_max

    @time_of_flight_max.setter
    def time_of_flight_max(self, value: float) -> None:
        """Set the upper time-of-flight bound (μs)."""
        self._raise_if_measured()
        self._time_of_flight_max.value = value
        self._invalidate_generated_grid()

    @property
    def time_of_flight_inc(self) -> NumericDescriptor:
        """
        Time-of-flight step between calculation points (μs).

        Reading this property returns the underlying
        ``NumericDescriptor`` object. Its value is ``NaN`` when a
        measured but non-uniform scan is present.
        """
        step = self._effective_axis()[2]
        self._time_of_flight_inc._value = float('nan') if step is None else step
        return self._time_of_flight_inc

    @time_of_flight_inc.setter
    def time_of_flight_inc(self, value: float) -> None:
        """
        Set the time-of-flight step between calculation points (μs).
        """
        self._raise_if_measured()
        self._time_of_flight_inc.value = value
        self._invalidate_generated_grid()

    # ------------------------------------------------------------------
    #  Active-axis aliases (float convenience views)
    # ------------------------------------------------------------------

    @property
    def x_min(self) -> float:
        """Lower bound on the active (time-of-flight) axis (μs)."""
        return self._effective_axis()[0]

    @property
    def x_max(self) -> float:
        """Upper bound on the active (time-of-flight) axis (μs)."""
        return self._effective_axis()[1]

    @property
    def x_step(self) -> float | None:
        """
        Step on the active (TOF) axis (μs), or None if non-uniform.
        """
        return self._effective_axis()[2]

    # ------------------------------------------------------------------
    #  Derived reciprocal views (d-spacing, sinθ/λ)
    # ------------------------------------------------------------------

    def _d_spacing_at(self, time_of_flight: float) -> float:
        """
        Return d-spacing (Å) for a TOF value, NaN without calibration.
        """
        calibration = self._tof_calibration()
        if calibration is None:
            return float('nan')
        offset, linear, quad = calibration
        return float(tof_to_d(np.asarray([time_of_flight], dtype=float), offset, linear, quad)[0])

    @property
    def d_spacing_min(self) -> float:
        """Smallest d-spacing in the range (at TOF_min) (Å)."""
        return self._d_spacing_at(self.x_min)

    @property
    def d_spacing_max(self) -> float:
        """Largest d-spacing in the range (at TOF_max) (Å)."""
        return self._d_spacing_at(self.x_max)

    @property
    def sin_theta_over_lambda_min(self) -> float:
        """
        Lower sinθ/λ bound derived from the largest d-spacing (Å⁻¹).
        """
        d_max = self.d_spacing_max
        return float(1.0 / (2.0 * d_max))

    @property
    def sin_theta_over_lambda_max(self) -> float:
        """
        Upper sinθ/λ bound derived from the smallest d-spacing (Å⁻¹).
        """
        d_min = self.d_spacing_min
        return float(1.0 / (2.0 * d_min))
