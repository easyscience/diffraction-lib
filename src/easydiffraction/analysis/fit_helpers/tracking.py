# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import time
from dataclasses import dataclass

import numpy as np

from easydiffraction.analysis.fit_helpers.metrics import calculate_reduced_chi_square
from easydiffraction.display.progress import ActivityIndicator
from easydiffraction.display.progress import _TerminalLiveHandle as _SharedTerminalLiveHandle
from easydiffraction.display.progress import make_display_handle
from easydiffraction.utils.enums import VerbosityEnum
from easydiffraction.utils.logging import console
from easydiffraction.utils.utils import build_table_renderable

SIGNIFICANT_CHANGE_THRESHOLD = 0.01  # 1% threshold
SAMPLER_PROGRESS_UPDATE_SECONDS = 5.0
TRACKING_MODE_FIT = 'fit'
TRACKING_MODE_SAMPLER = 'sampling'
DEFAULT_HEADERS = ['iteration', 'time (s)', 'χ²', 'change / status']
DEFAULT_ALIGNMENTS = ['center', 'center', 'center', 'center']
SAMPLER_HEADERS = ['iteration', 'progress', 'time (s)', 'log posterior', 'phase']
SAMPLER_ALIGNMENTS = ['center', 'center', 'center', 'center', 'center']
ACTIVITY_LABEL_BURN_IN = 'burn-in'
ACTIVITY_LABEL_FITTING = 'fitting'
ACTIVITY_LABEL_PROCESSING = 'processing'
ACTIVITY_LABEL_SAMPLING = 'sampling'

_TerminalLiveHandle = _SharedTerminalLiveHandle


def _make_display_handle() -> object | None:
    """Return a backward-compatible generic live display handle."""
    return make_display_handle()


@dataclass(frozen=True, slots=True)
class SamplerProgressUpdate:
    """
    Normalized sampler progress payload forwarded by monitor hooks.
    """

    iteration: int
    total_iterations: int
    phase: str
    progress_percent: float
    log_posterior: float
    reduced_chi2: float
    elapsed_time: float
    force_report: bool = False


