# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for persisted fit-state analysis categories."""

from __future__ import annotations

import gemmi


def test_fit_parameter_collection_is_empty_until_rows_exist():
    from easydiffraction.analysis.categories.fit_parameters.default import FitParameters

    collection = FitParameters()

    assert collection.as_cif == ''


def test_fit_parameter_collection_serializes_expected_tags_and_values():
    from easydiffraction.analysis.categories.fit_parameters.default import FitParameters

    collection = FitParameters()
    collection.create(
        param_unique_name='lbco.cell.length_a',
        fit_min=3.88,
        fit_max=3.90,
        fit_bounds_uncertainty_multiplier=4.0,
        start_value=3.89,
        start_uncertainty=0.01,
    )

    cif_text = collection.as_cif

    assert '_fit_parameter.param_unique_name' in cif_text
    assert '_fit_parameter.fit_bounds_uncertainty_multiplier' in cif_text
    assert 'lbco.cell.length_a' in cif_text


def test_fit_result_serializes_expected_tags_and_enum_value():
    from easydiffraction.analysis.categories.fit_result.default import FitResult

    fit_result = FitResult()
    fit_result._set_result_kind('bayesian')
    fit_result._set_success(value=True)
    fit_result._set_message('Sampler completed')
    fit_result._set_iterations(3000)
    fit_result._set_fitting_time(82.4)
    fit_result._set_reduced_chi_square(1.031)

    cif_text = fit_result.as_cif

    assert '_fit_result.result_kind bayesian' in cif_text
    assert '_fit_result.iterations 3000' in cif_text
    assert '_fit_result.reduced_chi_square' in cif_text


def test_fit_parameter_correlations_normalize_pair_order_and_replace_duplicate_ids():
    from easydiffraction.analysis.categories.fit_parameter_correlations.default import (
        FitParameterCorrelations,
    )

    correlations = FitParameterCorrelations()
    correlations.create(
        source_kind='posterior',
        param_unique_name_i='z.param',
        param_unique_name_j='a.param',
        correlation=0.87,
        id='1',
    )
    correlations.create(
        source_kind='posterior',
        param_unique_name_i='b.param',
        param_unique_name_j='c.param',
        correlation=0.55,
        id='1',
    )

    assert len(correlations) == 1
    assert correlations['1'].param_unique_name_i.value == 'b.param'
    assert correlations['1'].param_unique_name_j.value == 'c.param'


def test_fit_parameter_correlations_rebuild_index_from_cif():
    from easydiffraction.analysis.categories.fit_parameter_correlations.default import (
        FitParameterCorrelations,
    )

    cif_text = """data_fit_state
loop_
_fit_parameter_correlation.id
_fit_parameter_correlation.source_kind
_fit_parameter_correlation.param_unique_name_i
_fit_parameter_correlation.param_unique_name_j
_fit_parameter_correlation.correlation
2 posterior hrpt.scale lbco.cell.length_a 0.42
"""
    document = gemmi.cif.read_string(cif_text)

    correlations = FitParameterCorrelations()
    correlations.from_cif(document.sole_block())

    assert correlations.names == ['2']
    assert correlations['2'].correlation.value == 0.42


def test_bayesian_cache_manifest_collections_serialize_expected_keys():
    from easydiffraction.analysis.categories.bayesian_distribution_caches.default import (
        BayesianDistributionCaches,
    )
    from easydiffraction.analysis.categories.bayesian_pair_caches.default import (
        BayesianPairCachePaths,
        BayesianPairCaches,
    )
    from easydiffraction.analysis.categories.bayesian_predictive_datasets.default import (
        BayesianPredictiveDatasetPaths,
        BayesianPredictiveDatasets,
    )

    distributions = BayesianDistributionCaches()
    distributions.create(
        param_unique_name='lbco.cell.length_a',
        x_path='/posterior/distribution/0/x',
        density_path='/posterior/distribution/0/density',
        n_grid=256,
        n_draws_cached=48000,
    )
    pairs = BayesianPairCaches()
    pairs.create(
        parameter_names=('z.param', 'a.param'),
        paths=BayesianPairCachePaths(
            x_path='/posterior/pairs/0/x',
            y_path='/posterior/pairs/0/y',
            density_path='/posterior/pairs/0/density',
            contour_level_path='/posterior/pairs/0/contour_levels',
        ),
        grid_shape=(64, 64),
        n_draws_cached=4000,
        id='7',
    )
    predictive = BayesianPredictiveDatasets()
    predictive.create(
        experiment_name='hrpt',
        x_axis_name='two_theta',
        paths=BayesianPredictiveDatasetPaths(
            x_path='/predictive/hrpt/x',
            best_sample_prediction_path='/predictive/hrpt/best_sample_prediction',
            lower_95_path='/predictive/hrpt/lower_95',
            upper_95_path='/predictive/hrpt/upper_95',
        ),
        n_x=2500,
        n_draws_cached=0,
    )

    assert '_bayesian_distribution_cache.param_unique_name' in distributions.as_cif
    assert pairs['7'].param_unique_name_x.value == 'a.param'
    assert pairs['7'].param_unique_name_y.value == 'z.param'
    assert '_bayesian_predictive_dataset.experiment_name' in predictive.as_cif


def test_bayesian_sampler_and_convergence_use_integer_fields_in_cif():
    from easydiffraction.analysis.categories.bayesian_convergence.default import (
        BayesianConvergence,
    )
    from easydiffraction.analysis.categories.bayesian_sampler.default import BayesianSampler

    sampler = BayesianSampler()
    sampler._set_steps(100)
    sampler._set_burn(20)
    sampler._set_parallel(0)
    sampler._set_random_seed(123)

    convergence = BayesianConvergence()
    convergence._set_n_draws(80)
    convergence._set_n_chains(4)
    convergence._set_n_parameters(3)

    assert '_bayesian_sampler.steps 100' in sampler.as_cif
    assert '_bayesian_sampler.parallel 0' in sampler.as_cif
    assert '_bayesian_convergence.n_draws 80' in convergence.as_cif


def test_bayesian_parameter_posteriors_preserve_row_order_from_cif():
    from easydiffraction.analysis.categories.bayesian_parameter_posteriors.default import (
        BayesianParameterPosteriors,
    )

    cif_text = """data_fit_state
loop_
_bayesian_parameter_posterior.unique_name
_bayesian_parameter_posterior.display_name
_bayesian_parameter_posterior.best_sample_value
_bayesian_parameter_posterior.median
_bayesian_parameter_posterior.uncertainty
_bayesian_parameter_posterior.interval_68_lower
_bayesian_parameter_posterior.interval_68_upper
_bayesian_parameter_posterior.interval_95_lower
_bayesian_parameter_posterior.interval_95_upper
_bayesian_parameter_posterior.ess_bulk
_bayesian_parameter_posterior.r_hat
second.param second 2.0 2.1 0.2 1.9 2.3 1.8 2.4 20 1.01
first.param first 1.0 1.1 0.1 0.9 1.3 0.8 1.4 10 1.00
"""
    document = gemmi.cif.read_string(cif_text)

    posteriors = BayesianParameterPosteriors()
    posteriors.from_cif(document.sole_block())

    assert [row.unique_name.value for row in posteriors] == ['second.param', 'first.param']
