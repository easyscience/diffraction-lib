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
        _varname = 'proj'

    return P()


def test_show_supported_minimizer_types_prints(capsys):
    from easydiffraction.analysis.analysis import Analysis

    a = Analysis(project=_make_project_with_names([]))
    a.show_supported_minimizer_types()
    out = capsys.readouterr().out
    assert 'Minimizer types' in out
    assert 'lmfit (leastsq)' in out


def test_fit_mode_category_and_joint_fit(monkeypatch, capsys):
    from easydiffraction.analysis.analysis import Analysis

    a = Analysis(project=_make_project_with_names(['e1', 'e2']))

    # Default fit mode is 'single'
    assert a.fitting_mode_type == 'single'

    # Switch to joint
    a.fitting_mode_type = 'joint'
    assert a.fitting_mode_type == 'joint'

    # joint_fit exists but is empty until fit() populates it
    assert len(a.joint_fit) == 0


def test_restore_raises_when_bayesian_result_kind_with_lsq_minimizer():
    """Restoring a Bayesian projection onto an LSQ minimizer must raise.

    See minimizer-category-consolidation_review-8 finding F5: a CIF
    where ``_fit_result.result_kind = bayesian`` but
    ``_fitting.minimizer_type = lmfit (leastsq)`` would previously
    crash with ``AttributeError: 'LmfitLeastsqMinimizer' object has no
    attribute 'point_estimate_name'`` deep inside the restore path.
    We now raise a clear ``ValueError`` at the gate.
    """
    import pytest

    from easydiffraction.analysis.analysis import Analysis
    from easydiffraction.analysis.enums import FitResultKindEnum

    a = Analysis(project=_make_project_with_names([]))
    a.minimizer_type = 'lmfit (leastsq)'
    a.fit_result._set_result_kind(FitResultKindEnum.BAYESIAN.value)
    a._set_has_persisted_fit_state(value=True)

    with pytest.raises(ValueError) as excinfo:
        a._restore_fit_results_from_projection()

    message = str(excinfo.value)
    assert 'lmfit (leastsq)' in message
    assert 'Bayesian' in message
    assert FitResultKindEnum.BAYESIAN.value in message


def test_minimizer_type_swap_warns_for_different_defaults(monkeypatch):
    from easydiffraction.analysis import analysis as analysis_mod
    from easydiffraction.analysis.analysis import Analysis

    a = Analysis(project=_make_project_with_names([]))
    warnings: list[str] = []
    monkeypatch.setattr(analysis_mod.log, 'warning', warnings.append)

    a.minimizer_type = 'bumps (dream)'

    assert a.minimizer_type == 'bumps (dream)'
    # Inter-family swap should split warnings into "removed"/"added"
    # lines rather than emitting "<not available>" sentinels per
    # finding F3.
    assert any(
        'removes these settings' in w and 'max_iterations' in w for w in warnings
    )
    assert any(
        'adds these settings with defaults' in w and 'sampling_steps' in w
        for w in warnings
    )
    assert not any('<not available>' in w for w in warnings)


def test_analysis_help(capsys):
    from easydiffraction.analysis.analysis import Analysis

    a = Analysis(project=_make_project_with_names([]))
    a.help()
    out = capsys.readouterr().out
    assert "Help for 'Analysis'" in out
    assert 'fit' in out
    assert 'display' in out
    assert 'Properties' in out
    assert 'Methods' in out
    assert 'fit()' in out
    assert 'show_supported_fitting_mode_types()' in out


def test_analysis_display_help(capsys):
    from easydiffraction.analysis.analysis import Analysis

    a = Analysis(project=_make_project_with_names([]))
    a.display.help()
    out = capsys.readouterr().out
    assert "Help for 'AnalysisDisplay'" in out
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
        use_physical_limits: bool,
        random_seed: int | None,
    ) -> None:
        del structures, experiments, analysis, verbosity, use_physical_limits, random_seed
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
        use_physical_limits=False,
        random_seed=None,
    )

    assert tracker.display_handles == [handle, None]
    assert short_display_handles == [handle]
    assert handle.closed is True


def test_run_sequential_sets_mode_and_saves_project(monkeypatch, tmp_path):
    from easydiffraction.analysis.analysis import Analysis

    project = SimpleNamespace(
        info=SimpleNamespace(path=tmp_path),
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

    assert analysis.fitting_mode_type == 'sequential'
    analysis_cif = analysis.as_cif
    assert '_fitting.mode_type sequential' in analysis_cif
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