class FitProgressTracker:
    """
    Track and report reduced chi-square during optimization.

    The tracker keeps iteration counters, remembers the best observed
    reduced chi-square and when it occurred, and can display progress as
    a table in notebooks or a text UI in terminals.
    """

    def __init__(self) -> None:
        self._iteration: int = 0
        self._previous_chi2: float | None = None
        self._last_chi2: float | None = None
        self._last_iteration: int | None = None
        self._last_reported_iteration: int | None = None
        self._best_chi2: float | None = None
        self._best_iteration: int | None = None
        self._fitting_time: float | None = None
        self._start_time: float | None = None
        self._end_time: float | None = None
        self._verbosity: VerbosityEnum = VerbosityEnum.FULL
        self._last_progress_time: float | None = None
        self._tracking_mode: str = TRACKING_MODE_FIT
        self._sampler_total_iterations: int | None = None
        self._last_sampler_phase: str | None = None
        self._last_sampler_progress_percent: float | None = None
        self._last_sampler_log_posterior: float | None = None
        self._last_sampler_elapsed_time: float | None = None

        self._df_rows: list[list[str]] = []
        self._activity_indicator: ActivityIndicator | None = None
        self._activity_label: str = ACTIVITY_LABEL_FITTING

    def reset(self) -> None:
        """Reset internal state before a new optimization run."""
        self._stop_activity_indicator()
        self._iteration = 0
        self._previous_chi2 = None
        self._last_chi2 = None
        self._last_iteration = None
        self._last_reported_iteration = None
        self._best_chi2 = None
        self._best_iteration = None
        self._fitting_time = None
        self._start_time = None
        self._end_time = None
        self._last_progress_time = None
        self._tracking_mode = TRACKING_MODE_FIT
        self._sampler_total_iterations = None
        self._last_sampler_phase = None
        self._last_sampler_progress_percent = None
        self._last_sampler_log_posterior = None
        self._last_sampler_elapsed_time = None
        self._df_rows = []
        self._activity_label = ACTIVITY_LABEL_FITTING

    def track(
        self,
        residuals: np.ndarray,
        parameters: list[float],
    ) -> np.ndarray:
        """
        Update progress with current residuals and parameters.

        Parameters
        ----------
        residuals : np.ndarray
            Residuals between measured and calculated data.
        parameters : list[float]
            Current free parameters being fitted.

        Returns
        -------
        np.ndarray
            Residuals unchanged, for optimizer consumption.
        """
        self._iteration += 1

        reduced_chi2 = calculate_reduced_chi_square(residuals, len(parameters))

        if self._tracking_mode == TRACKING_MODE_SAMPLER:
            if self._previous_chi2 is None:
                self._previous_chi2 = reduced_chi2
                self._best_chi2 = reduced_chi2
            elif self._best_chi2 is None or reduced_chi2 < self._best_chi2:
                self._best_chi2 = reduced_chi2

            self._last_chi2 = reduced_chi2
            return residuals

        row: list[str] = []

        if self._previous_chi2 is None:
            self._previous_chi2 = reduced_chi2
            self._best_chi2 = reduced_chi2
            self._best_iteration = self._iteration

            row = [
                str(self._iteration),
                self._format_elapsed_time(),
                f'{reduced_chi2:.2f}',
                '',
            ]
        else:
            change = (self._previous_chi2 - reduced_chi2) / self._previous_chi2

            if change > SIGNIFICANT_CHANGE_THRESHOLD:
                change_in_percent = change * 100

                row = [
                    str(self._iteration),
                    self._format_elapsed_time(),
                    f'{reduced_chi2:.2f}',
                    f'{change_in_percent:.1f}% ↓',
                ]

                self._previous_chi2 = reduced_chi2

        if row:
            self.add_tracking_info(row)

        if self._best_chi2 is None or reduced_chi2 < self._best_chi2:
            self._best_chi2 = reduced_chi2
            self._best_iteration = self._iteration

        self._last_chi2 = reduced_chi2
        self._last_iteration = self._iteration

        return residuals

    def track_sampler_progress(self, update: SamplerProgressUpdate) -> None:
        """
        Update progress from a sampler monitor.

        Parameters
        ----------
        update : SamplerProgressUpdate
            Sampler iteration, phase, timing, and fit-quality payload.
        """
        self._iteration = update.iteration
        self._tracking_mode = TRACKING_MODE_SAMPLER
        self._sampler_total_iterations = max(1, update.total_iterations)

        clamped_iteration = min(max(1, update.iteration), self._sampler_total_iterations)
        clamped_progress = min(max(update.progress_percent, 0.0), 100.0)
        previous_phase = self._last_sampler_phase
        self._last_sampler_phase = update.phase
        self._last_sampler_progress_percent = clamped_progress
        self._last_sampler_log_posterior = update.log_posterior
        self._last_sampler_elapsed_time = update.elapsed_time
        self._set_activity_label(self._activity_label_for_sampler_phase(update.phase))

        row = self._initial_sampler_progress_row(
            update=update,
            clamped_iteration=clamped_iteration,
            clamped_progress=clamped_progress,
        )
        if not row:
            row = self._continued_sampler_progress_row(
                update=update,
                previous_phase=previous_phase,
                clamped_iteration=clamped_iteration,
                clamped_progress=clamped_progress,
            )

        if row:
            self.add_tracking_info(row)

        self._last_chi2 = update.reduced_chi2
        self._last_iteration = update.iteration

    @property
    def best_chi2(self) -> float | None:
        """Best recorded reduced chi-square value or None."""
        return self._best_chi2

    @property
    def best_iteration(self) -> int | None:
        """Iteration index at which the best chi-square was observed."""
        return self._best_iteration

    @property
    def iteration(self) -> int:
        """Current iteration counter."""
        return self._iteration

    @property
    def fitting_time(self) -> float | None:
        """Elapsed time of the last run in seconds, if available."""
        return self._fitting_time

    def start_timer(self) -> None:
        """Begin timing of a fit run."""
        self._start_time = time.perf_counter()
        self._end_time = None

    def stop_timer(self) -> None:
        """Stop timing and store elapsed time for the run."""
        if self._start_time is None:
            self._fitting_time = None
            return
        self._end_time = time.perf_counter()
        self._fitting_time = self._end_time - self._start_time

    def start_tracking(self, minimizer_name: str, *, mode: str = TRACKING_MODE_FIT) -> None:
        """
        Initialize display and headers and announce the minimizer.

        Parameters
        ----------
        minimizer_name : str
            Name of the minimizer used for the run.
        mode : str, default=TRACKING_MODE_FIT
            Tracking mode for the run.
        """
        self._tracking_mode = (
            TRACKING_MODE_SAMPLER if mode == TRACKING_MODE_SAMPLER else TRACKING_MODE_FIT
        )
        self._df_rows = []
        self._activity_label = self._default_activity_label()

        if self._verbosity is VerbosityEnum.SILENT:
            return

        if self._verbosity is VerbosityEnum.FULL:
            console.print(f"🚀 Starting fit process with '{minimizer_name}'...")
            if self._tracking_mode == TRACKING_MODE_SAMPLER:
                console.print('📈 Bayesian sampling progress:')
            else:
                console.print('📈 Goodness-of-fit progress:')

        self._start_activity_indicator()

    def add_tracking_info(self, row: list[str]) -> None:
        """
        Append a formatted row to the progress display.

        Parameters
        ----------
        row : list[str]
            Columns corresponding to the active tracking headers.
        """
        if row:
            iteration_cell = row[0].split('/', maxsplit=1)[0]
            if iteration_cell.isdigit():
                self._last_reported_iteration = int(iteration_cell)
        self._df_rows.append(row)
        if self._verbosity is VerbosityEnum.FULL:
            self._refresh_activity_indicator()

    def finish_tracking(self) -> None:
        """Finalize progress display and print best result summary."""
        if self._tracking_mode == TRACKING_MODE_SAMPLER:
            self._finalize_sampler_tracking_row()
        else:
            self._finalize_fit_tracking_row()

        if self._verbosity is VerbosityEnum.SILENT:
            return

        self._stop_activity_indicator()
        if self._verbosity is VerbosityEnum.FULL:
            self._print_completion_summary()

    def _initial_sampler_progress_row(
        self,
        *,
        update: SamplerProgressUpdate,
        clamped_iteration: int,
        clamped_progress: float,
    ) -> list[str]:
        if self._previous_chi2 is not None and self._best_chi2 is not None:
            return []

        self._previous_chi2 = update.reduced_chi2
        self._best_chi2 = update.reduced_chi2
        self._best_iteration = update.iteration
        self._last_progress_time = update.elapsed_time
        return self._sampler_progress_row(
            clamped_iteration=clamped_iteration,
            clamped_progress=clamped_progress,
            log_posterior=update.log_posterior,
            phase=update.phase,
            elapsed_time=update.elapsed_time,
        )

    def _continued_sampler_progress_row(
        self,
        *,
        update: SamplerProgressUpdate,
        previous_phase: str | None,
        clamped_iteration: int,
        clamped_progress: float,
    ) -> list[str]:
        if self._best_chi2 is not None and update.reduced_chi2 < self._best_chi2:
            self._best_chi2 = update.reduced_chi2
            self._best_iteration = update.iteration

        if not self._should_render_sampler_row(
            iteration=update.iteration,
            previous_phase=previous_phase,
            phase=update.phase,
            elapsed_time=update.elapsed_time,
            force_report=update.force_report,
            clamped_iteration=clamped_iteration,
        ):
            return []

        self._last_progress_time = update.elapsed_time
        return self._sampler_progress_row(
            clamped_iteration=clamped_iteration,
            clamped_progress=clamped_progress,
            log_posterior=update.log_posterior,
            phase=update.phase,
            elapsed_time=update.elapsed_time,
        )

    def _should_render_sampler_row(
        self,
        *,
        iteration: int,
        previous_phase: str | None,
        phase: str,
        elapsed_time: float,
        force_report: bool,
        clamped_iteration: int,
    ) -> bool:
        if iteration == self._last_reported_iteration:
            return False

        return (
            force_report
            or previous_phase != phase
            or self._last_progress_time is None
            or elapsed_time - self._last_progress_time >= SAMPLER_PROGRESS_UPDATE_SECONDS
            or clamped_iteration >= self._sampler_total_iterations
        )

    def _sampler_progress_row(
        self,
        *,
        clamped_iteration: int,
        clamped_progress: float,
        log_posterior: float,
        phase: str,
        elapsed_time: float,
    ) -> list[str]:
        return [
            self._sampler_iteration_label(clamped_iteration),
            f'{clamped_progress:.1f}%',
            self._format_elapsed_time(elapsed_time),
            f'{log_posterior:.2f}',
            phase,
        ]

    def _finalize_sampler_tracking_row(self) -> None:
        row = self._final_sampler_tracking_row()
        if row is None:
            return

        if not self._df_rows:
            self.add_tracking_info(row)
            return

        if self._rows_match_on_columns(self._df_rows[-1], row, (0, 1, 3, 4)):
            self._replace_last_tracking_row(row)
            return

        if self._df_rows[-1] != row:
            self.add_tracking_info(row)

    def _final_sampler_tracking_row(self) -> list[str] | None:
        if self._last_iteration is None or self._sampler_total_iterations is None:
            return None

        final_progress = self._resolved_final_sampler_progress()
        elapsed_time = self._resolved_final_sampler_elapsed_time()
        log_posterior = (
            f'{self._last_sampler_log_posterior:.2f}'
            if self._last_sampler_log_posterior is not None
            else ''
        )
        return [
            self._sampler_iteration_label(self._last_iteration),
            f'{final_progress:.1f}%',
            self._format_elapsed_time(elapsed_time),
            log_posterior,
            self._last_sampler_phase or ACTIVITY_LABEL_SAMPLING,
        ]

    def _finalize_fit_tracking_row(self) -> None:
        row = self._final_fit_tracking_row()
        if row is None:
            return

        if not self._df_rows:
            self.add_tracking_info(row)
            return

        if self._rows_match_on_columns(self._df_rows[-1], row, (0, 2)):
            self._replace_last_tracking_row(row)
            return

        if self._df_rows[-1][:3] != row[:3]:
            self.add_tracking_info(row)

    def _final_fit_tracking_row(self) -> list[str] | None:
        if self._last_iteration is None:
            return None

        return [
            str(self._last_iteration),
            self._format_elapsed_time(self._fitting_time),
            f'{self._last_chi2:.2f}' if self._last_chi2 is not None else '',
            '',
        ]

    def _resolved_final_sampler_progress(self) -> float:
        if self._last_sampler_progress_percent is not None:
            return self._last_sampler_progress_percent

        if self._last_iteration is None or self._sampler_total_iterations is None:
            msg = 'Sampler progress is unavailable without final iteration counts.'
            raise RuntimeError(msg)
        return (
            100.0
            * min(self._last_iteration, self._sampler_total_iterations)
            / self._sampler_total_iterations
        )

    def _resolved_final_sampler_elapsed_time(self) -> float | None:
        if self._fitting_time is not None:
            return self._fitting_time
        return self._last_sampler_elapsed_time

    def _sampler_iteration_label(self, iteration: int) -> str:
        if self._sampler_total_iterations is None:
            msg = 'Sampler iteration labels require a configured total iteration count.'
            raise RuntimeError(msg)
        clamped_iteration = min(iteration, self._sampler_total_iterations)
        return f'{clamped_iteration}/{self._sampler_total_iterations}'

    def _print_completion_summary(self) -> None:
        if self._tracking_mode == TRACKING_MODE_SAMPLER:
            console.print('✅ Bayesian sampling complete.')
            return

        console.print(
            f'🏆 Best goodness-of-fit (reduced χ²) is {self._best_chi2:.2f} '
            f'at iteration {self._best_iteration}'
        )
        console.print('✅ Fitting complete.')

    def _headers(self) -> list[str]:
        """Return column headers for the active tracking mode."""
        if self._tracking_mode == TRACKING_MODE_SAMPLER:
            return SAMPLER_HEADERS
        return DEFAULT_HEADERS

    def _alignments(self) -> list[str]:
        """Return column alignments for the active tracking mode."""
        if self._tracking_mode == TRACKING_MODE_SAMPLER:
            return SAMPLER_ALIGNMENTS
        return DEFAULT_ALIGNMENTS

    def _current_elapsed_time(self) -> float | None:
        """Return elapsed run time in seconds when timing is active."""
        if self._start_time is None:
            return None

        end_time = self._end_time if self._end_time is not None else time.perf_counter()
        return max(end_time - self._start_time, 0.0)

    def _format_elapsed_time(self, elapsed_time: float | None = None) -> str:
        """Format elapsed time in seconds with two decimal places."""
        resolved_time = elapsed_time
        if resolved_time is None:
            resolved_time = self._current_elapsed_time()
        if resolved_time is None:
            return ''
        return f'{resolved_time:.2f}'

    @staticmethod
    def _rows_match_on_columns(
        current_row: list[str],
        new_row: list[str],
        column_indices: tuple[int, ...],
    ) -> bool:
        """
        Return whether two tracking rows match on selected columns.
        """
        return all(
            len(current_row) > index
            and len(new_row) > index
            and current_row[index] == new_row[index]
            for index in column_indices
        )

    def _replace_last_tracking_row(self, row: list[str]) -> None:
        """
        Replace the last rendered tracking row and refresh the view.
        """
        if not self._df_rows:
            self.add_tracking_info(row)
            return

        self._df_rows[-1] = row
        if self._verbosity is VerbosityEnum.FULL:
            self._refresh_activity_indicator()

    def _default_activity_label(self) -> str:
        if self._tracking_mode == TRACKING_MODE_SAMPLER:
            return ACTIVITY_LABEL_SAMPLING
        return ACTIVITY_LABEL_FITTING

    def _activity_label_for_sampler_phase(self, phase: str) -> str:
        normalized_phase = phase.strip().lower()
        if normalized_phase == ACTIVITY_LABEL_BURN_IN:
            return ACTIVITY_LABEL_BURN_IN
        if normalized_phase == ACTIVITY_LABEL_SAMPLING:
            return ACTIVITY_LABEL_SAMPLING
        if normalized_phase:
            return normalized_phase
        return ACTIVITY_LABEL_PROCESSING

    def _start_activity_indicator(self) -> None:
        self._activity_indicator = ActivityIndicator(
            self._activity_label,
            verbosity=self._verbosity,
        )
        self._activity_indicator.start()
        self._refresh_activity_indicator()

    def _stop_activity_indicator(self) -> None:
        if self._activity_indicator is None:
            return

        self._activity_indicator.stop()
        self._activity_indicator = None

    def _set_activity_label(self, label: str) -> None:
        if label == self._activity_label:
            return

        self._activity_label = label
        self._refresh_activity_indicator()

    def _refresh_activity_indicator(self) -> None:
        if self._activity_indicator is None:
            return

        if self._verbosity is VerbosityEnum.FULL:
            self._activity_indicator.update(
                label=self._activity_label,
                content=self._table_renderable(),
            )
            return

        self._activity_indicator.update(label=self._activity_label)

    def _table_renderable(self) -> object:
        return build_table_renderable(
            columns_headers=self._headers(),
            columns_alignment=self._alignments(),
            columns_data=self._df_rows,
        )