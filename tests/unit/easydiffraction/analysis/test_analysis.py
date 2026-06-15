# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from types import SimpleNamespace


def test_module_import():
    import easydiffraction.analysis.analysis as MUT

    expected_module_name = 'easydiffraction.analysis.analysis'
    actual_module_name = MUT.__name__
    assert expected_module_name == actual_module_name


def _make_project_with_names(names):
    class ExpCol:
        def __init__(self, names):
            self._names = names

        @property
        def names(self):
            return self._names

    class P:
        experiments = ExpCol(names)
        structures = object()
        metadata = SimpleNamespace(path=None)
        _varname = 'proj'

    return P()


def _make_parameter(name, value):
    from easydiffraction.core.validation import AttributeSpec
    from easydiffraction.core.variable import Parameter
    from easydiffraction.io.cif.handler import TagSpec

    return Parameter(
        name=name,
        value_spec=AttributeSpec(default=value),
        tags=TagSpec(edi_names=[f'_{name}.value']),
    )


def _make_project_with_parameters(parameters):
    class ParamContainer:
        def __init__(self, parameters):
            self.parameters = list(parameters)

    class Experiments(ParamContainer):
        names = []

        def values(self):
            return []

    return SimpleNamespace(
        structures=ParamContainer(parameters),
        experiments=Experiments([]),
        metadata=SimpleNamespace(path=None),
        _varname='proj',
    )


def _posterior_field_values(row):
    return (
        row.posterior_best_sample_value.value,
        row.posterior_median.value,
        row.posterior_uncertainty.value,
        row.posterior_interval_68_low.value,
        row.posterior_interval_68_high.value,
        row.posterior_interval_95_low.value,
        row.posterior_interval_95_high.value,
        row.posterior_gelman_rubin.value,
        row.posterior_effective_sample_size_bulk.value,
    )


def test_minimizer_show_supported_prints(capsys):
    from easydiffraction.analysis.analysis import Analysis

    a = Analysis(project=_make_project_with_names([]))
    a.minimizer.show_supported()
    out = capsys.readouterr().out
    assert 'Minimizer types' in out
    assert 'lmfit (leastsq)' in out


def test_analysis_extension_descriptors_keep_save_tags_and_iucr_names():
    from easydiffraction.analysis.analysis import Analysis
    from easydiffraction.datablocks.experiment.categories.calculator import Calculator

    analysis = Analysis(project=_make_project_with_names([]))
    calculator = Calculator(type='cryspy')

    assert analysis.minimizer._type._tags.edi_names == ['_minimizer.type']
    assert analysis.minimizer._type._tags.cif_name == '_easydiffraction_minimizer.type'
    assert analysis.fitting_mode._type._tags.edi_names == ['_fitting_mode.type']
    assert analysis.fitting_mode._type._tags.cif_name == '_easydiffraction_fitting_mode.type'
    assert calculator._type._tags.edi_names == ['_calculator.type']
    assert calculator._type._tags.cif_name == '_easydiffraction_calculator.type'


def test_fit_mode_category_and_joint_fit(monkeypatch, capsys):
    from easydiffraction.analysis.analysis import Analysis

    a = Analysis(project=_make_project_with_names(['e1', 'e2']))

    # Default fit mode is 'single'
    assert a.fitting_mode.type == 'single'

    # Switch to joint
    a.fitting_mode.type = 'joint'
    assert a.fitting_mode.type == 'joint'

    # joint_fit exists but is empty until fit() populates it
    assert len(a.joint_fit) == 0


