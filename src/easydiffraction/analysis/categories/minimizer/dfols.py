# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Persisted category for the DFO-LS minimizer."""

from __future__ import annotations

from easydiffraction.analysis.categories.minimizer.factory import MinimizerCategoryFactory
from easydiffraction.analysis.categories.minimizer.lsq_base import (
    LeastSquaresMinimizerBase,
)
from easydiffraction.analysis.minimizers.enums import MinimizerTypeEnum
from easydiffraction.core.metadata import TypeInfo


@MinimizerCategoryFactory.register
class DfolsMinimizer(LeastSquaresMinimizerBase):
    """Persisted settings for the DFO-LS minimizer."""

    type_info = TypeInfo(
        tag=MinimizerTypeEnum.DFOLS,
        description='DFO-LS library for derivative-free least-squares optimization',
    )
