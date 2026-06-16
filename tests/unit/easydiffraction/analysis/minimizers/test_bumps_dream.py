# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock
from unittest.mock import patch

import numpy as np
import pytest


class FakeParam:
    """Minimal stand-in for an EasyDiffraction parameter."""

    def __init__(
        self,
        uid: str,
        value: float,
        uncertainty: float | None = None,
        *,
        fit_min: float | None = 0.0,
        fit_max: float | None = 1.0,
    ) -> None:
        self._minimizer_uid = uid
        self.unique_name = uid
        self.name = uid.upper()
        self.value = value
        self.uncertainty = uncertainty
        self.fit_min = fit_min
        self.fit_max = fit_max

    def _set_value_from_minimizer(self, value: float) -> None:
        self.value = value


def test_module_import():
    import easydiffraction.analysis.minimizers.bumps_dream as MUT

    assert MUT.__name__ == 'easydiffraction.analysis.minimizers.bumps_dream'


def test_type_info_and_default_init():
    from easydiffraction.analysis.minimizers.bumps_dream import BumpsDreamMinimizer
    from easydiffraction.analysis.minimizers.enums import DreamPopulationInitializationEnum
    from easydiffraction.analysis.minimizers.enums import MinimizerTypeEnum

    minimizer = BumpsDreamMinimizer()

    assert minimizer.type_info.tag == MinimizerTypeEnum.BUMPS_DREAM
    assert minimizer.init is DreamPopulationInitializationEnum.LHS
    assert minimizer.steps == 3000


def test_dream_uses_steps_instead_of_max_iterations():
    from easydiffraction.analysis.minimizers.bumps_dream import BumpsDreamMinimizer

    minimizer = BumpsDreamMinimizer()

    with pytest.raises(
        AttributeError,
        match=r"DREAM sampler uses 'steps' instead of 'max_iterations'\.",
    ):
        _ = minimizer.max_iterations

    with pytest.raises(
        AttributeError,
        match=r"DREAM sampler uses 'steps' instead of 'max_iterations'\.",
    ):
        minimizer.max_iterations = 300

    minimizer.steps = 300

    assert minimizer.steps == 300


def test_dream_progress_monitor_allocates_rows_by_phase_ratio():
    from easydiffraction.analysis.minimizers.bumps_dream import _DreamProgressMonitor

    monitor = _DreamProgressMonitor(
        tracker=MagicMock(),
        n_points=100,
        n_parameters=3,
        total_generations=100,
        burn_steps=40,
    )

    assert len(monitor._burn_targets) == 10
    assert len(monitor._sampling_targets) == 15


def test_dream_progress_monitor_reports_relative_progress_on_resume():
    from easydiffraction.analysis.minimizers.bumps_dream import _DreamProgressMonitor

    # Resume from a 1000-generation chain, adding 100 more (burn=0).
    monitor = _DreamProgressMonitor(
        tracker=MagicMock(),
        n_points=100,
        n_parameters=5,
        total_generations=1101,
        burn_steps=0,
        start_generation=1000,
    )

    # Progress is reported over the 100 new generations (1/100..100/100),
    # not the absolute 1001/1101.
    assert monitor._reported_iteration(1000) == 1
    assert monitor._reported_iteration(1050) == 50
    assert monitor._reported_iteration(1100) == 100
    assert monitor._reported_total_iterations() == 100
    assert monitor._progress_percent(1050) == pytest.approx(50.0)
    # Reporting targets fall within the new generation range.
    assert min(monitor._sampling_targets) >= 1001
    assert max(monitor._sampling_targets) == 1101


def test_dream_progress_monitor_reports_absolute_progress_when_fresh():
    from easydiffraction.analysis.minimizers.bumps_dream import _DreamProgressMonitor

    monitor = _DreamProgressMonitor(
        tracker=MagicMock(),
        n_points=100,
        n_parameters=3,
        total_generations=101,
        burn_steps=0,
    )

    assert monitor._reported_iteration(40) == 40
    assert monitor._reported_total_iterations() == 101
    assert monitor._progress_percent(40) == pytest.approx(100.0 * 40 / 101)


