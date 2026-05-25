# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for the emcee minimizer engine."""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest


class _FakeTracker:
    """Progress tracker test double."""

    best_chi2 = 1.23

    def __init__(self) -> None:
        self.updates = []

    def _current_elapsed_time(self) -> float:
        return float(len(self.updates) + 1)

    def track_sampler_progress(self, update: object) -> None:
        self.updates.append(update)


class _FakeSampler:
    """Minimal sampler test double for the emcee sample loop."""

    def __init__(self) -> None:
        self.calls = []

    def sample(
        self,
        initial_state: object,
        *,
        iterations: int,
        skip_initial_state_check: bool,
        progress: bool,
    ) -> object:
        self.calls.append(
            {
                'initial_state': initial_state,
                'iterations': iterations,
                'skip_initial_state_check': skip_initial_state_check,
                'progress': progress,
            }
        )
        for index in range(iterations):
            yield SimpleNamespace(log_prob=np.array([float(index)], dtype=float))


def test_emcee_minimizer_defaults_to_max_parallel_workers():
    from easydiffraction.analysis.minimizers.emcee import DEFAULT_PARALLEL_WORKERS
    from easydiffraction.analysis.minimizers.emcee import EmceeMinimizer

    minimizer = EmceeMinimizer()

    assert DEFAULT_PARALLEL_WORKERS == 0
    assert minimizer.parallel_workers == 0


def test_emcee_minimizer_defaults_to_de_without_thinning():
    from easydiffraction.analysis.minimizers.emcee import DEFAULT_PROPOSAL_MOVES
    from easydiffraction.analysis.minimizers.emcee import DEFAULT_THIN
    from easydiffraction.analysis.minimizers.emcee import EmceeMinimizer

    minimizer = EmceeMinimizer()

    assert DEFAULT_PROPOSAL_MOVES == 'de'
    assert DEFAULT_THIN == 1
    assert minimizer.proposal_moves == 'de'
    assert minimizer.thin == 1


def test_emcee_pool_context_uses_fork_worker_for_unpicklable_objective(monkeypatch):
    from easydiffraction.analysis.minimizers.emcee import EmceeMinimizer
    from easydiffraction.analysis.minimizers.emcee import _emcee_log_prob_worker

    class FakePool:
        def __init__(self) -> None:
            self.closed = False
            self.joined = False

        def close(self) -> None:
            self.closed = True

        def join(self) -> None:
            self.joined = True

    class FakeContext:
        def __init__(self) -> None:
            self.pool = FakePool()
            self.worker_count = None

        def Pool(self, worker_count: int) -> FakePool:  # noqa: N802
            self.worker_count = worker_count
            return self.pool

    fake_context = FakeContext()
    minimizer = EmceeMinimizer()
    minimizer.parallel_workers = 2

    monkeypatch.setattr(
        EmceeMinimizer,
        '_fork_context_available',
        staticmethod(lambda: True),
    )
    monkeypatch.setattr(
        'easydiffraction.analysis.minimizers.emcee.multiprocessing.get_context',
        lambda name: fake_context,
    )

    log_prob = minimizer._build_log_probability(
        parameters=[SimpleNamespace(fit_min=-10.0, fit_max=10.0)],
        parameter_names=['p'],
        objective_function=lambda values: np.array([values['p']], dtype=float),
    )
    pool_context = minimizer._build_pool_context(log_prob)

    assert fake_context.worker_count == 2
    assert pool_context.pool is fake_context.pool
    assert pool_context.log_prob_fn is _emcee_log_prob_worker
    assert pool_context.log_prob_fn(np.array([2.0], dtype=float)) == pytest.approx(-2.0)

    minimizer._close_pool_context(pool_context)

    assert fake_context.pool.closed is True
    assert fake_context.pool.joined is True
    with pytest.raises(RuntimeError, match='has not been initialized'):
        _emcee_log_prob_worker(np.array([2.0], dtype=float))


