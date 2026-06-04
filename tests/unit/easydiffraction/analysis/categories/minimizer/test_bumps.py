# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for the default BUMPS minimizer category."""

from __future__ import annotations


def test_bumps_minimizer_registers_expected_tag():
    from easydiffraction.analysis.categories.minimizer.bumps import BumpsMinimizer
    from easydiffraction.analysis.categories.minimizer.lsq_base import (
        LeastSquaresMinimizerBase,
    )
    from easydiffraction.analysis.minimizers.enums import MinimizerTypeEnum

    assert issubclass(BumpsMinimizer, LeastSquaresMinimizerBase)
    assert BumpsMinimizer.type_info.tag == MinimizerTypeEnum.BUMPS
