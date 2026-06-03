# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Shared report styling for fit-quality figures."""

from __future__ import annotations

import re
from typing import Any

import numpy as np

from easydiffraction.display.plotters.base import DEFAULT_HEIGHT
from easydiffraction.display.plotters.base import SERIES_CONFIG
from easydiffraction.display.plotters.plotly import BACKGROUND_LINE_WIDTH
from easydiffraction.display.plotters.plotly import BRAGG_TICK_COLORS
from easydiffraction.display.plotters.plotly import BRAGG_TICK_MARKER_LINE_WIDTH
from easydiffraction.display.plotters.plotly import BRAGG_TICK_MARKER_SIZE
from easydiffraction.display.plotters.plotly import BRAGG_TICK_SYMBOL_HEIGHT_SCALE
from easydiffraction.display.plotters.plotly import CALCULATED_LINE_WIDTH
from easydiffraction.display.plotters.plotly import COMPOSITE_MARGIN_BOTTOM
from easydiffraction.display.plotters.plotly import COMPOSITE_MARGIN_TOP
from easydiffraction.display.plotters.plotly import COMPOSITE_VERTICAL_SPACING
from easydiffraction.display.plotters.plotly import DEFAULT_COLORS
from easydiffraction.display.plotters.plotly import DIAGONAL_LINE_RGB
from easydiffraction.display.plotters.plotly import DISPLAY_TICK_FRACTIONS
from easydiffraction.display.plotters.plotly import MAIN_INTENSITY_RANGE_MARGIN_FRACTION
from easydiffraction.display.plotters.plotly import MEASURED_LINE_WIDTH
from easydiffraction.display.plotters.plotly import PLOTLY_HEIGHT_PER_UNIT
from easydiffraction.display.plotters.plotly import RESIDUAL_LINE_WIDTH
from easydiffraction.display.plotters.plotly import single_crystal_axis_range
from easydiffraction.display.plotters.plotly import single_crystal_tick_step
from easydiffraction.display.plotting import DEFAULT_RESIDUAL_HEIGHT_FRACTION
from easydiffraction.report.style import REPORT_AXIS_RGB
from easydiffraction.report.style import REPORT_CHART_GRID_RGB

_COLOR_PATTERN = re.compile(r'rgb\((\d+),\s*(\d+),\s*(\d+)\)')
_FIGURE_AXIS_WIDTH_CM = 12.0
_FIGURE_AXIS_HEIGHT_TO_WIDTH = 0.70
_PGFPLOTS_MEASURED_MARKER_SIZE_PT = 0.75
_PGFPLOTS_MEASURED_MARKER_LINE_WIDTH_PT = 0.0
_PGFPLOTS_SC_MARKER_SIZE_PT = 2.0
_PGFPLOTS_SC_MARKER_LINE_WIDTH_PT = 0.5
_STYLE_SOURCE_KEYS = {
    'meas': 'meas',
    'bkg': 'bkg',
    'calc': 'calc',
    'diff': 'resid',
}
_LINE_WIDTHS = {
    'meas': MEASURED_LINE_WIDTH,
    'bkg': BACKGROUND_LINE_WIDTH,
    'calc': CALCULATED_LINE_WIDTH,
    'diff': RESIDUAL_LINE_WIDTH,
}
_PGFPLOTS_LINE_WIDTHS_PT = {
    'meas': 0.5,
    'bkg': 0.75,
    'calc': 0.75,
    'diff': 0.5,
}
_LEGEND_RANKS = {
    'meas': 10,
    'bkg': 20,
    'calc': 30,
    'diff': 40,
}


def fit_plot_styles() -> dict[str, dict[str, Any]]:
    """Return Plotly-derived series styles for report figures."""
    return {
        key: _fit_plot_style(key, source_key) for key, source_key in _STYLE_SOURCE_KEYS.items()
    }


def fit_plot_ranges(fit_data: dict[str, Any]) -> dict[str, float]:
    """Return explicit x and main-intensity y ranges for fit figures."""
    x_values = _numeric_values(fit_data['x']['values'])
    y_series = [
        _numeric_values(fit_data['series']['meas']['values']),
        _numeric_values(fit_data['series']['calc']['values']),
    ]
    background = fit_data['series'].get('bkg')
    if background is not None:
        y_series.append(_numeric_values(background['values']))

    x_min, x_max = _data_range([x_values])
    y_min, y_max = _data_range(y_series)
    y_margin = max(y_max - y_min, 0.0) * MAIN_INTENSITY_RANGE_MARGIN_FRACTION
    if y_margin <= 0.0:
        y_margin = 1.0

    main_y_min = y_min - y_margin
    main_y_max = y_max + y_margin
    residual_limit = _residual_limit(main_y_min=main_y_min, main_y_max=main_y_max)
    return {
        'x_min': x_min,
        'x_max': x_max,
        'y_min': main_y_min,
        'y_max': main_y_max,
        'residual_y_min': -residual_limit,
        'residual_y_max': residual_limit,
        'residual_y_tick': _display_tick_limit(residual_limit),
    }