def test_restore_raises_when_bayesian_result_kind_with_lsq_minimizer():
    """Restoring a Bayesian projection onto an LSQ minimizer must raise.

    See minimizer-category-consolidation_review-8 finding F5: a CIF
    where ``_fit_result.result_kind = bayesian`` but
    ``_minimizer.type = lmfit (leastsq)`` would previously
    crash with ``AttributeError: 'LmfitLeastsqMinimizer' object has no
    attribute 'point_estimate_name'`` deep inside the restore path.
    We now raise a clear ``ValueError`` at the gate.
    """
    import pytest

    from easydiffraction.analysis.analysis import Analysis
    from easydiffraction.analysis.enums import FitResultKindEnum

    a = Analysis(project=_make_project_with_names([]))
    a.minimizer.type = 'lmfit (leastsq)'
    a.fit_result._set_result_kind(FitResultKindEnum.BAYESIAN.value)
    a._set_has_persisted_fit_state(value=True)

    with pytest.raises(
        ValueError,
        match=r"_minimizer\.type = 'lmfit \(leastsq\)'",
    ) as excinfo:
        a._restore_fit_results_from_projection()

    message = str(excinfo.value)
    assert 'Bayesian' in message
    assert FitResultKindEnum.BAYESIAN.value in message


def test_minimizer_selector_swap_warns_for_different_defaults(monkeypatch):
    from easydiffraction.analysis import analysis as analysis_mod
    from easydiffraction.analysis.analysis import Analysis

    a = Analysis(project=_make_project_with_names([]))
    warnings: list[str] = []
    monkeypatch.setattr(analysis_mod.log, 'warning', warnings.append)

    a.minimizer.type = 'bumps (dream)'

    assert a.minimizer.type == 'bumps (dream)'
    # Inter-family swap should split warnings into "removed"/"added"
    # lines rather than emitting "<not available>" sentinels per
    # finding F3.
    removed_warning = next(w for w in warnings if 'removes these settings' in w)
    added_warning = next(w for w in warnings if 'adds these settings' in w)
    assert removed_warning == (
        'Switching minimizer type removes these settings:\n• max_iterations'
    )
    assert added_warning.splitlines() == [
        'Switching minimizer type adds these settings with defaults:',
        '• burn_in_steps=600',
        "• initialization_method='latin_hypercube'",
        '• parallel_workers=0',
        '• population_size=4',
        '• random_seed=None',
        '• sampling_steps=3000',
        '• thinning_interval=1',
    ]
    assert not any('<not available>' in w for w in warnings)


def test_undo_fit_restores_scalars_and_clears_fit_outputs():
    from easydiffraction.analysis.analysis import Analysis
    from easydiffraction.core.posterior import PosteriorParameterSummary

    length_a = _make_parameter('length_a', 3.90)
    length_b = _make_parameter('length_b', 3.95)
    project = _make_project_with_parameters([length_a, length_b])
    analysis = Analysis(project=project)

    length_a.value = 4.10
    length_a.uncertainty = 0.08
    length_b.value = 4.15
    length_b.uncertainty = 0.09
    for parameter, start_value, start_uncertainty in (
        (length_a, 3.90, 0.02),
        (length_b, 3.95, 0.03),
    ):
        parameter.fit_min = 3.5
        parameter.fit_max = 4.5
        parameter._set_bounds_uncertainty_multiplier(4.0)
        summary = PosteriorParameterSummary(
            unique_name=parameter.unique_name,
            display_name=parameter.name,
            best_sample_value=parameter.value,
            median=parameter.value,
            standard_deviation=0.01,
            interval_68=(parameter.value - 0.01, parameter.value + 0.01),
            interval_95=(parameter.value - 0.02, parameter.value + 0.02),
            ess_bulk=100.0,
            r_hat=1.01,
        )
        parameter._set_posterior(summary)
        analysis.fit_parameters.create(
            parameter_unique_name=parameter.unique_name,
            fit_min=parameter.fit_min,
            fit_max=parameter.fit_max,
            bounds_uncertainty_multiplier=4.0,
            start_value=start_value,
            start_uncertainty=start_uncertainty,
        )
        analysis.fit_parameters[parameter.unique_name]._set_posterior_summary(summary)

    analysis.fit_result._set_result_kind('deterministic')
    analysis.fit_result._set_success(value=True)
    analysis.fit_parameter_correlations.create(
        source_kind='deterministic',
        parameter_unique_name_i=length_a.unique_name,
        parameter_unique_name_j=length_b.unique_name,
        correlation=0.25,
    )
    analysis._persisted_fit_state_sidecar = {'posterior': {'draws': object()}}
    analysis._set_has_persisted_fit_state(value=True)
    analysis.fit_results = object()
    analysis.fitter.results = object()

    outcome = analysis.undo_fit()

    assert outcome.restored_parameter_names == (length_a.unique_name, length_b.unique_name)
    assert outcome.cleared_fit_result is True
    assert outcome.cleared_sidecar is True
    assert outcome.was_no_op is False
    assert length_a.value == 3.90
    assert length_a.uncertainty == 0.02
    assert length_a.posterior is None
    assert length_b.value == 3.95
    assert length_b.uncertainty == 0.03
    assert length_b.posterior is None
    assert _posterior_field_values(analysis.fit_parameters[length_a.unique_name]) == (None,) * 9
    assert _posterior_field_values(analysis.fit_parameters[length_b.unique_name]) == (None,) * 9
    assert analysis.fit_results is None
    assert analysis.fitter.results is None
    assert analysis._has_persisted_fit_state() is False
    assert len(analysis.fit_parameter_correlations) == 0
    assert analysis._persisted_fit_state_sidecar == {}


