# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for analysis/categories/bayesian_sampler/."""


def test_bayesian_sampler_factory_create():
    from easydiffraction.analysis.categories.bayesian_sampler.default import BayesianSampler
    from easydiffraction.analysis.categories.bayesian_sampler.factory import BayesianSamplerFactory

    sampler = BayesianSamplerFactory.create('default')

    assert BayesianSamplerFactory.default_tag() == 'default'
    assert isinstance(sampler, BayesianSampler)
