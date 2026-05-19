# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for analysis/categories/bayesian_pair_caches/."""


def test_bayesian_pair_caches_factory_create():
    from easydiffraction.analysis.categories.bayesian_pair_caches.default import BayesianPairCaches
    from easydiffraction.analysis.categories.bayesian_pair_caches.factory import (
        BayesianPairCachesFactory,
    )

    caches = BayesianPairCachesFactory.create('default')

    assert BayesianPairCachesFactory.default_tag() == 'default'
    assert isinstance(caches, BayesianPairCaches)
