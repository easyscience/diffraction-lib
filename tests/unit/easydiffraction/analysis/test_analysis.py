# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause


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


def test_show_current_minimizer_prints(capsys):
    from easydiffraction.analysis.analysis import Analysis

    a = Analysis(project=_make_project_with_names([]))
    a.show_current_minimizer()
    out = capsys.readouterr().out
    assert 'Current minimizer' in out
    assert 'lmfit (leastsq)' in out


def test_fit_mode_category_and_joint_fit_experiments(monkeypatch, capsys):
    from easydiffraction.analysis.analysis import Analysis

    a = Analysis(project=_make_project_with_names(['e1', 'e2']))

    # Default fit mode is 'single'
    assert a.fit_mode.mode.value == 'single'

    # Switch to joint
    a.fit_mode.mode = 'joint'
    assert a.fit_mode.mode.value == 'joint'

    # joint_fit_experiments exists but is empty until fit() populates it
    assert len(a.joint_fit_experiments) == 0


def test_analysis_help(capsys):
    from easydiffraction.analysis.analysis import Analysis

    a = Analysis(project=_make_project_with_names([]))
    a.help()
    out = capsys.readouterr().out
    assert "Help for 'Analysis'" in out
    assert 'fit_mode' in out
    assert 'current_minimizer' in out
    assert 'Properties' in out
    assert 'Methods' in out
    assert 'fit()' in out


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
