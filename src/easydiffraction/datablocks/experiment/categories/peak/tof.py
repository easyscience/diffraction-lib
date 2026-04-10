# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
Time-of-flight peak profile classes.

Jorgensen: BBE ⊗ Gaussian (CrysPy ``peak_shape="Gauss"``). Jorgensen-Von
Dreele: BBE ⊗ pseudo-Voigt (CrysPy ``peak_shape="pseudo-Voigt"``).
"""

from easydiffraction.core.metadata import CalculatorSupport
from easydiffraction.core.metadata import Compatibility
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.datablocks.experiment.categories.peak.base import PeakBase
from easydiffraction.datablocks.experiment.categories.peak.factory import PeakFactory
from easydiffraction.datablocks.experiment.categories.peak.tof_mixins import (
    TofBackToBackExponentialMixin,
)
from easydiffraction.datablocks.experiment.categories.peak.tof_mixins import (
    TofGaussianBroadeningMixin,
)
from easydiffraction.datablocks.experiment.categories.peak.tof_mixins import (
    TofLorentzianBroadeningMixin,
)
from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
from easydiffraction.datablocks.experiment.item.enums import CalculatorEnum
from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum


@PeakFactory.register
class TofJorgensen(
    PeakBase,
    TofGaussianBroadeningMixin,
    TofBackToBackExponentialMixin,
):
    """Jorgensen TOF profile: back-to-back exponentials ⊗ Gaussian."""

    type_info = TypeInfo(
        tag='jorgensen',
        description='Jorgensen BBE ⊗ Gaussian profile',
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
class TofJorgensenVonDreele(
    PeakBase,
    TofGaussianBroadeningMixin,
    TofLorentzianBroadeningMixin,
    TofBackToBackExponentialMixin,
):
    """Jorgensen-Von Dreele TOF profile: BBE ⊗ pseudo-Voigt."""

    type_info = TypeInfo(
        tag='jorgensen-von-dreele',
        description='Jorgensen-Von Dreele BBE ⊗ pseudo-Voigt profile',
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
