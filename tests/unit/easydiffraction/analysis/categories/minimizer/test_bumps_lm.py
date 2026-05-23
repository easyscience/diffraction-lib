# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for the BUMPS lm minimizer category."""

from __future__ import annotations


def test_bumps_lm_minimizer_registers_expected_tag():
    from easydiffraction.analysis.categories.minimizer.bumps_lm import BumpsLmMinimizer
    from easydiffraction.analysis.categories.minimizer.lsq_base import (
        LeastSquaresMinimizerBase,
    )
    from easydiffraction.analysis.minimizers.enums import MinimizerTypeEnum

    assert issubclass(BumpsLmMinimizer, LeastSquaresMinimizerBase)
    assert BumpsLmMinimizer.type_info.tag == MinimizerTypeEnum.BUMPS_LM
