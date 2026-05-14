# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pytest


class DummyParam:
    def __init__(self, value: float) -> None:
        self.value = value
        self.fit_min = -np.inf
        self.fit_max = np.inf
        self.unique_name = f'param_{value}'

    def _physical_lower_bound(self) -> float:
        return -np.inf

    def _physical_upper_bound(self) -> float:
        return np.inf


def test_tracker_terminal_flow_prints_and_updates_best(monkeypatch, capsys):
    import easydiffraction.analysis.fit_helpers.tracking as tracking_mod
    from easydiffraction.analysis.fit_helpers.tracking import FitProgressTracker

    events: list[tuple[str, object]] = []

    class FakeIndicator:
        def __init__(self, label, *, verbosity):
            events.append(('init', label, verbosity))

        def start(self):
            events.append(('start', None))

        def update(self, *, label=None, content=None):
            events.append(('update', label))
            del content

        def stop(self):
            events.append(('stop', None))

    monkeypatch.setattr(tracking_mod, 'ActivityIndicator', FakeIndicator)
    monkeypatch.setattr(tracking_mod, 'build_table_renderable', lambda **kwargs: 'table')

    tracker = FitProgressTracker()
    tracker.start_tracking('dummy')
    tracker.start_timer()

    tracker.track(np.array([2.0, 1.0]), parameters=[1])
    out = capsys.readouterr().out
    assert 'Goodness-of-fit' in out

    tracker.track(np.array([1.9, 1.0]), parameters=[1])
    tracker.track(np.array([0.1, 0.1]), parameters=[1])

    tracker.stop_timer()
    tracker.finish_tracking()

    out = capsys.readouterr().out
    assert 'Best goodness-of-fit' in out
    assert tracker.best_iteration is not None
    assert ('init', tracking_mod.ACTIVITY_LABEL_FITTING, tracker._verbosity) in events


def test_tracker_sampler_progress_renders_and_completes(monkeypatch, capsys):
    import easydiffraction.analysis.fit_helpers.tracking as tracking_mod
    from easydiffraction.analysis.fit_helpers.tracking import FitProgressTracker
    from easydiffraction.analysis.fit_helpers.tracking import SamplerProgressUpdate

    events: list[tuple[str, object]] = []

    class FakeIndicator:
        def __init__(self, label, *, verbosity):
            events.append(('init', label, verbosity))

        def start(self):
            events.append(('start', None))

        def update(self, *, label=None, content=None):
            events.append(('update', label))
            del content

        def stop(self):
            events.append(('stop', None))

    monkeypatch.setattr(tracking_mod, 'ActivityIndicator', FakeIndicator)
    monkeypatch.setattr(tracking_mod, 'build_table_renderable', lambda **kwargs: 'table')

    tracker = FitProgressTracker()
    tracker.start_tracking('dream', mode='sampling')
    tracker.start_timer()
    tracker.track_sampler_progress(
        SamplerProgressUpdate(
            iteration=1,
            total_iterations=10,
            phase='burn-in',
            progress_percent=10.0,
            log_posterior=-12.0,
            reduced_chi2=5.0,
            elapsed_time=0.0,
            force_report=True,
        )
    )
    tracker.track_sampler_progress(
        SamplerProgressUpdate(
            iteration=10,
            total_iterations=10,
            phase='sampling',
            progress_percent=100.0,
            log_posterior=-3.0,
            reduced_chi2=1.0,
            elapsed_time=6.0,
            force_report=False,
        )
    )
    tracker.stop_timer()
    tracker.finish_tracking()

    out = capsys.readouterr().out
    assert 'Bayesian sampling progress' in out
    assert 'Bayesian sampling complete.' in out
    assert tracker.best_chi2 == pytest.approx(1.0)
    assert tracker.best_iteration == 10
    assert ('update', tracking_mod.ACTIVITY_LABEL_BURN_IN) in events
    assert ('update', tracking_mod.ACTIVITY_LABEL_SAMPLING) in events


