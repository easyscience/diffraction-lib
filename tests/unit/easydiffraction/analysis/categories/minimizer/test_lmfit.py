# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for the default LMFIT minimizer category."""

from __future__ import annotations


def test_lmfit_minimizer_registers_expected_tag():
    from easydiffraction.analysis.categories.minimizer.lmfit import LmfitMinimizer
    from easydiffraction.analysis.categories.minimizer.lsq_base import (
        LeastSquaresMinimizerBase,
    )
    from easydiffraction.analysis.minimizers.enums import MinimizerTypeEnum

    assert issubclass(LmfitMinimizer, LeastSquaresMinimizerBase)
    assert LmfitMinimizer.type_info.tag == MinimizerTypeEnum.LMFIT
