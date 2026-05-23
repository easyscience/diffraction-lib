# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for least-squares minimizer category behavior."""

from __future__ import annotations

import gemmi


def test_lsq_minimizer_defaults_and_result_reset():
    from easydiffraction.analysis.categories.minimizer.lmfit_leastsq import (
        LmfitLeastsqMinimizer,
    )

    minimizer = LmfitLeastsqMinimizer()
    minimizer._set_optimizer_name('lmfit')
    minimizer._set_objective_value(1.2)
    minimizer._set_covariance_available(value=True)

    assert minimizer.max_iterations.value == 1000
    assert minimizer.optimizer_name.value == 'lmfit'

    minimizer._reset_result_descriptors()

    assert minimizer.optimizer_name.value == ''
    assert minimizer.objective_value.value is None
    assert minimizer.covariance_available.value is False


def test_lsq_minimizer_reads_cif_unknown_values_as_defaults():
    from easydiffraction.analysis.categories.minimizer.lmfit_leastsq import (
        LmfitLeastsqMinimizer,
    )

    document = gemmi.cif.read_string(
        """data_minimizer
_minimizer.max_iterations 42
_minimizer.optimizer_name lmfit
_minimizer.objective_value ?
"""
    )
    minimizer = LmfitLeastsqMinimizer()
    minimizer.from_cif(document.sole_block())

    assert minimizer.max_iterations.value == 42
    assert minimizer.optimizer_name.value == 'lmfit'
    assert minimizer.objective_value.value is None
