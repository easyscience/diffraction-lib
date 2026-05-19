# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for analysis/categories/bayesian_parameter_posteriors/."""


def test_bayesian_parameter_posteriors_factory_create():
    from easydiffraction.analysis.categories.bayesian_parameter_posteriors.default import (
        BayesianParameterPosteriors,
    )
    from easydiffraction.analysis.categories.bayesian_parameter_posteriors.factory import (
        BayesianParameterPosteriorsFactory,
    )

    posteriors = BayesianParameterPosteriorsFactory.create('default')

    assert BayesianParameterPosteriorsFactory.default_tag() == 'default'
    assert isinstance(posteriors, BayesianParameterPosteriors)
