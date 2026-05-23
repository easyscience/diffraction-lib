# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Persisted category for the BUMPS lm minimizer."""

from __future__ import annotations

from easydiffraction.analysis.categories.minimizer.factory import MinimizerCategoryFactory
from easydiffraction.analysis.categories.minimizer.lsq_base import (
    LeastSquaresMinimizerBase,
)
from easydiffraction.analysis.minimizers.enums import MinimizerTypeEnum
from easydiffraction.core.metadata import TypeInfo

DEFAULT_MAX_ITERATIONS = 1000
DEFAULT_CONVERGENCE_TOLERANCE = 1.0e-6


@MinimizerCategoryFactory.register
class BumpsLmMinimizer(LeastSquaresMinimizerBase):
    """Persisted settings for the BUMPS lm minimizer."""

    type_info = TypeInfo(
        tag=MinimizerTypeEnum.BUMPS_LM,
        description='BUMPS library with Levenberg-Marquardt method',
    )

    def __init__(self) -> None:
        super().__init__()
        self._max_iterations = self._max_iterations_descriptor(DEFAULT_MAX_ITERATIONS)
        self._convergence_tolerance = self._convergence_tolerance_descriptor(
            DEFAULT_CONVERGENCE_TOLERANCE
        )
        self._random_seed = self._random_seed_descriptor()
