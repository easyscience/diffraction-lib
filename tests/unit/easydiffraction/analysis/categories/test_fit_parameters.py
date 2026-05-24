# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for analysis/categories/fit_parameters/."""

from types import SimpleNamespace


def test_fit_parameters_factory_create():
    from easydiffraction.analysis.categories.fit_parameters.default import FitParameters
    from easydiffraction.analysis.categories.fit_parameters.factory import FitParametersFactory

    collection = FitParametersFactory.create('default')

    assert FitParametersFactory.default_tag() == 'default'
    assert isinstance(collection, FitParameters)


def _fit_parameters_with_parent_result_kind(result_kind: str):
    from easydiffraction.analysis.categories.fit_parameters.default import FitParameters

    collection = FitParameters()
    collection.create(
        param_unique_name='cosio.cell.length_a',
        fit_min=-1.0,
        fit_max=1.0,
        start_value=10.3,
        start_uncertainty=None,
    )
    collection._parent = SimpleNamespace(
        fit_result=SimpleNamespace(
            result_kind=SimpleNamespace(value=result_kind),
        ),
    )
    return collection


def test_fit_parameters_cif_omits_posterior_columns_for_deterministic_result():
    from easydiffraction.analysis.enums import FitResultKindEnum

    collection = _fit_parameters_with_parent_result_kind(FitResultKindEnum.DETERMINISTIC.value)

    cif_text = collection.as_cif

    assert '_fit_parameter.start_value' in cif_text
    assert '_fit_parameter.posterior_median' not in cif_text
    assert '_fit_parameter.posterior_effective_sample_size_bulk' not in cif_text


def test_fit_parameters_cif_keeps_posterior_columns_for_bayesian_result():
    from easydiffraction.analysis.enums import FitResultKindEnum
    from easydiffraction.core.posterior import PosteriorParameterSummary

    collection = _fit_parameters_with_parent_result_kind(FitResultKindEnum.BAYESIAN.value)
    collection.set_posterior_summary(
        PosteriorParameterSummary(
            unique_name='cosio.cell.length_a',
            display_name='a',
            best_sample_value=10.1,
            median=10.2,
            standard_deviation=0.3,
            interval_68=(9.9, 10.5),
            interval_95=(9.7, 10.7),
            ess_bulk=80.0,
            r_hat=1.01,
        )
    )

    cif_text = collection.as_cif

    assert '_fit_parameter.posterior_median' in cif_text
    assert '_fit_parameter.posterior_effective_sample_size_bulk' in cif_text
    assert '10.2' in cif_text
