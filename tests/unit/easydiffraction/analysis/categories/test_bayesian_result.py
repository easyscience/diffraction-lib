# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for analysis/categories/bayesian_result/."""


def test_bayesian_result_factory_create():
    from easydiffraction.analysis.categories.bayesian_result.default import BayesianResult
    from easydiffraction.analysis.categories.bayesian_result.factory import BayesianResultFactory

    result = BayesianResultFactory.create('default')

    assert BayesianResultFactory.default_tag() == 'default'
    assert isinstance(result, BayesianResult)
