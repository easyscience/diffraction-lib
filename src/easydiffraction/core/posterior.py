# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Core posterior summary value objects."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class PosteriorParameterSummary:
    r"""
    Posterior summary statistics for one fitted parameter.

    Attributes
    ----------
    unique_name : str
        Unique parameter name used across EasyDiffraction.
    display_name : str
        Human-readable label used in plots and tables.
    best_sample_value : float
        Highest-posterior sampled parameter value.
    median : float
        Posterior median value.
    standard_deviation : float
        Posterior standard deviation.
    interval_68 : tuple[float, float]
        Central 68% interval.
    interval_95 : tuple[float, float]
        Central 95% interval.
    ess_bulk : float | None, default=None
        Bulk effective sample size when available.
    r_hat : float | None, default=None
        Rank-normalized split-$\hat{R}$ when available.
    """

    unique_name: str
    display_name: str
    best_sample_value: float
    median: float
    standard_deviation: float
    interval_68: tuple[float, float]
    interval_95: tuple[float, float]
    ess_bulk: float | None = None
    r_hat: float | None = None
