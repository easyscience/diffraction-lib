# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for analysis/categories/fit_result/."""


def test_fit_result_factory_create():
    from easydiffraction.analysis.categories.fit_result.default import FitResult
    from easydiffraction.analysis.categories.fit_result.factory import FitResultFactory

    fit_result = FitResultFactory.create('default')

    assert FitResultFactory.default_tag() == 'default'
    assert isinstance(fit_result, FitResult)
