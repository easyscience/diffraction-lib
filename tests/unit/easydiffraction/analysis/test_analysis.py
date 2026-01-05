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
        sample_models = object()
        _varname = 'proj'

    return P()


def test_show_current_calculator_and_minimizer_prints(capsys):
    from easydiffraction.analysis.analysis import Analysis

    a = Analysis(project=_make_project_with_names([]))
    a.show_current_calculator()
    a.show_current_minimizer()
    out = capsys.readouterr().out
    assert 'Current calculator' in out
    assert 'cryspy' in out
    assert 'Current minimizer' in out
    assert 'lmfit (leastsq)' in out


def test_current_calculator_setter_success_and_unknown(monkeypatch, capsys):
    from easydiffraction.analysis import calculators as calc_pkg
    from easydiffraction.analysis.analysis import Analysis

    a = Analysis(project=_make_project_with_names([]))

    # Success path
    monkeypatch.setattr(
        calc_pkg.factory.CalculatorFactory,
        'create_calculator',
        lambda name: object(),
    )
    a.current_calculator = 'pdffit'
    out = capsys.readouterr().out
    assert 'Current calculator changed to' in out
    assert a.current_calculator == 'pdffit'

    # Unknown path (create_calculator returns None): no change
    monkeypatch.setattr(
        calc_pkg.factory.CalculatorFactory,
        'create_calculator',
        lambda name: None,
    )
    a.current_calculator = 'unknown'
    assert a.current_calculator == 'pdffit'


def test_fit_modes_show_and_switch_to_joint(monkeypatch, capsys):
    from easydiffraction.analysis.analysis import Analysis

    a = Analysis(project=_make_project_with_names(['e1', 'e2']))

    a.show_available_fit_modes()
    a.show_current_fit_mode()
    out1 = capsys.readouterr().out
    assert 'Available fit modes' in out1
    assert 'Current fit mode' in out1
    assert 'single' in out1

    a.fit_mode = 'joint'
    out2 = capsys.readouterr().out
    assert 'Current fit mode changed to' in out2
    assert a.fit_mode == 'joint'


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

    def mock_process_fit_results(sample_models, experiments):
        process_called['called'] = True
        process_called['args'] = (sample_models, experiments)

    # Create a mock project with sample_models and experiments
    class MockProject:
        sample_models = object()
        experiments = object()
        _varname = 'proj'

        class experiments_cls:
            names = []

        experiments = experiments_cls()

    project = MockProject()
    project.sample_models = object()
    project.experiments.names = []

    a = Analysis(project=project)

    # Set up fit_results so show_fit_results doesn't return early
    a.fit_results = object()

    # Mock the fitter's _process_fit_results method
    monkeypatch.setattr(a.fitter, '_process_fit_results', mock_process_fit_results)

    a.show_fit_results()

    assert process_called['called'], '_process_fit_results should be called'
