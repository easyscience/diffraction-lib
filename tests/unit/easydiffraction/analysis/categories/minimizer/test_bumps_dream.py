# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for the BUMPS DREAM minimizer category."""

from __future__ import annotations


def test_bumps_dream_minimizer_registers_expected_tag():
    from easydiffraction.analysis.categories.minimizer.bayesian_base import (
        BayesianMinimizerBase,
    )
    from easydiffraction.analysis.categories.minimizer.bumps_dream import (
        BumpsDreamMinimizer,
    )
    from easydiffraction.analysis.minimizers.enums import MinimizerTypeEnum

    assert issubclass(BumpsDreamMinimizer, BayesianMinimizerBase)
    assert BumpsDreamMinimizer.type_info.tag == MinimizerTypeEnum.BUMPS_DREAM
