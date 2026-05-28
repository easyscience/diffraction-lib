# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Downsample report plot data while preserving extrema."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

MAX_FIGURE_POINTS = 5000


def downsample_min_max(
    x: Sequence[object],
    y: Sequence[object],
    max_points: int = MAX_FIGURE_POINTS,
) -> tuple[list[object], list[object]]:
    """
    Downsample paired data by keeping each bin's extrema.

    Parameters
    ----------
    x : Sequence[object]
        X-axis values.
    y : Sequence[object]
        Y-axis values used to select each bin's extrema.
    max_points : int, default=MAX_FIGURE_POINTS
        Maximum approximate number of output points.

    Returns
    -------
    tuple[list[object], list[object]]
        Downsampled x and y values in original order.

    Raises
    ------
    ValueError
        If the inputs have different lengths or ``max_points`` is
        smaller than two.
    """
    x_values = list(x)
    y_values = list(y)
    if len(x_values) != len(y_values):
        msg = (
            f"Cannot downsample arrays with different lengths: "
            f"x={len(x_values)}, y={len(y_values)}."
        )
        raise ValueError(msg)
    indices = downsample_min_max_indices(y_values, max_points)
    return (
        [x_values[index] for index in indices],
        [y_values[index] for index in indices],
    )


def downsample_min_max_indices(
    y: Sequence[object],
    max_points: int = MAX_FIGURE_POINTS,
) -> list[int]:
    """
    Return peak-preserving min/max indices for one series.

    Parameters
    ----------
    y : Sequence[object]
        Values whose bin minima and maxima select retained points.
    max_points : int, default=MAX_FIGURE_POINTS
        Maximum approximate number of output points.

    Returns
    -------
    list[int]
        Original indices retained in ascending order.

    Raises
    ------
    ValueError
        If ``max_points`` is smaller than two.
    """
    if max_points < 2:
        msg = 'max_points must be at least 2.'
        raise ValueError(msg)

    values = list(y)
    if len(values) <= max_points:
        return list(range(len(values)))

    numeric = np.asarray(values, dtype=float)
    bin_count = max_points // 2
    edges = np.linspace(0, len(values), num=bin_count + 1, dtype=int)
    indices: list[int] = []
    for start, stop in zip(edges[:-1], edges[1:], strict=True):
        if start == stop:
            continue
        segment = numeric[start:stop]
        bin_indices = {
            start + int(np.argmin(segment)),
            start + int(np.argmax(segment)),
        }
        indices.extend(sorted(bin_indices))
    return indices
