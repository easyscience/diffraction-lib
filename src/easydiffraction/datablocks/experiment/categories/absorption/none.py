# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""No-op sample-absorption correction (the default)."""

from __future__ import annotations

from easydiffraction.core.metadata import CalculatorSupport
from easydiffraction.core.metadata import Compatibility
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.datablocks.experiment.categories.absorption.base import AbsorptionBase
from easydiffraction.datablocks.experiment.categories.absorption.factory import AbsorptionFactory
from easydiffraction.datablocks.experiment.item.enums import AbsorptionTypeEnum
from easydiffraction.datablocks.experiment.item.enums import CalculatorEnum
from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum


@AbsorptionFactory.register
class NoAbsorption(AbsorptionBase):
    """No sample-absorption correction; the applied factor is unity."""

    type_info = TypeInfo(
        tag=AbsorptionTypeEnum.NONE.value,
        description=AbsorptionTypeEnum.NONE.description(),
    )
    compatibility = Compatibility(
        sample_form=frozenset({SampleFormEnum.POWDER}),
        scattering_type=frozenset({ScatteringTypeEnum.BRAGG}),
    )
    calculator_support = CalculatorSupport(
        calculators=frozenset({CalculatorEnum.CRYSPY, CalculatorEnum.CRYSFML}),
    )