def test_emcee_pool_context_terminates_on_interrupt_cleanup():
    from easydiffraction.analysis.minimizers.emcee import EmceeMinimizer
    from easydiffraction.analysis.minimizers.emcee import _EmceePoolContext

    class FakePool:
        def __init__(self) -> None:
            self.closed = False
            self.terminated = False
            self.joined = False

        def close(self) -> None:
            self.closed = True

        def terminate(self) -> None:
            self.terminated = True

        def join(self) -> None:
            self.joined = True

    fake_pool = FakePool()
    pool_context = _EmceePoolContext(pool=fake_pool, log_prob_fn=lambda values: 0.0)

    EmceeMinimizer._close_pool_context(pool_context, terminate=True)

    assert fake_pool.terminated is True
    assert fake_pool.closed is False
    assert fake_pool.joined is True


def test_emcee_run_solver_terminates_pool_when_interrupted(monkeypatch, tmp_path):
    import easydiffraction.analysis.minimizers.emcee as emcee_mod
    from easydiffraction.analysis.minimizers.emcee import EmceeMinimizer
    from easydiffraction.analysis.minimizers.emcee import _EmceePoolContext

    class FakeBackend:
        iteration = 0

        def __init__(
            self,
            path: str,
            *,
            name: str,
            read_only: bool,
        ) -> None:
            del path, name, read_only

    class FakePool:
        def __init__(self) -> None:
            self.terminated = False
            self.joined = False

        def terminate(self) -> None:
            self.terminated = True

        def join(self) -> None:
            self.joined = True

    fake_pool = FakePool()
    minimizer = EmceeMinimizer()
    minimizer.tracker = SimpleNamespace(start_sampler_pre_processing=lambda **kwargs: None)

    monkeypatch.setattr(
        emcee_mod.emcee.backends,
        'HDFBackend',
        FakeBackend,
    )
    monkeypatch.setattr(
        minimizer,
        '_resolved_sidecar_path',
        lambda: tmp_path / 'analysis' / 'results.h5',
    )
    monkeypatch.setattr(minimizer, '_validate_walker_count', lambda **kwargs: None)
    monkeypatch.setattr(
        minimizer,
        '_build_log_probability',
        lambda **kwargs: object(),
    )
    monkeypatch.setattr(
        minimizer,
        '_build_pool_context',
        lambda log_prob: _EmceePoolContext(pool=fake_pool, log_prob_fn=lambda values: 0.0),
    )
    monkeypatch.setattr(
        minimizer,
        '_run_sampler',
        lambda **kwargs: (_ for _ in ()).throw(KeyboardInterrupt),
    )

    with pytest.raises(KeyboardInterrupt):
        minimizer._run_solver(
            lambda values: np.array([0.0], dtype=float),
            parameters=[SimpleNamespace(fit_min=-1.0, fit_max=1.0)],
            parameter_names=['p'],
            parameter_display_names=['p'],
            random_seed=1,
            resume=False,
            extra_steps=None,
            starting_values=[0.0],
            starting_uncertainties=[None],
        )

    assert fake_pool.terminated is True
    assert fake_pool.joined is True


def test_emcee_progress_reporter_emits_burn_in_and_sampling_updates():
    from easydiffraction.analysis.minimizers.emcee import _EmceeProgressReporter

    tracker = _FakeTracker()
    reporter = _EmceeProgressReporter(tracker=tracker, total_steps=10, burn_steps=2)
    state = SimpleNamespace(log_prob=np.array([-10.0, -5.0], dtype=float))

    for iteration in range(1, 11):
        reporter.report(iteration=iteration, state=state)

    assert len(tracker.updates) > 2
    assert tracker.updates[0].iteration == 1
    assert tracker.updates[0].phase == 'burn-in'
    assert any(update.phase == 'sampling' for update in tracker.updates)
    assert tracker.updates[-1].iteration == 10
    assert tracker.updates[-1].progress_percent == pytest.approx(100.0)
    assert tracker.updates[-1].log_posterior == pytest.approx(-5.0)
    assert tracker.updates[-1].reduced_chi2 == pytest.approx(1.23)


