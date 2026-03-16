# SPDX-FileCopyrightText: 2021-2026 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Total-scattering (PDF) peak profile classes."""

from easydiffraction.datablocks.experiment.categories.peak.base import PeakBase
from easydiffraction.datablocks.experiment.categories.peak.total_mixins import TotalBroadeningMixin


class TotalGaussianDampedSinc(
    PeakBase,
    TotalBroadeningMixin,
):
    """Gaussian-damped sinc peak for total scattering (PDF)."""

    def __init__(self) -> None:
        super().__init__()
