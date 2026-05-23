# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Persisted category for the default LMFIT minimizer."""

from __future__ import annotations

from easydiffraction.analysis.categories.minimizer.factory import MinimizerCategoryFactory
from easydiffraction.analysis.categories.minimizer.lsq_base import (
    LeastSquaresMinimizerBase,
)
from easydiffraction.analysis.minimizers.enums import MinimizerTypeEnum
from easydiffraction.core.metadata import TypeInfo


@MinimizerCategoryFactory.register
class LmfitMinimizer(LeastSquaresMinimizerBase):
    """Persisted settings for the default LMFIT minimizer."""

    type_info = TypeInfo(
        tag=MinimizerTypeEnum.LMFIT,
        description='LMFIT library using the default Levenberg-Marquardt method',
    )
