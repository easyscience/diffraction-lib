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


def test_plot_backgrounds_opaque_and_paper_transparent():
    import easydiffraction.display.theme as theme

    # Inside the axes rectangle is opaque; the figure paper stays
    # transparent so charts blend into the host page.
    assert theme.LIGHT_BACKGROUND_COLOR == '#ffffff'
    assert theme.DARK_BACKGROUND_COLOR == '#212121'
    assert theme.PAPER_BACKGROUND_COLOR == 'rgba(0, 0, 0, 0)'


def test_hex_to_rgb_expands_short_and_full_forms():
    from easydiffraction.display.theme import hex_to_rgb

    assert hex_to_rgb('#ffffff') == (255, 255, 255)
    assert hex_to_rgb('#111111') == (17, 17, 17)
    assert hex_to_rgb('#e6e8ee') == (230, 232, 238)
    assert hex_to_rgb('#fff') == (255, 255, 255)
    assert hex_to_rgb('#111') == (17, 17, 17)
