# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""LMFIT minimizer variant using trust region reflective method."""

from __future__ import annotations

from easydiffraction.analysis.minimizers.enums import MinimizerTypeEnum
from easydiffraction.analysis.minimizers.factory import MinimizerFactory
from easydiffraction.analysis.minimizers.lmfit import LmfitMinimizer
from easydiffraction.core.metadata import TypeInfo

DEFAULT_METHOD = 'least_squares'
DEFAULT_MAX_ITERATIONS = 1000


@MinimizerFactory.register
class LmfitLeastSquaresMinimizer(LmfitMinimizer):
    """
    LMFIT minimizer using SciPy's trust region reflective algorithm.
    """

    type_info = TypeInfo(
        tag=MinimizerTypeEnum.LMFIT_LEAST_SQUARES,
        description="LMFIT library with SciPy's trust region reflective algorithm",
    )

    def __init__(
        self,
        name: str = MinimizerTypeEnum.LMFIT_LEAST_SQUARES,
        method: str = DEFAULT_METHOD,
        max_iterations: int = DEFAULT_MAX_ITERATIONS,
    ) -> None:
        super().__init__(
            name=name,
            method=method,
            max_iterations=max_iterations,
        )
