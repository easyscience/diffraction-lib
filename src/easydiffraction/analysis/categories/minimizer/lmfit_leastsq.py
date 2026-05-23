# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Persisted category for the LMFIT leastsq minimizer."""

from __future__ import annotations

from easydiffraction.analysis.categories.minimizer.factory import MinimizerCategoryFactory
from easydiffraction.analysis.categories.minimizer.lsq_base import (
    LeastSquaresMinimizerBase,
)
from easydiffraction.analysis.minimizers.enums import MinimizerTypeEnum
from easydiffraction.core.metadata import TypeInfo


@MinimizerCategoryFactory.register
class LmfitLeastsqMinimizer(LeastSquaresMinimizerBase):
    """Persisted settings for the LMFIT leastsq minimizer."""

    type_info = TypeInfo(
        tag=MinimizerTypeEnum.LMFIT_LEASTSQ,
        description='LMFIT library with Levenberg-Marquardt least squares method',
    )
