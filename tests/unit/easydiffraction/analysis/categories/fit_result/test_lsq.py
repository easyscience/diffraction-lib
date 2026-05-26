# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for least-squares fit-result metadata."""

from __future__ import annotations

import gemmi


def test_least_squares_fit_result_defaults_unknown_outputs_to_none():
    from easydiffraction.analysis.categories.fit_result.lsq import (
        LeastSquaresFitResult,
    )

    fit_result = LeastSquaresFitResult()

    assert fit_result.objective_name.value is None
    assert fit_result.objective_value.value is None
    assert fit_result.n_data_points.value is None
    assert fit_result.n_parameters.value is None
    assert fit_result.n_free_parameters.value is None
    assert fit_result.degrees_of_freedom.value is None
    assert fit_result.covariance_available.value is None
    assert fit_result.correlation_available.value is None
    assert fit_result.exit_reason.value is None


def test_least_squares_fit_result_round_trips_cif_outputs():
    from easydiffraction.analysis.categories.fit_result.lsq import (
        LeastSquaresFitResult,
    )

    fit_result = LeastSquaresFitResult()
    fit_result._set_objective_name('chi-square')
    fit_result._set_objective_value(1.25)
    fit_result._set_n_data_points(120)
    fit_result._set_n_parameters(4)
    fit_result._set_n_free_parameters(3)
    fit_result._set_degrees_of_freedom(117)
    fit_result._set_covariance_available(value=True)
    fit_result._set_correlation_available(value=False)
    fit_result._set_exit_reason('converged')

    restored = LeastSquaresFitResult()
    restored.from_cif(gemmi.cif.read_string(f'data_fit_result\n{fit_result.as_cif}').sole_block())

    assert restored.objective_name.value == 'chi-square'
    assert restored.objective_value.value == 1.25
    assert restored.n_data_points.value == 120
    assert restored.n_parameters.value == 4
    assert restored.n_free_parameters.value == 3
    assert restored.degrees_of_freedom.value == 117
    assert restored.covariance_available.value is True
    assert restored.correlation_available.value is False
    assert restored.exit_reason.value == 'converged'


def test_least_squares_fit_result_round_trips_reflection_outputs():
    from easydiffraction.analysis.categories.fit_result.lsq import (
        LeastSquaresFitResult,
    )

    fit_result = LeastSquaresFitResult()
    fit_result._set_r_factor_all(0.12)
    fit_result._set_wr_factor_all(0.13)
    fit_result._set_r_factor_gt(0.08)
    fit_result._set_wr_factor_gt(0.09)
    fit_result._set_threshold_expression('I > 3u(I)')
    fit_result._set_number_reflns_total(42)
    fit_result._set_number_reflns_gt(31)

    restored = LeastSquaresFitResult()
    restored.from_cif(gemmi.cif.read_string(f'data_fit_result\n{fit_result.as_cif}').sole_block())

    assert restored.r_factor_all.value == 0.12
    assert restored.wr_factor_all.value == 0.13
    assert restored.r_factor_gt.value == 0.08
    assert restored.wr_factor_gt.value == 0.09
    assert restored.threshold_expression.value == 'I > 3u(I)'
    assert restored.number_reflns_total.value == 42
    assert restored.number_reflns_gt.value == 31


def test_least_squares_fit_result_round_trips_powder_outputs():
    from easydiffraction.analysis.categories.fit_result.lsq import (
        LeastSquaresFitResult,
    )

    fit_result = LeastSquaresFitResult()
    fit_result._set_prof_r_factor(0.21)
    fit_result._set_prof_wr_factor(0.22)
    fit_result._set_prof_wr_expected(0.23)
    fit_result._set_profile_function('pseudo-Voigt')
    fit_result._set_background_function('Chebyshev')
    fit_result._set_number_restraints(2)
    fit_result._set_number_constraints(3)

    restored = LeastSquaresFitResult()
    restored.from_cif(gemmi.cif.read_string(f'data_fit_result\n{fit_result.as_cif}').sole_block())

    assert restored.prof_r_factor.value == 0.21
    assert restored.prof_wr_factor.value == 0.22
    assert restored.prof_wr_expected.value == 0.23
    assert restored.profile_function.value == 'pseudo-Voigt'
    assert restored.background_function.value == 'Chebyshev'
    assert restored.number_restraints.value == 2
    assert restored.number_constraints.value == 3


def test_least_squares_fit_result_serializes_only_active_families():
    from easydiffraction.analysis.categories.fit_result.lsq import (
        LeastSquaresFitResult,
    )

    fit_result = LeastSquaresFitResult()
    fit_result._set_number_restraints(0)
    fit_result._set_number_constraints(0)
    fit_result._set_shift_over_su_max(20.0)
    fit_result._set_shift_over_su_mean(4.0)

    cif_text = fit_result.as_cif

    assert '_fit_result.prof_R_factor' not in cif_text
    assert '_fit_result.R_factor_all' not in cif_text
    assert '_fit_result.number_restraints' not in cif_text
    assert '_fit_result.number_constraints' not in cif_text
    assert '_fit_result.shift_over_su_max' not in cif_text
    assert '_fit_result.shift_over_su_mean' not in cif_text

    fit_result._set_r_factor_all(0.12)
    fit_result._set_number_constraints(1)
    cif_text = fit_result.as_cif

    assert '_fit_result.R_factor_all 0.12' in cif_text
    assert '_fit_result.number_constraints 1' in cif_text
    assert '_fit_result.prof_R_factor' not in cif_text

    fit_result._set_prof_r_factor(0.21)
    cif_text = fit_result.as_cif

    assert '_fit_result.prof_R_factor 0.21' in cif_text


def test_least_squares_fit_result_omits_duplicate_exit_reason():
    from easydiffraction.analysis.categories.fit_result.lsq import (
        LeastSquaresFitResult,
    )

    fit_result = LeastSquaresFitResult()
    fit_result._set_message('Fit succeeded.')
    fit_result._set_exit_reason('Fit succeeded.')

    cif_text = fit_result.as_cif

    assert '_fit_result.message "Fit succeeded."' in cif_text
    assert '_fit_result.exit_reason' not in cif_text


def test_least_squares_fit_result_keeps_distinct_exit_reason():
    from easydiffraction.analysis.categories.fit_result.lsq import (
        LeastSquaresFitResult,
    )

    fit_result = LeastSquaresFitResult()
    fit_result._set_message('Fit failed.')
    fit_result._set_exit_reason('maximum number of evaluations reached')

    cif_text = fit_result.as_cif

    assert '_fit_result.message "Fit failed."' in cif_text
    assert '_fit_result.exit_reason "maximum number of evaluations reached"' in cif_text
