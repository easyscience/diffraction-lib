# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

"""Supplementary unit tests raising coverage for MinimizerBase."""

from dataclasses import FrozenInstanceError

import numpy as np
import pytest

from easydiffraction.analysis.minimizers import base as base_mod
from easydiffraction.analysis.minimizers.base import BOUNDARY_PROXIMITY_FRACTION
from easydiffraction.analysis.minimizers.base import MinimizerBase
from easydiffraction.analysis.minimizers.base import MinimizerFitOptions
from easydiffraction.utils.enums import VerbosityEnum


class _DummyParam:
    """Minimal stand-in for an EasyDiffraction parameter."""

    def __init__(
        self,
        value,
        *,
        fit_min=-np.inf,
        fit_max=np.inf,
        phys_lo=-np.inf,
        phys_hi=np.inf,
        name=None,
    ):
        self.value = value
        self.fit_min = fit_min
        self.fit_max = fit_max
        self.unique_name = name or f'param_{value}'
        self._phys_lo = phys_lo
        self._phys_hi = phys_hi
        self._outside_physical_limits = None

    def _physical_lower_bound(self):
        return self._phys_lo

    def _physical_upper_bound(self):
        return self._phys_hi


class _Minimal(MinimizerBase):
    """Concrete minimizer with trivial abstract-method bodies."""

    def _prepare_solver_args(self, parameters):
        del parameters
        return {}

    def _run_solver(self, objective_function, **kwargs):
        del objective_function, kwargs

    def _sync_result_to_parameters(self, parameters, raw_result):
        del parameters, raw_result

    def _check_success(self, raw_result):
        del raw_result
        return True


@pytest.fixture
def captured_warnings(monkeypatch):
    """Capture messages passed to ``base.log.warning``."""
    messages = []

    def _capture(msg):
        messages.append(msg)

    monkeypatch.setattr(base_mod.log, 'warning', _capture)
    return messages


# ---------------------------------------------------------------------------
# MinimizerFitOptions defaults
# ---------------------------------------------------------------------------


def test_fit_options_defaults():
    options = MinimizerFitOptions()

    assert options.finalize_tracking is True
    assert options.use_physical_limits is False
    assert options.random_seed is None
    assert options.resume is False
    assert options.extra_steps is None


def test_fit_options_is_frozen():
    options = MinimizerFitOptions()

    with pytest.raises(FrozenInstanceError):
        options.resume = True


# ---------------------------------------------------------------------------
# Static helper hooks (default values)
# ---------------------------------------------------------------------------


def test_tracking_mode_default_is_fit():
    assert _Minimal()._tracking_mode() == 'fit'


def test_tracks_progress_via_solver_monitor_default_false():
    assert _Minimal()._tracks_progress_via_solver_monitor() is False


# ---------------------------------------------------------------------------
# _finalize_timing — idempotency / inactive guard (line 104)
# ---------------------------------------------------------------------------


def test_finalize_timing_noop_when_not_tracking():
    minimizer = _Minimal()

    # Tracking never started: should be a no-op and not raise.
    assert minimizer._tracking_active is False
    minimizer._finalize_timing()
    assert minimizer._timing_finalized is False


def test_finalize_timing_noop_when_already_finalized():
    minimizer = _Minimal()
    minimizer._tracking_active = True
    minimizer._timing_finalized = True

    # Already finalized — must not call stop_timer again.
    minimizer.tracker.stop_timer = lambda: (_ for _ in ()).throw(
        AssertionError('stop_timer should not be called')
    )
    minimizer._finalize_timing()


# ---------------------------------------------------------------------------
# _stop_tracking — inactive branch flushes deferred warnings (lines 113-114)
# ---------------------------------------------------------------------------


def test_stop_tracking_when_inactive_emits_deferred_warnings(captured_warnings):
    minimizer = _Minimal()
    minimizer._tracking_active = False
    minimizer._deferred_warning_messages = ['deferred one', 'deferred two']

    minimizer._stop_tracking()

    assert captured_warnings == ['deferred one', 'deferred two']
    assert minimizer._deferred_warning_messages == []


# ---------------------------------------------------------------------------
# _warn_after_tracking — defer vs immediate (lines 123-127)
# ---------------------------------------------------------------------------


