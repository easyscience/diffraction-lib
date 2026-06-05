# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for minimizer category base helpers."""

from __future__ import annotations


def test_descriptor_values_and_native_kwargs_use_descriptor_values():
    from easydiffraction.analysis.categories.minimizer.lmfit_leastsq import LmfitLeastsqMinimizer

    minimizer = LmfitLeastsqMinimizer()
    minimizer.max_iterations = 25

    assert minimizer._descriptor_values(('max_iterations',)) == {
        'max_iterations': 25,
    }
    assert minimizer._native_kwargs() == {'max_iterations': 25}