def test_tracker_helper_error_paths_and_short_mode(monkeypatch):
    import easydiffraction.analysis.fit_helpers.tracking as tracking_mod
    from easydiffraction.analysis.fit_helpers.tracking import FitProgressTracker
    from easydiffraction.utils.enums import VerbosityEnum

    events: list[tuple[str, object]] = []

    class FakeIndicator:
        def __init__(self, label, *, verbosity):
            events.append(('init', label, verbosity))

        def start(self):
            events.append(('start', None))

        def update(self, *, label=None, content=None):
            events.append(('update', label))
            del content

        def stop(self):
            events.append(('stop', None))

    monkeypatch.setattr(tracking_mod, 'ActivityIndicator', FakeIndicator)

    tracker = FitProgressTracker()
    tracker._verbosity = VerbosityEnum.SHORT
    tracker.stop_timer()
    tracker.start_tracking('dream', mode='sampling')
    tracker.finish_tracking()

    with pytest.raises(RuntimeError, match='Sampler progress is unavailable'):
        FitProgressTracker()._resolved_final_sampler_progress()
    with pytest.raises(RuntimeError, match='Sampler iteration labels require'):
        FitProgressTracker()._sampler_iteration_label(1)

    assert FitProgressTracker._rows_match_on_columns(['1', 'a'], ['1', 'b'], (0,)) is True
    assert events == [
        ('init', tracking_mod.ACTIVITY_LABEL_PROCESSING, VerbosityEnum.SHORT),
        ('start', None),
        ('update', tracking_mod.ACTIVITY_LABEL_PROCESSING),
        ('stop', None),
    ]


def test_tracker_final_sampler_row_replaces_last_row():
    from easydiffraction.analysis.fit_helpers.tracking import FitProgressTracker

    tracker = FitProgressTracker()
    tracker._tracking_mode = 'sampling'
    tracker._sampler_total_iterations = 10
    tracker._last_iteration = 10
    tracker._last_sampler_progress_percent = 100.0
    tracker._last_sampler_log_posterior = -3.0
    tracker._last_sampler_phase = 'sampling'
    tracker._last_sampler_elapsed_time = 5.0
    tracker._df_rows = [['10/10', '90.0%', '4.00', '-3.00', 'sampling']]

    tracker.finish_tracking()

    assert tracker._df_rows[-1] == ['10/10', '100.0%', '5.00', '-3.00', 'sampling']


def test_make_display_handle_uses_terminal_live_when_available(monkeypatch):
    import easydiffraction.analysis.fit_helpers.tracking as tracking_mod

    sentinel = object()

    monkeypatch.setattr(tracking_mod, 'make_display_handle', lambda: sentinel)

    assert tracking_mod._make_display_handle() is sentinel


def test_tracker_misc_helper_paths(monkeypatch):
    import easydiffraction.analysis.fit_helpers.tracking as tracking_mod
    from easydiffraction.analysis.fit_helpers.tracking import FitProgressTracker
    from easydiffraction.utils.enums import VerbosityEnum

    render_calls: list[dict[str, object]] = []
    update_calls: list[dict[str, object]] = []
    monkeypatch.setattr(
        tracking_mod, 'calculate_reduced_chi_square', lambda residuals, n_params: 3.0
    )
    monkeypatch.setattr(
        tracking_mod,
        'build_table_renderable',
        lambda **kwargs: render_calls.append(kwargs) or 'renderable',
    )

    class FakeIndicator:
        def update(self, *, label=None, content=None):
            update_calls.append({'label': label, 'content': content})

    tracker = FitProgressTracker()
    tracker._tracking_mode = tracking_mod.TRACKING_MODE_SAMPLER
    tracker._previous_chi2 = 5.0
    tracker._best_chi2 = 5.0

    residuals = np.array([1.0, -1.0], dtype=float)

    assert np.array_equal(tracker.track(residuals, [1.0]), residuals)
    assert tracker.best_chi2 == pytest.approx(3.0)

    tracker.start_timer()
    tracker.stop_timer()
    assert tracker.fitting_time is not None

    tracker.reset()
    tracker._tracking_mode = tracking_mod.TRACKING_MODE_SAMPLER
    assert tracker._headers() == tracking_mod.SAMPLER_HEADERS
    assert tracker._alignments() == tracking_mod.SAMPLER_ALIGNMENTS
    assert tracker._current_elapsed_time() is None
    assert tracker._format_elapsed_time() == ''

    tracker._verbosity = VerbosityEnum.FULL
    tracker._activity_indicator = FakeIndicator()
    tracker._replace_last_tracking_row(['1'])

    assert tracker._df_rows == [['1']]
    assert len(render_calls) == 1
    assert update_calls == [
        {
            'label': tracking_mod.ACTIVITY_LABEL_FITTING,
            'content': 'renderable',
        }
    ]


