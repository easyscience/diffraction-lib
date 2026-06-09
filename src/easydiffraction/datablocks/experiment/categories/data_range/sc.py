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
    #  Public properties
    # ------------------------------------------------------------------

    @property
    def sin_theta_over_lambda_min(self) -> float:
        """Lower sinθ/λ bound of the calculation range (Å⁻¹)."""
        return self._sin_theta_over_lambda_min.value

    @sin_theta_over_lambda_min.setter
    def sin_theta_over_lambda_min(self, value: float) -> None:
        """Set the lower sinθ/λ bound of the calculation range (Å⁻¹)."""
        self._sin_theta_over_lambda_min.value = value

    @property
    def sin_theta_over_lambda_max(self) -> float:
        """Upper sinθ/λ bound of the calculation range (Å⁻¹)."""
        return self._sin_theta_over_lambda_max.value

    @sin_theta_over_lambda_max.setter
    def sin_theta_over_lambda_max(self, value: float) -> None:
        """Set the upper sinθ/λ bound of the calculation range (Å⁻¹)."""
        self._sin_theta_over_lambda_max.value = value
