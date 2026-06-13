# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from types import SimpleNamespace

import numpy as np
import pytest

from easydiffraction.analysis.fitting import FitterFitOptions
from easydiffraction.analysis.fitting import _resolve_fit_result_chi_square
from easydiffraction.analysis.fitting import _resolve_fit_result_iterations
from easydiffraction.analysis.fitting import _resolve_fit_result_message

# ---------------------------------------------------------------------------
# FitterFitOptions.as_minimizer_options
# ---------------------------------------------------------------------------


def test_as_minimizer_options_maps_fields_and_forces_no_finalize():
    options = FitterFitOptions(
        use_physical_limits=True,
        random_seed=42,
        resume=True,
        extra_steps=7,
    )

    minimizer_options = options.as_minimizer_options()

    # finalize_tracking is always forced off; the fitter owns finalization.
    assert minimizer_options.finalize_tracking is False
    assert minimizer_options.use_physical_limits is True
    assert minimizer_options.random_seed == 42
    assert minimizer_options.resume is True
    assert minimizer_options.extra_steps == 7


def test_fitter_fit_options_defaults():
    options = FitterFitOptions()

    assert options.use_physical_limits is False
    assert options.random_seed is None
    assert options.resume is False
    assert options.extra_steps is None


# ---------------------------------------------------------------------------
# _resolve_fit_result_message
# ---------------------------------------------------------------------------


def test_resolve_message_prefers_existing_message():
    results = SimpleNamespace(message='converged', engine_result=object())

    assert _resolve_fit_result_message(results) == 'converged'


def test_resolve_message_falls_back_to_engine_result_attribute():
    results = SimpleNamespace(
        message='',
        engine_result=SimpleNamespace(message='engine says hi'),
    )

    assert _resolve_fit_result_message(results) == 'engine says hi'


def test_resolve_message_handles_missing_engine_attribute():
    results = SimpleNamespace(message='', engine_result=object())

    assert _resolve_fit_result_message(results) == ''


def test_resolve_message_handles_none_engine_message():
    results = SimpleNamespace(
        message='',
        engine_result=SimpleNamespace(message=None),
    )

    assert _resolve_fit_result_message(results) == ''


# ---------------------------------------------------------------------------
# _resolve_fit_result_iterations
# ---------------------------------------------------------------------------


def test_resolve_iterations_prefers_existing_value():
    results = SimpleNamespace(iterations=5, engine_result=object())

    assert _resolve_fit_result_iterations(results) == 5


def test_resolve_iterations_reads_first_available_engine_attribute():
    # 'nfev' is checked before 'nit'; the first non-None wins.
    results = SimpleNamespace(
        iterations=0,
        engine_result=SimpleNamespace(nfev=11, nit=99),
    )

    assert _resolve_fit_result_iterations(results) == 11


def test_resolve_iterations_skips_none_attributes_in_order():
    results = SimpleNamespace(
        iterations=0,
        engine_result=SimpleNamespace(nfev=None, nit=None, iterations=None, niter=33),
    )

    assert _resolve_fit_result_iterations(results) == 33


def test_resolve_iterations_returns_zero_when_nothing_found():
    results = SimpleNamespace(iterations=0, engine_result=object())

    assert _resolve_fit_result_iterations(results) == 0


# ---------------------------------------------------------------------------
# _resolve_fit_result_chi_square
# ---------------------------------------------------------------------------


def test_resolve_chi_square_prefers_existing_value():
    results = SimpleNamespace(chi_square=2.5, engine_result=object())

    assert _resolve_fit_result_chi_square(results) == 2.5


def test_resolve_chi_square_uses_engine_chisqr():
    results = SimpleNamespace(
        chi_square=None,
        engine_result=SimpleNamespace(chisqr=3.0),
    )

    assert _resolve_fit_result_chi_square(results) == 3.0


def test_resolve_chi_square_uses_scalar_fun():
    results = SimpleNamespace(
        chi_square=None,
        engine_result=SimpleNamespace(chisqr=None, fun=4.0),
    )

    assert _resolve_fit_result_chi_square(results) == 4.0


def test_resolve_chi_square_sums_squares_of_array_fun():
    results = SimpleNamespace(
        chi_square=None,
        engine_result=SimpleNamespace(chisqr=None, fun=np.array([3.0, 4.0])),
    )

    # 3**2 + 4**2 = 25
    assert _resolve_fit_result_chi_square(results) == 25.0


def test_resolve_chi_square_returns_none_when_no_source():
    results = SimpleNamespace(chi_square=None, engine_result=object())

    assert _resolve_fit_result_chi_square(results) is None


