# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for the emcee minimizer category."""

from __future__ import annotations


def test_emcee_minimizer_category_defaults_to_max_parallel_workers():
    from easydiffraction.analysis.categories.minimizer.emcee import (
        DEFAULT_PARALLEL_WORKERS,
    )
    from easydiffraction.analysis.categories.minimizer.emcee import EmceeMinimizer

    minimizer = EmceeMinimizer()

    assert DEFAULT_PARALLEL_WORKERS == 0
    assert minimizer.parallel_workers.value == 0
    assert minimizer._native_kwargs()['parallel_workers'] == 0


def test_emcee_minimizer_category_defaults_to_de_without_thinning():
    from easydiffraction.analysis.categories.minimizer.emcee import (
        DEFAULT_PROPOSAL_MOVES,
    )
    from easydiffraction.analysis.categories.minimizer.emcee import (
        DEFAULT_THINNING_INTERVAL,
    )
    from easydiffraction.analysis.categories.minimizer.emcee import EmceeMinimizer

    minimizer = EmceeMinimizer()

    assert DEFAULT_PROPOSAL_MOVES == 'de'
    assert DEFAULT_THINNING_INTERVAL == 1
    assert minimizer.proposal_moves.value == 'de'
    assert minimizer.thinning_interval.value == 1
    assert minimizer._native_kwargs()['proposal_moves'] == 'de'
    assert minimizer._native_kwargs()['thin'] == 1
