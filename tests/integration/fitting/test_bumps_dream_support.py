# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock
from unittest.mock import patch

import numpy as np
import pytest


class FakeParam:
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


def test_type_info_and_default_init():
    from easydiffraction.analysis.minimizers.bumps_dream import BumpsDreamMinimizer
    from easydiffraction.analysis.minimizers.enums import DreamPopulationInitializationEnum
    from easydiffraction.analysis.minimizers.enums import MinimizerTypeEnum

    minimizer = BumpsDreamMinimizer()

    assert minimizer.type_info.tag == MinimizerTypeEnum.BUMPS_DREAM
    assert minimizer.init is DreamPopulationInitializationEnum.LHS
    assert minimizer.steps == 3000


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


def test_dream_progress_monitor_helper_edge_cases():
    from easydiffraction.analysis.minimizers.bumps_dream import _DreamProgressMonitor

    monitor = _DreamProgressMonitor(
        tracker=MagicMock(),
        n_points=2,
        n_parameters=3,
        total_generations=10,
        burn_steps=2,
    )

    assert _DreamProgressMonitor._progress_targets(start=3, stop=2, target_count=2) == []
    assert _DreamProgressMonitor._progress_targets(start=1, stop=5, target_count=0) == []
    assert _DreamProgressMonitor._phase_progress_point_counts(
        total_generations=10, burn_steps=0
    ) == (0, 10)
    assert _DreamProgressMonitor._phase_progress_point_counts(
        total_generations=10, burn_steps=10
    ) == (10, 0)
    assert _DreamProgressMonitor._population_mean_log_posterior(
        SimpleNamespace(population_values=[], value=[2.5])
    ) == pytest.approx(-2.5)
    assert _DreamProgressMonitor._population_mean_log_posterior(
        SimpleNamespace(population_values=[np.array([np.nan, np.inf])], value=[1.5])
    ) == pytest.approx(-1.5)
    assert monitor._reduced_chi_square_from_nllf(4.0) == pytest.approx(8.0)


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


def test_dream_numeric_validators_reject_boolean_inputs():
    from easydiffraction.analysis.minimizers.bumps_dream import BumpsDreamMinimizer

    minimizer = BumpsDreamMinimizer()

    with pytest.raises(
        TypeError,
        match=r"DREAM setting 'steps' must be a positive integer\.",
    ):
        minimizer.steps = True
    with pytest.raises(
        TypeError,
        match=r"DREAM setting 'parallel' must be a non-negative integer\.",
    ):
        minimizer.parallel = True
    with pytest.raises(TypeError, match='DREAM random_seed must be an integer'):
        minimizer._validated_random_seed_value(random_seed=True)


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
def test_prepare_solver_args_rejects_invalid_dream_bounds(fit_min, fit_max, value, message):
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


