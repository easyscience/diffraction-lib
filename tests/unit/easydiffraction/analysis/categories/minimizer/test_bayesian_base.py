# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for Bayesian minimizer category behavior."""

from __future__ import annotations

import gemmi
import pytest


def test_bayesian_minimizer_defaults_and_native_kwargs():
    from easydiffraction.analysis.categories.minimizer.bumps_dream import (
        BumpsDreamMinimizer,
    )

    minimizer = BumpsDreamMinimizer()

    assert minimizer.sampling_steps.value == 3000
    assert minimizer.burn_in_steps.value == 600
    assert minimizer.thinning_interval.value == 1
    assert minimizer.population_size.value == 4
    assert minimizer.parallel_workers.value == 0
    assert minimizer.initialization_method.value == 'latin_hypercube'
    assert minimizer._native_kwargs() == {
        'steps': 3000,
        'burn': 600,
        'thin': 1,
        'pop': 4,
        'parallel': 0,
        'init': 'lhs',
        'random_seed': None,
    }


def test_bayesian_minimizer_rejects_unsupported_initialization_method():
    from easydiffraction.analysis.categories.minimizer.bumps_dream import (
        BumpsDreamMinimizer,
    )

    minimizer = BumpsDreamMinimizer()

    with pytest.raises(ValueError, match='unsupported'):
        minimizer.initialization_method = 'ball'


def test_bayesian_minimizer_keeps_unset_random_seed_in_cif():
    from easydiffraction.analysis.categories.minimizer.bumps_dream import (
        BumpsDreamMinimizer,
    )

    cif_text = BumpsDreamMinimizer().as_cif

    assert '_minimizer.random_seed ?' in cif_text


def test_bayesian_minimizer_keeps_configured_random_seed_in_cif():
    from easydiffraction.analysis.categories.minimizer.bumps_dream import (
        BumpsDreamMinimizer,
    )

    minimizer = BumpsDreamMinimizer()
    minimizer.random_seed = 123

    cif_text = minimizer.as_cif

    assert '_minimizer.random_seed 123' in cif_text


def test_bayesian_minimizer_reads_cif_unknown_values_as_defaults():
    from easydiffraction.analysis.categories.minimizer.bumps_dream import (
        BumpsDreamMinimizer,
    )

    document = gemmi.cif.read_string(
        """data_minimizer
_minimizer.sampling_steps 42
_minimizer.burn_in_steps ?
_minimizer.initialization_method ?
_minimizer.random_seed ?
"""
    )
    minimizer = BumpsDreamMinimizer()
    minimizer.from_cif(document.sole_block())

    assert minimizer.sampling_steps.value == 42
    assert minimizer.burn_in_steps.value == 600
    assert minimizer.initialization_method.value == 'latin_hypercube'
    assert minimizer.random_seed.value is None
