# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for analysis/categories/bayesian_distribution_caches/."""


def test_bayesian_distribution_caches_factory_create():
    from easydiffraction.analysis.categories.bayesian_distribution_caches.default import (
        BayesianDistributionCaches,
    )
    from easydiffraction.analysis.categories.bayesian_distribution_caches.factory import (
        BayesianDistributionCachesFactory,
    )

    caches = BayesianDistributionCachesFactory.create('default')

    assert BayesianDistributionCachesFactory.default_tag() == 'default'
    assert isinstance(caches, BayesianDistributionCaches)