def test_build_mapper_falls_back_for_serial_and_unpicklable(monkeypatch):
    from easydiffraction.analysis.minimizers.bumps_dream import BumpsDreamMinimizer

    minimizer = BumpsDreamMinimizer()
    minimizer.parallel = 1
    assert minimizer._build_mapper('problem') is None

    warnings: list[str] = []
    minimizer.parallel = 0
    monkeypatch.setattr(
        'easydiffraction.analysis.minimizers.bumps_dream.can_pickle', lambda problem: False
    )
    monkeypatch.setattr(
        'easydiffraction.analysis.minimizers.bumps_dream.log.warning',
        lambda message: warnings.append(message),
    )

    assert minimizer._build_mapper('problem') is None
    assert any('falling back to serial execution' in message for message in warnings)


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
                    map_value=22.0,
                    median=21.0,
                    standard_deviation=0.4,
                    interval_68=(20.5, 21.5),
                    interval_95=(20.0, 22.0),
                ),
                PosteriorParameterSummary(
                    unique_name='alpha',
                    display_name='Alpha',
                    map_value=11.0,
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
                init=minimizer.init,
                sampler_settings={'samples': 40},
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


def test_run_solver_failure_paths_return_failure_results(monkeypatch):
    from easydiffraction.analysis.minimizers.bumps_dream import BumpsDreamMinimizer
    from easydiffraction.analysis.minimizers.bumps_dream import _DreamDriverResult
    from easydiffraction.analysis.minimizers.bumps_dream import _DreamRunContext

    minimizer = BumpsDreamMinimizer()
    context = _DreamRunContext(
        driver=object(),
        parameter_names=['alpha'],
        parameter_display_names=['Alpha'],
        parameter_uids=['uid_alpha'],
        sampler_settings={'random_seed': 7},
        starting_values=np.array([1.0]),
        starting_uncertainties=[0.1],
    )

    monkeypatch.setattr(
        minimizer,
        '_prepare_run_context',
        lambda *, objective_function, kwargs: context,
    )
    monkeypatch.setattr(
        minimizer,
        '_execute_driver',
        lambda *, driver, random_seed: _DreamDriverResult(
            best_values=None,
            best_nllf=None,
            raw_state='state',
            error=RuntimeError('boom'),
        ),
    )

    failed = minimizer._run_solver(lambda _: np.array([0.0]))

    assert failed.success is False
    assert failed.message == 'DREAM sampling failed: boom'
    assert failed.sampler_completed is False

    monkeypatch.setattr(
        minimizer,
        '_execute_driver',
        lambda *, driver, random_seed: _DreamDriverResult(
            best_values=np.array([1.0]),
            best_nllf=0.5,
            raw_state=None,
            error=None,
        ),
    )

    unusable = minimizer._run_solver(lambda _: np.array([0.0]))

    assert unusable.success is False
    assert unusable.message == 'DREAM sampling did not produce usable posterior samples.'
    assert unusable.sampler_completed is False


def test_build_success_result_handles_invalid_samples_and_warns_when_not_converged(monkeypatch):
    from easydiffraction.analysis.fit_helpers.bayesian import PosteriorParameterSummary
    from easydiffraction.analysis.minimizers.bumps_dream import BumpsDreamMinimizer
    from easydiffraction.analysis.minimizers.bumps_dream import _DreamRunContext

    minimizer = BumpsDreamMinimizer()
    context = _DreamRunContext(
        driver=object(),
        parameter_names=['alpha'],
        parameter_display_names=['Alpha'],
        parameter_uids=['uid_alpha'],
        sampler_settings={'random_seed': 7},
        starting_values=np.array([1.0]),
        starting_uncertainties=[0.1],
    )

    class BadState:
        labels = ['uid_alpha']

        @staticmethod
        def chains():
            return np.array([0.0]), np.array([1.0]), np.array([0.0])

        @staticmethod
        def best():
            return np.array([1.0]), 0.5

    failed = minimizer._build_success_result(context=context, raw_state=BadState(), best_nllf=0.5)

    assert failed.success is False
    assert failed.sampler_completed is True

    class GoodState:
        labels = ['uid_alpha']

        @staticmethod
        def chains():
            return (
                np.array([0.0, 1.0]),
                np.ones((2, 2, 1), dtype=float),
                np.zeros((2, 2), dtype=float),
            )

        @staticmethod
        def best():
            return np.array([1.0]), 0.5

    warnings: list[str] = []
    monkeypatch.setattr(
        'easydiffraction.analysis.minimizers.bumps_dream.compute_convergence_diagnostics',
        lambda posterior_samples: {'converged': False},
    )
    monkeypatch.setattr(
        'easydiffraction.analysis.minimizers.bumps_dream.summarize_posterior_parameters',
        lambda **kwargs: [
            PosteriorParameterSummary(
                unique_name='alpha',
                display_name='Alpha',
                map_value=1.0,
                median=1.0,
                standard_deviation=0.2,
                interval_68=(0.9, 1.1),
                interval_95=(0.8, 1.2),
            )
        ],
    )
    monkeypatch.setattr(
        'easydiffraction.analysis.minimizers.bumps_dream.standard_deviations_from_summaries',
        lambda summaries: np.array([0.2]),
    )
    monkeypatch.setattr(
        'easydiffraction.analysis.minimizers.bumps_dream.log.warning',
        lambda message: warnings.append(message),
    )

    successful = minimizer._build_success_result(
        context=context,
        raw_state=GoodState(),
        best_nllf=0.5,
    )

    assert successful.success is True
    assert successful.sampler_completed is True
    assert any('poorly mixed' in message for message in warnings)