def test_undo_fit_second_call_is_noop(monkeypatch):
    from easydiffraction.analysis import analysis as analysis_mod
    from easydiffraction.analysis.analysis import Analysis

    parameter = _make_parameter('scale', 1.0)
    project = _make_project_with_parameters([parameter])
    analysis = Analysis(project=project)
    parameter.value = 1.5
    analysis.fit_parameters.create(
        parameter_unique_name=parameter.unique_name,
        fit_min=0.0,
        fit_max=2.0,
        start_value=1.0,
        start_uncertainty=0.1,
    )
    analysis.fit_result._set_result_kind('deterministic')
    analysis._set_has_persisted_fit_state(value=True)
    messages: list[str] = []
    monkeypatch.setattr(analysis_mod.log, 'info', messages.append)

    first_outcome = analysis.undo_fit()
    second_outcome = analysis.undo_fit()

    assert first_outcome.was_no_op is False
    assert second_outcome.was_no_op is True
    assert second_outcome.restored_parameter_names == ()
    assert messages == ['No fit to undo.']


def test_undo_fit_never_fit_project_is_noop(monkeypatch):
    from easydiffraction.analysis import analysis as analysis_mod
    from easydiffraction.analysis.analysis import Analysis

    analysis = Analysis(project=_make_project_with_parameters([_make_parameter('scale', 1.0)]))
    messages: list[str] = []
    monkeypatch.setattr(analysis_mod.log, 'info', messages.append)

    outcome = analysis.undo_fit()

    assert outcome.was_no_op is True
    assert outcome.restored_parameter_names == ()
    assert outcome.cleared_fit_result is False
    assert outcome.cleared_sidecar is False
    assert messages == ['No fit to undo.']


def test_undo_fit_loaded_no_movement_fit_is_not_noop():
    from easydiffraction.analysis.analysis import Analysis

    parameter = _make_parameter('scale', 1.0)
    project = _make_project_with_parameters([parameter])
    analysis = Analysis(project=project)
    analysis.fit_parameters.create(
        parameter_unique_name=parameter.unique_name,
        fit_min=0.0,
        fit_max=2.0,
        start_value=1.0,
        start_uncertainty=0.1,
    )
    analysis.fit_result._set_result_kind('deterministic')
    analysis._set_has_persisted_fit_state(value=True)

    outcome = analysis.undo_fit()

    assert outcome.was_no_op is False
    assert outcome.restored_parameter_names == (parameter.unique_name,)
    assert outcome.cleared_fit_result is True
    assert analysis._has_persisted_fit_state() is False


def test_minimizer_type_invalid_assignment_raises_and_preserves_state():
    import pytest

    from easydiffraction.analysis.analysis import Analysis

    a = Analysis(project=_make_project_with_names([]))
    initial_type = a.minimizer.type

    with pytest.raises(ValueError, match='Unsupported minimizer type'):
        a.minimizer.type = 'bogus-minimizer'

    assert a.minimizer.type == initial_type


