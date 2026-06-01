# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Shared display theme colors for plots and notebook tables."""

from __future__ import annotations

from dataclasses import dataclass

LIGHT_BACKGROUND_COLOR = 'rgba(0, 0, 0, 0)'
DARK_BACKGROUND_COLOR = 'rgba(0, 0, 0, 0)'
LIGHT_FOREGROUND_COLOR = '#222222'
DARK_FOREGROUND_COLOR = '#e6e8ee'
LIGHT_AXIS_FRAME_COLOR = '#e0e0e0'
DARK_AXIS_FRAME_COLOR = '#333'
LIGHT_INNER_TICK_GRID_COLOR = '#f2f2f2'
DARK_INNER_TICK_GRID_COLOR = '#222'
LIGHT_HOVER_BACKGROUND_COLOR = '#ffffff'
DARK_HOVER_BACKGROUND_COLOR = '#212121'
LIGHT_LEGEND_BACKGROUND_COLOR = 'rgba(255, 255, 255, 0.5)'
DARK_LEGEND_BACKGROUND_COLOR = 'rgba(0, 0, 0, 0.5)'
TABLE_AXIS_FRAME_CSS_VAR = '--ed-axis-frame-color'


@dataclass(frozen=True)
class DisplayThemeColors:
    """
    Theme colors shared by interactive display outputs.

    Attributes
    ----------
    background : str
        Plot or output background color.
    foreground : str
        Primary text color.
    axis_frame : str
        Axis rectangle and table border color.
    inner_tick_grid : str
        Inner Plotly tick-grid color.
    hover_background : str
        Plotly hover label background color.
    legend_background : str
        Plotly legend background color.
    """

    background: str
    foreground: str
    axis_frame: str
    inner_tick_grid: str
    hover_background: str
    legend_background: str


LIGHT_THEME_COLORS = DisplayThemeColors(
    background=LIGHT_BACKGROUND_COLOR,
    foreground=LIGHT_FOREGROUND_COLOR,
    axis_frame=LIGHT_AXIS_FRAME_COLOR,
    inner_tick_grid=LIGHT_INNER_TICK_GRID_COLOR,
    hover_background=LIGHT_HOVER_BACKGROUND_COLOR,
    legend_background=LIGHT_LEGEND_BACKGROUND_COLOR,
)
DARK_THEME_COLORS = DisplayThemeColors(
    background=DARK_BACKGROUND_COLOR,
    foreground=DARK_FOREGROUND_COLOR,
    axis_frame=DARK_AXIS_FRAME_COLOR,
    inner_tick_grid=DARK_INNER_TICK_GRID_COLOR,
    hover_background=DARK_HOVER_BACKGROUND_COLOR,
    legend_background=DARK_LEGEND_BACKGROUND_COLOR,
)


def display_theme_colors(*, is_dark_theme: bool) -> DisplayThemeColors:
    """
    Return the display colors for the requested theme.

    Parameters
    ----------
    is_dark_theme : bool
        Whether to return the dark theme colors.

    Returns
    -------
    DisplayThemeColors
        Shared colors for the requested theme.
    """
    if is_dark_theme:
        return DARK_THEME_COLORS
    return LIGHT_THEME_COLORS


def display_theme_colors_for_template(template: str) -> DisplayThemeColors | None:
    """
    Return display colors for a Plotly template name.

    Parameters
    ----------
    template : str
        Plotly template name.

    Returns
    -------
    DisplayThemeColors | None
        Theme colors for known Plotly templates, otherwise ``None``.
    """
    if template == 'plotly_white':
        return LIGHT_THEME_COLORS
    if template == 'plotly_dark':
        return DARK_THEME_COLORS
    return None