def test_init_accepts_enum_or_string_and_rejects_invalid():
    from easydiffraction.analysis.minimizers.bumps_dream import BumpsDreamMinimizer
    from easydiffraction.analysis.minimizers.enums import DreamPopulationInitializationEnum

    minimizer = BumpsDreamMinimizer()

    minimizer.init = DreamPopulationInitializationEnum.LHS
    assert minimizer.init is DreamPopulationInitializationEnum.LHS

    minimizer.init = 'random'
    assert minimizer.init is DreamPopulationInitializationEnum.RANDOM

    with pytest.raises(
        ValueError,
        match=r"DREAM setting 'init' must be one of: eps, cov, lhs, random\.",
    ):
        minimizer.init = 'bad-init'


def test_resolve_random_seed_returns_provided_or_generated(monkeypatch):
    from easydiffraction.analysis.minimizers.bumps_dream import BumpsDreamMinimizer

    minimizer = BumpsDreamMinimizer()

    assert minimizer._resolve_random_seed(17) == 17
    assert minimizer._resolved_random_seed == 17

    generator = SimpleNamespace(integers=lambda *args, **kwargs: 123456)
    monkeypatch.setattr(np.random, 'default_rng', lambda: generator)

    assert minimizer._resolve_random_seed(None) == 123456
    assert minimizer._resolved_random_seed == 123456


@pytest.mark.parametrize('seed', [-1, np.iinfo(np.uint32).max + 1])
def test_resolve_random_seed_rejects_out_of_range_values(seed):
    from easydiffraction.analysis.minimizers.bumps_dream import BumpsDreamMinimizer

    minimizer = BumpsDreamMinimizer()

    with pytest.raises(
        ValueError,
        match=r'DREAM random_seed must be an integer between 0 and 4294967295\.',
    ):
        minimizer._resolve_random_seed(seed)


def test_resolved_burn_uses_auto_or_explicit_and_validates():
    from easydiffraction.analysis.minimizers.bumps_dream import BumpsDreamMinimizer

    minimizer = BumpsDreamMinimizer()

    assert minimizer._resolved_burn(steps=200) == 50

    minimizer.burn = 20
    assert minimizer._resolved_burn(steps=200) == 20

    minimizer.burn = 200
    with pytest.raises(
        ValueError,
        match=r"DREAM setting 'burn' must be smaller than 'steps'\.",
    ):
        minimizer._resolved_burn(steps=200)


def test_sampler_settings_include_init_and_sample_count():
    from easydiffraction.analysis.minimizers.bumps_dream import BumpsDreamMinimizer
    from easydiffraction.analysis.minimizers.enums import DreamPopulationInitializationEnum

    minimizer = BumpsDreamMinimizer()
    minimizer.thin = 1
    minimizer.pop = 4
    minimizer.init = DreamPopulationInitializationEnum.LHS

    settings = minimizer._sampler_settings(
        random_seed=7,
        steps=10,
        burn=2,
        n_parameters=3,
    )

    assert settings['random_seed'] == 7
    assert settings['parallel'] == 0
    assert settings['init'] == 'lhs'
    assert settings['samples'] == 120


@pytest.mark.parametrize(
    ('fit_min', 'fit_max', 'value', 'message'),
    [
        (None, 1.0, 0.5, r'fit_min must be finite'),
        (0.0, np.inf, 0.5, r'fit_max must be finite'),
        (2.0, 1.0, 1.5, r'fit_min \(2\.0\) must be smaller than fit_max \(1\.0\)'),
        (0.0, 1.0, 2.0, r'starting value 2\.0 is outside \[0\.0, 1\.0\]'),
    ],
)
def test_prepare_solver_args_rejects_invalid_dream_bounds(
    fit_min,
    fit_max,
    value,
    message,
):
    from easydiffraction.analysis.minimizers.bumps_dream import BumpsDreamMinimizer

    minimizer = BumpsDreamMinimizer()
    parameter = FakeParam('alpha', value, fit_min=fit_min, fit_max=fit_max)

    with pytest.raises(ValueError, match=message):
        minimizer._prepare_solver_args([parameter])


