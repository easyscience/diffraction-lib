# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for shared report fit-plot helpers."""

from __future__ import annotations

import pytest


def test_fit_plot_styles_reuse_plotly_series_conventions():
    from easydiffraction.report.fit_plot import fit_bragg_tick_styles
    from easydiffraction.report.fit_plot import fit_plot_styles

    styles = fit_plot_styles()
    bragg_styles = fit_bragg_tick_styles()

    assert styles['meas']['name'] == 'Measured (Imeas)'
    assert styles['meas']['mode'] == 'lines+markers'
    assert styles['meas']['rgb'] == '31,119,180'
    assert styles['meas']['line_width'] == 2.0
    assert styles['meas']['legend_rank'] == 10
    assert styles['diff']['name'] == 'Residual (Imeas - Icalc)'
    assert bragg_styles[0]['color_name'] == 'ed_bragg_0'
    assert bragg_styles[0]['rgb'] == '255,127,14'


def test_fit_plot_ranges_match_plotly_main_intensity_margin():
    from easydiffraction.report.fit_plot import fit_plot_ranges

    fit_data = {
        'x': {'values': [1.0, 2.0]},
        'series': {
            'meas': {'values': [10.0, 30.0]},
            'calc': {'values': [12.0, 20.0]},
            'diff': {'values': [-2.0, 10.0]},
            'bkg': {'values': [5.0, 15.0]},
        },
    }

    ranges = fit_plot_ranges(fit_data)

    assert ranges['x_min'] == pytest.approx(1.0)
    assert ranges['x_max'] == pytest.approx(2.0)
    assert ranges['y_min'] == pytest.approx(3.75)
    assert ranges['y_max'] == pytest.approx(31.25)
    assert ranges['residual_y_min'] == pytest.approx(-3.4375)
    assert ranges['residual_y_max'] == pytest.approx(3.4375)
