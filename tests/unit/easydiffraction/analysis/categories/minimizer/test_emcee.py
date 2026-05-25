# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for the emcee minimizer category."""

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator


class _ExperimentCollection:
    @property
    def names(self) -> list[str]:
        return []


def _make_project() -> object:
    return SimpleNamespace(
        experiments=_ExperimentCollection(),
        structures=object(),
        info=SimpleNamespace(path=None),
        _varname='proj',
    )


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


def test_emcee_minimizer_category_maps_native_kwargs():
    from easydiffraction.analysis.categories.minimizer.emcee import (
        DEFAULT_BURN_IN_STEPS,
    )
    from easydiffraction.analysis.categories.minimizer.emcee import (
        DEFAULT_INITIALIZATION_METHOD,
    )
    from easydiffraction.analysis.categories.minimizer.emcee import (
        DEFAULT_PARALLEL_WORKERS,
    )
    from easydiffraction.analysis.categories.minimizer.emcee import (
        DEFAULT_POPULATION_SIZE,
    )
    from easydiffraction.analysis.categories.minimizer.emcee import (
        DEFAULT_PROPOSAL_MOVES,
    )
    from easydiffraction.analysis.categories.minimizer.emcee import (
        DEFAULT_SAMPLING_STEPS,
    )
    from easydiffraction.analysis.categories.minimizer.emcee import (
        DEFAULT_THINNING_INTERVAL,
    )
    from easydiffraction.analysis.categories.minimizer.emcee import EmceeMinimizer

    native_kwargs = EmceeMinimizer()._native_kwargs()

    assert native_kwargs == {
        'nsteps': DEFAULT_SAMPLING_STEPS,
        'nburn': DEFAULT_BURN_IN_STEPS,
        'thin': DEFAULT_THINNING_INTERVAL,
        'nwalkers': DEFAULT_POPULATION_SIZE,
        'parallel_workers': DEFAULT_PARALLEL_WORKERS,
        'initialization_method': DEFAULT_INITIALIZATION_METHOD.value,
        'random_seed': None,
        'proposal_moves': DEFAULT_PROPOSAL_MOVES,
    }
    assert 'steps' not in native_kwargs
    assert 'burn' not in native_kwargs
    assert 'pop' not in native_kwargs
    assert 'init' not in native_kwargs


def test_emcee_minimizer_swap_pairs_bayesian_fit_result():
    from easydiffraction.analysis.analysis import Analysis
    from easydiffraction.analysis.categories.fit_result.bayesian import BayesianFitResult

    analysis = Analysis(project=_make_project())

    analysis.minimizer.type = 'emcee'

    assert isinstance(analysis.fit_result, BayesianFitResult)
    assert analysis.fit_result._parent is analysis


def test_emcee_resume_parameter_set_mismatch_raises_before_sampler():
    import pytest

    from easydiffraction.analysis.fitting import Fitter
    from easydiffraction.analysis.fitting import FitterFitOptions

    class Structures:
        def __init__(self) -> None:
            self.free_parameters = [SimpleNamespace(unique_name='current.param')]

        def __iter__(self) -> Iterator[object]:
            return iter([self])

        def _update_categories(self) -> None:
            pass

    analysis = SimpleNamespace(
        fit_parameters=[
            SimpleNamespace(
                param_unique_name=SimpleNamespace(value='saved.param'),
            ),
        ],
    )

    with pytest.raises(ValueError, match='Resume parameter set differs'):
        Fitter('emcee').fit(
            structures=Structures(),
            experiments=[],
            analysis=analysis,
            options=FitterFitOptions(resume=True),
        )
