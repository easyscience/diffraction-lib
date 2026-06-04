# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for Bayesian fit-result metadata."""

from __future__ import annotations

import gemmi


def test_bayesian_fit_result_defaults_unknown_outputs_to_none():
    from easydiffraction.analysis.categories.fit_result.bayesian import (
        BayesianFitResult,
    )

    fit_result = BayesianFitResult()

    assert fit_result.point_estimate_name.value is None
    assert fit_result.sampler_completed.value is None
    assert fit_result.credible_interval_inner.value == 0.68
    assert fit_result.credible_interval_outer.value == 0.95
    assert fit_result.resolved_random_seed.value is None
    assert fit_result.acceptance_rate_mean.value is None
    assert fit_result.gelman_rubin_max.value is None
    assert fit_result.effective_sample_size_min.value is None
    assert fit_result.best_log_posterior.value is None


def test_bayesian_fit_result_round_trips_cif_outputs():
    from easydiffraction.analysis.categories.fit_result.bayesian import (
        BayesianFitResult,
    )

    fit_result = BayesianFitResult()
    fit_result._set_point_estimate_name('posterior_median')
    fit_result._set_sampler_completed(value=True)
    fit_result._set_credible_interval_inner(0.5)
    fit_result._set_credible_interval_outer(0.9)
    fit_result._set_resolved_random_seed(12345)
    fit_result._set_acceptance_rate_mean(0.42)
    fit_result._set_gelman_rubin_max(1.01)
    fit_result._set_effective_sample_size_min(80)
    fit_result._set_best_log_posterior(-12.5)

    restored = BayesianFitResult()
    restored.from_cif(gemmi.cif.read_string(f'data_fit_result\n{fit_result.as_cif}').sole_block())

    assert restored.point_estimate_name.value == 'posterior_median'
    assert restored.sampler_completed.value is True
    assert restored.credible_interval_inner.value == 0.5
    assert restored.credible_interval_outer.value == 0.9
    assert restored.resolved_random_seed.value == 12345
    assert restored.acceptance_rate_mean.value == 0.42
    assert restored.gelman_rubin_max.value == 1.01
    assert restored.effective_sample_size_min.value == 80
    assert restored.best_log_posterior.value == -12.5


def test_bayesian_fit_result_omits_optional_unknown_outputs():
    from easydiffraction.analysis.categories.fit_result.bayesian import (
        BayesianFitResult,
    )

    cif_text = BayesianFitResult().as_cif

    assert '_fit_result.acceptance_rate_mean' not in cif_text
    assert '_fit_result.resolved_random_seed' not in cif_text


def test_bayesian_fit_result_omits_redundant_iterations():
    from easydiffraction.analysis.categories.fit_result.bayesian import (
        BayesianFitResult,
    )

    fit_result = BayesianFitResult()
    fit_result._set_iterations(100)

    cif_text = fit_result.as_cif

    assert '_fit_result.iterations' not in cif_text


def test_bayesian_fit_result_keeps_optional_outputs_when_populated():
    from easydiffraction.analysis.categories.fit_result.bayesian import (
        BayesianFitResult,
    )

    fit_result = BayesianFitResult()
    fit_result._set_resolved_random_seed(12345)
    fit_result._set_acceptance_rate_mean(0.42)

    cif_text = fit_result.as_cif

    assert '_fit_result.resolved_random_seed 12345' in cif_text
    assert '_fit_result.acceptance_rate_mean 0.42' in cif_text