def test_store_posterior_projection_persists_resolved_random_seed():
    from easydiffraction.analysis.analysis import Analysis
    from easydiffraction.analysis.categories.fit_result.bayesian import BayesianFitResult
    from easydiffraction.analysis.fit_helpers.bayesian import BayesianFitResults

    analysis = Analysis(project=_make_project_with_names([]))
    analysis._fit_result._parent = None
    analysis._fit_result = BayesianFitResult()
    analysis._fit_result._parent = analysis
    results = BayesianFitResults(
        success=True,
        convergence_diagnostics={},
        sampler_settings={'random_seed': 12345},
        posterior_samples=None,
        posterior_parameter_summaries=[],
    )

    analysis._store_posterior_fit_projection(results)

    assert analysis.fit_result.resolved_random_seed.value == 12345


def test_restored_bayesian_diagnostics_reconstruct_passed_status():
    from easydiffraction.analysis.analysis import Analysis
    from easydiffraction.analysis.categories.fit_result.bayesian import BayesianFitResult

    analysis = Analysis(project=_make_project_with_names([]))
    analysis._fit_result._parent = None
    analysis._fit_result = BayesianFitResult()
    analysis._fit_result._parent = analysis
    analysis.fit_result._set_gelman_rubin_max(1.002)
    analysis.fit_result._set_effective_sample_size_min(8810.5)
    analysis.fit_result._set_acceptance_rate_mean(0.3)

    diagnostics = analysis._restored_bayesian_convergence_diagnostics(
        sample_shape=(10001, 16, 5),
        n_parameters=5,
    )

    assert diagnostics['converged'] is True
    assert diagnostics['max_r_hat'] == 1.002
    assert diagnostics['min_ess_bulk'] == 8810.5
    assert diagnostics['acceptance_rate_mean'] == 0.3
    assert diagnostics['n_draws'] == 10001
    assert diagnostics['n_chains'] == 16
    assert diagnostics['n_parameters'] == 5


def test_restored_bayesian_sampler_settings_reconstruct_sample_count():
    from easydiffraction.analysis.analysis import Analysis

    analysis = Analysis(project=_make_project_with_names([]))
    analysis.minimizer.type = 'emcee'

    settings = analysis._restored_bayesian_sampler_settings(
        {
            'nsteps': 10000,
            'nburn': 2000,
            'thin': 1,
            'nwalkers': 16,
            'parallel_workers': 0,
            'initialization_method': 'ball',
            'proposal_moves': 'de',
        },
        random_seed=123,
        n_parameters=5,
    )

    assert settings['nsteps'] == 10000
    assert settings['nburn'] == 2000
    assert settings['thin'] == 1
    assert settings['nwalkers'] == 16
    assert settings['parallel_workers'] == 0
    assert settings['initialization_method'] == 'ball'
    assert settings['proposal_moves'] == 'de'
    assert settings['samples'] == 800000
    assert settings['random_seed'] == 123


def test_emcee_fit_requires_saved_project_for_new_and_resume_runs():
    import pytest

    from easydiffraction.analysis.analysis import Analysis

    analysis = Analysis(project=_make_project_with_names([]))
    analysis.minimizer.type = 'emcee'

    with pytest.raises(ValueError, match='emcee requires a saved project'):
        analysis.fit()

    with pytest.raises(ValueError, match='emcee requires a saved project'):
        analysis.fit(resume=True)


def test_restored_bayesian_reduced_chi_square_recovers_from_log_posterior(monkeypatch):
    from easydiffraction.analysis.analysis import Analysis
    from easydiffraction.analysis.categories.fit_result.bayesian import BayesianFitResult

    analysis = Analysis(project=_make_project_with_names([]))
    analysis._fit_result._parent = None
    analysis._fit_result = BayesianFitResult()
    analysis._fit_result._parent = analysis
    analysis.fit_result._set_best_log_posterior(-50.0)
    monkeypatch.setattr(analysis, '_fit_data_point_count', lambda experiments: 102)

    reduced_chi_square = analysis._restored_bayesian_reduced_chi_square(
        float('nan'),
        restored_parameters=[object(), object()],
    )

    assert reduced_chi_square == 1.0


