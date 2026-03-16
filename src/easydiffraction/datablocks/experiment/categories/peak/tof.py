# SPDX-FileCopyrightText: 2021-2026 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Time-of-flight peak profile classes."""

from easydiffraction.datablocks.experiment.categories.peak.base import PeakBase
from easydiffraction.datablocks.experiment.categories.peak.tof_mixins import (
    IkedaCarpenterAsymmetryMixin,
)
from easydiffraction.datablocks.experiment.categories.peak.tof_mixins import TofBroadeningMixin


class TofPseudoVoigt(
    PeakBase,
    TofBroadeningMixin,
):
    """Time-of-flight pseudo-Voigt peak shape."""

    def __init__(self) -> None:
        super().__init__()


class TofPseudoVoigtIkedaCarpenter(
    PeakBase,
    TofBroadeningMixin,
    IkedaCarpenterAsymmetryMixin,
):
    """TOF pseudo-Voigt with Ikeda–Carpenter asymmetry."""

    def __init__(self) -> None:
        super().__init__()


class TofPseudoVoigtBackToBack(
    PeakBase,
    TofBroadeningMixin,
    IkedaCarpenterAsymmetryMixin,
):
    """TOF back-to-back pseudo-Voigt with asymmetry."""

    def __init__(self) -> None:
        super().__init__()
