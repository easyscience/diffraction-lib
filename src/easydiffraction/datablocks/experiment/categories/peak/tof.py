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
from easydiffraction.datablocks.experiment.item.enums import PeakProfileTypeEnum
from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum


@PeakFactory.register
class TofPseudoVoigt(
    PeakBase,
    TofGaussianBroadeningMixin,
    TofLorentzianBroadeningMixin,
):
    """Simple non-convoluted pseudo-Voigt TOF profile."""

    type_info = TypeInfo(
        tag=PeakProfileTypeEnum.TOF_PSEUDO_VOIGT.value,
        description=PeakProfileTypeEnum.TOF_PSEUDO_VOIGT.description(),
    )
    compatibility = Compatibility(
        scattering_type=frozenset({ScatteringTypeEnum.BRAGG}),
        beam_mode=frozenset({BeamModeEnum.TIME_OF_FLIGHT}),
    )
    calculator_support = CalculatorSupport(
        calculators=frozenset({CalculatorEnum.CRYSPY}),
    )

    def __init__(self) -> None:
        """Initialize the non-convoluted pseudo-Voigt TOF peak."""
        super().__init__()


@PeakFactory.register
class TofJorgensen(
    PeakBase,
    TofGaussianBroadeningMixin,
    TofBackToBackExponentialMixin,
):
    """Jorgensen TOF profile: back-to-back exponentials ⊗ Gaussian."""

    type_info = TypeInfo(
        tag=PeakProfileTypeEnum.TOF_JORGENSEN.value,
        description=PeakProfileTypeEnum.TOF_JORGENSEN.description(),
    )
    compatibility = Compatibility(
        scattering_type=frozenset({ScatteringTypeEnum.BRAGG}),
        beam_mode=frozenset({BeamModeEnum.TIME_OF_FLIGHT}),
    )
    calculator_support = CalculatorSupport(
        calculators=frozenset({CalculatorEnum.CRYSPY, CalculatorEnum.CRYSFML}),
    )

    def __init__(self) -> None:
        """Initialize the Jorgensen TOF peak profile."""
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
        tag=PeakProfileTypeEnum.TOF_JORGENSEN_VON_DREELE.value,
        description=PeakProfileTypeEnum.TOF_JORGENSEN_VON_DREELE.description(),
    )
    compatibility = Compatibility(
        scattering_type=frozenset({ScatteringTypeEnum.BRAGG}),
        beam_mode=frozenset({BeamModeEnum.TIME_OF_FLIGHT}),
    )
    calculator_support = CalculatorSupport(
        calculators=frozenset({CalculatorEnum.CRYSPY, CalculatorEnum.CRYSFML}),
    )

    def __init__(self) -> None:
        """Initialize the Jorgensen-Von Dreele TOF peak profile."""
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
        tag=PeakProfileTypeEnum.TOF_DOUBLE_JORGENSEN_VON_DREELE.value,
        description=PeakProfileTypeEnum.TOF_DOUBLE_JORGENSEN_VON_DREELE.description(),
    )
    compatibility = Compatibility(
        scattering_type=frozenset({ScatteringTypeEnum.BRAGG}),
        beam_mode=frozenset({BeamModeEnum.TIME_OF_FLIGHT}),
    )
    calculator_support = CalculatorSupport(
        calculators=frozenset({CalculatorEnum.CRYSPY}),
    )

    def __init__(self) -> None:
        """Initialize the double Jorgensen-Von Dreele TOF peak."""
        super().__init__()
