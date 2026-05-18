# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for analysis/categories/deterministic_parameter_results/."""


def test_deterministic_parameter_results_factory_create():
    from easydiffraction.analysis.categories.deterministic_parameter_results.default import (
        DeterministicParameterResults,
    )
    from easydiffraction.analysis.categories.deterministic_parameter_results.factory import (
        DeterministicParameterResultsFactory,
    )

    results = DeterministicParameterResultsFactory.create('default')

    assert DeterministicParameterResultsFactory.default_tag() == 'default'
    assert isinstance(results, DeterministicParameterResults)
