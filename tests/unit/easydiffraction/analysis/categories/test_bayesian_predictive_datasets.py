# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for analysis/categories/bayesian_predictive_datasets/."""


def test_bayesian_predictive_datasets_factory_create():
    from easydiffraction.analysis.categories.bayesian_predictive_datasets.default import (
        BayesianPredictiveDatasets,
    )
    from easydiffraction.analysis.categories.bayesian_predictive_datasets.factory import (
        BayesianPredictiveDatasetsFactory,
    )

    datasets = BayesianPredictiveDatasetsFactory.create('default')

    assert BayesianPredictiveDatasetsFactory.default_tag() == 'default'
    assert isinstance(datasets, BayesianPredictiveDatasets)
