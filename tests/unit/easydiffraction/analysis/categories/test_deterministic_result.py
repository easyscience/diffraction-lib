# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for analysis/categories/deterministic_result/."""


def test_deterministic_result_factory_create():
    from easydiffraction.analysis.categories.deterministic_result.default import (
        DeterministicResult,
    )
    from easydiffraction.analysis.categories.deterministic_result.factory import (
        DeterministicResultFactory,
    )

    result = DeterministicResultFactory.create('default')

    assert DeterministicResultFactory.default_tag() == 'default'
    assert isinstance(result, DeterministicResult)
