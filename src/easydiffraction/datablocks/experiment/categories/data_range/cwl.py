# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Constant-wavelength powder data range (2θ bounds and step)."""

from __future__ import annotations

import numpy as np

from easydiffraction.core.display_handler import DisplayHandler
from easydiffraction.core.metadata import Compatibility
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import RangeValidator
from easydiffraction.core.variable import NumericDescriptor
from easydiffraction.datablocks.experiment.categories.data_range.base import DEFAULT_NUM_POINTS
from easydiffraction.datablocks.experiment.categories.data_range.base import DataRangeBase
from easydiffraction.datablocks.experiment.categories.data_range.factory import DataRangeFactory
from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum
from easydiffraction.io.cif.handler import CifHandler
from easydiffraction.utils.utils import twotheta_to_d

# Bragg geometry caps sin(θ) at just under 1 so the 2θ projection of a
# fine d-spacing stays a valid angle below 180°.
_MAX_SIN_THETA = 0.999999


@DataRangeFactory.register
class CwlPdDataRange(DataRangeBase):
    """
    Constant-wavelength powder calculation range.

    Stores the 2θ window (``two_theta_min``/``two_theta_max``) and the
    profile step (``two_theta_inc``). Unset bounds default to ``NaN`` and
    are filled by projecting the default d-spacing window through the
    instrument wavelength.
    """

    type_info = TypeInfo(
        tag='cwl-pd',
        description='CW powder calculation range',
    )
    compatibility = Compatibility(
        scattering_type=frozenset({ScatteringTypeEnum.BRAGG, ScatteringTypeEnum.TOTAL}),
        beam_mode=frozenset({BeamModeEnum.CONSTANT_WAVELENGTH}),
        sample_form=frozenset({SampleFormEnum.POWDER}),
    )

    def __init__(self) -> None:
        """Initialize the constant-wavelength powder data range."""
        super().__init__()

        self._two_theta_min = NumericDescriptor(
            name='two_theta_min',
            description='Lower 2θ bound of the calculation range',
            units='degrees',
            display_handler=DisplayHandler(
                display_name='2θ min',
                display_units='deg',
                latex_name=r'$2\theta_{\min}$',
                latex_units=r'\mathrm{deg}',
            ),
            value_spec=AttributeSpec(
                default=np.nan,
                validator=RangeValidator(ge=0, le=180),
            ),
            cif_handler=CifHandler(names=['_pd_meas.2theta_range_min']),
        )
        self._two_theta_max = NumericDescriptor(
            name='two_theta_max',
            description='Upper 2θ bound of the calculation range',
            units='degrees',
            display_handler=DisplayHandler(
                display_name='2θ max',
                display_units='deg',
                latex_name=r'$2\theta_{\max}$',
                latex_units=r'\mathrm{deg}',
            ),
            value_spec=AttributeSpec(
                default=np.nan,
                validator=RangeValidator(ge=0, le=180),
            ),
            cif_handler=CifHandler(names=['_pd_meas.2theta_range_max']),
        )
        self._two_theta_inc = NumericDescriptor(
            name='two_theta_inc',
            description='2θ step between calculation points',
            units='degrees',
            display_handler=DisplayHandler(
                display_name='2θ step',
                display_units='deg',
                latex_name=r'$2\theta_{\mathrm{inc}}$',
                latex_units=r'\mathrm{deg}',
            ),
            value_spec=AttributeSpec(
                default=np.nan,
                validator=RangeValidator(gt=0, le=180),
            ),
            cif_handler=CifHandler(names=['_pd_meas.2theta_range_inc']),
        )

    # ------------------------------------------------------------------
    #  Defaults projection
    # ------------------------------------------------------------------

    def _wavelength(self) -> float | None:
        """Return the instrument wavelength (Å), or None if absent."""
        instrument = self._instrument()
        if instrument is None:
            return None
        return instrument.setup_wavelength.value

    @staticmethod
    def _two_theta_from_sin_theta_over_lambda(
        sin_theta_over_lambda: float,
        wavelength: float,
    ) -> float:
        """Return 2θ (deg) for a sinθ/λ value at the given wavelength."""
        sin_theta = min(wavelength * sin_theta_over_lambda, _MAX_SIN_THETA)
        return float(2.0 * np.degrees(np.arcsin(sin_theta)))

    def _ensure_default_range(self) -> None:
        """Project the default d window onto unset 2θ bounds and step."""
        wavelength = self._wavelength()
        if wavelength is None:
            return
        sthovl_min, sthovl_max = self._default_sin_theta_over_lambda_bounds()
        if np.isnan(self._two_theta_min.value):
            self._two_theta_min._value = self._two_theta_from_sin_theta_over_lambda(
                sthovl_min, wavelength
            )
        if np.isnan(self._two_theta_max.value):
            self._two_theta_max._value = self._two_theta_from_sin_theta_over_lambda(
                sthovl_max, wavelength
            )
        if np.isnan(self._two_theta_inc.value):
            span = self._two_theta_max.value - self._two_theta_min.value
            self._two_theta_inc._value = span / (DEFAULT_NUM_POINTS - 1)

    # ------------------------------------------------------------------
    #  Stored axis (2θ)
    # ------------------------------------------------------------------

    @property
    def two_theta_min(self) -> float:
        """Lower 2θ bound of the calculation range (deg)."""
        measured = self._measured_axis_range()
        if measured is not None:
            return measured[0]
        self._ensure_default_range()
        return self._two_theta_min.value

    @two_theta_min.setter
    def two_theta_min(self, value: float) -> None:
        """Set the lower 2θ bound of the calculation range (deg)."""
        self._raise_if_measured()
        self._two_theta_min.value = value

    @property
    def two_theta_max(self) -> float:
        """Upper 2θ bound of the calculation range (deg)."""
        measured = self._measured_axis_range()
        if measured is not None:
            return measured[1]
        self._ensure_default_range()
        return self._two_theta_max.value

    @two_theta_max.setter
    def two_theta_max(self, value: float) -> None:
        """Set the upper 2θ bound of the calculation range (deg)."""
        self._raise_if_measured()
        self._two_theta_max.value = value

    @property
    def two_theta_inc(self) -> float:
        """2θ step between calculation points (deg)."""
        measured = self._measured_axis_range()
        if measured is not None and measured[2] is not None:
            return measured[2]
        self._ensure_default_range()
        return self._two_theta_inc.value

    @two_theta_inc.setter
    def two_theta_inc(self, value: float) -> None:
        """Set the 2θ step between calculation points (deg)."""
        self._raise_if_measured()
        self._two_theta_inc.value = value

    # ------------------------------------------------------------------
    #  Active-axis aliases
    # ------------------------------------------------------------------

    @property
    def x_min(self) -> float:
        """Lower bound on the active (2θ) axis (deg)."""
        return self.two_theta_min

    @property
    def x_max(self) -> float:
        """Upper bound on the active (2θ) axis (deg)."""
        return self.two_theta_max

    @property
    def x_step(self) -> float:
        """Step on the active (2θ) axis (deg)."""
        return self.two_theta_inc

    # ------------------------------------------------------------------
    #  Derived reciprocal views (sinθ/λ, d-spacing)
    # ------------------------------------------------------------------

    def _sin_theta_over_lambda_at(self, two_theta: float) -> float:
        """Return sinθ/λ (Å⁻¹) for a 2θ value, NaN without wavelength."""
        wavelength = self._wavelength()
        if wavelength is None:
            return float('nan')
        return float(np.sin(np.radians(two_theta / 2.0)) / wavelength)

    @property
    def sin_theta_over_lambda_min(self) -> float:
        """Lower sinθ/λ bound derived from 2θ_min (Å⁻¹)."""
        return self._sin_theta_over_lambda_at(self.two_theta_min)

    @property
    def sin_theta_over_lambda_max(self) -> float:
        """Upper sinθ/λ bound derived from 2θ_max (Å⁻¹)."""
        return self._sin_theta_over_lambda_at(self.two_theta_max)

    @property
    def d_spacing_min(self) -> float:
        """Smallest d-spacing in the range (at 2θ_max) (Å)."""
        wavelength = self._wavelength()
        if wavelength is None:
            return float('nan')
        return float(twotheta_to_d(self.two_theta_max, wavelength))

    @property
    def d_spacing_max(self) -> float:
        """Largest d-spacing in the range (at 2θ_min) (Å)."""
        wavelength = self._wavelength()
        if wavelength is None:
            return float('nan')
        return float(twotheta_to_d(self.two_theta_min, wavelength))
