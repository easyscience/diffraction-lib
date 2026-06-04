# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from types import SimpleNamespace

import numpy as np


def test_module_import():
    import easydiffraction.analysis.fit_helpers.tracking as MUT

    expected_module_name = 'easydiffraction.analysis.fit_helpers.tracking'
    actual_module_name = MUT.__name__
    assert expected_module_name == actual_module_name


def test_tracker_terminal_flow_prints_and_updates_best(monkeypatch, capsys):
    import easydiffraction.display.progress as progress_mod
    from easydiffraction.analysis.fit_helpers.tracking import FitProgressTracker

    # Force terminal branch (not notebook) in the shared progress layer.
    monkeypatch.setattr(progress_mod, 'in_jupyter', lambda: False)

    tracker = FitProgressTracker()
    tracker.start_tracking('dummy')
    tracker.start_timer()

    # First iteration sets previous and best
    res1 = np.array([2.0, 1.0])  # chi2 = 5, dof depends on num params but relative change only
    tracker.track(res1, parameters=[1])

    # Second iteration small change below threshold -> no row emitted
    out1 = capsys.readouterr().out
    assert 'Goodness-of-fit' in out1

    res2 = np.array([1.9, 1.0])
    tracker.track(res2, parameters=[1])

    # Third iteration large improvement -> row emitted
    res3 = np.array([0.1, 0.1])
    tracker.track(res3, parameters=[1])

    tracker.stop_timer()
    tracker.finish_tracking()
    out2 = capsys.readouterr().out
    assert 'Best goodness-of-fit' in out2
    assert tracker.best_iteration is not None


def test_tracker_fit_adds_timed_rows_and_resets_counter(monkeypatch):
    import easydiffraction.analysis.fit_helpers.tracking as tracking_mod
    from easydiffraction.analysis.fit_helpers.tracking import FitProgressTracker

    chi2_values = iter([5.0, 4.0, 3.97, 3.97, 3.97, 3.97])
    perf_counter_values = iter([0.0, 0.0, 2.0, 6.9, 7.1, 11.9, 12.2])

    monkeypatch.setattr(
        tracking_mod,
        'calculate_reduced_chi_square',
        lambda residuals, n_parameters: next(chi2_values),
    )
    monkeypatch.setattr(
        tracking_mod.time,
        'perf_counter',
        lambda: next(perf_counter_values),
    )

    tracker = FitProgressTracker()
    tracker.start_timer()

    for _ in range(6):
        tracker.track(np.array([1.0]), parameters=[1.0])

    assert tracker._df_rows == [
        ['1', '0.00', '5.00', ''],
        ['2', '2.00', '4.00', '20.0% ↓'],
        ['4', '7.10', '3.97', ''],
        ['6', '12.20', '3.97', ''],
    ]
    assert tracker._last_progress_time == 12.2
    assert tracker._previous_chi2 == 4.0


def test_tracker_fit_progress_uses_backend_iterations_for_display():
    from easydiffraction.analysis.fit_helpers.tracking import FitProgressTracker

    tracker = FitProgressTracker()

    tracker.track_fit_progress(iteration=1, reduced_chi2=10.0, elapsed_time=0.1)
    tracker.track_fit_progress(iteration=63, reduced_chi2=5.0, elapsed_time=1.0)
    tracker.track_fit_progress(iteration=122, reduced_chi2=4.0, elapsed_time=2.0)

    assert tracker._df_rows == [
        ['1', '0.10', '10.00', ''],
        ['63', '1.00', '5.00', '50.0% ↓'],
        ['122', '2.00', '4.00', '20.0% ↓'],
    ]
    assert tracker.best_iteration == 122


def test_tracker_sampler_post_processing_adds_final_status_row():
    from easydiffraction.analysis.fit_helpers.tracking import FitProgressTracker
    from easydiffraction.analysis.fit_helpers.tracking import SamplerProgressUpdate

    tracker = FitProgressTracker()
    tracker.start_tracking('dream', mode='sampling')
    tracker.start_timer()
    tracker.track_sampler_progress(
        SamplerProgressUpdate(
            iteration=10,
            total_iterations=10,
            phase='sampling',
            progress_percent=100.0,
            log_posterior=-3.0,
            reduced_chi2=1.0,
            elapsed_time=5.0,
            force_report=True,
        )
    )

    tracker.start_sampler_post_processing()
    tracker.stop_timer()
    tracker.finish_tracking()

    assert tracker._df_rows[-1][0] == ''
    assert tracker._df_rows[-1][1] == ''
    assert tracker._df_rows[-1][3] == ''
    assert tracker._df_rows[-1][4] == 'post-processing'


def test_notebook_fit_stop_control_renders_interrupt_button(monkeypatch):
    import easydiffraction.display.progress as progress_mod
    from easydiffraction.utils.enums import VerbosityEnum

    html_updates: list[str] = []
    javascript_outputs: list[str] = []

    class FakeDisplayHandle:
        def display(self, value: SimpleNamespace) -> None:
            html_updates.append(value.data)

        def update(self, value: SimpleNamespace) -> None:
            html_updates.append(value.data)

    monkeypatch.setattr(progress_mod, 'in_jupyter', lambda: True)
    monkeypatch.setattr(progress_mod, 'HTML', lambda data: SimpleNamespace(data=data))
    monkeypatch.setattr(
        progress_mod,
        'Javascript',
        lambda data: SimpleNamespace(data=data),
    )
    monkeypatch.setattr(progress_mod, 'DisplayHandle', FakeDisplayHandle)
    monkeypatch.setattr(
        progress_mod,
        'display',
        lambda value: javascript_outputs.append(value.data),
    )

    with progress_mod.notebook_fit_stop_control(verbosity=VerbosityEnum.FULL):
        pass

    assert 'Stop fitting' in html_updates[0]
    assert 'api/kernels/' in javascript_outputs[0]
    assert 'Interrupt sent...' in javascript_outputs[0]
    assert html_updates[-1] == ''


def test_notebook_fit_stop_control_clears_button_after_interrupt(monkeypatch):
    import easydiffraction.display.progress as progress_mod
    from easydiffraction.utils.enums import VerbosityEnum

    html_updates: list[str] = []

    class FakeDisplayHandle:
        def display(self, value: SimpleNamespace) -> None:
            html_updates.append(value.data)

        def update(self, value: SimpleNamespace) -> None:
            html_updates.append(value.data)

    monkeypatch.setattr(progress_mod, 'in_jupyter', lambda: True)
    monkeypatch.setattr(progress_mod, 'HTML', lambda data: SimpleNamespace(data=data))
    monkeypatch.setattr(
        progress_mod,
        'Javascript',
        lambda data: SimpleNamespace(data=data),
    )
    monkeypatch.setattr(progress_mod, 'DisplayHandle', FakeDisplayHandle)
    monkeypatch.setattr(progress_mod, 'display', lambda value: None)

    try:
        with progress_mod.notebook_fit_stop_control(verbosity=VerbosityEnum.FULL):
            raise KeyboardInterrupt
    except KeyboardInterrupt:
        pass

    assert html_updates[-1] == ''


def test_notebook_fit_stop_control_extracts_kernel_id_from_connection_file():
    from easydiffraction.display.progress import NotebookFitStopControl

    kernel_id = NotebookFitStopControl._kernel_id_from_connection_file('kernel-abc-123.json')

    assert kernel_id == 'abc-123'
