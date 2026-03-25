# SPDX-FileCopyrightText: 2021-2026 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
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
    assert 'lmfit' in out


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


def test_fit_mode_type_getter(capsys):
    from easydiffraction.analysis.analysis import Analysis

    a = Analysis(project=_make_project_with_names([]))
    assert a.fit_mode_type == 'default'


def test_show_supported_fit_mode_types(capsys):
    from easydiffraction.analysis.analysis import Analysis

    a = Analysis(project=_make_project_with_names([]))
    a.show_supported_fit_mode_types()
    out = capsys.readouterr().out
    assert 'default' in out


def test_show_current_fit_mode_type(capsys):
    from easydiffraction.analysis.analysis import Analysis

    a = Analysis(project=_make_project_with_names([]))
    a.show_current_fit_mode_type()
    out = capsys.readouterr().out
    assert 'Current fit-mode type' in out
    assert 'default' in out


def test_fit_mode_type_setter_valid(capsys):
    from easydiffraction.analysis.analysis import Analysis

    a = Analysis(project=_make_project_with_names([]))
    a.fit_mode_type = 'default'
    assert a.fit_mode_type == 'default'


def test_fit_mode_type_setter_invalid(capsys):
    from easydiffraction.analysis.analysis import Analysis

    a = Analysis(project=_make_project_with_names([]))
    a.fit_mode_type = 'nonexistent'
    out = capsys.readouterr().out
    assert 'Unsupported' in out
    # Type should remain unchanged
    assert a.fit_mode_type == 'default'


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
    assert 'show_fit_results()' in out


def test_show_fit_results_warns_when_no_results(capsys):
    """Test that show_fit_results logs a warning when fit() has not been run."""
    from easydiffraction.analysis.analysis import Analysis

    a = Analysis(project=_make_project_with_names([]))

    # Ensure fit_results is not set
    assert not hasattr(a, 'fit_results') or a.fit_results is None

    a.show_fit_results()
    out = capsys.readouterr().out
    assert 'No fit results available' in out


def test_show_fit_results_calls_process_fit_results(monkeypatch):
    """Test that show_fit_results delegates to fitter._process_fit_results."""
    from easydiffraction.analysis.analysis import Analysis

    # Track if _process_fit_results was called
    process_called = {'called': False, 'args': None}

    def mock_process_fit_results(structures, experiments):
        process_called['called'] = True
        process_called['args'] = (structures, experiments)

    # Create a mock project with structures and experiments
    class MockProject:
        structures = object()
        experiments = object()
        _varname = 'proj'

        class experiments_cls:
            names = []

        experiments = experiments_cls()

    project = MockProject()
    project.structures = object()
    project.experiments.names = []

    a = Analysis(project=project)

    # Set up fit_results so show_fit_results doesn't return early
    a.fit_results = object()

    # Mock the fitter's _process_fit_results method
    monkeypatch.setattr(a.fitter, '_process_fit_results', mock_process_fit_results)

    a.show_fit_results()

    assert process_called['called'], '_process_fit_results should be called'