def test_prepare_solver_args_lists_all_offending_dream_parameters():
    from easydiffraction.analysis.minimizers.bumps_dream import BumpsDreamMinimizer

    minimizer = BumpsDreamMinimizer()
    parameters = [
        FakeParam('alpha', 2.0, fit_min=0.0, fit_max=1.0),
        FakeParam('beta', 0.5, fit_min=None, fit_max=1.0),
    ]

    with pytest.raises(
        ValueError,
        match=r'alpha: .*outside \[0\.0, 1\.0\][\s\S]*beta: .*fit_min',
    ):
        minimizer._prepare_solver_args(parameters)


def test_sync_result_to_parameters_restores_starting_values_on_failure():
    from easydiffraction.analysis.minimizers.bumps_dream import BumpsDreamMinimizer

    minimizer = BumpsDreamMinimizer()
    parameters = [FakeParam('a', 10.0, uncertainty=0.7), FakeParam('b', 20.0, uncertainty=0.8)]
    raw_result = SimpleNamespace(
        x=np.array([99.0, 88.0]),
        success=False,
        starting_values=np.array([1.5, 2.5]),
        starting_uncertainties=[0.1, None],
    )

    minimizer._sync_result_to_parameters(parameters, raw_result)

    assert parameters[0].value == 1.5
    assert parameters[0].uncertainty == 0.1
    assert parameters[1].value == 2.5
    assert parameters[1].uncertainty is None


def test_run_solver_preserves_parameter_order_and_forwards_init():
    from easydiffraction.analysis.fit_helpers.bayesian import PosteriorParameterSummary
    from easydiffraction.analysis.minimizers.bumps_dream import BumpsDreamMinimizer

    minimizer = BumpsDreamMinimizer()
    minimizer.steps = 4
    minimizer.burn = 1
    minimizer.thin = 1
    minimizer.pop = 2
    minimizer.init = 'lhs'

    draw_index = np.array([0.0, 1.0])
    parameter_samples = np.array(
        [
            [[1.0, 10.0], [2.0, 20.0]],
            [[3.0, 30.0], [4.0, 40.0]],
        ],
        dtype=float,
    )
    log_posterior = np.array([[0.1, 0.2], [0.3, 0.4]], dtype=float)

    class FakeState:
        labels = ['uid_a', 'uid_b']

        def chains(self):
            return draw_index, parameter_samples, log_posterior

        def best(self):
            return np.array([11.0, 22.0]), 3.5

    fake_fitter = SimpleNamespace(id='dream')

    with (
        patch('easydiffraction.analysis.minimizers.bumps_dream.FitDriver') as mock_driver_cls,
        patch('easydiffraction.analysis.minimizers.bumps_dream.FitProblem'),
        patch('easydiffraction.analysis.minimizers.bumps_dream.FITTERS', [fake_fitter]),
        patch(
            'easydiffraction.analysis.minimizers.bumps_dream.compute_convergence_diagnostics',
            return_value={'converged': True},
        ),
        patch(
            'easydiffraction.analysis.minimizers.bumps_dream.summarize_posterior_parameters',
            return_value=[
                PosteriorParameterSummary(
                    unique_name='beta',
                    display_name='Beta',
                    best_sample_value=22.0,
                    median=21.0,
                    standard_deviation=0.4,
                    interval_68=(20.5, 21.5),
                    interval_95=(20.0, 22.0),
                ),
                PosteriorParameterSummary(
                    unique_name='alpha',
                    display_name='Alpha',
                    best_sample_value=11.0,
                    median=10.5,
                    standard_deviation=0.3,
                    interval_68=(10.0, 11.0),
                    interval_95=(9.5, 11.5),
                ),
            ],
        ) as summarize_mock,
        patch(
            'easydiffraction.analysis.minimizers.bumps_dream.standard_deviations_from_summaries',
            return_value=np.array([0.4, 0.3]),
        ),
    ):
        driver_instance = mock_driver_cls.return_value
        driver_instance.clip = MagicMock()
        driver_instance.fit.return_value = (np.array([22.0, 11.0]), 0.25)
        driver_instance.fitter = SimpleNamespace(state=FakeState())

        result = minimizer._run_solver(
            lambda values: np.array([0.0, 0.0]),
            bumps_params=[
                SimpleNamespace(name='uid_a', value=1.0),
                SimpleNamespace(name='uid_b', value=2.0),
            ],
            parameter_names=['beta', 'alpha'],
            parameter_display_names=['Beta', 'Alpha'],
            parameter_uids=['uid_b', 'uid_a'],
            random_seed=17,
            starting_uncertainties=[0.01, 0.02],
        )

    assert mock_driver_cls.call_args.kwargs['init'] == 'lhs'
    np.testing.assert_allclose(result.x, np.array([22.0, 11.0]))
    np.testing.assert_allclose(result.dx, np.array([0.4, 0.3]))
    assert result.posterior_samples.parameter_names == ['beta', 'alpha']
    np.testing.assert_allclose(
        result.posterior_samples.parameter_samples[:, :, 0], parameter_samples[:, :, 1]
    )
    np.testing.assert_allclose(
        result.posterior_samples.parameter_samples[:, :, 1], parameter_samples[:, :, 0]
    )
    assert result.sampler_settings['init'] == 'lhs'
    assert result.sampler_settings['random_seed'] == 17
    assert summarize_mock.call_args.kwargs['parameter_names'] == ['beta', 'alpha']