def test_emcee_progress_reporter_treats_resume_as_sampling_only():
    from easydiffraction.analysis.minimizers.emcee import _EmceeProgressReporter

    tracker = _FakeTracker()
    reporter = _EmceeProgressReporter(tracker=tracker, total_steps=5, burn_steps=0)
    state = SimpleNamespace(log_prob=np.array([-2.0, -1.0], dtype=float))

    for iteration in range(1, 6):
        reporter.report(iteration=iteration, state=state)

    assert tracker.updates
    assert {update.phase for update in tracker.updates} == {'sampling'}


def test_emcee_total_iterations_adds_burn_in_and_initial_generation():
    from easydiffraction.analysis.minimizers.emcee import EmceeMinimizer

    minimizer = EmceeMinimizer()
    minimizer.nsteps = 100
    minimizer.nburn = 20

    assert minimizer._resolved_total_iterations(resume=False, extra_steps=None) == 121
    assert minimizer._resolved_total_iterations(resume=True, extra_steps=50) == 50


def test_emcee_run_sampler_resumes_from_backend_last_sample(monkeypatch):
    import easydiffraction.analysis.minimizers.emcee as emcee_mod
    from easydiffraction.analysis.minimizers.emcee import EmceeMinimizer

    class FakeEnsembleSampler:
        def __init__(self, **kwargs) -> None:
            del kwargs
            self.fake_sampler = _FakeSampler()

        def sample(self, *args, **kwargs):
            return self.fake_sampler.sample(*args, **kwargs)

    backend = SimpleNamespace(
        shape=(4, 2),
        iteration=3,
        reset=lambda *args: (_ for _ in ()).throw(AssertionError('no reset')),
    )
    last_sample = SimpleNamespace(log_prob=np.array([-1.0, -2.0], dtype=float))
    backend.get_last_sample = lambda: last_sample
    minimizer = EmceeMinimizer()
    minimizer.nwalkers = 4
    minimizer.tracker = _FakeTracker()
    created_samplers: list[FakeEnsembleSampler] = []

    def fake_sampler_factory(**kwargs):
        sampler = FakeEnsembleSampler(**kwargs)
        created_samplers.append(sampler)
        return sampler

    monkeypatch.setattr(emcee_mod.emcee, 'EnsembleSampler', fake_sampler_factory)

    minimizer._run_sampler(
        backend=backend,
        log_prob=lambda values: -1.0,
        pool=None,
        parameters=[],
        n_parameters=2,
        random_seed=1,
        resume=True,
        extra_steps=2,
        total_iterations=2,
    )

    assert created_samplers[0].fake_sampler.calls == [
        {
            'initial_state': last_sample,
            'iterations': 2,
            'skip_initial_state_check': True,
            'progress': False,
        }
    ]
    assert [update.iteration for update in minimizer.tracker.updates] == [1, 2]


def test_emcee_sampler_settings_record_sampling_and_total_steps():
    from easydiffraction.analysis.minimizers.emcee import EmceeMinimizer

    minimizer = EmceeMinimizer()
    minimizer.nsteps = 100
    minimizer.nburn = 20

    settings = minimizer._sampler_settings(
        random_seed=123,
        total_steps=121,
        n_parameters=2,
    )

    assert settings['steps'] == 100
    assert settings['burn'] == 20
    assert settings['total_steps'] == 121
    assert settings['samples'] == 100 * minimizer.nwalkers * 2


def test_sample_with_progress_iterates_sampler_and_reports_each_state():
    from easydiffraction.analysis.minimizers.emcee import EmceeMinimizer

    sampler = _FakeSampler()
    reporter = SimpleNamespace(updates=[])

    def report(*, iteration: int, state: object) -> None:
        reporter.updates.append((iteration, state.log_prob.copy()))

    reporter.report = report

    EmceeMinimizer._sample_with_progress(
        sampler=sampler,
        initial_state=None,
        iterations=3,
        reporter=reporter,
        skip_initial_state_check=True,
    )

    assert sampler.calls == [
        {
            'initial_state': None,
            'iterations': 3,
            'skip_initial_state_check': True,
            'progress': False,
        }
    ]
    assert [iteration for iteration, _log_prob in reporter.updates] == [1, 2, 3]
