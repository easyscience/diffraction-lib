# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Constant-wavelength peak profile classes."""

from easydiffraction.core.metadata import CalculatorSupport
from easydiffraction.core.metadata import Compatibility
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.datablocks.experiment.categories.peak.base import PeakBase
from easydiffraction.datablocks.experiment.categories.peak.cwl_mixins import (
    BerarBaldinozziAsymmetryMixin,
)
from easydiffraction.datablocks.experiment.categories.peak.cwl_mixins import CwlBroadeningMixin
from easydiffraction.datablocks.experiment.categories.peak.cwl_mixins import FcjAsymmetryMixin
from easydiffraction.datablocks.experiment.categories.peak.factory import PeakFactory
from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
from easydiffraction.datablocks.experiment.item.enums import CalculatorEnum
from easydiffraction.datablocks.experiment.item.enums import PeakProfileTypeEnum
from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum


@PeakFactory.register
class CwlPseudoVoigt(
    PeakBase,
    CwlBroadeningMixin,
):
    """Constant-wavelength pseudo-Voigt peak shape."""

    type_info = TypeInfo(
        tag=PeakProfileTypeEnum.CWL_PSEUDO_VOIGT.value,
        description=PeakProfileTypeEnum.CWL_PSEUDO_VOIGT.description(),
    )
    compatibility = Compatibility(
        scattering_type=frozenset({ScatteringTypeEnum.BRAGG}),
        beam_mode=frozenset({BeamModeEnum.CONSTANT_WAVELENGTH}),
    )
    calculator_support = CalculatorSupport(
        calculators=frozenset({CalculatorEnum.CRYSPY, CalculatorEnum.CRYSFML}),
    )

    def __init__(self) -> None:
        """Initialize the constant-wavelength pseudo-Voigt peak."""
        super().__init__()


@PeakFactory.register
class CwlPseudoVoigtBerarBaldinozziAsymmetry(
    PeakBase,
    CwlBroadeningMixin,
    BerarBaldinozziAsymmetryMixin,
):
    """Pseudo-Voigt with Berar-Baldinozzi asymmetry for CWL mode."""

    type_info = TypeInfo(
        tag=PeakProfileTypeEnum.CWL_PSEUDO_VOIGT_BERAR_BALDINOZZI_ASYMMETRY.value,
        description=(
            PeakProfileTypeEnum.CWL_PSEUDO_VOIGT_BERAR_BALDINOZZI_ASYMMETRY.description()
        ),
    )
    compatibility = Compatibility(
        scattering_type=frozenset({ScatteringTypeEnum.BRAGG}),
        beam_mode=frozenset({BeamModeEnum.CONSTANT_WAVELENGTH}),
    )
    calculator_support = CalculatorSupport(
        calculators=frozenset({CalculatorEnum.CRYSPY}),
    )

    def __init__(self) -> None:
        """
        Initialize the pseudo-Voigt with Berar-Baldinozzi asymmetry.
        """
        super().__init__()


@PeakFactory.register
class CwlThompsonCoxHastings(
    PeakBase,
    CwlBroadeningMixin,
    FcjAsymmetryMixin,
):
    """Thompson-Cox-Hastings with FCJ asymmetry for CWL mode."""

    type_info = TypeInfo(
        tag=PeakProfileTypeEnum.CWL_THOMPSON_COX_HASTINGS.value,
        description=PeakProfileTypeEnum.CWL_THOMPSON_COX_HASTINGS.description(),
    )
    compatibility = Compatibility(
        scattering_type=frozenset({ScatteringTypeEnum.BRAGG}),
        beam_mode=frozenset({BeamModeEnum.CONSTANT_WAVELENGTH}),
    )
    calculator_support = CalculatorSupport(
        calculators=frozenset({CalculatorEnum.CRYSFML}),
    )

    def __init__(self) -> None:
        """Initialize the Thompson-Cox-Hastings FCJ peak."""
        super().__init__()
