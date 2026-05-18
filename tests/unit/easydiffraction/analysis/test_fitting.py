# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from types import SimpleNamespace

from easydiffraction.utils.enums import VerbosityEnum


def test_module_import():
    import easydiffraction.analysis.fitting as MUT

    expected_module_name = 'easydiffraction.analysis.fitting'
    actual_module_name = MUT.__name__
    assert expected_module_name == actual_module_name


def test_fitter_early_exit_when_no_params(capsys, monkeypatch):
    from easydiffraction.analysis.fitting import Fitter

    class DummyStructure:
        _need_categories_update = False

        def _update_categories(self):
            pass

    class DummyStructures:
        free_parameters = []

        def __iter__(self):
            return iter([DummyStructure()])

    class DummyExperiment:
        parameters = []

    class DummyMin:
        tracker = type('T', (), {'track': staticmethod(lambda a, b: a)})()

        def fit(self, params, obj, verbosity=None, **kwargs):
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

    class DummyStructure:
        _need_categories_update = False

        def _update_categories(self):
            pass

    class DummyStructures:
        free_parameters = [DummyParam()]

        def __iter__(self):
            return iter([DummyStructure()])

    class DummyExperiment:
        parameters = []

    class MockFitResults:
        def __init__(self):
            self.message = ''
            self.iterations = 0
            self.chi_square = None
            self.engine_result = object()

    class DummyMin:
        tracker = type('T', (), {'track': staticmethod(lambda a, b: a)})()

        def fit(self, params, obj, verbosity=None, **kwargs):
            return MockFitResults()

        def _sync_result_to_parameters(self, params, engine_params):
            pass

        def _stop_tracking(self):
            return None

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


def test_fitter_fit_defers_minimizer_tracking_until_postprocessing(monkeypatch):
    from easydiffraction.analysis.fit_helpers.bayesian import BayesianFitResults
    from easydiffraction.analysis.fitting import Fitter

    class DummyParam:
        value = 1.0
        uncertainty = 0.1
        _fit_start_value = None

    class DummyStructure:
        _need_categories_update = False

        def _update_categories(self):
            return None

    class DummyStructures:
        def __iter__(self):
            return iter([DummyStructure()])

    class DummyExperiment:
        parameters = []

    class DummyMin:
        def __init__(self):
            self.fit_calls: list[dict[str, object]] = []
            self.stop_calls = 0
            self.tracker = SimpleNamespace(track=lambda residuals, parameters: residuals)

        def fit(self, params, obj, verbosity=None, **kwargs):
            del params, obj
            self.fit_calls.append({'verbosity': verbosity, **kwargs})
            return BayesianFitResults(
                success=True,
                reduced_chi_square=1.2,
                convergence_diagnostics={'converged': False},
                sampler_settings={'steps': 300},
                best_log_posterior=-10.0,
            )

        def _stop_tracking(self):
            self.stop_calls += 1

    analysis_events: list[str] = []
    analysis = SimpleNamespace(
        _capture_fit_parameter_state=lambda params: analysis_events.append('capture'),
        _store_fit_result_projection=lambda results, experiments, fitted_parameters: analysis_events.append(
            'store'
        ),
    )

    fitter = Fitter()
    fitter.minimizer = DummyMin()
    monkeypatch.setattr(
        fitter,
        '_collect_fit_parameters',
        lambda structures, experiments: [DummyParam()],
    )

    fitter.fit(
        structures=DummyStructures(),
        experiments=[DummyExperiment()],
        analysis=analysis,
        verbosity=VerbosityEnum.FULL,
    )

    assert fitter.minimizer.fit_calls[0]['finalize_tracking'] is False
    assert fitter.minimizer.stop_calls == 1
    assert analysis_events == ['capture', 'store']