def test_build_driver_stops_mapper_when_driver_clip_fails():
    from easydiffraction.analysis.minimizers.bumps_dream import BumpsDreamMinimizer

    minimizer = BumpsDreamMinimizer()

    with (
        patch.object(minimizer, '_build_mapper', return_value='mapper'),
        patch(
            'easydiffraction.analysis.minimizers.bumps_dream.FitProblem', return_value='problem'
        ),
        patch('easydiffraction.analysis.minimizers.bumps_dream.FitDriver') as mock_driver_cls,
        patch(
            'easydiffraction.analysis.minimizers.bumps_dream.MPMapper.stop_mapper'
        ) as stop_mapper,
    ):
        mock_driver_cls.return_value.clip.side_effect = RuntimeError('clip failed')

        with pytest.raises(RuntimeError, match='clip failed'):
            minimizer._build_driver(
                fitclass=object(),
                fitness=SimpleNamespace(numpoints=lambda: 10),
                steps=10,
                burn=2,
                sampler_settings={'samples': 40, 'pop': 4},
                n_parameters=1,
            )

    stop_mapper.assert_called_once()


def test_execute_driver_stops_mapper_when_seed_is_invalid():
    from easydiffraction.analysis.minimizers.bumps_dream import BumpsDreamMinimizer

    driver = SimpleNamespace(fit=MagicMock(), fitter=SimpleNamespace(state=None))

    with patch(
        'easydiffraction.analysis.minimizers.bumps_dream.MPMapper.stop_mapper'
    ) as stop_mapper:
        result = BumpsDreamMinimizer._execute_driver(driver=driver, random_seed=-1)

    assert isinstance(result.error, ValueError)
    driver.fit.assert_not_called()
    stop_mapper.assert_called_once()


def _build_dream_state(*, n_var=2, n_pop=6, n_gen=8, n_cr=3, labels=None, seed=0):
    """Build a populated, h5-dumpable bumps ``MCMCDraw`` for tests."""
    from bumps.dream.state import MCMCDraw

    state = MCMCDraw(
        Ngen=n_gen,
        Nthin=n_gen,
        Nupdate=n_gen,
        Nvar=n_var,
        Npop=n_pop,
        Ncr=n_cr,
        thinning=1,
    )
    rng = np.random.RandomState(seed)
    for _ in range(n_gen):
        x = rng.rand(n_pop, n_var)
        logp = -rng.rand(n_pop)
        accept = np.ones(n_pop, dtype=bool)
        state._generation(new_draws=n_pop, x=x, logp=logp, accept=accept)
        state._update(CR_weight=np.ones(n_cr) / n_cr)
    state.labels = labels if labels is not None else [f'p{index}' for index in range(n_var)]
    return state