def test_warn_after_tracking_defers_while_active(captured_warnings):
    minimizer = _Minimal()
    minimizer._tracking_active = True

    minimizer._warn_after_tracking('hold this')

    # Deferred, not logged yet.
    assert captured_warnings == []
    assert minimizer._deferred_warning_messages == ['hold this']


def test_warn_after_tracking_logs_immediately_when_inactive(captured_warnings):
    minimizer = _Minimal()
    minimizer._tracking_active = False

    minimizer._warn_after_tracking('emit now')

    assert captured_warnings == ['emit now']
    assert minimizer._deferred_warning_messages == []


# ---------------------------------------------------------------------------
# _emit_deferred_warnings — flush order (line 132)
# ---------------------------------------------------------------------------


def test_emit_deferred_warnings_flushes_in_fifo_order(captured_warnings):
    minimizer = _Minimal()
    minimizer._deferred_warning_messages = ['a', 'b', 'c']

    minimizer._emit_deferred_warnings()

    assert captured_warnings == ['a', 'b', 'c']
    assert minimizer._deferred_warning_messages == []


# ---------------------------------------------------------------------------
# _warn_boundary_parameters — unbounded/one-sided + bounded branches
# (lines 254, 261-273)
# ---------------------------------------------------------------------------


def test_warn_boundary_one_sided_lower_bound(captured_warnings):
    # Finite lower bound, infinite upper => span is inf, not finite.
    param = _DummyParam(10.0, fit_min=10.0, fit_max=np.inf, name='lo')

    MinimizerBase._warn_boundary_parameters([param])

    assert len(captured_warnings) == 1
    assert 'lower' in captured_warnings[0]
    assert 'fit_min' in captured_warnings[0]


def test_warn_boundary_one_sided_upper_bound(captured_warnings):
    # Finite upper bound, infinite lower => span not finite.
    param = _DummyParam(5.0, fit_min=-np.inf, fit_max=5.0, name='hi')

    MinimizerBase._warn_boundary_parameters([param])

    assert len(captured_warnings) == 1
    assert 'upper' in captured_warnings[0]
    assert 'fit_max' in captured_warnings[0]


def test_warn_boundary_one_sided_not_near_bound_is_silent(captured_warnings):
    # Value far from the finite one-sided bound: no warning.
    param = _DummyParam(100.0, fit_min=10.0, fit_max=np.inf)

    MinimizerBase._warn_boundary_parameters([param])

    assert captured_warnings == []


def test_warn_boundary_bounded_near_lower(captured_warnings):
    # span = 100, tol = 1.0; value within tol of lower bound.
    param = _DummyParam(0.5, fit_min=0.0, fit_max=100.0, name='lo')

    MinimizerBase._warn_boundary_parameters([param])

    assert len(captured_warnings) == 1
    assert 'lower' in captured_warnings[0]


def test_warn_boundary_bounded_near_upper(captured_warnings):
    param = _DummyParam(99.5, fit_min=0.0, fit_max=100.0, name='hi')

    MinimizerBase._warn_boundary_parameters([param])

    assert len(captured_warnings) == 1
    assert 'upper' in captured_warnings[0]


def test_warn_boundary_bounded_centred_is_silent(captured_warnings):
    # Value in the middle of [0, 100]; comfortably outside both tolerances.
    param = _DummyParam(50.0, fit_min=0.0, fit_max=100.0)

    MinimizerBase._warn_boundary_parameters([param])

    assert captured_warnings == []


def test_warn_boundary_centred_param_followed_by_another(captured_warnings):
    # Two bounded params: the first is centred (no warning, loop continues
    # to the next iteration) and the second sits at its upper bound.
    centred = _DummyParam(50.0, fit_min=0.0, fit_max=100.0)
    edge = _DummyParam(99.9, fit_min=0.0, fit_max=100.0, name='edge')

    MinimizerBase._warn_boundary_parameters([centred, edge])

    assert len(captured_warnings) == 1
    assert 'upper' in captured_warnings[0]
    assert 'edge' in captured_warnings[0]


def test_warn_boundary_zero_span_is_silent(captured_warnings):
    # fit_min == fit_max => span is finite but not > 0: neither branch runs.
    param = _DummyParam(5.0, fit_min=5.0, fit_max=5.0)

    MinimizerBase._warn_boundary_parameters([param])

    assert captured_warnings == []