def fit_plot_geometry(fit_data: dict[str, Any]) -> dict[str, float]:
    """
    Return Plotly-matched pgfplots axis geometry.

    Row heights are anchored to the reference three-row layout so the
    main and residual panels keep a fixed centimetre height; the axis
    stack grows or shrinks with the rows shown, matching the interactive
    composite figure.
    """
    bragg_tick_sets = fit_data.get('bragg_tick_sets') or []
    has_bragg_ticks = bool(bragg_tick_sets)
    has_residual = _has_residual(fit_data)
    row_count = 1 + int(has_bragg_ticks) + int(has_residual)
    main_pixels, residual_pixels = _non_bragg_row_heights(has_residual=has_residual)

    row_heights = [main_pixels]
    if has_bragg_ticks:
        row_heights.append(_bragg_row_height_pixels(len(bragg_tick_sets)))
    if has_residual and residual_pixels is not None:
        row_heights.append(residual_pixels)

    cm_per_pixel = _figure_cm_per_pixel()
    row_heights_cm = [row_height * cm_per_pixel for row_height in row_heights]
    plot_area_cm = sum(row_heights_cm) / _subplot_available_height_fraction(row_count)
    return {
        'axis_width_cm': _FIGURE_AXIS_WIDTH_CM,
        'main_height_cm': row_heights_cm[0],
        'bragg_height_cm': row_heights_cm[1] if has_bragg_ticks else 0.0,
        'residual_height_cm': row_heights_cm[-1] if has_residual else 0.0,
        'vertical_sep_cm': _vertical_sep_cm(plot_area_cm),
    }


def fit_bragg_tick_styles() -> list[dict[str, str]]:
    """Return Plotly-derived Bragg tick colors for pgfplots."""
    return [
        {
            'color_name': f'ed_bragg_{idx}',
            'rgb': _rgb_channels(color),
        }
        for idx, color in enumerate(BRAGG_TICK_COLORS)
    ]


def fit_plot_axis_styles() -> dict[str, str]:
    """Return Plotly-derived axis colors for report figures."""
    return {
        'axis_rgb': _style_rgb_channels(REPORT_AXIS_RGB),
        'grid_rgb': _style_rgb_channels(REPORT_CHART_GRID_RGB),
        'diag_rgb': _style_rgb_channels(DIAGONAL_LINE_RGB),
    }


def fit_scatter_geometry() -> dict[str, float]:
    """Return pgfplots geometry for the single-crystal scatter plot."""
    return {
        'axis_width_cm': _FIGURE_AXIS_WIDTH_CM,
        'axis_height_cm': _FIGURE_AXIS_WIDTH_CM * _FIGURE_AXIS_HEIGHT_TO_WIDTH,
    }


def fit_scatter_ranges(fit_data: dict[str, Any]) -> dict[str, float]:
    """
    Return the shared x/y range, tick step, and y=x diagonal span.

    The x and y axes share one range (computed across the calculated
    values and the measured values widened by their uncertainties) so
    the diagonal is a true y=x line and the ticks can match.
    """
    x_values = _numeric_values(fit_data['x']['values'])
    meas = fit_data['series']['meas']
    y_values = _numeric_values(meas['values'])
    su = meas.get('su')
    su_values = _numeric_values(su) if su is not None else None

    axis_min, axis_max = single_crystal_axis_range(x_values, y_values, su_values)
    tick_step = single_crystal_tick_step(axis_min, axis_max)
    return {
        'x_min': axis_min,
        'x_max': axis_max,
        'y_min': axis_min,
        'y_max': axis_max,
        'diag_min': axis_min,
        'diag_max': axis_max,
        'tick_step': tick_step,
    }


def fit_scatter_style() -> dict[str, Any]:
    """Return the marker style for the single-crystal scatter plot."""
    color = DEFAULT_COLORS['meas']
    return {
        'color_name': 'ed_meas',
        'rgb': _rgb_channels(color),
        'marker_size_pt': _PGFPLOTS_SC_MARKER_SIZE_PT,
        'marker_line_width_pt': _PGFPLOTS_SC_MARKER_LINE_WIDTH_PT,
    }


