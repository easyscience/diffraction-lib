# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for shared emcee minimizer defaults."""

from __future__ import annotations


def test_emcee_defaults_match_category_and_engine_imports():
    from easydiffraction.analysis.categories.minimizer import emcee as category_defaults
    from easydiffraction.analysis.minimizers import emcee as engine_defaults
    from easydiffraction.analysis.minimizers import emcee_defaults

    assert category_defaults.DEFAULT_SAMPLING_STEPS == emcee_defaults.DEFAULT_NSTEPS
    assert category_defaults.DEFAULT_BURN_IN_STEPS == emcee_defaults.DEFAULT_NBURN
    assert category_defaults.DEFAULT_POPULATION_SIZE == emcee_defaults.DEFAULT_NWALKERS
    assert category_defaults.DEFAULT_PROPOSAL_MOVES == emcee_defaults.DEFAULT_PROPOSAL_MOVES
    assert engine_defaults.DEFAULT_NSTEPS == emcee_defaults.DEFAULT_NSTEPS
    assert engine_defaults.DEFAULT_NBURN == emcee_defaults.DEFAULT_NBURN
    assert engine_defaults.DEFAULT_NWALKERS == emcee_defaults.DEFAULT_NWALKERS
    assert engine_defaults.DEFAULT_PROPOSAL_MOVES == emcee_defaults.DEFAULT_PROPOSAL_MOVES