def test_warn_boundary_uses_proximity_fraction_constant():
    # Sanity-check the documented constant the tolerance derives from.
    assert BOUNDARY_PROXIMITY_FRACTION == 0.01


# ---------------------------------------------------------------------------
# _apply_physical_limits — replace infinite fit bounds (lines 292-300)
# ---------------------------------------------------------------------------


def test_apply_physical_limits_fills_both_infinite_bounds():
    param = _DummyParam(0.5, fit_min=-np.inf, fit_max=np.inf, phys_lo=0.0, phys_hi=1.0)

    MinimizerBase._apply_physical_limits([param])

    assert param.fit_min == 0.0
    assert param.fit_max == 1.0


def test_apply_physical_limits_skips_when_physical_bound_infinite():
    # Physical bounds are infinite => fit bounds remain unchanged.
    param = _DummyParam(0.5, fit_min=-np.inf, fit_max=np.inf, phys_lo=-np.inf, phys_hi=np.inf)

    MinimizerBase._apply_physical_limits([param])

    assert param.fit_min == -np.inf
    assert param.fit_max == np.inf


def test_apply_physical_limits_leaves_finite_fit_bounds_untouched():
    param = _DummyParam(0.5, fit_min=-2.0, fit_max=2.0, phys_lo=0.0, phys_hi=1.0)

    MinimizerBase._apply_physical_limits([param])

    # fit bounds were already finite => physical bounds are not applied.
    assert param.fit_min == -2.0
    assert param.fit_max == 2.0


# ---------------------------------------------------------------------------
# _warn_physical_limit_violations — below/above + flag (lines 320-330)
# ---------------------------------------------------------------------------


def test_warn_physical_violation_below_lower(captured_warnings):
    param = _DummyParam(-1.0, phys_lo=0.0, phys_hi=10.0, name='below')

    MinimizerBase._warn_physical_limit_violations([param])

    assert len(captured_warnings) == 1
    assert 'below' in captured_warnings[0]
    assert param._outside_physical_limits is True


def test_warn_physical_violation_above_upper(captured_warnings):
    param = _DummyParam(11.0, phys_lo=0.0, phys_hi=10.0, name='above')

    MinimizerBase._warn_physical_limit_violations([param])

    assert len(captured_warnings) == 1
    assert 'above' in captured_warnings[0]
    assert param._outside_physical_limits is True


def test_warn_physical_violation_within_limits_clears_flag(captured_warnings):
    param = _DummyParam(5.0, phys_lo=0.0, phys_hi=10.0)
    param._outside_physical_limits = True  # stale True from a prior run

    MinimizerBase._warn_physical_limit_violations([param])

    assert captured_warnings == []
    assert param._outside_physical_limits is False


def test_warn_physical_violation_infinite_limits_no_warning(captured_warnings):
    param = _DummyParam(1e9, phys_lo=-np.inf, phys_hi=np.inf)

    MinimizerBase._warn_physical_limit_violations([param])

    assert captured_warnings == []
    assert param._outside_physical_limits is False


# ---------------------------------------------------------------------------
# _resolve_random_seed — None passthrough vs unsupported raise (lines 356-362)
# ---------------------------------------------------------------------------


def test_resolve_random_seed_none_returns_none():
    minimizer = _Minimal()

    assert minimizer._resolve_random_seed(None) is None
    assert minimizer._resolved_random_seed is None


def test_resolve_random_seed_unsupported_raises_with_name():
    minimizer = _Minimal(name='my-minimizer')

    with pytest.raises(ValueError, match="'my-minimizer' does not support random_seed"):
        minimizer._resolve_random_seed(7)


def test_resolve_random_seed_unsupported_falls_back_to_class_name():
    minimizer = _Minimal()  # no name => uses class name

    with pytest.raises(ValueError, match='_Minimal'):
        minimizer._resolve_random_seed(7)


# ---------------------------------------------------------------------------
# fit — resume + physical-limit + random-seed + method-suffix branches
# (lines 401-403, 406, 411->414, 419)
# ---------------------------------------------------------------------------


def test_fit_resume_unsupported_raises():
    minimizer = _Minimal(name='dummy')

    with pytest.raises(NotImplementedError, match="'dummy' does not support resume"):
        minimizer.fit(
            parameters=[],
            objective_function=lambda _: np.array([0.0]),
            options=MinimizerFitOptions(resume=True),
        )


