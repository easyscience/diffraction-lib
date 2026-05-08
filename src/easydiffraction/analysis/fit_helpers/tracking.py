# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import time
from contextlib import suppress

import numpy as np

from easydiffraction.utils.logging import console

try:
    from IPython.display import HTML
    from IPython.display import DisplayHandle
    from IPython.display import display
except ImportError:
    display = None
    clear_output = None

from easydiffraction.analysis.fit_helpers.metrics import calculate_reduced_chi_square
from easydiffraction.utils.enums import VerbosityEnum
from easydiffraction.utils.environment import in_jupyter
from easydiffraction.utils.utils import render_table

try:
    from rich.live import Live
except ImportError:  # pragma: no cover - rich always available in app env
    Live = None  # type: ignore[assignment]

from easydiffraction.utils.logging import ConsoleManager

SIGNIFICANT_CHANGE_THRESHOLD = 0.01  # 1% threshold
SAMPLER_PROGRESS_UPDATE_SECONDS = 5.0
TRACKING_MODE_FIT = 'fit'
TRACKING_MODE_SAMPLER = 'sampling'
DEFAULT_HEADERS = ['iteration', 'χ²', 'change / status']
DEFAULT_ALIGNMENTS = ['center', 'center', 'center']
SAMPLER_HEADERS = ['iteration', 'progress', 'log posterior', 'phase']
SAMPLER_ALIGNMENTS = ['center', 'center', 'center', 'center']


class _TerminalLiveHandle:
    """
    Adapter that exposes update()/close() for terminal live updates.

    Wraps a rich.live.Live instance but keeps the tracker decoupled from
    the underlying UI mechanism.
    """

    def __init__(self, live: object) -> None:
        self._live = live

    def update(self, renderable: object) -> None:
        """
        Refresh the live display with a new renderable.

        Parameters
        ----------
        renderable : object
            A Rich-compatible renderable to display.
        """
        self._live.update(renderable, refresh=True)

    def close(self) -> None:
        """Stop the live display, suppressing any errors."""
        with suppress(Exception):
            self._live.stop()