def test_resolve_chi_square_returns_none_when_fun_is_none():
    results = SimpleNamespace(
        chi_square=None,
        engine_result=SimpleNamespace(chisqr=None, fun=None),
    )

    assert _resolve_fit_result_chi_square(results) is None


# ---------------------------------------------------------------------------
# Fitter helpers and branches
# ---------------------------------------------------------------------------


def _make_fitter_with_dummy_minimizer():
    from easydiffraction.analysis.fitting import Fitter

    fitter = Fitter()
    fitter.minimizer = SimpleNamespace()
    return fitter


def _make_param(name):
    from easydiffraction.core.validation import AttributeSpec
    from easydiffraction.core.variable import Parameter
    from easydiffraction.io.cif.handler import CifHandler

    return Parameter(
        name=name,
        value_spec=AttributeSpec(default=0.0),
        cif_handler=CifHandler(names=[f'_param.{name}']),
    )


def test_collect_fit_parameters_filters_constrained_and_fixed():
    from easydiffraction.analysis.fitting import Fitter

    free = _make_param('free')
    free.free = True

    fixed = _make_param('fixed')
    fixed.free = False

    constrained = _make_param('constrained')
    constrained.free = True
    constrained._user_constrained = True

    experiment = SimpleNamespace(parameters=[free, fixed, constrained, 'not-a-parameter'])
    structures = SimpleNamespace(free_parameters=[])

    collected = Fitter._collect_fit_parameters(structures, [experiment])

    assert collected == [free]


def test_collect_fit_parameters_includes_structure_free_parameters():
    from easydiffraction.analysis.fitting import Fitter

    struct_param = _make_param('struct')
    expt_param = _make_param('expt')
    expt_param.free = True

    experiment = SimpleNamespace(parameters=[expt_param])
    structures = SimpleNamespace(free_parameters=[struct_param])

    collected = Fitter._collect_fit_parameters(structures, [experiment])

    assert collected == [struct_param, expt_param]


def test_fit_no_params_resume_raises_value_error():
    fitter = _make_fitter_with_dummy_minimizer()

    with pytest.raises(ValueError, match='Resume requires the same free parameters'):
        fitter.fit(
            structures=_NoStructures(),
            experiments=[],
            options=FitterFitOptions(resume=True),
        )


def test_fit_no_params_clears_analysis_state(monkeypatch):
    from easydiffraction.utils.logging import log

    monkeypatch.setattr(log, '_reaction', log.Reaction.WARN, raising=True)

    fitter = _make_fitter_with_dummy_minimizer()
    events = []
    analysis = SimpleNamespace(
        _clear_persisted_fit_state=lambda: events.append('clear'),
        fit_results='stale',
    )

    fitter.fit(structures=_NoStructures(), experiments=[], analysis=analysis)

    assert events == ['clear']
    assert analysis.fit_results is None
    assert fitter.results is None


def test_fit_resume_with_params_invokes_resume_validation(monkeypatch):
    from easydiffraction.analysis.fitting import Fitter

    param = SimpleNamespace(value=1.0, unique_name='a', _fit_start_value=None)

    class DummyMin:
        def __init__(self):
            self.tracker = SimpleNamespace(track=lambda residuals, parameters: residuals)

        def fit(self, params, obj, verbosity=None, **kwargs):
            del params, obj, verbosity, kwargs
            return SimpleNamespace(
                message='ok',
                iterations=1,
                chi_square=1.0,
                minimizer_type=None,
                engine_result=object(),
                fitting_time=2.0,
            )

        def _finalize_timing(self):
            return None

        def _stop_tracking(self):
            return None

    fitter = Fitter()
    fitter.minimizer = DummyMin()
    monkeypatch.setattr(
        fitter,
        '_collect_fit_parameters',
        lambda structures, experiments: [param],
    )

    validate_calls = []

    def fake_validate(*, params, analysis):
        validate_calls.append((params, analysis))

    # resume path runs the resume validation instead of capturing state.
    monkeypatch.setattr(fitter, '_validate_resume_parameter_set', fake_validate)

    persisted = [SimpleNamespace(parameter_unique_name=SimpleNamespace(value='a'))]
    analysis = SimpleNamespace(
        fit_parameters=persisted,
        fit_result=SimpleNamespace(),
        _store_fit_result_projection=lambda results, experiments, fitted_parameters: None,
    )

    fitter.fit(
        structures=_NoStructures(),
        experiments=[],
        analysis=analysis,
        options=FitterFitOptions(resume=True),
    )

    assert len(validate_calls) == 1
    assert validate_calls[0][0] == [param]
    assert validate_calls[0][1] is analysis


