# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from easydiffraction.experiments.components.peak_profiles.base import PeakBase
from easydiffraction.experiments.components.peak_profiles.cw_mixins import (
    ConstantWavelengthBroadeningMixin,
)
from easydiffraction.experiments.components.peak_profiles.cw_mixins import EmpiricalAsymmetryMixin
from easydiffraction.experiments.components.peak_profiles.cw_mixins import FcjAsymmetryMixin


class ConstantWavelengthPseudoVoigt(
    PeakBase,
    ConstantWavelengthBroadeningMixin,
):
    def __init__(self) -> None:
        super().__init__()
        self._add_constant_wavelength_broadening()


class ConstantWavelengthSplitPseudoVoigt(
    PeakBase,
    ConstantWavelengthBroadeningMixin,
    EmpiricalAsymmetryMixin,
):
    def __init__(self) -> None:
        super().__init__()
        self._add_constant_wavelength_broadening()
        self._add_empirical_asymmetry()


class ConstantWavelengthThompsonCoxHastings(
    PeakBase,
    ConstantWavelengthBroadeningMixin,
    FcjAsymmetryMixin,
):
    def __init__(self) -> None:
        super().__init__()
        self._add_constant_wavelength_broadening()
        self._add_fcj_asymmetry()
