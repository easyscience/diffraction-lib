# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Shared visual constants for generated reports."""

from __future__ import annotations

REPORT_AXIS_RGB = (190, 199, 208)
REPORT_TABLE_INNER_RGB = (217, 223, 228)
REPORT_CHART_GRID_RGB = (235, 240, 248)
REPORT_ROW_RGB = (235, 240, 248)
REPORT_LINK_RGB = (36, 90, 155)  # mirrors --link (#245a9b) in html/style.css
REPORT_SUBTITLE = 'EasyDiffraction Report'
REPORT_HTML_FONT_FAMILY = '"PT Sans", "Trebuchet MS", "Segoe UI", sans-serif'
REPORT_TEX_FONT_FAMILY = 'Nunito'
REPORT_TEX_MATH_FONT_FAMILY = 'Fira Math'


def report_style_context() -> dict[str, object]:
    """Return shared visual constants for report templates."""
    return {
        'axis_hex': _rgb_hex(REPORT_AXIS_RGB),
        'axis_rgb': _rgb_channels(REPORT_AXIS_RGB),
        'grid_hex': _rgb_hex(REPORT_TABLE_INNER_RGB),
        'grid_rgb': _rgb_channels(REPORT_TABLE_INNER_RGB),
        'chart_grid_hex': _rgb_hex(REPORT_CHART_GRID_RGB),
        'chart_grid_rgb': _rgb_channels(REPORT_CHART_GRID_RGB),
        'row_hex': _rgb_hex(REPORT_ROW_RGB),
        'row_rgb': _rgb_channels(REPORT_ROW_RGB),
        'link_hex': _rgb_hex(REPORT_LINK_RGB),
        'link_rgb': _rgb_channels(REPORT_LINK_RGB),
        'html_font_family': REPORT_HTML_FONT_FAMILY,
        'tex_font_family': REPORT_TEX_FONT_FAMILY,
        'tex_math_font_family': REPORT_TEX_MATH_FONT_FAMILY,
        'subtitle': REPORT_SUBTITLE,
    }


def _rgb_hex(rgb: tuple[int, int, int]) -> str:
    """Return CSS hex notation for an RGB triple."""
    return f'#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}'


def _rgb_channels(rgb: tuple[int, int, int]) -> str:
    """Return comma-separated channels for TeX RGB definitions."""
    return ','.join(str(channel) for channel in rgb)
