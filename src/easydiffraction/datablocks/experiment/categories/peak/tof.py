# SPDX-FileCopyrightText: 2021-2026 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Time-of-flight peak profile classes."""

from easydiffraction.core.metadata import CalculatorSupport
from easydiffraction.core.metadata import Compatibility
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.datablocks.experiment.categories.peak.base import PeakBase
from easydiffraction.datablocks.experiment.categories.peak.factory import PeakFactory
from easydiffraction.datablocks.experiment.categories.peak.tof_mixins import (
    IkedaCarpenterAsymmetryMixin,
)
from easydiffraction.datablocks.experiment.categories.peak.tof_mixins import TofBroadeningMixin
from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
from easydiffraction.datablocks.experiment.item.enums import CalculatorEnum
from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum


@PeakFactory.register
class TofPseudoVoigt(
    PeakBase,
    TofBroadeningMixin,
):
    """Time-of-flight pseudo-Voigt peak shape."""

    type_info = TypeInfo(tag='tof-pseudo-voigt', description='TOF pseudo-Voigt profile')
    compatibility = Compatibility(
        scattering_type=frozenset({ScatteringTypeEnum.BRAGG}),
        beam_mode=frozenset({BeamModeEnum.TIME_OF_FLIGHT}),
    )
    calculator_support = CalculatorSupport(
        calculators=frozenset({CalculatorEnum.CRYSPY, CalculatorEnum.CRYSFML}),
    )

    def __init__(self) -> None:
        super().__init__()


@PeakFactory.register
class TofPseudoVoigtIkedaCarpenter(
    PeakBase,
    TofBroadeningMixin,
    IkedaCarpenterAsymmetryMixin,
):
    """TOF pseudo-Voigt with Ikeda–Carpenter asymmetry."""

    type_info = TypeInfo(
        tag='tof-pseudo-voigt-ikeda-carpenter',
        description='Pseudo-Voigt with Ikeda-Carpenter asymmetry correction',
    )
    compatibility = Compatibility(
        scattering_type=frozenset({ScatteringTypeEnum.BRAGG}),
        beam_mode=frozenset({BeamModeEnum.TIME_OF_FLIGHT}),
    )
    calculator_support = CalculatorSupport(
        calculators=frozenset({CalculatorEnum.CRYSPY, CalculatorEnum.CRYSFML}),
    )

    def __init__(self) -> None:
        super().__init__()


@PeakFactory.register
class TofPseudoVoigtBackToBack(
    PeakBase,
    TofBroadeningMixin,
    IkedaCarpenterAsymmetryMixin,
):
    """TOF back-to-back pseudo-Voigt with asymmetry."""

    type_info = TypeInfo(
        tag='tof-pseudo-voigt-back-to-back',
        description='TOF back-to-back pseudo-Voigt with asymmetry',
    )
    compatibility = Compatibility(
        scattering_type=frozenset({ScatteringTypeEnum.BRAGG}),
        beam_mode=frozenset({BeamModeEnum.TIME_OF_FLIGHT}),
    )
    calculator_support = CalculatorSupport(
        calculators=frozenset({CalculatorEnum.CRYSPY, CalculatorEnum.CRYSFML}),
    )

    def __init__(self) -> None:
        super().__init__()
