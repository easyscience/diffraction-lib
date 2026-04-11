# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Bumps minimizer variant using the differential evolution method."""

from __future__ import annotations

from easydiffraction.analysis.minimizers.bumps import BumpsMinimizer
from easydiffraction.analysis.minimizers.enums import MinimizerTypeEnum
from easydiffraction.analysis.minimizers.factory import MinimizerFactory
from easydiffraction.core.metadata import TypeInfo

DEFAULT_METHOD = 'de'
DEFAULT_MAX_ITERATIONS = 1000


@MinimizerFactory.register
class BumpsDEMinimizer(BumpsMinimizer):
    """Bumps minimizer using the differential evolution method."""

    type_info = TypeInfo(
        tag=MinimizerTypeEnum.BUMPS_DE,
        description='Bumps library with differential evolution method',
    )

    def __init__(
        self,
        name: str = MinimizerTypeEnum.BUMPS_DE,
        method: str = DEFAULT_METHOD,
        max_iterations: int = DEFAULT_MAX_ITERATIONS,
    ) -> None:
        super().__init__(
            name=name,
            method=method,
            max_iterations=max_iterations,
        )
