# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from easydiffraction.experiments.categories.peak.base import PeakBase
from easydiffraction.experiments.categories.peak.cwl_mixins import CwlBroadeningMixin
from easydiffraction.experiments.categories.peak.cwl_mixins import EmpiricalAsymmetryMixin
from easydiffraction.experiments.categories.peak.cwl_mixins import FcjAsymmetryMixin


class CwlPseudoVoigt(
    PeakBase,
    CwlBroadeningMixin,
):
    def __init__(self) -> None:
        super().__init__()
        self._add_constant_wavelength_broadening()


class CwlSplitPseudoVoigt(
    PeakBase,
    CwlBroadeningMixin,
    EmpiricalAsymmetryMixin,
):
    def __init__(self) -> None:
        super().__init__()
        self._add_constant_wavelength_broadening()
        self._add_empirical_asymmetry()


class CwlThompsonCoxHastings(
    PeakBase,
    CwlBroadeningMixin,
    FcjAsymmetryMixin,
):
    def __init__(self) -> None:
        super().__init__()
        self._add_constant_wavelength_broadening()
        self._add_fcj_asymmetry()