def test_fit_interrupt_cleans_state_and_prints_message(monkeypatch, capsys):
    from easydiffraction.analysis import analysis as analysis_mod
    from easydiffraction.analysis.analysis import Analysis

    events: list[object] = []

    class FakeStopControl:
        def __init__(self, *, verbosity: object) -> None:
            del verbosity

        def __enter__(self) -> object:
            events.append('enter')
            return self

        def __exit__(self, exc_type, exc_value, traceback) -> None:
            del exc_value
            del traceback
            events.append(exc_type)

    analysis = Analysis(project=_make_project_with_names([]))
    analysis.project.verbosity = SimpleNamespace(fit=SimpleNamespace(value='full'))
    analysis.fit_results = object()
    analysis.fitter.results = object()

    monkeypatch.setattr(
        analysis_mod,
        'notebook_fit_stop_control',
        FakeStopControl,
    )
    monkeypatch.setattr(
        analysis,
        '_run_single',
        lambda **kwargs: (_ for _ in ()).throw(KeyboardInterrupt),
    )
    monkeypatch.setattr(
        analysis,
        '_prepare_results_sidecar_for_new_fit',
        lambda: events.append('sidecar-cleanup'),
    )

    analysis.fit()

    assert events == ['enter', KeyboardInterrupt, 'sidecar-cleanup']
    assert analysis.fit_results is None
    assert analysis.fitter.results is None
    assert 'Fitting stopped by user.' in capsys.readouterr().out


def test_fit_resume_defaults_extra_steps_to_sampling_steps(monkeypatch, tmp_path):
    from easydiffraction.analysis.analysis import Analysis

    analysis = Analysis(project=_make_project_with_names(['e1']))
    analysis.project.verbosity = SimpleNamespace(fit=SimpleNamespace(value='silent'))
    analysis.project.metadata = SimpleNamespace(path=tmp_path)
    analysis.minimizer.type = 'emcee'
    analysis.minimizer.sampling_steps = 123
    captured: dict[str, object] = {}

    monkeypatch.setattr(analysis, '_has_resumable_emcee_sidecar', lambda: True)
    monkeypatch.setattr(
        analysis,
        '_run_single',
        lambda **kwargs: captured.update(kwargs),
    )

    analysis.fit(resume=True)

    assert captured == {'resume': True, 'extra_steps': 123}


def test_fit_resume_preserves_explicit_extra_steps(monkeypatch, tmp_path):
    from easydiffraction.analysis.analysis import Analysis

    analysis = Analysis(project=_make_project_with_names(['e1']))
    analysis.project.verbosity = SimpleNamespace(fit=SimpleNamespace(value='silent'))
    analysis.project.metadata = SimpleNamespace(path=tmp_path)
    analysis.minimizer.type = 'emcee'
    analysis.minimizer.sampling_steps = 123
    captured: dict[str, object] = {}

    monkeypatch.setattr(analysis, '_has_resumable_emcee_sidecar', lambda: True)
    monkeypatch.setattr(
        analysis,
        '_run_single',
        lambda **kwargs: captured.update(kwargs),
    )

    analysis.fit(resume=True, extra_steps=10)

    assert captured == {'resume': True, 'extra_steps': 10}


def test_fit_resume_missing_sidecar_raises(
    monkeypatch,
    tmp_path,
):
    import pytest

    from easydiffraction.analysis.analysis import Analysis

    analysis = Analysis(project=_make_project_with_names(['e1']))
    analysis.project.verbosity = SimpleNamespace(fit=SimpleNamespace(value='silent'))
    analysis.project.metadata = SimpleNamespace(path=tmp_path)
    analysis.minimizer.type = 'emcee'

    monkeypatch.setattr(
        analysis,
        '_run_single',
        lambda **kwargs: None,
    )

    with pytest.raises(ValueError, match=r'no saved.*resumable chain'):
        analysis.fit(resume=True)


