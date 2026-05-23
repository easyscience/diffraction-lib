# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Persisted category for the LMFIT least_squares minimizer."""

from __future__ import annotations

from easydiffraction.analysis.categories.minimizer.factory import MinimizerCategoryFactory
from easydiffraction.analysis.categories.minimizer.lsq_base import LeastSquaresMinimizerBase
from easydiffraction.analysis.minimizers.enums import MinimizerTypeEnum
from easydiffraction.core.metadata import TypeInfo


@MinimizerCategoryFactory.register
class LmfitLeastSquaresMinimizer(LeastSquaresMinimizerBase):
    """Persisted settings for the LMFIT least_squares minimizer."""

    type_info = TypeInfo(
        tag=MinimizerTypeEnum.LMFIT_LEAST_SQUARES,
        description="LMFIT library with SciPy's trust region reflective algorithm",
    )