def test_dream_state_sidecar_round_trips_through_mcmc_h5(tmp_path):
    from easydiffraction.analysis.minimizers.bumps_dream import DREAM_STATE_GROUP
    from easydiffraction.analysis.minimizers.bumps_dream import _read_dream_state_sidecar
    from easydiffraction.analysis.minimizers.bumps_dream import _write_dream_state_sidecar

    sidecar_path = tmp_path / 'analysis' / 'mcmc.h5'
    state = _build_dream_state(labels=['alpha', 'beta'])

    _write_dream_state_sidecar(sidecar_path, state, ['alpha', 'beta'])

    import h5py

    with h5py.File(sidecar_path, 'r') as handle:
        assert DREAM_STATE_GROUP in handle
        assert 'state' in handle[DREAM_STATE_GROUP]
        assert 'param_names' in handle[DREAM_STATE_GROUP]

    loaded = _read_dream_state_sidecar(sidecar_path)
    assert loaded is not None
    restored_state, restored_names = loaded
    assert restored_names == ['alpha', 'beta']
    assert int(restored_state.Nvar) == 2
    assert int(restored_state.Npop) == 6
    np.testing.assert_allclose(
        restored_state.draw().points,
        state.draw().points,
    )


def test_dream_state_sidecar_write_replaces_existing_group(tmp_path):
    from easydiffraction.analysis.minimizers.bumps_dream import _read_dream_state_sidecar
    from easydiffraction.analysis.minimizers.bumps_dream import _write_dream_state_sidecar

    sidecar_path = tmp_path / 'mcmc.h5'
    _write_dream_state_sidecar(sidecar_path, _build_dream_state(n_gen=8), ['a', 'b'])
    _write_dream_state_sidecar(sidecar_path, _build_dream_state(n_gen=4), ['c', 'd'])

    loaded = _read_dream_state_sidecar(sidecar_path)
    assert loaded is not None
    _, restored_names = loaded
    assert restored_names == ['c', 'd']


def test_read_dream_state_sidecar_returns_none_when_file_absent(tmp_path):
    from easydiffraction.analysis.minimizers.bumps_dream import _read_dream_state_sidecar

    assert _read_dream_state_sidecar(tmp_path / 'missing.h5') is None


def test_read_dream_state_sidecar_returns_none_when_group_absent(tmp_path):
    import h5py

    from easydiffraction.analysis.minimizers.bumps_dream import _read_dream_state_sidecar

    sidecar_path = tmp_path / 'mcmc.h5'
    with h5py.File(sidecar_path, 'w') as handle:
        handle.create_group('posterior')

    assert _read_dream_state_sidecar(sidecar_path) is None


def test_read_dream_state_sidecar_raises_when_group_malformed(tmp_path):
    import h5py

    from easydiffraction.analysis.minimizers.bumps_dream import DREAM_STATE_GROUP
    from easydiffraction.analysis.minimizers.bumps_dream import _read_dream_state_sidecar

    sidecar_path = tmp_path / 'mcmc.h5'
    with h5py.File(sidecar_path, 'w') as handle:
        handle.create_group(DREAM_STATE_GROUP)

    with pytest.raises(ValueError, match=r"Malformed 'dream_state' group"):
        _read_dream_state_sidecar(sidecar_path)


def test_persist_dream_state_is_noop_without_sidecar_path():
    from easydiffraction.analysis.minimizers.bumps_dream import BumpsDreamMinimizer

    minimizer = BumpsDreamMinimizer()
    assert minimizer._sidecar_path is None

    # Should not raise and should not attempt any write.
    minimizer._persist_dream_state(raw_state=object(), parameter_names=['a'])


