# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations


def test_display_theme_colors_returns_light_and_dark_constants():
    import easydiffraction.display.theme as theme

    light = theme.display_theme_colors(is_dark_theme=False)
    dark = theme.display_theme_colors(is_dark_theme=True)

    assert light.background == theme.LIGHT_BACKGROUND_COLOR
    assert light.axis_frame == theme.LIGHT_AXIS_FRAME_COLOR
    assert light.inner_tick_grid == theme.LIGHT_INNER_TICK_GRID_COLOR
    assert dark.background == theme.DARK_BACKGROUND_COLOR
    assert dark.axis_frame == theme.DARK_AXIS_FRAME_COLOR
    assert dark.inner_tick_grid == theme.DARK_INNER_TICK_GRID_COLOR


def test_display_theme_colors_for_template_maps_plotly_templates():
    import easydiffraction.display.theme as theme

    assert theme.display_theme_colors_for_template('plotly_white') is theme.LIGHT_THEME_COLORS
    assert theme.display_theme_colors_for_template('plotly_dark') is theme.DARK_THEME_COLORS
    assert theme.display_theme_colors_for_template('custom') is None