def test_dream_fit_resume_defaults_extra_steps_to_sampling_steps(monkeypatch, tmp_path):
    from easydiffraction.analysis.analysis import Analysis

    analysis = Analysis(project=_make_project_with_names(['e1']))
    analysis.project.verbosity = SimpleNamespace(fit=SimpleNamespace(value='silent'))
    analysis.project.metadata = SimpleNamespace(path=tmp_path)
    analysis.minimizer.type = 'bumps (dream)'
    analysis.minimizer.sampling_steps = 77
    captured: dict[str, object] = {}

    monkeypatch.setattr(analysis, '_has_resumable_dream_sidecar', lambda: True)
    monkeypatch.setattr(
        analysis,
        '_run_single',
        lambda **kwargs: captured.update(kwargs),
    )

    analysis.fit(resume=True)

    assert captured == {'resume': True, 'extra_steps': 77}


def test_dream_fit_resume_missing_sidecar_raises(monkeypatch, tmp_path):
    import pytest

    from easydiffraction.analysis.analysis import Analysis

    analysis = Analysis(project=_make_project_with_names(['e1']))
    analysis.project.verbosity = SimpleNamespace(fit=SimpleNamespace(value='silent'))
    analysis.project.metadata = SimpleNamespace(path=tmp_path)
    analysis.minimizer.type = 'bumps (dream)'

    monkeypatch.setattr(analysis, '_has_resumable_dream_sidecar', lambda: False)
    monkeypatch.setattr(analysis, '_run_single', lambda **kwargs: None)

    with pytest.raises(ValueError, match=r'no saved.*resumable chain'):
        analysis.fit(resume=True)


def test_has_resumable_dream_sidecar_detects_state_group(tmp_path):
    import h5py

    from easydiffraction.analysis.analysis import Analysis
    from easydiffraction.analysis.minimizers.bumps_dream import DREAM_STATE_GROUP

    analysis = Analysis(project=_make_project_with_names([]))
    analysis.project.metadata = SimpleNamespace(path=tmp_path)
    analysis.minimizer.type = 'bumps (dream)'

    # No sidecar file yet.
    assert analysis._has_resumable_dream_sidecar() is False

    analysis_dir = tmp_path / 'analysis'
    analysis_dir.mkdir(parents=True)
    sidecar_path = analysis_dir / 'mcmc.h5'

    # Sidecar without the dream_state group.
    with h5py.File(sidecar_path, 'w') as handle:
        handle.create_group('posterior')
    assert analysis._has_resumable_dream_sidecar() is False

    # Sidecar with the dream_state group.
    with h5py.File(sidecar_path, 'a') as handle:
        handle.create_group(DREAM_STATE_GROUP)
    assert analysis._has_resumable_dream_sidecar() is True


def test_default_resume_extra_steps_reads_sampling_steps():
    from easydiffraction.analysis.analysis import Analysis

    analysis = Analysis(project=_make_project_with_names([]))
    analysis.minimizer.type = 'bumps (dream)'
    analysis.minimizer.sampling_steps = 42

    assert analysis._default_resume_extra_steps() == 42


def test_fitting_mode_type_invalid_assignment_raises_and_preserves_state():
    import pytest

    from easydiffraction.analysis.analysis import Analysis

    a = Analysis(project=_make_project_with_names([]))
    initial_type = a.fitting_mode.type

    with pytest.raises(ValueError, match='Unsupported fitting mode'):
        a.fitting_mode.type = 'bogus-mode'

    assert a.fitting_mode.type == initial_type


def test_cif_restore_path_tolerates_invalid_minimizer_type(monkeypatch):
    from easydiffraction.analysis import analysis as analysis_mod
    from easydiffraction.analysis.analysis import Analysis

    a = Analysis(project=_make_project_with_names([]))
    initial_type = a.minimizer.type
    warnings: list[str] = []
    monkeypatch.setattr(analysis_mod.log, 'warning', warnings.append)

    # CIF-restore path uses strict=False so bad data warns instead of
    # raising — kept tolerant for partially-broken saved projects.
    a._set_minimizer_type('bogus-minimizer')

    assert a.minimizer.type == initial_type
    assert any('Unsupported minimizer type' in w for w in warnings)


