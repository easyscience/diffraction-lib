# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Bumps minimizer variant using the Levenberg-Marquardt method."""

from __future__ import annotations

from easydiffraction.analysis.minimizers.bumps import BumpsMinimizer
from easydiffraction.analysis.minimizers.enums import MinimizerTypeEnum
from easydiffraction.analysis.minimizers.factory import MinimizerFactory
from easydiffraction.core.metadata import TypeInfo

DEFAULT_METHOD = 'lm'
DEFAULT_MAX_ITERATIONS = 1000
DEFAULT_CHI_SQUARE_CHANGE_TOLERANCE = 1e-8
DEFAULT_PARAMETER_CHANGE_TOLERANCE = 1e-8


@MinimizerFactory.register
class BumpsLmMinimizer(BumpsMinimizer):
    """
    Bumps minimizer explicitly using the Levenberg-Marquardt method.
    """

    type_info = TypeInfo(
        tag=MinimizerTypeEnum.BUMPS_LM,
        description='Bumps library with Levenberg-Marquardt method',
    )

    def __init__(
        self,
        name: str = MinimizerTypeEnum.BUMPS_LM,
        method: str = DEFAULT_METHOD,
        max_iterations: int = DEFAULT_MAX_ITERATIONS,
        chi_square_change_tolerance: float = DEFAULT_CHI_SQUARE_CHANGE_TOLERANCE,
        parameter_change_tolerance: float = DEFAULT_PARAMETER_CHANGE_TOLERANCE,
    ) -> None:
        """Initialize the BUMPS Levenberg-Marquardt minimizer."""
        super().__init__(
            name=name,
            method=method,
            max_iterations=max_iterations,
            chi_square_change_tolerance=chi_square_change_tolerance,
            parameter_change_tolerance=parameter_change_tolerance,
        )