def test_validate_dream_resume_accepts_matching_state():
    from easydiffraction.analysis.minimizers.bumps_dream import BumpsDreamMinimizer

    state = _build_dream_state(n_var=2, n_pop=6, labels=['a', 'b'])

    # ceil(pop_scale * n_parameters) == Npop -> 3 * 2 == 6.
    BumpsDreamMinimizer._validate_dream_resume(
        state=state,
        saved_names=['a', 'b'],
        names=['a', 'b'],
        pop_scale=3,
        n_parameters=2,
    )


def test_validate_dream_resume_rejects_parameter_count_mismatch():
    from easydiffraction.analysis.minimizers.bumps_dream import BumpsDreamMinimizer

    state = _build_dream_state(n_var=2, n_pop=6, labels=['a', 'b'])

    with pytest.raises(ValueError, match='free-parameter set must match'):
        BumpsDreamMinimizer._validate_dream_resume(
            state=state,
            saved_names=['a', 'b'],
            names=['a', 'b', 'c'],
            pop_scale=2,
            n_parameters=3,
        )


def test_validate_dream_resume_rejects_name_order_mismatch():
    from easydiffraction.analysis.minimizers.bumps_dream import BumpsDreamMinimizer

    state = _build_dream_state(n_var=2, n_pop=6, labels=['a', 'b'])

    with pytest.raises(ValueError, match='Parameter names/order differ'):
        BumpsDreamMinimizer._validate_dream_resume(
            state=state,
            saved_names=['a', 'b'],
            names=['b', 'a'],
            pop_scale=3,
            n_parameters=2,
        )


def test_validate_dream_resume_rejects_population_mismatch():
    from easydiffraction.analysis.minimizers.bumps_dream import BumpsDreamMinimizer

    state = _build_dream_state(n_var=2, n_pop=6, labels=['a', 'b'])

    with pytest.raises(ValueError, match='population cannot change on resume'):
        BumpsDreamMinimizer._validate_dream_resume(
            state=state,
            saved_names=['a', 'b'],
            names=['a', 'b'],
            pop_scale=4,
            n_parameters=2,
        )


def test_state_generations_divides_total_draws_by_population():
    from easydiffraction.analysis.minimizers.bumps_dream import BumpsDreamMinimizer

    state = _build_dream_state(n_var=2, n_pop=6, n_gen=8, labels=['a', 'b'])

    generations = BumpsDreamMinimizer._state_generations(
        state=state,
        pop_scale=3,
        n_parameters=2,
    )

    assert generations == 8


def test_prepare_dream_resume_builds_ring_buffer_overrides(tmp_path):
    from easydiffraction.analysis.minimizers.bumps_dream import BumpsDreamMinimizer
    from easydiffraction.analysis.minimizers.bumps_dream import _write_dream_state_sidecar

    sidecar_path = tmp_path / 'mcmc.h5'
    state = _build_dream_state(n_var=2, n_pop=6, n_gen=8, labels=['a', 'b'])
    _write_dream_state_sidecar(sidecar_path, state, ['a', 'b'])

    minimizer = BumpsDreamMinimizer()
    minimizer._sidecar_path = sidecar_path
    minimizer.pop = 3

    overrides, fit_state = minimizer._prepare_dream_resume(
        kwargs={'parameter_names': ['a', 'b']},
        extra_steps=5,
    )

    assert overrides == {
        'steps_override': 13,
        'burn_override': 0,
        'samples_override': 13 * 3 * 2,
        'pop_override': 3,
        'start_generation': 8,
    }
    # bumps mutates state in place, so resume must pass a deep copy.
    assert fit_state is not state
    np.testing.assert_allclose(fit_state.draw().points, state.draw().points)


@pytest.mark.parametrize('extra_steps', [0, -1, 1.5, True])
def test_prepare_dream_resume_rejects_non_positive_extra_steps(tmp_path, extra_steps):
    from easydiffraction.analysis.minimizers.bumps_dream import BumpsDreamMinimizer

    minimizer = BumpsDreamMinimizer()
    minimizer._sidecar_path = tmp_path / 'mcmc.h5'

    with pytest.raises(ValueError, match='positive integer extra_steps'):
        minimizer._prepare_dream_resume(
            kwargs={'parameter_names': ['a', 'b']},
            extra_steps=extra_steps,
        )