def test_analysis_help(capsys):
    from easydiffraction.analysis.analysis import Analysis

    a = Analysis(project=_make_project_with_names([]))
    a.help()
    out = capsys.readouterr().out
    assert 'fit' in out
    assert 'display' in out
    assert 'Properties' in out
    assert 'Methods' in out
    assert 'fit()' in out
    assert 'fitting_mode' in out


def test_analysis_display_help(capsys):
    from easydiffraction.analysis.analysis import Analysis

    a = Analysis(project=_make_project_with_names([]))
    a.display.help()
    out = capsys.readouterr().out
    assert 'all_params()' in out
    assert 'fit_results()' in out
    assert 'how_to_access_parameters()' in out


def test_display_fit_results_warns_when_no_results(capsys):
    """Test that display.fit_results logs a warning when fit() has not been run."""
    from easydiffraction.analysis.analysis import Analysis

    a = Analysis(project=_make_project_with_names([]))

    # Ensure fit_results is not set
    assert not hasattr(a, 'fit_results') or a.fit_results is None

    a.display.fit_results()
    out = capsys.readouterr().out
    assert 'No fit results available' in out


def test_display_fit_results_calls_process_fit_results(monkeypatch):
    """Test that display.fit_results delegates to fitter._process_fit_results."""
    from easydiffraction.analysis.analysis import Analysis

    # Track if _process_fit_results was called
    process_called = {'called': False, 'args': None}

    def mock_process_fit_results(structures, experiments):
        process_called['called'] = True
        process_called['args'] = (structures, experiments)

    # Create a mock project with structures and experiments
    class MockProject:
        structures = object()
        _varname = 'proj'

        class experiments_cls:
            names = []

            def values(self):
                return []

        experiments = experiments_cls()

    project = MockProject()
    project.structures = object()
    project.experiments.names = []

    a = Analysis(project=project)

    # Set up fit_results so display.fit_results doesn't return early
    a.fit_results = object()

    # Mock the fitter's _process_fit_results method
    monkeypatch.setattr(a.fitter, '_process_fit_results', mock_process_fit_results)

    a.display.fit_results()

    assert process_called['called'], '_process_fit_results should be called'


def test_fit_single_short_reuses_tracker_display_handle(monkeypatch):
    from easydiffraction.analysis.analysis import Analysis
    from easydiffraction.analysis.fitting import FitterFitOptions
    from easydiffraction.utils.enums import VerbosityEnum

    class Handle:
        def __init__(self) -> None:
            self.closed = False

        def close(self) -> None:
            self.closed = True

    class Experiments:
        def __init__(self) -> None:
            self.names = ['e1']

        def __getitem__(self, name: str) -> object:
            del name
            return object()

    class Tracker:
        def __init__(self) -> None:
            self.best_iteration = 7
            self.display_handles: list[object | None] = []

        def _set_shared_display_handle(self, display_handle: object | None) -> None:
            self.display_handles.append(display_handle)

    project = SimpleNamespace(
        experiments=Experiments(),
        structures=object(),
        _varname='proj',
    )
    analysis = Analysis(project=project)
    tracker = Tracker()
    analysis.fitter.minimizer = SimpleNamespace(tracker=tracker)
    analysis.fitter.results = None

    handle = Handle()
    short_display_handles: list[object | None] = []

    def fake_make_display_handle() -> Handle:
        return handle

    def fake_fit(
        structures: object,
        experiments: list[object],
        *,
        analysis: object,
        verbosity: object,
        options: FitterFitOptions,
    ) -> None:
        del (
            structures,
            experiments,
            analysis,
            verbosity,
            options,
        )
        analysis_obj = fake_fit.analysis_obj
        analysis_obj.fitter.results = SimpleNamespace(
            reduced_chi_square=1.23,
            success=True,
            parameters=[],
        )

    fake_fit.analysis_obj = analysis

    def fake_update_short_table(
        self,
        short_rows: list[list[str]],
        expt_name: str,
        results: object,
        display_handle: object | None,
    ) -> None:
        del self, expt_name, results
        short_rows.append(['e1', '1.23', '7', '✅'])
        short_display_handles.append(display_handle)

    monkeypatch.setattr(
        'easydiffraction.analysis.analysis.make_display_handle', fake_make_display_handle
    )
    monkeypatch.setattr(analysis, '_snapshot_params', lambda expt_name, results: None)
    monkeypatch.setattr(analysis.fitter, 'fit', fake_fit)
    monkeypatch.setattr(Analysis, '_fit_single_update_short_table', fake_update_short_table)

    analysis._fit_single(
        VerbosityEnum.SHORT,
        project.structures,
        project.experiments,
        fit_options=FitterFitOptions(),
    )

    assert tracker.display_handles == [handle, None]
    assert short_display_handles == [handle]
    assert handle.closed is True


