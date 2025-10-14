# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from easydiffraction.experiments.categories.peak.base import PeakBase
from easydiffraction.experiments.categories.peak.total_mixins import TotalBroadeningMixin


class TotalGaussianDampedSinc(
    PeakBase,
    TotalBroadeningMixin,
):
    def __init__(self) -> None:
        super().__init__()
        self._add_pair_distribution_function_broadening()
