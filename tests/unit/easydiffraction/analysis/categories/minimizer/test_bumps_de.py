# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for the BUMPS de minimizer category."""

from __future__ import annotations


def test_bumps_de_minimizer_registers_expected_tag():
    from easydiffraction.analysis.categories.minimizer.bumps_de import BumpsDeMinimizer
    from easydiffraction.analysis.categories.minimizer.lsq_base import LeastSquaresMinimizerBase
    from easydiffraction.analysis.minimizers.enums import MinimizerTypeEnum

    assert issubclass(BumpsDeMinimizer, LeastSquaresMinimizerBase)
    assert BumpsDeMinimizer.type_info.tag == MinimizerTypeEnum.BUMPS_DE
