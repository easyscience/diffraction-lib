# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
Time-of-flight peak profile classes.

Jorgensen: back-to-back exponentials ⊗ Gaussian (CrysPy
``peak_shape="Gauss"``). Jorgensen-Von Dreele: back-to-back exponentials
⊗ pseudo-Voigt (CrysPy ``peak_shape="pseudo-Voigt"``).
Double-Jorgensen-Von Dreele: double back-to-back exponentials ⊗
pseudo-Voigt (CrysPy ``peak_shape="type0m"``, Z-Rietveld).
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
    TofDoubleExponentialMixin,
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
class TofPseudoVoigt(
    PeakBase,
    TofGaussianBroadeningMixin,
    TofLorentzianBroadeningMixin,
):
    """Simple non-convoluted pseudo-Voigt TOF profile."""

    type_info = TypeInfo(
        tag='pseudo-voigt',
        description='Non-convoluted pseudo-Voigt profile',
    )
    compatibility = Compatibility(
        scattering_type=frozenset({ScatteringTypeEnum.BRAGG}),
        beam_mode=frozenset({BeamModeEnum.TIME_OF_FLIGHT}),
    )
    calculator_support = CalculatorSupport(
        calculators=frozenset({CalculatorEnum.CRYSPY}),
    )

    def __init__(self) -> None:
        super().__init__()


@PeakFactory.register
class TofJorgensen(
    PeakBase,
    TofGaussianBroadeningMixin,
    TofBackToBackExponentialMixin,
):
    """Jorgensen TOF profile: back-to-back exponentials ⊗ Gaussian."""

    type_info = TypeInfo(
        tag='jorgensen',
        description='Jorgensen profile: back-to-back exponentials ⊗ Gaussian',
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
    """Back-to-back exponentials ⊗ pseudo-Voigt TOF profile."""

    type_info = TypeInfo(
        tag='jorgensen-von-dreele',
        description='Jorgensen-Von Dreele profile: back-to-back exponentials ⊗ pseudo-Voigt',
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
class TofDoubleJorgensenVonDreele(
    PeakBase,
    TofGaussianBroadeningMixin,
    TofLorentzianBroadeningMixin,
    TofDoubleExponentialMixin,
):
    """Double back-to-back exponentials ⊗ pseudo-Voigt TOF profile."""

    type_info = TypeInfo(
        tag='double-jorgensen-von-dreele',
        description=(
            'Double-Jorgensen-Von Dreele profile: double back-to-back exponentials '
            '⊗ pseudo-Voigt (Z-Rietveld type0m)'
        ),
    )
    compatibility = Compatibility(
        scattering_type=frozenset({ScatteringTypeEnum.BRAGG}),
        beam_mode=frozenset({BeamModeEnum.TIME_OF_FLIGHT}),
    )
    calculator_support = CalculatorSupport(
        calculators=frozenset({CalculatorEnum.CRYSPY}),
    )

    def __init__(self) -> None:
        super().__init__()
