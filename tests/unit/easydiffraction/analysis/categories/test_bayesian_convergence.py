# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for analysis/categories/bayesian_convergence/."""


def test_bayesian_convergence_factory_create():
    from easydiffraction.analysis.categories.bayesian_convergence.default import (
        BayesianConvergence,
    )
    from easydiffraction.analysis.categories.bayesian_convergence.factory import (
        BayesianConvergenceFactory,
    )

    convergence = BayesianConvergenceFactory.create('default')

    assert BayesianConvergenceFactory.default_tag() == 'default'
    assert isinstance(convergence, BayesianConvergence)