def test_validate_resume_parameter_set_no_persisted_names_is_noop():
    from easydiffraction.analysis.fitting import Fitter

    analysis = SimpleNamespace(fit_parameters=[])
    param = SimpleNamespace(unique_name='a')

    # No persisted names -> returns without raising.
    Fitter._validate_resume_parameter_set(params=[param], analysis=analysis)


def test_validate_resume_parameter_set_matching_names_ok():
    from easydiffraction.analysis.fitting import Fitter

    persisted = [SimpleNamespace(parameter_unique_name=SimpleNamespace(value='a'))]
    analysis = SimpleNamespace(fit_parameters=persisted)
    param = SimpleNamespace(unique_name='a')

    Fitter._validate_resume_parameter_set(params=[param], analysis=analysis)


def test_validate_resume_parameter_set_mismatch_raises():
    from easydiffraction.analysis.fitting import Fitter

    persisted = [SimpleNamespace(parameter_unique_name=SimpleNamespace(value='a'))]
    analysis = SimpleNamespace(fit_parameters=persisted)
    param = SimpleNamespace(unique_name='b')

    with pytest.raises(ValueError, match='differs from the saved emcee chain'):
        Fitter._validate_resume_parameter_set(params=[param], analysis=analysis)


def test_set_minimizer_sidecar_path_noop_when_analysis_none():
    fitter = _make_fitter_with_dummy_minimizer()
    fitter.minimizer._sidecar_path = 'unchanged'

    fitter._set_minimizer_sidecar_path(None)

    assert fitter.minimizer._sidecar_path == 'unchanged'


def test_set_minimizer_sidecar_path_noop_when_no_attribute():
    fitter = _make_fitter_with_dummy_minimizer()
    # Minimizer without _sidecar_path attribute -> early return, no crash.
    analysis = SimpleNamespace(project=SimpleNamespace(metadata=SimpleNamespace(path=None)))

    fitter._set_minimizer_sidecar_path(analysis)

    assert not hasattr(fitter.minimizer, '_sidecar_path')


def test_set_minimizer_sidecar_path_none_when_no_project_path():
    fitter = _make_fitter_with_dummy_minimizer()
    fitter.minimizer._sidecar_path = 'unset'
    analysis = SimpleNamespace(project=SimpleNamespace(metadata=SimpleNamespace(path=None)))

    fitter._set_minimizer_sidecar_path(analysis)

    assert fitter.minimizer._sidecar_path is None


def test_set_minimizer_sidecar_path_builds_results_path(tmp_path):
    fitter = _make_fitter_with_dummy_minimizer()
    fitter.minimizer._sidecar_path = None
    analysis = SimpleNamespace(
        project=SimpleNamespace(metadata=SimpleNamespace(path=tmp_path)),
    )

    fitter._set_minimizer_sidecar_path(analysis)

    assert fitter.minimizer._sidecar_path == tmp_path / 'analysis' / 'results.h5'


def test_backfill_persisted_fitting_time_noop_when_analysis_none():
    fitter = _make_fitter_with_dummy_minimizer()
    fitter.results = SimpleNamespace(fitting_time=1.0)

    # Should not raise even though no analysis is provided.
    fitter._backfill_persisted_fitting_time(None)


def test_backfill_persisted_fitting_time_noop_when_results_none():
    fitter = _make_fitter_with_dummy_minimizer()
    fitter.results = None
    analysis = SimpleNamespace(fit_result=SimpleNamespace())

    fitter._backfill_persisted_fitting_time(analysis)


def test_backfill_persisted_fitting_time_sets_time_when_callable():
    fitter = _make_fitter_with_dummy_minimizer()
    fitter.results = SimpleNamespace(fitting_time=9.5)
    captured = {}
    fit_result = SimpleNamespace(_set_fitting_time=lambda value: captured.setdefault('t', value))
    analysis = SimpleNamespace(fit_result=fit_result)

    fitter._backfill_persisted_fitting_time(analysis)

    assert captured == {'t': 9.5}


def test_backfill_persisted_fitting_time_skips_when_not_callable():
    fitter = _make_fitter_with_dummy_minimizer()
    fitter.results = SimpleNamespace(fitting_time=9.5)
    # fit_result has no _set_fitting_time -> getattr returns None -> skipped.
    analysis = SimpleNamespace(fit_result=SimpleNamespace())

    # Should not raise.
    fitter._backfill_persisted_fitting_time(analysis)


