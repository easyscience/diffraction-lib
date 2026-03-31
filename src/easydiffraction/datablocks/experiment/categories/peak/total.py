# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Total-scattering (PDF) peak profile classes."""

from easydiffraction.core.metadata import CalculatorSupport
from easydiffraction.core.metadata import Compatibility
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.datablocks.experiment.categories.peak.base import PeakBase
from easydiffraction.datablocks.experiment.categories.peak.factory import PeakFactory
from easydiffraction.datablocks.experiment.categories.peak.total_mixins import TotalBroadeningMixin
from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
from easydiffraction.datablocks.experiment.item.enums import CalculatorEnum
from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum


@PeakFactory.register
class TotalGaussianDampedSinc(
    PeakBase,
    TotalBroadeningMixin,
):
    """Gaussian-damped sinc peak for total scattering (PDF)."""

    type_info = TypeInfo(
        tag='gaussian-damped-sinc',
        description='Gaussian-damped sinc for pair distribution function analysis',
    )
    compatibility = Compatibility(
        scattering_type=frozenset({ScatteringTypeEnum.TOTAL}),
        beam_mode=frozenset({BeamModeEnum.CONSTANT_WAVELENGTH, BeamModeEnum.TIME_OF_FLIGHT}),
    )
    calculator_support = CalculatorSupport(
        calculators=frozenset({CalculatorEnum.PDFFIT}),
    )

    def __init__(self) -> None:
        super().__init__()