def test_fit_applies_physical_limits_when_requested():
    applied = []

    class M(_Minimal):
        @staticmethod
        def _apply_physical_limits(parameters):
            applied.append(parameters)

        def _prepare_solver_args(self, parameters):
            del parameters
            return {}

        def _run_solver(self, objective_function, **kwargs):
            del objective_function, kwargs
            return object()

        def _sync_result_to_parameters(self, parameters, raw_result):
            del parameters, raw_result

        def _check_success(self, raw_result):
            del raw_result
            return True

    minimizer = M(name='m')
    params = [_DummyParam(1.0)]
    minimizer.fit(
        parameters=params,
        objective_function=lambda _: np.array([0.0]),
        verbosity=VerbosityEnum.SILENT,
        options=MinimizerFitOptions(use_physical_limits=True),
    )

    assert applied == [params]


def test_fit_injects_resolved_random_seed_into_solver_args():
    seen = {}

    class M(_Minimal):
        def _resolve_random_seed(self, random_seed):
            # Pretend this minimizer supports a seed.
            self._resolved_random_seed = random_seed
            return random_seed

        def _prepare_solver_args(self, parameters):
            del parameters
            return {}

        def _run_solver(self, objective_function, **kwargs):
            del objective_function
            seen.update(kwargs)
            return object()

        def _sync_result_to_parameters(self, parameters, raw_result):
            del parameters, raw_result

        def _check_success(self, raw_result):
            del raw_result
            return True

    minimizer = M(name='m')
    minimizer.fit(
        parameters=[_DummyParam(1.0)],
        objective_function=lambda _: np.array([0.0]),
        verbosity=VerbosityEnum.SILENT,
        options=MinimizerFitOptions(random_seed=123),
    )

    assert seen.get('random_seed') == 123


def test_fit_appends_method_suffix_to_name():
    captured_names = []

    class M(_Minimal):
        def _start_tracking(self, minimizer_name, verbosity=VerbosityEnum.FULL):
            captured_names.append(minimizer_name)

        def _stop_tracking(self):
            pass

        def _prepare_solver_args(self, parameters):
            del parameters
            return {}

        def _run_solver(self, objective_function, **kwargs):
            del objective_function, kwargs
            return object()

        def _sync_result_to_parameters(self, parameters, raw_result):
            del parameters, raw_result

        def _check_success(self, raw_result):
            del raw_result
            return True

    minimizer = M(name='Solver', method='leastsq')
    minimizer.fit(
        parameters=[_DummyParam(1.0)],
        objective_function=lambda _: np.array([0.0]),
    )

    assert captured_names == ['Solver (leastsq)']


def test_fit_does_not_double_append_method_suffix():
    captured_names = []

    class M(_Minimal):
        def _start_tracking(self, minimizer_name, verbosity=VerbosityEnum.FULL):
            captured_names.append(minimizer_name)

        def _stop_tracking(self):
            pass

        def _prepare_solver_args(self, parameters):
            del parameters
            return {}

        def _run_solver(self, objective_function, **kwargs):
            del objective_function, kwargs
            return object()

        def _sync_result_to_parameters(self, parameters, raw_result):
            del parameters, raw_result

        def _check_success(self, raw_result):
            del raw_result
            return True

    # Name already contains '(leastsq)' => the suffix is not re-appended.
    minimizer = M(name='Solver (leastsq)', method='leastsq')
    minimizer.fit(
        parameters=[_DummyParam(1.0)],
        objective_function=lambda _: np.array([0.0]),
    )

    assert captured_names == ['Solver (leastsq)']


def test_fit_uses_default_name_when_unnamed():
    captured_names = []

    class M(_Minimal):
        def _start_tracking(self, minimizer_name, verbosity=VerbosityEnum.FULL):
            captured_names.append(minimizer_name)

        def _stop_tracking(self):
            pass

        def _prepare_solver_args(self, parameters):
            del parameters
            return {}

        def _run_solver(self, objective_function, **kwargs):
            del objective_function, kwargs
            return object()

        def _sync_result_to_parameters(self, parameters, raw_result):
            del parameters, raw_result

        def _check_success(self, raw_result):
            del raw_result
            return True

    minimizer = M()  # no name, no method
    minimizer.fit(
        parameters=[_DummyParam(1.0)],
        objective_function=lambda _: np.array([0.0]),
    )

    assert captured_names == ['Unnamed Minimizer']
