# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for the DFO-LS minimizer category."""

from __future__ import annotations


def test_dfols_minimizer_registers_expected_tag():
    from easydiffraction.analysis.categories.minimizer.dfols import DfolsMinimizer
    from easydiffraction.analysis.categories.minimizer.lsq_base import (
        LeastSquaresMinimizerBase,
    )
    from easydiffraction.analysis.minimizers.enums import MinimizerTypeEnum

    assert issubclass(DfolsMinimizer, LeastSquaresMinimizerBase)
    assert DfolsMinimizer.type_info.tag == MinimizerTypeEnum.DFOLS