def test_prepare_dream_resume_requires_sidecar_path():
    from easydiffraction.analysis.minimizers.bumps_dream import BumpsDreamMinimizer

    minimizer = BumpsDreamMinimizer()
    assert minimizer._sidecar_path is None

    with pytest.raises(ValueError, match='requires a saved project'):
        minimizer._prepare_dream_resume(
            kwargs={'parameter_names': ['a', 'b']},
            extra_steps=5,
        )


def test_prepare_dream_resume_requires_existing_chain(tmp_path):
    from easydiffraction.analysis.minimizers.bumps_dream import BumpsDreamMinimizer

    minimizer = BumpsDreamMinimizer()
    minimizer._sidecar_path = tmp_path / 'mcmc.h5'

    with pytest.raises(ValueError, match='No saved bumps-dream chain to resume'):
        minimizer._prepare_dream_resume(
            kwargs={'parameter_names': ['a', 'b']},
            extra_steps=5,
        )


def test_chains_alias_shares_storage_with_pop():
    from easydiffraction.analysis.minimizers.bumps_dream import BumpsDreamMinimizer

    minimizer = BumpsDreamMinimizer()
    minimizer.chains = 7
    assert minimizer.pop == 7
    assert minimizer.chains == 7

    minimizer.pop = 2
    assert minimizer.chains == 2


def test_dream_nllf_worker_requires_initialized_problem():
    from easydiffraction.analysis.minimizers import bumps_dream as bd

    bd._set_dream_worker_problem(None)
    with pytest.raises(RuntimeError, match='worker problem has not been initialized'):
        bd._dream_nllf_worker(np.array([1.0]))

    problem = SimpleNamespace(nllf=lambda point: float(point[0]) * 2.0)
    bd._set_dream_worker_problem(problem)
    try:
        assert bd._dream_nllf_worker(np.array([3.0])) == 6.0
    finally:
        bd._set_dream_worker_problem(None)


def test_dream_fork_pool_mapper_maps_points_via_pool():
    from easydiffraction.analysis.minimizers import bumps_dream as bd

    class FakePool:
        def map(self, fn, points):
            return [fn(point) for point in points]

    problem = SimpleNamespace(nllf=lambda point: float(point[0]))
    bd._set_dream_worker_problem(problem)
    try:
        mapper = bd._DreamForkPoolMapper(FakePool())
        assert mapper([np.array([1.0]), np.array([2.5])]) == [1.0, 2.5]
    finally:
        bd._set_dream_worker_problem(None)


def test_shutdown_fork_pool_mapper_terminates_and_clears_problem():
    from easydiffraction.analysis.minimizers import bumps_dream as bd
    from easydiffraction.analysis.minimizers.bumps_dream import BumpsDreamMinimizer

    events: list[str] = []

    class FakePool:
        def terminate(self):
            events.append('terminate')

        def join(self):
            events.append('join')

    bd._set_dream_worker_problem(object())
    mapper = bd._DreamForkPoolMapper(FakePool())

    BumpsDreamMinimizer._shutdown_fork_pool_mapper(mapper)

    assert events == ['terminate', 'join']
    assert bd._DREAM_WORKER_PROBLEM is None

    # Tolerates a non-fork mapper (e.g. MPMapper's plain function) and None.
    BumpsDreamMinimizer._shutdown_fork_pool_mapper(lambda points: points)
    BumpsDreamMinimizer._shutdown_fork_pool_mapper(None)


def test_build_fork_pool_mapper_returns_none_without_fork(monkeypatch):
    from easydiffraction.analysis.minimizers import bumps_dream as bd
    from easydiffraction.analysis.minimizers.bumps_dream import BumpsDreamMinimizer

    minimizer = BumpsDreamMinimizer()
    minimizer.parallel = 0
    monkeypatch.setattr(
        bd.multiprocessing,
        'get_all_start_methods',
        lambda: ['spawn', 'forkserver'],
    )

    assert minimizer._build_fork_pool_mapper('problem') is None
