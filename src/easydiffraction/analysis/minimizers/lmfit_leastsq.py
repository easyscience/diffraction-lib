# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
LMFIT minimizer variant using the Levenberg-Marquardt (leastsq) method.
"""

from __future__ import annotations

from easydiffraction.analysis.minimizers.enums import MinimizerTypeEnum
from easydiffraction.analysis.minimizers.factory import MinimizerFactory
from easydiffraction.analysis.minimizers.lmfit import LmfitMinimizer
from easydiffraction.core.metadata import TypeInfo

DEFAULT_METHOD = 'leastsq'
DEFAULT_MAX_ITERATIONS = 1000


@MinimizerFactory.register
class LmfitLeastsqMinimizer(LmfitMinimizer):
    """
    LMFIT minimizer explicitly using the Levenberg-Marquardt method.
    """

    type_info = TypeInfo(
        tag=MinimizerTypeEnum.LMFIT_LEASTSQ,
        description='LMFIT library with Levenberg-Marquardt least squares method',
    )

    def __init__(
        self,
        name: str = MinimizerTypeEnum.LMFIT_LEASTSQ,
        method: str = DEFAULT_METHOD,
        max_iterations: int = DEFAULT_MAX_ITERATIONS,
    ) -> None:
        """Initialize the lmfit leastsq minimizer."""
        super().__init__(
            name=name,
            method=method,
            max_iterations=max_iterations,
        )
