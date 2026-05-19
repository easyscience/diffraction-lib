# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for analysis/categories/fit_parameters/."""


def test_fit_parameters_factory_create():
    from easydiffraction.analysis.categories.fit_parameters.default import FitParameters
    from easydiffraction.analysis.categories.fit_parameters.factory import FitParametersFactory

    collection = FitParametersFactory.create('default')

    assert FitParametersFactory.default_tag() == 'default'
    assert isinstance(collection, FitParameters)
