# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for posterior summary value objects."""

from __future__ import annotations


def test_posterior_parameter_summary_stores_statistics_and_diagnostics():
    from easydiffraction.core.posterior import PosteriorParameterSummary

    summary = PosteriorParameterSummary(
        unique_name='lbco.cell.length_a',
        display_name='a',
        best_sample_value=3.89,
        median=3.885,
        standard_deviation=0.004,
        interval_68=(3.881, 3.889),
        interval_95=(3.877, 3.893),
        ess_bulk=120,
        r_hat=1.01,
    )

    assert summary.unique_name == 'lbco.cell.length_a'
    assert summary.interval_68 == (3.881, 3.889)
    assert summary.ess_bulk == 120
    assert summary.r_hat == 1.01
