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
    minimizer._set_objective_name('chi-square')
    minimizer._set_objective_value(1.2)
    minimizer._set_covariance_available(value=True)

    assert minimizer.max_iterations.value == 1000
    assert minimizer.objective_name.value == 'chi-square'

    minimizer._reset_result_descriptors()

    # LSQ result descriptors default to None so a CIF written before
    # any fit emits `?` rather than `''`, `0`, or `False`. See
    # minimizer-category-consolidation_review-8 finding F6.
    assert minimizer.objective_name.value is None
    assert minimizer.objective_value.value is None
    assert minimizer.covariance_available.value is None
    assert minimizer.n_data_points.value is None
    assert minimizer.iterations_performed.value is None


def test_lsq_minimizer_reads_cif_unknown_values_as_defaults():
    from easydiffraction.analysis.categories.minimizer.lmfit_leastsq import (
        LmfitLeastsqMinimizer,
    )

    document = gemmi.cif.read_string(
        """data_minimizer
_minimizer.max_iterations 42
_minimizer.objective_name chi-square
_minimizer.objective_value ?
"""
    )
    minimizer = LmfitLeastsqMinimizer()
    minimizer.from_cif(document.sole_block())

    assert minimizer.max_iterations.value == 42
    assert minimizer.objective_name.value == 'chi-square'
    assert minimizer.objective_value.value is None
