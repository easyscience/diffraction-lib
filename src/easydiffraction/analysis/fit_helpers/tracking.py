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
SAMPLER_PROGRESS_STATUS = 'sampling...'
DEFAULT_HEADERS = ['iteration', 'χ²', 'improvement [%]']
DEFAULT_ALIGNMENTS = ['center', 'center', 'center']


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
        self._best_chi2: float | None = None
        self._best_iteration: int | None = None
        self._fitting_time: float | None = None
        self._verbosity: VerbosityEnum = VerbosityEnum.FULL
        self._last_progress_time: float | None = None

        self._df_rows: list[list[str]] = []
        self._display_handle: object | None = None
        self._live: object | None = None

    def reset(self) -> None:
        """Reset internal state before a new optimization run."""
        self._iteration = 0
        self._previous_chi2 = None
        self._last_chi2 = None
        self._last_iteration = None
        self._best_chi2 = None
        self._best_iteration = None
        self._fitting_time = None
        self._last_progress_time = None

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
        if reduced_chi2 < self._best_chi2:
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
        reduced_chi2: float,
        elapsed_time: float,
        status: str = SAMPLER_PROGRESS_STATUS,
    ) -> None:
        """Update progress from a sampler monitor.

        Parameters
        ----------
        iteration : int
            Sampler iteration or generation index.
        reduced_chi2 : float
            Best reduced chi-square implied by the current best sample.
        elapsed_time : float
            Elapsed wall time in seconds.
        status : str, default='sampling...'
            Text shown for periodic progress rows without a chi-square
            improvement.
        """
        self._iteration = iteration

        row: list[str] = []
        if self._previous_chi2 is None or self._best_chi2 is None:
            self._previous_chi2 = reduced_chi2
            self._best_chi2 = reduced_chi2
            self._best_iteration = iteration
            self._last_progress_time = elapsed_time
            row = [
                str(iteration),
                f'{reduced_chi2:.2f}',
                '',
            ]
        else:
            if reduced_chi2 < self._best_chi2:
                self._best_chi2 = reduced_chi2
                self._best_iteration = iteration

            change = 0.0
            if self._previous_chi2 > 0:
                change = (self._previous_chi2 - reduced_chi2) / self._previous_chi2

            if change > SIGNIFICANT_CHANGE_THRESHOLD:
                row = [
                    str(iteration),
                    f'{reduced_chi2:.2f}',
                    f'{change * 100:.1f}% ↓',
                ]
                self._previous_chi2 = reduced_chi2
                self._last_progress_time = elapsed_time
            elif (
                self._last_progress_time is None
                or elapsed_time - self._last_progress_time >= SAMPLER_PROGRESS_UPDATE_SECONDS
            ):
                row = [
                    str(iteration),
                    f'{self._best_chi2:.2f}',
                    status,
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

    def start_tracking(self, minimizer_name: str) -> None:
        """
        Initialize display and headers and announce the minimizer.

        Parameters
        ----------
        minimizer_name : str
            Name of the minimizer used for the run.
        """
        if self._verbosity is VerbosityEnum.SILENT:
            return
        if self._verbosity is VerbosityEnum.SHORT:
            return

        console.print(f"🚀 Starting fit process with '{minimizer_name}'...")
        console.print('📈 Goodness-of-fit (reduced χ²) change:')

        # Reset rows and create an environment-appropriate handle
        self._df_rows = []
        self._display_handle = _make_display_handle()

        # Initial empty table; subsequent updates will reuse the handle
        render_table(
            columns_headers=DEFAULT_HEADERS,
            columns_alignment=DEFAULT_ALIGNMENTS,
            columns_data=self._df_rows,
            display_handle=self._display_handle,
        )

    def add_tracking_info(self, row: list[str]) -> None:
        """
        Append a formatted row to the progress display.

        Parameters
        ----------
        row : list[str]
            Columns corresponding to DEFAULT_HEADERS.
        """
        self._df_rows.append(row)
        if self._verbosity is not VerbosityEnum.FULL:
            return
        # Append and update via the active handle (Jupyter or
        # terminal live)
        render_table(
            columns_headers=DEFAULT_HEADERS,
            columns_alignment=DEFAULT_ALIGNMENTS,
            columns_data=self._df_rows,
            display_handle=self._display_handle,
        )

    def finish_tracking(self) -> None:
        """Finalize progress display and print best result summary."""
        if self._last_iteration is not None:
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

        # Print best result
        console.print(
            f'🏆 Best goodness-of-fit (reduced χ²) is {self._best_chi2:.2f} '
            f'at iteration {self._best_iteration}'
        )
        console.print('✅ Fitting complete.')
