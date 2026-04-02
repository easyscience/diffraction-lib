# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause


def test_module_import():
    import easydiffraction.analysis.fitting as MUT

    expected_module_name = 'easydiffraction.analysis.fitting'
    actual_module_name = MUT.__name__
    assert expected_module_name == actual_module_name


def test_fitter_early_exit_when_no_params(capsys, monkeypatch):
    from easydiffraction.analysis.fitting import Fitter

    class DummyStructures:
        free_parameters = []

    class DummyExperiment:
        parameters = []

    class DummyMin:
        tracker = type('T', (), {'track': staticmethod(lambda a, b: a)})()

        def fit(self, params, obj, verbosity=None):
            return None

    f = Fitter()
    # Avoid creating a real minimizer
    f.minimizer = DummyMin()
    f.fit(structures=DummyStructures(), experiments=[DummyExperiment()])
    out = capsys.readouterr().out
    assert 'No parameters selected for fitting' in out


def test_fitter_fit_does_not_call_process_fit_results(monkeypatch):
    """Test that Fitter.fit() does not automatically call _process_fit_results.

    The display of results is now the responsibility of Analysis.show_fit_results().
    """
    from easydiffraction.analysis.fitting import Fitter

    process_called = {'called': False}

    class DummyParam:
        value = 1.0
        _fit_start_value = None

    class DummyStructures:
        free_parameters = [DummyParam()]

    class DummyExperiment:
        parameters = []

    class MockFitResults:
        pass

    class DummyMin:
        tracker = type('T', (), {'track': staticmethod(lambda a, b: a)})()

        def fit(self, params, obj, verbosity=None):
            return MockFitResults()

        def _sync_result_to_parameters(self, params, engine_params):
            pass

    f = Fitter()
    f.minimizer = DummyMin()

    # Track if _process_fit_results is called
    original_process = f._process_fit_results

    def mock_process(*args, **kwargs):
        process_called['called'] = True
        return original_process(*args, **kwargs)

    monkeypatch.setattr(f, '_process_fit_results', mock_process)

    f.fit(structures=DummyStructures(), experiments=[DummyExperiment()])

    assert not process_called['called'], (
        'Fitter.fit() should not call _process_fit_results automatically. '
        'Use Analysis.show_fit_results() instead.'
    )
    assert f.results is not None, 'Fitter.fit() should still set results'