def _fit_plot_style(key: str, source_key: str) -> dict[str, Any]:
    color = DEFAULT_COLORS[source_key]
    style = {
        'name': SERIES_CONFIG[source_key]['name'],
        'mode': SERIES_CONFIG[source_key]['mode'],
        'plotly_color': color,
        'rgb': _rgb_channels(color),
        'color_name': f'ed_{key}',
        'line_width': _LINE_WIDTHS[key],
        'line_width_pt': _PGFPLOTS_LINE_WIDTHS_PT[key],
        'legend_rank': _LEGEND_RANKS[key],
    }
    if key == 'meas':
        style.update({
            'marker_size_pt': _PGFPLOTS_MEASURED_MARKER_SIZE_PT,
            'marker_line_width_pt': _PGFPLOTS_MEASURED_MARKER_LINE_WIDTH_PT,
        })
    return style


def _residual_limit(*, main_y_min: float, main_y_max: float) -> float:
    main_y_range = max(main_y_max - main_y_min, 0.0)
    residual_limit = 0.5 * main_y_range * DEFAULT_RESIDUAL_HEIGHT_FRACTION
    if residual_limit > 0.0:
        return residual_limit
    return 1.0


def _has_residual(fit_data: dict[str, Any]) -> bool:
    series = fit_data.get('series')
    return isinstance(series, dict) and 'diff' in series


def _non_bragg_row_heights(*, has_residual: bool) -> tuple[float, float | None]:
    """
    Return fixed main and residual row heights in pixels.

    Anchored to the reference three-row layout so the rows keep a
    constant height regardless of which rows the figure shows.
    """
    plot_area_height = _composite_plot_area_height()
    available_row_pixels = plot_area_height * _subplot_available_height_fraction(3)
    non_bragg_pixels = max(available_row_pixels - _bragg_tick_symbol_height_pixels(), 1.0)

    main_pixels = non_bragg_pixels / (1.0 + DEFAULT_RESIDUAL_HEIGHT_FRACTION)
    if not has_residual:
        return main_pixels, None

    residual_pixels = main_pixels * DEFAULT_RESIDUAL_HEIGHT_FRACTION
    return main_pixels, residual_pixels


def _figure_cm_per_pixel() -> float:
    """
    Return the fixed cm-per-pixel scale for fit-figure rows.

    Anchored so the reference three-row layout fills the nominal axis
    stack height (axis width times the reference aspect ratio).
    """
    reference_stack_cm = _FIGURE_AXIS_WIDTH_CM * _FIGURE_AXIS_HEIGHT_TO_WIDTH
    return reference_stack_cm / _composite_plot_area_height()


def _composite_plot_area_height() -> float:
    full_height = float(DEFAULT_HEIGHT * PLOTLY_HEIGHT_PER_UNIT)
    return max(full_height - COMPOSITE_MARGIN_TOP - COMPOSITE_MARGIN_BOTTOM, 1.0)


def _subplot_available_height_fraction(row_count: int) -> float:
    return 1.0 - COMPOSITE_VERTICAL_SPACING * max(row_count - 1, 0)


def _bragg_tick_symbol_height_pixels() -> float:
    return BRAGG_TICK_MARKER_SIZE * BRAGG_TICK_SYMBOL_HEIGHT_SCALE + BRAGG_TICK_MARKER_LINE_WIDTH


def _bragg_row_height_pixels(tick_set_count: int) -> float:
    return float(tick_set_count) * _bragg_tick_symbol_height_pixels()


def _vertical_sep_cm(plot_area_cm: float) -> float:
    return plot_area_cm * COMPOSITE_VERTICAL_SPACING


def _display_tick_limit(raw_limit: float) -> float:
    if raw_limit <= 0:
        return 1.0

    exponent = float(np.floor(np.log10(raw_limit)))
    base = 10.0**exponent
    fraction = raw_limit / base

    for nice_fraction in reversed(DISPLAY_TICK_FRACTIONS):
        if fraction >= nice_fraction:
            return nice_fraction * base
    return DISPLAY_TICK_FRACTIONS[0] * base


def _rgb_channels(color: str) -> str:
    match = _COLOR_PATTERN.fullmatch(color)
    if match is None:
        msg = f"Unsupported Plotly RGB color '{color}'."
        raise ValueError(msg)
    return ','.join(match.groups())


def _style_rgb_channels(rgb: tuple[int, int, int]) -> str:
    """Return comma-separated channels for report style RGB colors."""
    return ','.join(str(channel) for channel in rgb)


def _data_range(series_list: list[list[float]]) -> tuple[float, float]:
    values = [value for series in series_list for value in series]
    if not values:
        return 0.0, 1.0
    minimum = float(np.min(values))
    maximum = float(np.max(values))
    if minimum == maximum:
        return minimum - 1.0, maximum + 1.0
    return minimum, maximum


def _numeric_values(values: object) -> list[float]:
    return [float(value) for value in values]
