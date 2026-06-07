# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Supplementary coverage tests for the fit-progress tracker.

These exercise behaviour not covered by ``test_tracking.py``: state
reset, sampler-mode tracking, timer edge cases, verbosity branches,
final-row finalization, activity-label mapping, and the activity
indicator wiring. External display/progress backends are stubbed so the
tests stay deterministic and engine-free.
"""

from __future__ import annotations

import numpy as np
import pytest

import easydiffraction.analysis.fit_helpers.tracking as tracking_mod
from easydiffraction.analysis.fit_helpers.tracking import FitProgressTracker
from easydiffraction.analysis.fit_helpers.tracking import SamplerProgressUpdate
from easydiffraction.display.progress import ACTIVITY_LABEL_BURN_IN
from easydiffraction.display.progress import ACTIVITY_LABEL_FITTING
from easydiffraction.display.progress import ACTIVITY_LABEL_POST_PROCESSING
from easydiffraction.display.progress import ACTIVITY_LABEL_PRE_PROCESSING
from easydiffraction.display.progress import ACTIVITY_LABEL_PROCESSING
from easydiffraction.display.progress import ACTIVITY_LABEL_SAMPLING
from easydiffraction.utils.enums import VerbosityEnum


class _RecordingIndicator:
    """Minimal stand-in for ``ActivityIndicator`` recording calls."""

    def __init__(self, label, *, verbosity, display_handle=None):
        self.label = label
        self.verbosity = verbosity
        self.display_handle = display_handle
        self.started = False
        self.stopped = False
        self.updates: list[dict] = []

    def start(self) -> None:
        self.started = True

    def stop(self) -> None:
        self.stopped = True

    def update(self, *, label=None, content=None) -> None:
        self.updates.append({'label': label, 'content': content})


@pytest.fixture
def silent_tracker():
    """Return a tracker whose verbosity suppresses all console output."""
    tracker = FitProgressTracker()
    tracker._verbosity = VerbosityEnum.SILENT
    return tracker


def _sampler_update(**overrides):
    """Build a SamplerProgressUpdate with sensible defaults."""
    payload = {
        'iteration': 1,
        'total_iterations': 10,
        'phase': 'sampling',
        'progress_percent': 10.0,
        'log_posterior': -2.0,
        'reduced_chi2': 5.0,
        'elapsed_time': 0.5,
        'force_report': False,
    }
    payload.update(overrides)
    return SamplerProgressUpdate(**payload)


def test_make_display_handle_delegates(monkeypatch):
    sentinel = object()
    monkeypatch.setattr(tracking_mod, 'make_display_handle', lambda: sentinel)

    assert tracking_mod._make_display_handle() is sentinel


def test_reset_clears_all_state_and_stops_indicator():
    tracker = FitProgressTracker()
    indicator = _RecordingIndicator('x', verbosity=VerbosityEnum.FULL)
    tracker._activity_indicator = indicator
    tracker._iteration = 7
    tracker._best_chi2 = 1.0
    tracker._best_iteration = 3
    tracker._df_rows = [['a']]
    tracker._tracking_mode = tracking_mod.TRACKING_MODE_SAMPLER
    tracker._sampler_total_iterations = 42
    tracker._sampler_pre_processing_pending = True

    tracker.reset()

    assert indicator.stopped is True
    assert tracker._activity_indicator is None
    assert tracker._iteration == 0
    assert tracker._best_chi2 is None
    assert tracker._best_iteration is None
    assert tracker._df_rows == []
    assert tracker._tracking_mode == tracking_mod.TRACKING_MODE_FIT
    assert tracker._sampler_total_iterations is None
    assert tracker._sampler_pre_processing_pending is False
    assert tracker._activity_label == ACTIVITY_LABEL_FITTING


def test_track_in_sampler_mode_records_best_without_rows(monkeypatch):
    monkeypatch.setattr(
        tracking_mod,
        'calculate_reduced_chi_square',
        lambda residuals, n_parameters: next(chi2_values),
    )
    chi2_values = iter([8.0, 4.0, 6.0])

    tracker = FitProgressTracker()
    tracker._tracking_mode = tracking_mod.TRACKING_MODE_SAMPLER

    residuals = np.array([1.0, 2.0])
    out = tracker.track(residuals, parameters=[1.0])
    assert out is residuals  # residuals returned unchanged
    assert tracker._previous_chi2 == 8.0
    assert tracker._best_chi2 == 8.0

    # Lower chi2 improves best.
    tracker.track(residuals, parameters=[1.0])
    assert tracker._best_chi2 == 4.0

    # Higher chi2 does not regress best, but updates last.
    tracker.track(residuals, parameters=[1.0])
    assert tracker._best_chi2 == 4.0
    assert tracker._last_chi2 == 6.0

    # Sampler mode never emits progress rows from track().
    assert tracker._df_rows == []


def test_start_sampler_pre_processing_marks_pending_status(silent_tracker):
    silent_tracker.start_sampler_pre_processing(total_iterations=0)

    assert silent_tracker._tracking_mode == tracking_mod.TRACKING_MODE_SAMPLER
    # total_iterations clamped to at least 1.
    assert silent_tracker._sampler_total_iterations == 1
    assert silent_tracker._last_sampler_phase == tracking_mod.SAMPLER_PHASE_PRE_PROCESSING
    assert silent_tracker._sampler_pre_processing_pending is True
    assert silent_tracker._activity_label == ACTIVITY_LABEL_PRE_PROCESSING


def test_pre_processing_pending_emits_status_row_first(silent_tracker):
    silent_tracker.start_sampler_pre_processing(total_iterations=10)
    silent_tracker.track_sampler_progress(
        _sampler_update(iteration=2, progress_percent=20.0, elapsed_time=1.0)
    )

    first_row = silent_tracker._df_rows[0]
    # Status row: blank progress column, phase = pre-processing.
    assert first_row[1] == ''
    assert first_row[4] == tracking_mod.SAMPLER_PHASE_PRE_PROCESSING
    assert silent_tracker._sampler_pre_processing_pending is False


def test_start_sampler_post_processing_ignored_outside_sampler_mode(silent_tracker):
    # Default tracking mode is fit; call should be a no-op.
    silent_tracker.start_sampler_post_processing()

    assert silent_tracker._last_sampler_phase is None
    assert silent_tracker._activity_label == ACTIVITY_LABEL_FITTING


def test_start_sampler_post_processing_fills_totals_and_label(silent_tracker):
    silent_tracker._tracking_mode = tracking_mod.TRACKING_MODE_SAMPLER
    silent_tracker._last_iteration = 5
    silent_tracker._sampler_total_iterations = None

    silent_tracker.start_sampler_post_processing(log_posterior=-1.25)

    assert silent_tracker._sampler_total_iterations == 5
    assert silent_tracker._last_sampler_phase == tracking_mod.SAMPLER_PHASE_POST_PROCESSING
    assert silent_tracker._last_sampler_progress_percent == 100.0
    assert silent_tracker._last_sampler_log_posterior == -1.25
    assert silent_tracker._activity_label == ACTIVITY_LABEL_POST_PROCESSING


def test_properties_expose_internal_state():
    tracker = FitProgressTracker()
    tracker._best_chi2 = 2.5
    tracker._best_iteration = 9
    tracker._iteration = 11
    tracker._fitting_time = 3.5

    assert tracker.best_chi2 == 2.5
    assert tracker.best_iteration == 9
    assert tracker.iteration == 11
    assert tracker.fitting_time == 3.5


def test_stop_timer_without_start_yields_none():
    tracker = FitProgressTracker()
    # No start_timer() call.
    tracker.stop_timer()

    assert tracker.fitting_time is None


def test_stop_timer_records_elapsed(monkeypatch):
    times = iter([1.0, 4.0])
    monkeypatch.setattr(tracking_mod.time, 'perf_counter', lambda: next(times))

    tracker = FitProgressTracker()
    tracker.start_timer()
    tracker.stop_timer()

    assert tracker.fitting_time == 3.0


def test_elapsed_since_start_branches(monkeypatch):
    tracker = FitProgressTracker()
    # No timer started.
    assert tracker._elapsed_since_start() is None

    # Started but not stopped: uses live perf_counter.
    tracker._start_time = 10.0
    tracker._end_time = None
    monkeypatch.setattr(tracking_mod.time, 'perf_counter', lambda: 13.0)
    assert tracker._elapsed_since_start() == 3.0

    # Stopped: uses recorded end time.
    tracker._end_time = 12.5
    assert tracker._elapsed_since_start() == 2.5


def test_start_tracking_silent_skips_output_and_indicator(monkeypatch, silent_tracker):
    monkeypatch.setattr(tracking_mod, 'ActivityIndicator', _RecordingIndicator, raising=True)

    silent_tracker.start_tracking('lm', mode=tracking_mod.TRACKING_MODE_FIT)

    # Silent verbosity returns before starting an indicator.
    assert silent_tracker._activity_indicator is None
    assert silent_tracker._df_rows == []


def test_start_tracking_full_sampler_announces_and_starts_indicator(monkeypatch, capsys):
    monkeypatch.setattr(tracking_mod, 'ActivityIndicator', _RecordingIndicator, raising=True)

    tracker = FitProgressTracker()
    tracker.start_tracking('dream', mode=tracking_mod.TRACKING_MODE_SAMPLER)

    out = capsys.readouterr().out
    assert 'Bayesian sampling progress' in out
    assert tracker._activity_label == ACTIVITY_LABEL_PROCESSING
    assert isinstance(tracker._activity_indicator, _RecordingIndicator)
    assert tracker._activity_indicator.started is True


def test_finish_tracking_silent_returns_without_summary(silent_tracker, capsys):
    silent_tracker._tracking_mode = tracking_mod.TRACKING_MODE_FIT
    silent_tracker._last_iteration = 3
    silent_tracker._last_chi2 = 1.0

    silent_tracker.finish_tracking()

    out = capsys.readouterr().out
    assert out == ''


def test_finish_tracking_skips_summary_during_exception(monkeypatch, capsys):
    tracker = FitProgressTracker()
    tracker._tracking_mode = tracking_mod.TRACKING_MODE_FIT
    tracker._last_iteration = 4
    tracker._last_chi2 = 2.0
    tracker._best_chi2 = 2.0
    tracker._best_iteration = 4

    # Simulate finalization while an exception is being handled.
    monkeypatch.setattr(tracker, '_cleanup_during_exception', lambda: True)

    tracker.finish_tracking()

    out = capsys.readouterr().out
    assert 'Best goodness-of-fit' not in out
    assert 'Fitting complete' not in out


def test_finish_tracking_prints_sampler_completion(monkeypatch, capsys):
    tracker = FitProgressTracker()
    tracker._tracking_mode = tracking_mod.TRACKING_MODE_SAMPLER
    tracker._last_iteration = 10
    tracker._sampler_total_iterations = 10
    tracker._last_sampler_phase = 'sampling'
    tracker._last_sampler_progress_percent = 100.0
    tracker._last_sampler_log_posterior = -3.0
    monkeypatch.setattr(tracker, '_cleanup_during_exception', lambda: False)

    tracker.finish_tracking()

    out = capsys.readouterr().out
    assert 'Bayesian sampling complete' in out


def test_cleanup_during_exception_reflects_active_exception():
    assert FitProgressTracker._cleanup_during_exception() is False
    message = 'boom'
    try:
        raise ValueError(message)
    except ValueError:
        assert FitProgressTracker._cleanup_during_exception() is True


def test_continued_sampler_row_updates_best_and_renders(silent_tracker):
    silent_tracker.start_tracking('dream', mode=tracking_mod.TRACKING_MODE_SAMPLER)
    silent_tracker.track_sampler_progress(
        _sampler_update(iteration=1, reduced_chi2=5.0, elapsed_time=0.0)
    )
    rows_after_first = len(silent_tracker._df_rows)

    # A phase change forces a row even within the update interval, and a
    # lower reduced_chi2 improves the best estimate.
    silent_tracker.track_sampler_progress(
        _sampler_update(
            iteration=2,
            phase='burn-in',
            reduced_chi2=1.0,
            progress_percent=20.0,
            elapsed_time=0.1,
        )
    )

    assert silent_tracker._best_chi2 == 1.0
    assert silent_tracker._best_iteration == 2
    assert len(silent_tracker._df_rows) == rows_after_first + 1
    assert silent_tracker._df_rows[-1][4] == 'burn-in'


def test_continued_sampler_row_suppressed_when_not_due(silent_tracker):
    silent_tracker.start_tracking('dream', mode=tracking_mod.TRACKING_MODE_SAMPLER)
    silent_tracker.track_sampler_progress(
        _sampler_update(iteration=1, phase='sampling', reduced_chi2=5.0, elapsed_time=0.0)
    )
    rows_after_first = len(silent_tracker._df_rows)

    # Same phase, no force, within interval, not final iteration -> no row.
    silent_tracker.track_sampler_progress(
        _sampler_update(
            iteration=2,
            phase='sampling',
            reduced_chi2=4.0,
            progress_percent=20.0,
            elapsed_time=0.1,
        )
    )

    assert len(silent_tracker._df_rows) == rows_after_first


def test_should_render_sampler_row_dedupes_reported_iteration():
    tracker = FitProgressTracker()
    tracker._sampler_total_iterations = 10
    tracker._last_reported_iteration = 5

    assert (
        tracker._should_render_sampler_row(
            iteration=5,
            previous_phase='sampling',
            phase='sampling',
            elapsed_time=100.0,
            force_report=True,
            clamped_iteration=5,
        )
        is False
    )


def test_finalize_sampler_post_processing_replaces_matching_row(silent_tracker):
    silent_tracker.start_tracking('dream', mode=tracking_mod.TRACKING_MODE_SAMPLER)
    silent_tracker.track_sampler_progress(
        _sampler_update(
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
    silent_tracker.start_sampler_post_processing()
    silent_tracker._fitting_time = 5.5

    silent_tracker.finish_tracking()

    last = silent_tracker._df_rows[-1]
    assert last[0] == ''
    assert last[4] == tracking_mod.SAMPLER_PHASE_POST_PROCESSING


def test_finalize_sampler_row_appended_when_no_rows(silent_tracker):
    silent_tracker._tracking_mode = tracking_mod.TRACKING_MODE_SAMPLER
    silent_tracker._last_iteration = 8
    silent_tracker._sampler_total_iterations = 10
    silent_tracker._last_sampler_phase = 'sampling'
    silent_tracker._last_sampler_progress_percent = 80.0
    silent_tracker._last_sampler_log_posterior = -2.0
    silent_tracker._last_sampler_elapsed_time = 4.0

    silent_tracker.finish_tracking()

    assert len(silent_tracker._df_rows) == 1
    row = silent_tracker._df_rows[0]
    assert row[0] == '8/10'
    assert row[1] == '80.0%'
    assert row[4] == 'sampling'


def test_final_sampler_tracking_row_none_without_iteration():
    tracker = FitProgressTracker()
    tracker._tracking_mode = tracking_mod.TRACKING_MODE_SAMPLER
    # No last iteration / totals -> finalize is a no-op.
    assert tracker._final_sampler_tracking_row() is None


def test_finalize_fit_replaces_matching_row():
    tracker = FitProgressTracker()
    tracker._tracking_mode = tracking_mod.TRACKING_MODE_FIT
    tracker._last_iteration = 5
    tracker._last_chi2 = 3.0
    tracker._fitting_time = 2.0
    # Existing row matches on iteration (col 0) and chi2 (col 2).
    tracker._df_rows = [['5', '1.00', '3.00', '']]

    tracker._finalize_fit_tracking_row()

    assert tracker._df_rows == [['5', '2.00', '3.00', '']]


def test_finalize_fit_appends_when_no_rows():
    tracker = FitProgressTracker()
    tracker._tracking_mode = tracking_mod.TRACKING_MODE_FIT
    tracker._last_iteration = 2
    tracker._last_chi2 = 4.0
    tracker._fitting_time = 1.5

    tracker._finalize_fit_tracking_row()

    assert tracker._df_rows == [['2', '1.50', '4.00', '']]


def test_finalize_fit_appends_distinct_row():
    tracker = FitProgressTracker()
    tracker._tracking_mode = tracking_mod.TRACKING_MODE_FIT
    tracker._last_iteration = 9
    tracker._last_chi2 = 1.0
    tracker._fitting_time = 3.0
    tracker._df_rows = [['1', '0.00', '5.00', '']]

    tracker._finalize_fit_tracking_row()

    assert tracker._df_rows[-1] == ['9', '3.00', '1.00', '']
    assert len(tracker._df_rows) == 2


def test_final_fit_tracking_row_blank_chi2_when_unset():
    tracker = FitProgressTracker()
    tracker._last_iteration = 4
    tracker._last_chi2 = None
    tracker._fitting_time = None

    row = tracker._final_fit_tracking_row()

    assert row == ['4', '', '', '']


def test_final_fit_tracking_row_none_without_iteration():
    tracker = FitProgressTracker()
    assert tracker._final_fit_tracking_row() is None


def test_resolved_final_sampler_progress_uses_recorded_percent():
    tracker = FitProgressTracker()
    tracker._last_sampler_progress_percent = 73.0
    assert tracker._resolved_final_sampler_progress() == 73.0


def test_resolved_final_sampler_progress_computes_from_iterations():
    tracker = FitProgressTracker()
    tracker._last_sampler_progress_percent = None
    tracker._last_iteration = 7
    tracker._sampler_total_iterations = 10
    assert tracker._resolved_final_sampler_progress() == pytest.approx(70.0)


def test_resolved_final_sampler_progress_raises_without_counts():
    tracker = FitProgressTracker()
    tracker._last_sampler_progress_percent = None
    tracker._last_iteration = None
    tracker._sampler_total_iterations = None

    with pytest.raises(RuntimeError, match='progress is unavailable'):
        tracker._resolved_final_sampler_progress()


def test_resolved_final_sampler_elapsed_time_prefers_fitting_time():
    tracker = FitProgressTracker()
    tracker._fitting_time = 9.0
    tracker._last_sampler_elapsed_time = 4.0
    assert tracker._resolved_final_sampler_elapsed_time() == 9.0

    tracker._fitting_time = None
    assert tracker._resolved_final_sampler_elapsed_time() == 4.0


def test_sampler_iteration_label_clamps_and_requires_total():
    tracker = FitProgressTracker()
    tracker._sampler_total_iterations = 10
    assert tracker._sampler_iteration_label(15) == '10/10'
    assert tracker._sampler_iteration_label(3) == '3/10'

    tracker._sampler_total_iterations = None
    with pytest.raises(RuntimeError, match='total iteration count'):
        tracker._sampler_iteration_label(1)


def test_print_completion_summary_skips_when_best_missing(capsys):
    tracker = FitProgressTracker()
    tracker._tracking_mode = tracking_mod.TRACKING_MODE_FIT
    tracker._best_chi2 = None
    tracker._best_iteration = None

    tracker._print_completion_summary()

    assert capsys.readouterr().out == ''


def test_headers_and_alignments_switch_with_mode():
    tracker = FitProgressTracker()
    assert tracker._headers() == tracking_mod.DEFAULT_HEADERS
    assert tracker._alignments() == tracking_mod.DEFAULT_ALIGNMENTS

    tracker._tracking_mode = tracking_mod.TRACKING_MODE_SAMPLER
    assert tracker._headers() == tracking_mod.SAMPLER_HEADERS
    assert tracker._alignments() == tracking_mod.SAMPLER_ALIGNMENTS


def test_current_elapsed_time_none_without_timer():
    tracker = FitProgressTracker()
    assert tracker._current_elapsed_time() is None


def test_current_elapsed_time_clamps_to_zero(monkeypatch):
    tracker = FitProgressTracker()
    tracker._start_time = 10.0
    tracker._end_time = 9.0  # clock went backwards
    assert tracker._current_elapsed_time() == 0.0


def test_format_elapsed_time_branches(monkeypatch):
    tracker = FitProgressTracker()
    # Explicit value formatted.
    assert tracker._format_elapsed_time(1.234) == '1.23'

    # None argument and no timer -> empty string.
    assert tracker._format_elapsed_time(None) == ''

    # None argument falls back to current elapsed time.
    tracker._start_time = 0.0
    tracker._end_time = 2.0
    assert tracker._format_elapsed_time(None) == '2.00'


def test_should_render_fit_row_requires_known_times():
    tracker = FitProgressTracker()
    assert tracker._should_render_fit_row(None) is False

    tracker._last_progress_time = None
    assert tracker._should_render_fit_row(1.0) is False

    tracker._last_progress_time = 0.0
    assert tracker._should_render_fit_row(2.0) is False
    assert tracker._should_render_fit_row(tracking_mod.FIT_PROGRESS_UPDATE_SECONDS) is True


def test_rows_match_on_columns_handles_short_rows():
    assert FitProgressTracker._rows_match_on_columns(['a', 'b'], ['a', 'b'], (0, 1)) is True
    # Index out of range on the new row -> no match.
    assert FitProgressTracker._rows_match_on_columns(['a', 'b'], ['a'], (0, 1)) is False
    assert FitProgressTracker._rows_match_on_columns(['a', 'x'], ['a', 'b'], (0, 1)) is False


def test_replace_last_tracking_row_appends_when_empty():
    tracker = FitProgressTracker()
    tracker._verbosity = VerbosityEnum.SILENT
    tracker._replace_last_tracking_row(['1', '0.00', '5.00', ''])
    assert tracker._df_rows == [['1', '0.00', '5.00', '']]


def test_replace_last_tracking_row_refreshes_indicator_when_full():
    tracker = FitProgressTracker()
    tracker._verbosity = VerbosityEnum.FULL
    indicator = _RecordingIndicator('x', verbosity=VerbosityEnum.FULL)
    tracker._activity_indicator = indicator
    tracker._df_rows = [['1', '0.00', '5.00', '']]

    new_row = ['1', '2.00', '5.00', '']
    tracker._replace_last_tracking_row(new_row)

    assert tracker._df_rows == [new_row]
    assert indicator.updates  # refresh triggered


def test_default_activity_label_by_mode():
    tracker = FitProgressTracker()
    assert tracker._default_activity_label() == ACTIVITY_LABEL_FITTING
    tracker._tracking_mode = tracking_mod.TRACKING_MODE_SAMPLER
    assert tracker._default_activity_label() == ACTIVITY_LABEL_PROCESSING


@pytest.mark.parametrize(
    ('phase', 'expected'),
    [
        ('pre-processing', ACTIVITY_LABEL_PRE_PROCESSING),
        ('  Burn-In ', ACTIVITY_LABEL_BURN_IN),
        ('post-processing', ACTIVITY_LABEL_POST_PROCESSING),
        ('SAMPLING', ACTIVITY_LABEL_SAMPLING),
        ('exploration', 'exploration'),
        ('', ACTIVITY_LABEL_SAMPLING),
    ],
)
def test_activity_label_for_sampler_phase(phase, expected):
    assert FitProgressTracker._activity_label_for_sampler_phase(phase) == expected


def test_set_shared_display_handle_flows_to_indicator(monkeypatch):
    handle = object()
    monkeypatch.setattr(tracking_mod, 'ActivityIndicator', _RecordingIndicator, raising=True)

    tracker = FitProgressTracker()
    tracker._set_shared_display_handle(handle)
    assert tracker._shared_display_handle is handle

    tracker._start_activity_indicator()
    assert tracker._activity_indicator.display_handle is handle
    assert tracker._activity_indicator.started is True


def test_stop_activity_indicator_noop_when_absent():
    tracker = FitProgressTracker()
    # Should not raise when no indicator exists.
    tracker._stop_activity_indicator()
    assert tracker._activity_indicator is None


def test_set_activity_label_skips_when_unchanged():
    tracker = FitProgressTracker()
    indicator = _RecordingIndicator('x', verbosity=VerbosityEnum.FULL)
    tracker._activity_indicator = indicator
    tracker._activity_label = ACTIVITY_LABEL_FITTING

    tracker._set_activity_label(ACTIVITY_LABEL_FITTING)
    assert indicator.updates == []  # no refresh for identical label

    tracker._set_activity_label(ACTIVITY_LABEL_SAMPLING)
    assert tracker._activity_label == ACTIVITY_LABEL_SAMPLING
    assert indicator.updates  # refresh triggered


def test_refresh_activity_indicator_label_only_when_not_full():
    tracker = FitProgressTracker()
    tracker._verbosity = VerbosityEnum.SHORT
    indicator = _RecordingIndicator('x', verbosity=VerbosityEnum.SHORT)
    tracker._activity_indicator = indicator
    tracker._activity_label = 'Working...'

    tracker._refresh_activity_indicator()

    assert indicator.updates == [{'label': 'Working...', 'content': None}]


def test_refresh_activity_indicator_includes_content_when_full():
    tracker = FitProgressTracker()
    tracker._verbosity = VerbosityEnum.FULL
    indicator = _RecordingIndicator('x', verbosity=VerbosityEnum.FULL)
    tracker._activity_indicator = indicator
    tracker._df_rows = [['1', '0.00', '5.00', '']]

    tracker._refresh_activity_indicator()

    assert indicator.updates
    assert indicator.updates[-1]['content'] is not None
