# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for analysis/categories/fit_parameter_correlations/."""


def test_fit_parameter_correlations_factory_create():
    from easydiffraction.analysis.categories.fit_parameter_correlations.default import (
        FitParameterCorrelations,
    )
    from easydiffraction.analysis.categories.fit_parameter_correlations.factory import (
        FitParameterCorrelationsFactory,
    )

    correlations = FitParameterCorrelationsFactory.create('default')

    assert FitParameterCorrelationsFactory.default_tag() == 'default'
    assert isinstance(correlations, FitParameterCorrelations)
