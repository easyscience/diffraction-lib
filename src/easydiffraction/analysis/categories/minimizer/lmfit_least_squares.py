# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Persisted category for the LMFIT least_squares minimizer."""

from __future__ import annotations

from typing import ClassVar

from easydiffraction.analysis.categories.minimizer.factory import MinimizerCategoryFactory
from easydiffraction.analysis.categories.minimizer.lsq_base import LeastSquaresMinimizerBase
from easydiffraction.analysis.minimizers.enums import MinimizerTypeEnum
from easydiffraction.core.metadata import TypeInfo


@MinimizerCategoryFactory.register
class LmfitLeastSquaresMinimizer(LeastSquaresMinimizerBase):
    """Persisted settings for the LMFIT least_squares minimizer."""

    _engine_metadata: ClassVar[dict[str, str]] = {
        'optimizer_name': 'lmfit (least_squares)',
        'method_name': 'least_squares',
    }

    type_info = TypeInfo(
        tag=MinimizerTypeEnum.LMFIT_LEAST_SQUARES,
        description="LMFIT library with SciPy's trust region reflective algorithm",
    )
