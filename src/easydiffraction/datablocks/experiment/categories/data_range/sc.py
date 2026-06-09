# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Single-crystal data range (sinθ/λ bounds, no profile step)."""

from __future__ import annotations

import numpy as np

from easydiffraction.core.display_handler import DisplayHandler
from easydiffraction.core.metadata import Compatibility
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import RangeValidator
from easydiffraction.core.variable import NumericDescriptor
from easydiffraction.datablocks.experiment.categories.data_range.base import DataRangeBase
from easydiffraction.datablocks.experiment.categories.data_range.factory import DataRangeFactory
from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum
from easydiffraction.io.cif.handler import CifHandler


@DataRangeFactory.register
class ScDataRange(DataRangeBase):
    """
    Single-crystal calculation range in reciprocal coordinates.

    Single-crystal data has no measurement axis, so sinθ/λ is the stored
    truth. Bounds (``sin_theta_over_lambda_min``/``_max``) limit
    reflection generation; there is no profile step. Unset bounds default
    to ``NaN`` and are filled from the default d-spacing window
    (``sinθ/λ = 1/(2·d)``, instrument-independent).
    """

    type_info = TypeInfo(
        tag='sc',
        description='Single-crystal calculation range',
    )
    compatibility = Compatibility(
        scattering_type=frozenset({ScatteringTypeEnum.BRAGG}),
        beam_mode=frozenset({
            BeamModeEnum.CONSTANT_WAVELENGTH,
            BeamModeEnum.TIME_OF_FLIGHT,
        }),
        sample_form=frozenset({SampleFormEnum.SINGLE_CRYSTAL}),
    )

    def __init__(self) -> None:
        """Initialize the single-crystal data range."""
        super().__init__()

        self._sin_theta_over_lambda_min = NumericDescriptor(
            name='sin_theta_over_lambda_min',
            description='Lower sinθ/λ bound of the calculation range',
            units='reciprocal_angstroms',
            display_handler=DisplayHandler(
                display_name='sinθ/λ min',
                display_units='Å⁻¹',
                latex_name=r'$(\sin\theta/\lambda)_{\min}$',
                latex_units=r'\AA$^{-1}$',
            ),
            value_spec=AttributeSpec(
                default=np.nan,
                validator=RangeValidator(ge=0),
            ),
            cif_handler=CifHandler(names=['_refln.sin_theta_over_lambda_range_min']),
        )
        self._sin_theta_over_lambda_max = NumericDescriptor(
            name='sin_theta_over_lambda_max',
            description='Upper sinθ/λ bound of the calculation range',
            units='reciprocal_angstroms',
            display_handler=DisplayHandler(
                display_name='sinθ/λ max',
                display_units='Å⁻¹',
                latex_name=r'$(\sin\theta/\lambda)_{\max}$',
                latex_units=r'\AA$^{-1}$',
            ),
            value_spec=AttributeSpec(
                default=np.nan,
                validator=RangeValidator(ge=0),
            ),
            cif_handler=CifHandler(names=['_refln.sin_theta_over_lambda_range_max']),
        )

    # ------------------------------------------------------------------
    #  Defaults projection
    # ------------------------------------------------------------------

    def _ensure_default_range(self) -> None:
        """Fill unset sinθ/λ bounds from the default d window."""
        sthovl_min, sthovl_max = self._default_sin_theta_over_lambda_bounds()
        if np.isnan(self._sin_theta_over_lambda_min.value):
            self._sin_theta_over_lambda_min._value = sthovl_min
        if np.isnan(self._sin_theta_over_lambda_max.value):
            self._sin_theta_over_lambda_max._value = sthovl_max

    def _measured_axis_values(self) -> np.ndarray | None:
        """Return measured sinθ/λ values from the reflection collection."""
        category = self._intensity_category()
        values = getattr(category, 'sin_theta_over_lambda', None)
        if values is None:
            return None
        return np.asarray(values, dtype=float)

    def _measured_step(self, values: np.ndarray) -> None:  # noqa: ARG002, PLR6301
        """Single-crystal data has no profile step."""
        return None

    # ------------------------------------------------------------------
    #  Stored axis (sinθ/λ)
    # ------------------------------------------------------------------

    @property
    def sin_theta_over_lambda_min(self) -> float:
        """Lower sinθ/λ bound of the calculation range (Å⁻¹)."""
        measured = self._measured_axis_range()
        if measured is not None:
            return measured[0]
        self._ensure_default_range()
        return self._sin_theta_over_lambda_min.value

    @sin_theta_over_lambda_min.setter
    def sin_theta_over_lambda_min(self, value: float) -> None:
        """Set the lower sinθ/λ bound of the calculation range (Å⁻¹)."""
        self._raise_if_measured()
        self._sin_theta_over_lambda_min.value = value

    @property
    def sin_theta_over_lambda_max(self) -> float:
        """Upper sinθ/λ bound of the calculation range (Å⁻¹)."""
        measured = self._measured_axis_range()
        if measured is not None:
            return measured[1]
        self._ensure_default_range()
        return self._sin_theta_over_lambda_max.value

    @sin_theta_over_lambda_max.setter
    def sin_theta_over_lambda_max(self, value: float) -> None:
        """Set the upper sinθ/λ bound of the calculation range (Å⁻¹)."""
        self._raise_if_measured()
        self._sin_theta_over_lambda_max.value = value

    # ------------------------------------------------------------------
    #  Active-axis aliases (single crystal has no profile step)
    # ------------------------------------------------------------------

    @property
    def x_min(self) -> float:
        """Lower bound on the active (sinθ/λ) axis (Å⁻¹)."""
        return self.sin_theta_over_lambda_min

    @property
    def x_max(self) -> float:
        """Upper bound on the active (sinθ/λ) axis (Å⁻¹)."""
        return self.sin_theta_over_lambda_max

    @property
    def x_step(self) -> None:
        """Single-crystal data has no profile step."""
        return None

    # ------------------------------------------------------------------
    #  Derived d-spacing view
    # ------------------------------------------------------------------

    @property
    def d_spacing_min(self) -> float:
        """Smallest d-spacing in the range (at sinθ/λ_max) (Å)."""
        return float(1.0 / (2.0 * self.sin_theta_over_lambda_max))

    @property
    def d_spacing_max(self) -> float:
        """Largest d-spacing in the range (at sinθ/λ_min) (Å)."""
        return float(1.0 / (2.0 * self.sin_theta_over_lambda_min))
