# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Cylindrical Debye-Scherrer absorption correction (Hewat)."""

from __future__ import annotations

from easydiffraction.core.display_handler import DisplayHandler
from easydiffraction.core.metadata import CalculatorSupport
from easydiffraction.core.metadata import Compatibility
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import RangeValidator
from easydiffraction.core.variable import Parameter
from easydiffraction.datablocks.experiment.categories.absorption.base import AbsorptionBase
from easydiffraction.datablocks.experiment.categories.absorption.factory import AbsorptionFactory
from easydiffraction.datablocks.experiment.item.enums import AbsorptionTypeEnum
from easydiffraction.datablocks.experiment.item.enums import CalculatorEnum
from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum
from easydiffraction.io.cif.handler import CifHandler


@AbsorptionFactory.register
class CylinderHewatAbsorption(AbsorptionBase):
    """
    Cylindrical Debye-Scherrer absorption correction (Hewat).

    Applies the angle-dependent transmission factor

    ``A(θ) = exp(-(1.7133 - 0.0368·sin²θ)·μR
              + (0.0927 + 0.375·sin²θ)·μR²)``

    for a cylindrical sample, where ``μR`` is the linear absorption
    coefficient times the sample radius. Validated to four decimals
    against FullProf for μR ≲ 1.5; for larger μR a Lobanov form is
    preferable (not yet implemented).
    """

    type_info = TypeInfo(
        tag=AbsorptionTypeEnum.CYLINDER_HEWAT.value,
        description=AbsorptionTypeEnum.CYLINDER_HEWAT.description(),
    )
    compatibility = Compatibility(
        sample_form=frozenset({SampleFormEnum.POWDER}),
        scattering_type=frozenset({ScatteringTypeEnum.BRAGG}),
    )
    calculator_support = CalculatorSupport(
        calculators=frozenset({CalculatorEnum.CRYSPY, CalculatorEnum.CRYSFML}),
    )

    def __init__(self) -> None:
        super().__init__()

        self._mu_r = Parameter(
            name='mu_r',
            description='Absorption coefficient times sample radius (μR).',
            display_handler=DisplayHandler(
                display_name='μR',
                latex_name=r'\mu R',
            ),
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(ge=0.0),
            ),
            cif_handler=CifHandler(
                names=['_absorption.mu_r'],
                iucr_name='_easydiffraction_absorption.mu_r',
            ),
        )

    # ------------------------------------------------------------------
    #  Public properties
    # ------------------------------------------------------------------

    @property
    def mu_r(self) -> Parameter:
        """
        Absorption coefficient times sample radius (μR).

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._mu_r

    @mu_r.setter
    def mu_r(self, value: float) -> None:
        self._mu_r.value = value