def _make_display_handle() -> object | None:
    """
    Create and initialize a display/update handle for the environment.

    - In Jupyter, returns an IPython DisplayHandle and creates a
    placeholder. - In terminal, returns a _TerminalLiveHandle backed by
    rich Live. - If neither applies, returns None.
    """
    if in_jupyter() and display is not None and HTML is not None:
        h = DisplayHandle()
        # Create an empty placeholder area to update in place
        h.display(HTML(''))
        return h
    if Live is not None:
        # Reuse the shared Console to coordinate with logging output
        # and keep consistent width
        live = Live(console=ConsoleManager.get(), auto_refresh=True)
        live.start()
        return _TerminalLiveHandle(live)
    return None


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
        self._verbosity: VerbosityEnum = VerbosityEnum.FULL
        self._last_progress_time: float | None = None
        self._tracking_mode: str = TRACKING_MODE_FIT
        self._sampler_total_iterations: int | None = None
        self._last_sampler_phase: str | None = None
        self._last_sampler_progress_percent: float | None = None
        self._last_sampler_log_posterior: float | None = None

        self._df_rows: list[list[str]] = []
        self._display_handle: object | None = None
        self._live: object | None = None

    def reset(self) -> None:
        """Reset internal state before a new optimization run."""
        self._iteration = 0
        self._previous_chi2 = None
        self._last_chi2 = None
        self._last_iteration = None
        self._last_reported_iteration = None
        self._best_chi2 = None
        self._best_iteration = None
        self._fitting_time = None
        self._last_progress_time = None
        self._tracking_mode = TRACKING_MODE_FIT
        self._sampler_total_iterations = None
        self._last_sampler_phase = None
        self._last_sampler_progress_percent = None
        self._last_sampler_log_posterior = None

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

        # First iteration, initialize tracking
        if self._previous_chi2 is None:
            self._previous_chi2 = reduced_chi2
            self._best_chi2 = reduced_chi2
            self._best_iteration = self._iteration

            row = [
                str(self._iteration),
                f'{reduced_chi2:.2f}',
                '',
            ]

        # Subsequent iterations, check for significant changes
        else:
            change = (self._previous_chi2 - reduced_chi2) / self._previous_chi2

            # Improvement check
            if change > SIGNIFICANT_CHANGE_THRESHOLD:
                change_in_percent = change * 100

                row = [
                    str(self._iteration),
                    f'{reduced_chi2:.2f}',
                    f'{change_in_percent:.1f}% ↓',
                ]

                self._previous_chi2 = reduced_chi2

        # Output if there is something new to display
        if row:
            self.add_tracking_info(row)

        # Update best chi-square if better
        if self._best_chi2 is None or reduced_chi2 < self._best_chi2:
            self._best_chi2 = reduced_chi2
            self._best_iteration = self._iteration

        # Store last chi-square and iteration
        self._last_chi2 = reduced_chi2
        self._last_iteration = self._iteration

        return residuals

    def track_sampler_progress(
        self,
        *,
        iteration: int,
        total_iterations: int,
        phase: str,
        progress_percent: float,
        log_posterior: float,
        reduced_chi2: float,
        elapsed_time: float,
    ) -> None:
        """Update progress from a sampler monitor.

        Parameters
        ----------
        iteration : int
            Sampler iteration or generation index.
        total_iterations : int
            Total sampler generations configured for the run.
        phase : str
            Current sampler phase, e.g. ``'burn-in'`` or ``'sampling'``.
        progress_percent : float
            Completed fraction expressed in percent.
        log_posterior : float
            Current best log-posterior implied by the sampler state.
        reduced_chi2 : float
            Best reduced chi-square implied by the current best sample.
        elapsed_time : float
            Elapsed wall time in seconds.
        """
        self._iteration = iteration
        self._tracking_mode = TRACKING_MODE_SAMPLER
        self._sampler_total_iterations = max(1, total_iterations)

        clamped_iteration = min(max(1, iteration), self._sampler_total_iterations)
        clamped_progress = min(max(progress_percent, 0.0), 100.0)
        previous_phase = self._last_sampler_phase
        self._last_sampler_phase = phase
        self._last_sampler_progress_percent = clamped_progress
        self._last_sampler_log_posterior = log_posterior

        row: list[str] = []
        if self._previous_chi2 is None or self._best_chi2 is None:
            self._previous_chi2 = reduced_chi2
            self._best_chi2 = reduced_chi2
            self._best_iteration = iteration
            self._last_progress_time = elapsed_time
            row = [
                f'{clamped_iteration}/{self._sampler_total_iterations}',
                f'{clamped_progress:.1f}%',
                f'{log_posterior:.2f}',
                phase,
            ]
        else:
            if reduced_chi2 < self._best_chi2:
                self._best_chi2 = reduced_chi2
                self._best_iteration = iteration

            if (
                iteration != self._last_reported_iteration
                and (
                    previous_phase != phase
                    or self._last_progress_time is None
                    or elapsed_time - self._last_progress_time >= SAMPLER_PROGRESS_UPDATE_SECONDS
                    or clamped_iteration >= self._sampler_total_iterations
                )
            ):
                row = [
                    f'{clamped_iteration}/{self._sampler_total_iterations}',
                    f'{clamped_progress:.1f}%',
                    f'{log_posterior:.2f}',
                    phase,
                ]
                self._last_progress_time = elapsed_time

        if row:
            self.add_tracking_info(row)

        self._last_chi2 = reduced_chi2
        self._last_iteration = iteration

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

    def stop_timer(self) -> None:
        """Stop timing and store elapsed time for the run."""
        self._end_time = time.perf_counter()
        self._fitting_time = self._end_time - self._start_time

    def start_tracking(self, minimizer_name: str, *, mode: str = TRACKING_MODE_FIT) -> None:
        """
        Initialize display and headers and announce the minimizer.

        Parameters
        ----------
        minimizer_name : str
            Name of the minimizer used for the run.
        mode : str, default='fit'
            Tracking mode for the run.
        """
        self._tracking_mode = (
            TRACKING_MODE_SAMPLER if mode == TRACKING_MODE_SAMPLER else TRACKING_MODE_FIT
        )

        if self._verbosity is VerbosityEnum.SILENT:
            return
        if self._verbosity is VerbosityEnum.SHORT:
            return

        console.print(f"🚀 Starting fit process with '{minimizer_name}'...")
        if self._tracking_mode == TRACKING_MODE_SAMPLER:
            console.print('📈 Bayesian sampling progress:')
        else:
            console.print('📈 Fit progress:')

        # Reset rows and create an environment-appropriate handle
        self._df_rows = []
        self._display_handle = _make_display_handle()

        # Initial empty table; subsequent updates will reuse the handle
        render_table(
            columns_headers=self._headers(),
            columns_alignment=self._alignments(),
            columns_data=self._df_rows,
            display_handle=self._display_handle,
        )

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
        if self._verbosity is not VerbosityEnum.FULL:
            return
        # Append and update via the active handle (Jupyter or
        # terminal live)
        render_table(
            columns_headers=self._headers(),
            columns_alignment=self._alignments(),
            columns_data=self._df_rows,
            display_handle=self._display_handle,
        )

    def finish_tracking(self) -> None:
        """Finalize progress display and print best result summary."""
        if self._tracking_mode == TRACKING_MODE_SAMPLER:
            if self._last_iteration is not None and self._sampler_total_iterations is not None:
                final_progress = self._last_sampler_progress_percent
                if final_progress is None:
                    final_progress = 100.0 * min(
                        self._last_iteration,
                        self._sampler_total_iterations,
                    ) / self._sampler_total_iterations
                row = [
                    f'{min(self._last_iteration, self._sampler_total_iterations)}/'
                    f'{self._sampler_total_iterations}',
                    f'{final_progress:.1f}%',
                    (
                        f'{self._last_sampler_log_posterior:.2f}'
                        if self._last_sampler_log_posterior is not None
                        else ''
                    ),
                    self._last_sampler_phase or 'sampling',
                ]
                if not self._df_rows or self._df_rows[-1] != row:
                    self.add_tracking_info(row)
        elif self._last_iteration is not None:
            row: list[str] = [
                str(self._last_iteration),
                f'{self._last_chi2:.2f}' if self._last_chi2 is not None else '',
                '',
            ]
            if not self._df_rows or self._df_rows[-1][:2] != row[:2]:
                self.add_tracking_info(row)

        if self._verbosity is not VerbosityEnum.FULL:
            return

        # Close terminal live if used
        if self._display_handle is not None and hasattr(self._display_handle, 'close'):
            with suppress(Exception):
                self._display_handle.close()

        if self._tracking_mode == TRACKING_MODE_SAMPLER:
            console.print('✅ Bayesian sampling complete.')
            return

        # Print best result
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
