# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for least-squares minimizer category behavior."""

from __future__ import annotations

import gemmi


def test_lsq_minimizer_defaults_to_settings_only():
    from easydiffraction.analysis.categories.minimizer.lmfit_leastsq import LmfitLeastsqMinimizer

    minimizer = LmfitLeastsqMinimizer()

    assert minimizer.max_iterations.value == 1000
    assert minimizer.chi_square_change_tolerance.value == 1e-8
    assert minimizer.parameter_change_tolerance.value == 1e-8
    assert minimizer.gradient_tolerance.value == 0.0
    assert minimizer._setting_descriptor_names == (
        'max_iterations',
        'chi_square_change_tolerance',
        'parameter_change_tolerance',
        'gradient_tolerance',
    )
    assert minimizer._result_descriptor_names == ()


def test_lsq_minimizer_reads_cif_settings():
    from easydiffraction.analysis.categories.minimizer.lmfit_leastsq import LmfitLeastsqMinimizer

    document = gemmi.cif.read_string(
        """data_minimizer
_minimizer.max_iterations 42
_minimizer.chi_square_change_tolerance 0.000000001
_minimizer.parameter_change_tolerance 0.000000002
_minimizer.gradient_tolerance 0.000000003
"""
    )
    minimizer = LmfitLeastsqMinimizer()
    minimizer.from_cif(document.sole_block())

    assert minimizer.max_iterations.value == 42
    assert minimizer.chi_square_change_tolerance.value == 1e-9
    assert minimizer.parameter_change_tolerance.value == 2e-9
    assert minimizer.gradient_tolerance.value == 3e-9
