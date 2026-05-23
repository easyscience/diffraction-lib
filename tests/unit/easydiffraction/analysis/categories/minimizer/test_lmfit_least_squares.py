# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for the LMFIT least_squares minimizer category."""

from __future__ import annotations


def test_lmfit_least_squares_minimizer_registers_expected_tag():
    from easydiffraction.analysis.categories.minimizer.lmfit_least_squares import (
        LmfitLeastSquaresMinimizer,
    )
    from easydiffraction.analysis.categories.minimizer.lsq_base import (
        LeastSquaresMinimizerBase,
    )
    from easydiffraction.analysis.minimizers.enums import MinimizerTypeEnum

    assert issubclass(LmfitLeastSquaresMinimizer, LeastSquaresMinimizerBase)
    assert LmfitLeastSquaresMinimizer.type_info.tag == (
        MinimizerTypeEnum.LMFIT_LEAST_SQUARES
    )