def test_tracker_final_rows_cover_fallbacks_and_activity_labels():
    import easydiffraction.analysis.fit_helpers.tracking as tracking_mod
    from easydiffraction.analysis.fit_helpers.tracking import FitProgressTracker

    tracker = FitProgressTracker()
    tracker._tracking_mode = tracking_mod.TRACKING_MODE_SAMPLER
    tracker._sampler_total_iterations = 10
    tracker._last_iteration = 8
    tracker._last_sampler_elapsed_time = 2.5

    assert tracker._final_sampler_tracking_row() == ['8/10', '80.0%', '2.50', '', 'sampling']

    tracker._tracking_mode = tracking_mod.TRACKING_MODE_FIT
    tracker._fitting_time = 1.5
    assert tracker._final_fit_tracking_row() == ['8', '1.50', '', '']
    tracker._tracking_mode = tracking_mod.TRACKING_MODE_SAMPLER
    assert tracker._default_activity_label() == tracking_mod.ACTIVITY_LABEL_PROCESSING
    tracker._tracking_mode = tracking_mod.TRACKING_MODE_FIT
    assert tracker._default_activity_label() == tracking_mod.ACTIVITY_LABEL_FITTING
    assert (
        tracker._activity_label_for_sampler_phase('burn-in') == tracking_mod.ACTIVITY_LABEL_BURN_IN
    )
    assert (
        tracker._activity_label_for_sampler_phase('sampling')
        == tracking_mod.ACTIVITY_LABEL_SAMPLING
    )
    assert tracker._activity_label_for_sampler_phase('annealing') == 'annealing'
    assert tracker._activity_label_for_sampler_phase('') == tracking_mod.ACTIVITY_LABEL_PROCESSING


def test_minimizer_base_fit_flow_and_finalize():
    from easydiffraction.analysis.minimizers.base import MinimizerBase

    @dataclass
    class DummyResult:
        success: bool = True

    class DummyMinimizer(MinimizerBase):
        def __init__(self) -> None:
            super().__init__(name='dummy', method='m', max_iterations=5)
            self.synced = False

        def _prepare_solver_args(self, parameters):
            return {'engine_parameters': {'ok': True}}

        def _run_solver(self, objective_function, **kwargs):
            residuals = objective_function(kwargs.get('engine_parameters'))
            self.tracker.track(residuals=np.array(residuals), parameters=[1])
            return DummyResult(success=True)

        def _sync_result_to_parameters(self, parameters, raw_result):
            self.synced = True
            if parameters:
                parameters[0].value = 42

        def _check_success(self, raw_result):
            return getattr(raw_result, 'success', False)

        def _compute_residuals(
            self, engine_params, parameters, structures, experiments, calculator
        ):
            assert engine_params == {'ok': True}
            return np.array([0.0, 0.0])

    minimizer = DummyMinimizer()
    params = [DummyParam(1.0), DummyParam(2.0)]
    objective = minimizer._create_objective_function(
        parameters=params,
        structures=None,
        experiments=None,
        calculator=None,
    )

    result = minimizer.fit(parameters=params, objective_function=objective)

    assert result.success is True
    assert minimizer.synced is True
    assert isinstance(result.parameters, list)
    assert result.parameters[0].value == 42
    assert minimizer.tracker.fitting_time is not None
    assert minimizer.tracker.fitting_time >= 0.0


def test_minimizer_base_create_objective_function_uses_compute_residuals():
    from easydiffraction.analysis.minimizers.base import MinimizerBase

    class Minimizer(MinimizerBase):
        def _prepare_solver_args(self, parameters):
            return {}

        def _run_solver(self, objective_function, **kwargs):
            return None

        def _sync_result_to_parameters(self, parameters, raw_result):
            return None

        def _check_success(self, raw_result):
            return True

        def _compute_residuals(
            self, engine_params, parameters, structures, experiments, calculator
        ):
            return np.array([1.0, 2.0, 3.0])

    minimizer = Minimizer()
    objective = minimizer._create_objective_function(
        parameters=[],
        structures=None,
        experiments=None,
        calculator=None,
    )

    np.testing.assert_allclose(objective({}), np.array([1.0, 2.0, 3.0]))


