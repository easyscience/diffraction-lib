# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from easydiffraction.experiments.category_items.peak import PeakBase
from easydiffraction.experiments.category_items.peak_profiles.pdf_mixins import (
    PairDistributionFunctionBroadeningMixin,
)


class PairDistributionFunctionGaussianDampedSinc(
    PeakBase,
    PairDistributionFunctionBroadeningMixin,
):
    def __init__(self) -> None:
        super().__init__()
        self._add_pair_distribution_function_broadening()
