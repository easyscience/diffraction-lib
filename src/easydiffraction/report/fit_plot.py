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
from easydiffraction.display.plotters.plotly import DISPLAY_TICK_FRACTIONS
from easydiffraction.display.plotters.plotly import MAIN_INTENSITY_RANGE_MARGIN_FRACTION
from easydiffraction.display.plotters.plotly import MEASURED_LINE_WIDTH
from easydiffraction.display.plotters.plotly import PLOTLY_HEIGHT_PER_UNIT
from easydiffraction.display.plotters.plotly import RESIDUAL_LINE_WIDTH
from easydiffraction.display.plotting import DEFAULT_RESIDUAL_HEIGHT_FRACTION

_COLOR_PATTERN = re.compile(r'rgb\((\d+),\s*(\d+),\s*(\d+)\)')
_FIGURE_AXIS_WIDTH_CM = 12.0
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
_LEGEND_RANKS = {
    'meas': 10,
    'bkg': 20,
    'calc': 30,
    'diff': 40,
}


def fit_plot_styles() -> dict[str, dict[str, Any]]:
    """Return Plotly-derived series styles for report figures."""
    return {
        key: _fit_plot_style(key, source_key)
        for key, source_key in _STYLE_SOURCE_KEYS.items()
    }


def fit_plot_ranges(fit_data: dict[str, Any]) -> dict[str, float]:
    """Return explicit x and main-intensity y ranges for fit figures."""
    x_values = _numeric_values(fit_data['x']['values'])
    y_series = [
        _numeric_values(fit_data['series']['meas']['values']),
        _numeric_values(fit_data['series']['calc']['values']),
    ]

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
    """Return Plotly-matched pgfplots axis geometry."""
    bragg_tick_sets = fit_data.get('bragg_tick_sets') or []
    has_bragg_ticks = bool(bragg_tick_sets)
    has_residual = _has_residual(fit_data)
    row_count = 1 + int(has_bragg_ticks) + int(has_residual)
    main_pixels, residual_pixels = _non_bragg_row_heights(
        row_count=row_count,
        has_bragg_ticks=has_bragg_ticks,
        has_residual=has_residual,
    )

    row_heights = [main_pixels]
    if has_bragg_ticks:
        row_heights.append(_bragg_row_height_pixels(len(bragg_tick_sets)))
    if has_residual and residual_pixels is not None:
        row_heights.append(residual_pixels)

    height_sum = sum(row_heights)
    scaled_heights = [
        _FIGURE_AXIS_WIDTH_CM * row_height / height_sum
        for row_height in row_heights
    ]
    return {
        'axis_width_cm': _FIGURE_AXIS_WIDTH_CM,
        'main_height_cm': scaled_heights[0],
        'bragg_height_cm': scaled_heights[1] if has_bragg_ticks else 0.0,
        'residual_height_cm': scaled_heights[-1] if has_residual else 0.0,
        'vertical_sep_cm': _vertical_sep_cm(row_count),
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


def _fit_plot_style(key: str, source_key: str) -> dict[str, Any]:
    color = DEFAULT_COLORS[source_key]
    return {
        'name': SERIES_CONFIG[source_key]['name'],
        'mode': SERIES_CONFIG[source_key]['mode'],
        'plotly_color': color,
        'rgb': _rgb_channels(color),
        'color_name': f'ed_{key}',
        'line_width': _LINE_WIDTHS[key],
        'legend_rank': _LEGEND_RANKS[key],
    }


def _residual_limit(*, main_y_min: float, main_y_max: float) -> float:
    main_y_range = max(main_y_max - main_y_min, 0.0)
    residual_limit = 0.5 * main_y_range * DEFAULT_RESIDUAL_HEIGHT_FRACTION
    if residual_limit > 0.0:
        return residual_limit
    return 1.0


def _has_residual(fit_data: dict[str, Any]) -> bool:
    series = fit_data.get('series')
    return isinstance(series, dict) and 'diff' in series


def _non_bragg_row_heights(
    *,
    row_count: int,
    has_bragg_ticks: bool,
    has_residual: bool,
) -> tuple[float, float | None]:
    plot_area_height = _composite_plot_area_height()
    available_row_pixels = plot_area_height * _subplot_available_height_fraction(row_count)
    baseline_bragg_pixels = (
        _bragg_tick_symbol_height_pixels() if has_bragg_ticks else 0.0
    )
    non_bragg_pixels = max(available_row_pixels - baseline_bragg_pixels, 1.0)

    if not has_residual:
        return non_bragg_pixels, None

    main_pixels = non_bragg_pixels / (1.0 + DEFAULT_RESIDUAL_HEIGHT_FRACTION)
    residual_pixels = main_pixels * DEFAULT_RESIDUAL_HEIGHT_FRACTION
    return main_pixels, residual_pixels


def _composite_plot_area_height() -> float:
    full_height = float(DEFAULT_HEIGHT * PLOTLY_HEIGHT_PER_UNIT)
    return max(full_height - COMPOSITE_MARGIN_TOP - COMPOSITE_MARGIN_BOTTOM, 1.0)


def _subplot_available_height_fraction(row_count: int) -> float:
    return 1.0 - COMPOSITE_VERTICAL_SPACING * max(row_count - 1, 0)


def _bragg_tick_symbol_height_pixels() -> float:
    return (
        BRAGG_TICK_MARKER_SIZE * BRAGG_TICK_SYMBOL_HEIGHT_SCALE
        + BRAGG_TICK_MARKER_LINE_WIDTH
    )


def _bragg_row_height_pixels(tick_set_count: int) -> float:
    return float(tick_set_count) * _bragg_tick_symbol_height_pixels()


def _vertical_sep_cm(row_count: int) -> float:
    available_fraction = _subplot_available_height_fraction(row_count)
    if available_fraction <= 0.0:
        return 0.0
    return (
        _FIGURE_AXIS_WIDTH_CM
        * COMPOSITE_VERTICAL_SPACING
        / available_fraction
    )


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
