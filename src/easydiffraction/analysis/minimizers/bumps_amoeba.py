# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Bumps minimizer variant using the Nelder-Mead simplex method."""

from __future__ import annotations

from easydiffraction.analysis.minimizers.bumps import BumpsMinimizer
from easydiffraction.analysis.minimizers.enums import MinimizerTypeEnum
from easydiffraction.analysis.minimizers.factory import MinimizerFactory
from easydiffraction.core.metadata import TypeInfo

DEFAULT_METHOD = 'amoeba'
DEFAULT_MAX_ITERATIONS = 1000


@MinimizerFactory.register
class BumpsAmoebaMinimizer(BumpsMinimizer):
    """Bumps minimizer using the Nelder-Mead simplex method."""

    type_info = TypeInfo(
        tag=MinimizerTypeEnum.BUMPS_AMOEBA,
        description='Bumps library with Nelder-Mead simplex method',
    )

    def __init__(
        self,
        name: str = MinimizerTypeEnum.BUMPS_AMOEBA,
        method: str = DEFAULT_METHOD,
        max_iterations: int = DEFAULT_MAX_ITERATIONS,
    ) -> None:
        """Initialize the BUMPS Nelder-Mead simplex minimizer."""
        super().__init__(
            name=name,
            method=method,
            max_iterations=max_iterations,
        )