def test_postprocess_fit_results_noop_when_results_none():
    fitter = _make_fitter_with_dummy_minimizer()
    fitter.results = None

    # Should return immediately without touching analysis.
    fitter._postprocess_fit_results(
        analysis=object(),
        experiments=[],
        fitted_parameters=[],
    )


def test_postprocess_fit_results_normalizes_fields_without_analysis():
    fitter = _make_fitter_with_dummy_minimizer()
    fitter.selection = 'lmfit'
    fitter.results = SimpleNamespace(
        message='',
        iterations=0,
        chi_square=None,
        minimizer_type=None,
        engine_result=SimpleNamespace(message='done', nfev=7, chisqr=2.0),
    )

    fitter._postprocess_fit_results(
        analysis=None,
        experiments=[],
        fitted_parameters=[],
    )

    assert fitter.results.message == 'done'
    assert fitter.results.iterations == 7
    assert fitter.results.chi_square == 2.0
    assert fitter.results.minimizer_type == 'lmfit'


def test_postprocess_fit_results_stores_projection_when_analysis_present():
    fitter = _make_fitter_with_dummy_minimizer()
    fitter.selection = 'lmfit'
    fitter.results = SimpleNamespace(
        message='ok',
        iterations=3,
        chi_square=1.0,
        minimizer_type=None,
        engine_result=object(),
    )
    stored = {}
    analysis = SimpleNamespace(
        _store_fit_result_projection=lambda results, experiments, fitted_parameters: stored.update(
            results=results,
            experiments=experiments,
            fitted_parameters=fitted_parameters,
        ),
    )
    experiments = ['expt']
    fitted = ['param']

    fitter._postprocess_fit_results(
        analysis=analysis,
        experiments=experiments,
        fitted_parameters=fitted,
    )

    assert stored['results'] is fitter.results
    assert stored['experiments'] == experiments
    assert stored['fitted_parameters'] == fitted


# ---------------------------------------------------------------------------
# _process_fit_results
# ---------------------------------------------------------------------------


def test_process_fit_results_displays_when_results_present(monkeypatch):
    fitter = _make_fitter_with_dummy_minimizer()

    monkeypatch.setattr(
        'easydiffraction.analysis.fitting.get_reliability_inputs',
        lambda structures, experiments: (
            np.array([1.0]),
            np.array([1.1]),
            np.array([0.1]),
        ),
    )

    displayed = {}

    def display_results(*, y_obs, y_calc, y_err, f_obs, f_calc):
        displayed.update(
            y_obs=y_obs,
            y_calc=y_calc,
            y_err=y_err,
            f_obs=f_obs,
            f_calc=f_calc,
        )

    fitter.results = SimpleNamespace(display_results=display_results)

    fitter._process_fit_results(structures=object(), experiments=[])

    np.testing.assert_allclose(displayed['y_obs'], np.array([1.0]))
    np.testing.assert_allclose(displayed['y_calc'], np.array([1.1]))
    np.testing.assert_allclose(displayed['y_err'], np.array([0.1]))
    assert displayed['f_obs'] is None
    assert displayed['f_calc'] is None


def test_process_fit_results_skips_display_when_no_results(monkeypatch):
    fitter = _make_fitter_with_dummy_minimizer()
    fitter.results = None

    called = {'display': False}

    monkeypatch.setattr(
        'easydiffraction.analysis.fitting.get_reliability_inputs',
        lambda structures, experiments: (None, None, None),
    )

    # Even though get_reliability_inputs runs, display must not be invoked.
    fitter._process_fit_results(structures=object(), experiments=[])

    assert called['display'] is False


# ---------------------------------------------------------------------------
# _residual_function
# ---------------------------------------------------------------------------


def test_residual_function_updates_structures_and_analysis(monkeypatch):
    fitter = _make_fitter_with_dummy_minimizer()

    events = []

    def sync(parameters, engine_params):
        events.append('sync')

    fitter.minimizer._sync_result_to_parameters = sync
    fitter.minimizer.tracker = SimpleNamespace(
        track=lambda residuals, parameters: residuals * 10.0,
    )

    structure = SimpleNamespace(
        _update_categories=lambda *, called_by_minimizer=False: events.append((
            'struct',
            called_by_minimizer,
        ))
    )
    analysis = SimpleNamespace(
        _update_categories=lambda *, called_by_minimizer=False: events.append((
            'analysis',
            called_by_minimizer,
        ))
    )
    experiment = SimpleNamespace(
        _update_categories=lambda *, called_by_minimizer=False: events.append((
            'expt',
            called_by_minimizer,
        ))
    )

    monkeypatch.setattr(
        'easydiffraction.analysis.fitting.intensity_category_for',
        lambda experiment: SimpleNamespace(
            intensity_calc=np.array([1.0]),
            intensity_meas=np.array([3.0]),
            intensity_meas_su=np.array([1.0]),
        ),
    )

    residuals = fitter._residual_function(
        engine_params={},
        parameters=[],
        structures=[structure],
        experiments=[experiment],
        weights=None,
        analysis=analysis,
    )

    # diff = (3 - 1) / 1 = 2, weight = 1 (single experiment), tracker *10.
    np.testing.assert_allclose(residuals, np.array([20.0]))
    assert ('struct', True) in events
    assert ('analysis', True) in events
    assert ('expt', True) in events
    assert 'sync' in events


