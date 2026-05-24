# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for the emcee minimizer category."""

from __future__ import annotations


def test_emcee_minimizer_category_defaults_to_serial_parallel_workers():
    from easydiffraction.analysis.categories.minimizer.emcee import (
        DEFAULT_PARALLEL_WORKERS,
    )
    from easydiffraction.analysis.categories.minimizer.emcee import EmceeMinimizer

    minimizer = EmceeMinimizer()

    assert DEFAULT_PARALLEL_WORKERS == 1
    assert minimizer.parallel_workers.value == 1
    assert minimizer._native_kwargs()['parallel_workers'] == 1