def test_minimizer_base_fit_stops_tracking_when_solver_prep_fails():
    from easydiffraction.analysis.minimizers.base import MinimizerBase

    class Minimizer(MinimizerBase):
        def __init__(self) -> None:
            super().__init__(name='dummy', method='m', max_iterations=5)
            self.started = False
            self.stopped = False

        def _start_tracking(self, minimizer_name, verbosity=None):
            self.started = True

        def _stop_tracking(self):
            self.stopped = True

        def _prepare_solver_args(self, parameters):
            message = 'prep failed'
            raise ValueError(message)

        def _run_solver(self, objective_function, **kwargs):
            message = 'should not run solver'
            raise AssertionError(message)

        def _sync_result_to_parameters(self, parameters, raw_result):
            return None

        def _check_success(self, raw_result):
            return True

    minimizer = Minimizer()

    with pytest.raises(ValueError, match='prep failed'):
        minimizer.fit(parameters=[DummyParam(1.0)], objective_function=lambda _: np.array([0.0]))

    assert minimizer.started is True
    assert minimizer.stopped is True


def test_minimizer_base_applies_physical_limits_and_warns(monkeypatch):
    from easydiffraction.analysis.minimizers.base import MinimizerBase

    warnings: list[str] = []
    monkeypatch.setattr(
        'easydiffraction.analysis.minimizers.base.log.warning',
        lambda message: warnings.append(message),
    )

    class BoundaryParam(DummyParam):
        def __init__(self) -> None:
            super().__init__(5.0)
            self.unique_name = 'boundary'

        def _physical_lower_bound(self) -> float:
            return 0.0

        def _physical_upper_bound(self) -> float:
            return 10.0

    class DummyResult:
        success = True

    class Minimizer(MinimizerBase):
        def __init__(self) -> None:
            super().__init__(name='dummy', method='m', max_iterations=5)

        def _prepare_solver_args(self, parameters):
            return {'engine_parameters': {}}

        def _run_solver(self, objective_function, **kwargs):
            residuals = objective_function(kwargs.get('engine_parameters'))
            self.tracker.track(residuals=np.array(residuals), parameters=[1])
            return DummyResult()

        def _sync_result_to_parameters(self, parameters, raw_result):
            parameters[0].value = 11.0

        def _check_success(self, raw_result):
            return True

        def _compute_residuals(
            self, engine_params, parameters, structures, experiments, calculator
        ):
            return np.array([0.0, 0.0])

    minimizer = Minimizer()
    parameter = BoundaryParam()
    objective = minimizer._create_objective_function(
        parameters=[parameter],
        structures=None,
        experiments=None,
        calculator=None,
    )

    result = minimizer.fit(
        parameters=[parameter],
        objective_function=objective,
        use_physical_limits=True,
    )

    assert result.success is True
    assert parameter.fit_min == 0.0
    assert parameter.fit_max == 10.0
    assert parameter._outside_physical_limits is True
    assert any('upper bound' in message for message in warnings)
    assert any('physical upper limit' in message for message in warnings)


def test_minimizer_base_rejects_random_seed_when_not_supported():
    from easydiffraction.analysis.minimizers.base import MinimizerBase

    class Minimizer(MinimizerBase):
        def _prepare_solver_args(self, parameters):
            return {'engine_parameters': {}}

        def _run_solver(self, objective_function, **kwargs):
            return object()

        def _sync_result_to_parameters(self, parameters, raw_result):
            return None

        def _check_success(self, raw_result):
            return True

        def _compute_residuals(
            self, engine_params, parameters, structures, experiments, calculator
        ):
            return np.array([0.0])

    minimizer = Minimizer(name='dummy')

    with pytest.raises(
        ValueError,
        match=r"Minimizer 'dummy' does not support random_seed\.",
    ):
        minimizer.fit(parameters=[], objective_function=lambda _: np.array([0.0]), random_seed=7)
