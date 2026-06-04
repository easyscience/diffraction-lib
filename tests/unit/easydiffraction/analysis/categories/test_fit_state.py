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
    from easydiffraction.analysis.categories.fit_result.base import FitResultBase

    fit_result = FitResultBase()
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


def test_fit_parameter_posterior_summary_serializes_expected_tags():
    from easydiffraction.analysis.categories.fit_parameters.default import FitParameters
    from easydiffraction.core.posterior import PosteriorParameterSummary

    collection = FitParameters()
    collection.create(
        param_unique_name='lbco.cell.length_a',
        fit_min=3.88,
        fit_max=3.90,
    )
    collection.set_posterior_summary(
        PosteriorParameterSummary(
            unique_name='lbco.cell.length_a',
            display_name='length_a',
            best_sample_value=3.89,
            median=3.885,
            standard_deviation=0.004,
            interval_68=(3.881, 3.889),
            interval_95=(3.877, 3.893),
            ess_bulk=120,
            r_hat=1.01,
        )
    )

    cif_text = collection.as_cif

    assert '_fit_parameter.posterior_best_sample_value' in cif_text
    assert '_fit_parameter.posterior_effective_sample_size_bulk' in cif_text
    summary = collection['lbco.cell.length_a'].posterior_summary(
        display_name='length_a',
    )
    assert summary is not None
    assert summary.best_sample_value == 3.89
    assert summary.ess_bulk == 120


def test_dream_sampler_settings_and_diagnostics_use_split_cif_fields():
    from easydiffraction.analysis.categories.fit_result.bayesian import (
        BayesianFitResult,
    )
    from easydiffraction.analysis.categories.minimizer.bumps_dream import (
        BumpsDreamMinimizer,
    )

    minimizer = BumpsDreamMinimizer()
    minimizer.sampling_steps = 100
    minimizer.burn_in_steps = 20
    minimizer.parallel_workers = 0
    minimizer.random_seed = 123
    fit_result = BayesianFitResult()
    fit_result._set_gelman_rubin_max(1.01)
    fit_result._set_effective_sample_size_min(80)

    minimizer_cif_text = minimizer.as_cif
    fit_result_cif_text = fit_result.as_cif

    assert '_minimizer.sampling_steps 100' in minimizer_cif_text
    assert '_minimizer.parallel_workers 0' in minimizer_cif_text
    assert '_minimizer.random_seed 123' in minimizer_cif_text
    assert '_fit_result.effective_sample_size_min' in fit_result_cif_text


def test_fit_parameter_posteriors_preserve_row_order_from_cif():
    from easydiffraction.analysis.categories.fit_parameters.default import FitParameters

    cif_text = """data_fit_state
loop_
_fit_parameter.param_unique_name
_fit_parameter.posterior_best_sample_value
_fit_parameter.posterior_median
_fit_parameter.posterior_uncertainty
_fit_parameter.posterior_interval_68_low
_fit_parameter.posterior_interval_68_high
_fit_parameter.posterior_interval_95_low
_fit_parameter.posterior_interval_95_high
_fit_parameter.posterior_effective_sample_size_bulk
_fit_parameter.posterior_gelman_rubin
second.param 2.0 2.1 0.2 1.9 2.3 1.8 2.4 20 1.01
first.param 1.0 1.1 0.1 0.9 1.3 0.8 1.4 10 1.00
"""
    document = gemmi.cif.read_string(cif_text)

    posteriors = FitParameters()
    posteriors.from_cif(document.sole_block())

    assert [row.param_unique_name.value for row in posteriors] == [
        'second.param',
        'first.param',
    ]
