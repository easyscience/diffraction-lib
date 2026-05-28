# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Shared report styling for fit-quality figures."""

from __future__ import annotations

import re
from typing import Any

import numpy as np

from easydiffraction.display.plotters.base import SERIES_CONFIG
from easydiffraction.display.plotters.plotly import BACKGROUND_LINE_WIDTH
from easydiffraction.display.plotters.plotly import BRAGG_TICK_COLORS
from easydiffraction.display.plotters.plotly import CALCULATED_LINE_WIDTH
from easydiffraction.display.plotters.plotly import DEFAULT_COLORS
from easydiffraction.display.plotters.plotly import DISPLAY_TICK_FRACTIONS
from easydiffraction.display.plotters.plotly import MAIN_INTENSITY_RANGE_MARGIN_FRACTION
from easydiffraction.display.plotters.plotly import MEASURED_LINE_WIDTH
from easydiffraction.display.plotters.plotly import RESIDUAL_LINE_WIDTH
from easydiffraction.display.plotting import DEFAULT_RESIDUAL_HEIGHT_FRACTION

_COLOR_PATTERN = re.compile(r'rgb\((\d+),\s*(\d+),\s*(\d+)\)')
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