def test_residual_function_applies_normalized_weights(monkeypatch):
    fitter = _make_fitter_with_dummy_minimizer()
    fitter.minimizer._sync_result_to_parameters = lambda parameters, engine_params: None
    fitter.minimizer.tracker = SimpleNamespace(track=lambda residuals, parameters: residuals)

    def make_experiment(meas):
        return SimpleNamespace(
            _update_categories=lambda *, called_by_minimizer=False: None,
            _meas=meas,
        )

    experiments = [make_experiment(3.0), make_experiment(5.0)]

    def category_for(experiment):
        return SimpleNamespace(
            intensity_calc=np.array([1.0]),
            intensity_meas=np.array([experiment._meas]),
            intensity_meas_su=np.array([1.0]),
        )

    monkeypatch.setattr(
        'easydiffraction.analysis.fitting.intensity_category_for',
        category_for,
    )

    # Weights [1, 3] normalized to sum=2 (num experiments): [0.5, 1.5].
    residuals = fitter._residual_function(
        engine_params={},
        parameters=[],
        structures=[],
        experiments=experiments,
        weights=np.array([1.0, 3.0]),
        analysis=None,
    )

    # diff0 = (3-1)/1 * sqrt(0.5); diff1 = (5-1)/1 * sqrt(1.5).
    expected = np.array([2.0 * np.sqrt(0.5), 4.0 * np.sqrt(1.5)])
    np.testing.assert_allclose(residuals, expected)


def test_residual_function_handles_minimizer_without_solver_monitor_attr(monkeypatch):
    fitter = _make_fitter_with_dummy_minimizer()
    fitter.minimizer._sync_result_to_parameters = lambda parameters, engine_params: None
    # No _tracks_progress_via_solver_monitor attribute -> default lambda False
    # path -> tracker.track is used.
    fitter.minimizer.tracker = SimpleNamespace(
        track=lambda residuals, parameters: residuals + 100.0,
    )

    experiment = SimpleNamespace(
        _update_categories=lambda *, called_by_minimizer=False: None,
    )

    monkeypatch.setattr(
        'easydiffraction.analysis.fitting.intensity_category_for',
        lambda experiment: SimpleNamespace(
            intensity_calc=np.array([1.0]),
            intensity_meas=np.array([2.0]),
            intensity_meas_su=np.array([1.0]),
        ),
    )

    residuals = fitter._residual_function(
        engine_params={},
        parameters=[],
        structures=[],
        experiments=[experiment],
        weights=None,
        analysis=None,
    )

    np.testing.assert_allclose(residuals, np.array([101.0]))


def test_build_objective_function_delegates_to_residual(monkeypatch):
    fitter = _make_fitter_with_dummy_minimizer()

    captured = {}

    def fake_residual(*, engine_params, parameters, structures, experiments, weights, analysis):
        captured.update(
            engine_params=engine_params,
            parameters=parameters,
            structures=structures,
            experiments=experiments,
            weights=weights,
            analysis=analysis,
        )
        return np.array([7.0])

    monkeypatch.setattr(fitter, '_residual_function', fake_residual)

    params = ['p']
    structures = 's'
    experiments = ['e']
    weights = np.array([1.0])
    analysis = 'a'

    objective = fitter._build_objective_function(
        params=params,
        structures=structures,
        experiments=experiments,
        weights=weights,
        analysis=analysis,
    )

    result = objective({'x': 1.0})

    np.testing.assert_allclose(result, np.array([7.0]))
    assert captured['engine_params'] == {'x': 1.0}
    assert captured['parameters'] is params
    assert captured['structures'] is structures
    assert captured['experiments'] is experiments
    assert captured['weights'] is weights
    assert captured['analysis'] is analysis


class _NoStructures:
    """Structures double with no structures and no free parameters."""

    free_parameters: list = []

    def __iter__(self):
        return iter([])