def test_run_sequential_sets_mode_and_saves_project(monkeypatch, tmp_path):
    from easydiffraction.analysis.analysis import Analysis

    project = SimpleNamespace(
        metadata=SimpleNamespace(path=tmp_path),
        experiments=SimpleNamespace(values=list),
        save_calls=0,
        _varname='proj',
    )

    def save() -> None:
        project.save_calls += 1

    project.save = save

    analysis = Analysis(project=project)
    analysis.sequential_fit.data_dir.value = 'scans'
    analysis.sequential_fit.file_pattern.value = '*.xye'
    analysis.sequential_fit.max_workers.value = 'auto'
    analysis.sequential_fit.chunk_size.value = '.'
    analysis.sequential_fit.reverse.value = True

    calls: list[tuple[str, object]] = []

    def fake_fit_sequential(
        *,
        analysis: object,
        data_dir: str,
        max_workers: int | str,
        chunk_size: int | None,
        file_pattern: str,
        reverse: bool,
    ) -> None:
        calls.append(('analysis', analysis))
        calls.append(('data_dir', data_dir))
        calls.append(('max_workers', max_workers))
        calls.append(('chunk_size', chunk_size))
        calls.append(('file_pattern', file_pattern))
        calls.append(('reverse', reverse))

    monkeypatch.setattr('easydiffraction.analysis.sequential.fit_sequential', fake_fit_sequential)
    monkeypatch.setattr(
        analysis, '_update_categories', lambda: calls.append(('update_categories', None))
    )
    monkeypatch.setattr(
        analysis, '_resolve_sequential_data_dir', lambda: tmp_path / 'resolved-scans'
    )
    analysis.fit_results = object()
    analysis.fitter.results = object()

    analysis._run_sequential()

    assert analysis.fitting_mode.type == 'sequential'
    analysis_cif = analysis.as_cif
    assert '_fitting_mode.type sequential' in analysis_cif
    assert '_sequential_fit.data_dir scans' in analysis_cif
    assert '_sequential_fit.file_pattern *.xye' in analysis_cif
    assert calls == [
        ('update_categories', None),
        ('analysis', analysis),
        ('data_dir', str(tmp_path / 'resolved-scans')),
        ('max_workers', 'auto'),
        ('chunk_size', None),
        ('file_pattern', '*.xye'),
        ('reverse', True),
        ('update_categories', None),
    ]
    assert project.save_calls == 1
    assert analysis.fit_results is None
    assert analysis.fitter.results is None


def test_calculate_forces_structure_and_experiment_updates():
    # Regression: editing a structure marks only the structure dirty, so
    # a dependent experiment's pattern stayed stale on the next
    # calculate(). calculate() must force-refresh both so structure edits
    # (e.g. cell.length_a) are reflected, like experiment edits already
    # were.
    from easydiffraction.analysis.analysis import Analysis

    calls: list[tuple[str, bool]] = []

    def _stub(label):
        ns = SimpleNamespace()
        ns._update_categories = lambda *, force=False, _l=label: calls.append((_l, force))
        return ns

    class _Project:
        structures = [_stub('structure')]
        experiments = [_stub('experiment')]
        metadata = SimpleNamespace(path=None)
        _varname = 'proj'

    Analysis.calculate(SimpleNamespace(project=_Project()))

    assert calls == [('structure', True), ('experiment', True)]
