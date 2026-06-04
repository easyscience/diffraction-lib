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


def test_fit_scatter_ranges_share_one_range_and_add_tick_step():
    from easydiffraction.report.fit_plot import fit_scatter_ranges

    fit_data = {
        'x': {'values': [10.0, 90.0]},
        'series': {'meas': {'values': [0.0, 80.0], 'su': [5.0, 5.0]}},
    }

    ranges = fit_scatter_ranges(fit_data)

    # x and y share one range (so the diagonal is a true y=x line), and it
    # unions calc (10..90) with meas +/- su (-5..85), padded both ends.
    assert ranges['x_min'] == ranges['y_min'] == ranges['diag_min']
    assert ranges['x_max'] == ranges['y_max'] == ranges['diag_max']
    assert ranges['x_min'] < -5.0
    assert ranges['x_max'] > 90.0
    assert ranges['tick_step'] > 0.0


def test_fit_plot_axis_styles_expose_shared_diagonal_color():
    from easydiffraction.report.fit_plot import fit_plot_axis_styles

    styles = fit_plot_axis_styles()

    assert styles['diag_rgb'] == '190,199,208'


def test_fit_plot_geometry_keeps_panel_heights_fixed_across_rows():
    from easydiffraction.report.fit_plot import _FIGURE_AXIS_HEIGHT_TO_WIDTH
    from easydiffraction.report.fit_plot import _FIGURE_AXIS_WIDTH_CM
    from easydiffraction.report.fit_plot import fit_plot_geometry

    def fit_data(*, phases: int, residual: bool) -> dict:
        data = {'bragg_tick_sets': ['phase'] * phases}
        data['series'] = {'diff': [0.0]} if residual else {}
        return data

    def stack_height_cm(geometry: dict, row_count: int) -> float:
        return (
            geometry['main_height_cm']
            + geometry['bragg_height_cm']
            + geometry['residual_height_cm']
            + (row_count - 1) * geometry['vertical_sep_cm']
        )

    full = fit_plot_geometry(fit_data(phases=1, residual=True))
    main_bragg = fit_plot_geometry(fit_data(phases=1, residual=False))
    main_resid = fit_plot_geometry(fit_data(phases=0, residual=True))
    main_only = fit_plot_geometry(fit_data(phases=0, residual=False))
    two_phase = fit_plot_geometry(fit_data(phases=2, residual=True))

    # The main panel keeps the same cm height in every layout.
    assert main_bragg['main_height_cm'] == pytest.approx(full['main_height_cm'])
    assert main_resid['main_height_cm'] == pytest.approx(full['main_height_cm'])
    assert main_only['main_height_cm'] == pytest.approx(full['main_height_cm'])
    # The residual panel keeps its height with or without Bragg ticks.
    assert main_resid['residual_height_cm'] == pytest.approx(full['residual_height_cm'])
    # The Bragg panel grows linearly with the phase count.
    assert two_phase['bragg_height_cm'] == pytest.approx(2 * full['bragg_height_cm'])
    # The reference three-row figure keeps its nominal height; reduced
    # layouts are shorter and extra phases make it taller.
    reference_cm = _FIGURE_AXIS_WIDTH_CM * _FIGURE_AXIS_HEIGHT_TO_WIDTH
    assert stack_height_cm(full, 3) == pytest.approx(reference_cm)
    assert stack_height_cm(main_only, 1) < reference_cm
    assert stack_height_cm(two_phase, 3) > reference_cm
