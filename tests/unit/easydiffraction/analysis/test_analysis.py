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


def test_show_minimizer_types_prints(capsys):
    from easydiffraction.analysis.analysis import Analysis

    a = Analysis(project=_make_project_with_names([]))
    a.fit.show_minimizer_types()
    out = capsys.readouterr().out
    assert 'Minimizer types' in out
    assert 'lmfit (leastsq)' in out


def test_fit_mode_category_and_joint_fit_experiments(monkeypatch, capsys):
    from easydiffraction.analysis.analysis import Analysis

    a = Analysis(project=_make_project_with_names(['e1', 'e2']))

    # Default fit mode is 'single'
    assert a.fit.mode.value == 'single'

    # Switch to joint
    a.fit.mode = 'joint'
    assert a.fit.mode.value == 'joint'

    # joint_fit_experiments exists but is empty until fit() populates it
    assert len(a.joint_fit_experiments) == 0


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
    assert 'fit_sequential()' in out


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
