# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for posterior summaries on fittable parameters."""

from __future__ import annotations


def test_parameter_posterior_summary_is_set_internally():
    from easydiffraction.core.posterior import PosteriorParameterSummary
    from easydiffraction.core.validation import AttributeSpec
    from easydiffraction.core.variable import Parameter
    from easydiffraction.io.cif.handler import CifHandler

    parameter = Parameter(
        name='length_a',
        value_spec=AttributeSpec(default=3.88),
        cif_handler=CifHandler(names=['_cell.length_a']),
    )
    summary = PosteriorParameterSummary(
        unique_name=parameter.unique_name,
        display_name='a',
        best_sample_value=3.89,
        median=3.885,
        standard_deviation=0.004,
        interval_68=(3.881, 3.889),
        interval_95=(3.877, 3.893),
    )

    assert parameter.posterior is None

    parameter._set_posterior(summary)

    assert parameter.posterior is summary

    parameter._set_posterior(None)

    assert parameter.posterior is None
