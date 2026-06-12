# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Abstract base class for pluggable least-squares minimizers."""

from abc import ABC
from abc import abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import numpy as np

from easydiffraction.analysis.fit_helpers.reporting import FitResults
from easydiffraction.analysis.fit_helpers.tracking import FitProgressTracker
from easydiffraction.utils.enums import VerbosityEnum
from easydiffraction.utils.logging import log

BOUNDARY_PROXIMITY_FRACTION = 0.01


@dataclass(frozen=True, slots=True)
class MinimizerFitOptions:
    """Execution options for one minimizer run."""

    finalize_tracking: bool = True
    use_physical_limits: bool = False
    random_seed: int | None = None
    resume: bool = False
    extra_steps: int | None = None


class MinimizerBase(ABC):
    """
    Abstract base for concrete minimizers.

    Contract: - Subclasses must implement ``_prepare_solver_args``,
    ``_run_solver``, ``_sync_result_to_parameters`` and
    ``_check_success``. - The ``fit`` method orchestrates the full
    workflow and returns     :class:`FitResults`.
    """

    def __init__(
        self,
        name: str | None = None,
        method: str | None = None,
        max_iterations: int | None = None,
    ) -> None:
        """Initialize the minimizer with optional configuration."""
        self.name: str | None = name
        self.method: str | None = method
        self._max_iterations: int | None = max_iterations
        self.result: FitResults | None = None
        self._previous_chi2: float | None = None
        self._best_chi2: float | None = None
        self._best_iteration: int | None = None
        self._fitting_time: float | None = None
        self._resolved_random_seed: int | None = None
        self._tracking_active: bool = False
        self._timing_finalized: bool = False
        self._deferred_warning_messages: list[str] = []
        self.tracker: FitProgressTracker = FitProgressTracker()

    @property
    def max_iterations(self) -> int | None:
        """User-facing iteration limit for the current minimizer."""
        return self._max_iterations

    @max_iterations.setter
    def max_iterations(self, value: int | None) -> None:
        """Set the user-facing iteration limit."""
        self._max_iterations = value

    def _start_tracking(
        self,
        minimizer_name: str,
        verbosity: VerbosityEnum = VerbosityEnum.FULL,
    ) -> None:
        """
        Initialize progress tracking and timer.

        Parameters
        ----------
        minimizer_name : str
            Human-readable name shown in progress.
        verbosity : VerbosityEnum, default=VerbosityEnum.FULL
            Console output verbosity.
        """
        self.tracker.reset()
        self.tracker._verbosity = verbosity
        self._tracking_active = True
        self._timing_finalized = False
        self._deferred_warning_messages = []
        self.tracker.start_tracking(minimizer_name, mode=self._tracking_mode())
        self.tracker.start_timer()

    def _finalize_timing(self) -> None:
        """
        Stop the timer and propagate fitting_time to the result.

        Idempotent: subsequent calls within the same run are no-ops, so
        callers can finalize timing before post-processing without the
        later display teardown overwriting the recorded duration.
        """
        if not self._tracking_active or self._timing_finalized:
            return
        self.tracker.stop_timer()
        if self.result is not None:
            self.result.fitting_time = self.tracker.fitting_time
        self._timing_finalized = True

    def _stop_tracking(self) -> None:
        """Stop timer and finalize tracking."""
        if not self._tracking_active:
            self._emit_deferred_warnings()
            return

        self._finalize_timing()
        self._tracking_active = False
        self.tracker.finish_tracking()
        self._emit_deferred_warnings()

    def _warn_after_tracking(self, message: str) -> None:
        """Log immediately or defer a warning until tracking stops."""
        if self._tracking_active:
            self._deferred_warning_messages.append(message)
            return

        log.warning(message)

    def _emit_deferred_warnings(self) -> None:
        """Flush warnings deferred during live progress display."""
        while self._deferred_warning_messages:
            log.warning(self._deferred_warning_messages.pop(0))

    @staticmethod
    def _tracking_mode() -> str:
        """Return the tracker mode for the current minimizer."""
        return 'fit'

    @staticmethod
    def _tracks_progress_via_solver_monitor() -> bool:
        """Return whether live progress comes from solver callbacks."""
        return False

    @abstractmethod
    def _prepare_solver_args(self, parameters: list[Any]) -> dict[str, Any]:
        """
        Prepare keyword-arguments for the underlying solver.

        Parameters
        ----------
        parameters : list[Any]
            List of free parameters to be fitted.

        Returns
        -------
        dict[str, Any]
            Mapping of keyword arguments to pass into ``_run_solver``.
        """

    @abstractmethod
    def _run_solver(
        self,
        objective_function: Callable[..., object],
        engine_parameters: dict[str, object],
    ) -> object:
        """Execute the concrete solver and return its raw result."""

    @abstractmethod
    def _sync_result_to_parameters(
        self,
        raw_result: object,
        parameters: list[object],
    ) -> None:
        """Copy raw_result values back to parameters in-place."""

    def _finalize_fit(
        self,
        parameters: list[object],
        raw_result: object,
    ) -> FitResults:
        """
        Build :class:`FitResults` and store it on ``self.result``.

        Parameters
        ----------
        parameters : list[object]
            Parameters after the solver finished.
        raw_result : object
            Backend-specific solver output object.

        Returns
        -------
        FitResults
            Aggregated outcome of the fit.
        """
        self._sync_result_to_parameters(parameters, raw_result)
        self._warn_boundary_parameters(parameters)
        self._warn_physical_limit_violations(parameters)
        success = self._check_success(raw_result)
        self.result = self._build_fit_results(
            parameters=parameters,
            raw_result=raw_result,
            success=success,
        )
        return self.result

    def _build_fit_results(
        self,
        *,
        parameters: list[object],
        raw_result: object,
        success: bool,
    ) -> FitResults:
        """
        Build the final fit-result object for this minimizer.

        Parameters
        ----------
        parameters : list[object]
            Parameters after the solver finished.
        raw_result : object
            Backend-specific solver output object.
        success : bool
            Whether the minimizer considers the run successful.

        Returns
        -------
        FitResults
            Aggregated outcome of the fit.
        """
        return FitResults(
            success=success,
            parameters=parameters,
            reduced_chi_square=self.tracker.best_chi2,
            engine_result=raw_result,
            starting_parameters=parameters,
            fitting_time=self.tracker.fitting_time,
        )

    @staticmethod
    def _warn_boundary_parameters(parameters: list[object]) -> None:
        """
        Warn if any parameter is near its fit bounds after fitting.
        """
        for param in parameters:
            v = param.value
            lo, hi = param.fit_min, param.fit_max
            span = hi - lo
            if not np.isfinite(span):
                # One-sided or unbounded — check absolute proximity
                if np.isfinite(lo) and abs(v - lo) < BOUNDARY_PROXIMITY_FRACTION * max(
                    abs(lo), 1.0
                ):
                    log.warning(
                        f"Parameter '{param.unique_name}' ({v}) is at its lower "
                        f'bound ({lo}). Consider widening fit_min.'
                    )
                if np.isfinite(hi) and abs(v - hi) < BOUNDARY_PROXIMITY_FRACTION * max(
                    abs(hi), 1.0
                ):
                    log.warning(
                        f"Parameter '{param.unique_name}' ({v}) is at its upper "
                        f'bound ({hi}). Consider widening fit_max.'
                    )
            elif span > 0:
                tol = BOUNDARY_PROXIMITY_FRACTION * span
                if (v - lo) < tol:
                    log.warning(
                        f"Parameter '{param.unique_name}' ({v}) is at its lower "
                        f'bound ({lo}). Consider widening fit_min.'
                    )
                if (hi - v) < tol:
                    log.warning(
                        f"Parameter '{param.unique_name}' ({v}) is at its upper "
                        f'bound ({hi}). Consider widening fit_max.'
                    )

    @staticmethod
    def _apply_physical_limits(parameters: list[object]) -> None:
        """
        Set fit bounds from physical limits for unbounded parameters.

        For each parameter whose ``fit_min`` is ``-inf``, replace it
        with the lower physical limit from the value spec.  Likewise for
        ``fit_max`` and the upper physical limit.

        Parameters
        ----------
        parameters : list[object]
            Free parameters to adjust.
        """
        for param in parameters:
            if param.fit_min == -np.inf:
                phys_lo = param._physical_lower_bound()
                if np.isfinite(phys_lo):
                    param.fit_min = phys_lo
            if param.fit_max == np.inf:
                phys_hi = param._physical_upper_bound()
                if np.isfinite(phys_hi):
                    param.fit_max = phys_hi

    @staticmethod
    def _warn_physical_limit_violations(parameters: list[object]) -> None:
        """
        Flag parameters outside their physical limits.

        Sets ``param._outside_physical_limits = True`` on any parameter
        whose value falls outside its physical bounds.

        Parameters
        ----------
        parameters : list[object]
            Parameters after fitting.
        """
        for param in parameters:
            lo = param._physical_lower_bound()
            hi = param._physical_upper_bound()
            outside = False
            if np.isfinite(lo) and param.value < lo:
                log.warning(
                    f"Parameter '{param.unique_name}' ({param.value:.8f}) is below "
                    f'its physical lower limit ({lo}).'
                )
                outside = True
            if np.isfinite(hi) and param.value > hi:
                log.warning(
                    f"Parameter '{param.unique_name}' ({param.value:.8f}) is above "
                    f'its physical upper limit ({hi}).'
                )
                outside = True
            param._outside_physical_limits = outside

    @abstractmethod
    def _check_success(self, raw_result: object) -> bool:
        """Determine whether the fit was successful."""

    def _resolve_random_seed(self, random_seed: int | None) -> int | None:
        """
        Validate or normalize the random seed for this minimizer.

        Parameters
        ----------
        random_seed : int | None
            User-provided random seed.

        Returns
        -------
        int | None
            Seed accepted by the minimizer, or ``None`` when not used.

        Raises
        ------
        ValueError
            If this minimizer does not support ``random_seed``.
        """
        if random_seed is None:
            self._resolved_random_seed = None
            return None

        minimizer_name = self.name or self.__class__.__name__
        msg = f"Minimizer '{minimizer_name}' does not support random_seed."
        raise ValueError(msg)

    def fit(
        self,
        parameters: list[object],
        objective_function: Callable[..., object],
        verbosity: VerbosityEnum = VerbosityEnum.FULL,
        *,
        options: MinimizerFitOptions | None = None,
    ) -> FitResults:
        """
        Run the full minimization workflow.

        Parameters
        ----------
        parameters : list[object]
            Free parameters to optimize.
        objective_function : Callable[..., object]
            Callable returning residuals for a given set of engine
            arguments.
        verbosity : VerbosityEnum, default=VerbosityEnum.FULL
            Console output verbosity.
        options : MinimizerFitOptions | None, default=None
            Execution options controlling limits, randomness, resume,
            and tracker finalization.

        Returns
        -------
        FitResults
            FitResults with success flag, best chi2 and timing.

        Raises
        ------
        NotImplementedError
            If resume is requested for a minimizer that does not support
            it.
        """
        fit_options = options or MinimizerFitOptions()
        if fit_options.resume:
            minimizer_name = self.name or self.__class__.__name__
            msg = f"Minimizer '{minimizer_name}' does not support resume."
            raise NotImplementedError(msg)

        if fit_options.use_physical_limits:
            self._apply_physical_limits(parameters)

        resolved_random_seed = self._resolve_random_seed(fit_options.random_seed)

        minimizer_name = self.name or 'Unnamed Minimizer'
        if self.method is not None and f'({self.method})' not in minimizer_name:
            minimizer_name += f' ({self.method})'

        self._start_tracking(minimizer_name, verbosity=verbosity)

        try:
            solver_args = self._prepare_solver_args(parameters)
            if resolved_random_seed is not None:
                solver_args['random_seed'] = resolved_random_seed
            raw_result = self._run_solver(objective_function, **solver_args)
            return self._finalize_fit(parameters, raw_result)
        finally:
            if fit_options.finalize_tracking:
                self._stop_tracking()

    def _objective_function(
        self,
        engine_params: dict[str, object],
        parameters: list[object],
        structures: object,
        experiments: object,
        calculator: object,
    ) -> np.ndarray:
        """Default objective helper computing residuals array."""
        return self._compute_residuals(
            engine_params,
            parameters,
            structures,
            experiments,
            calculator,
        )

    def _create_objective_function(
        self,
        parameters: list[object],
        structures: object,
        experiments: object,
        calculator: object,
    ) -> Callable[[dict[str, object]], np.ndarray]:
        """Return a closure capturing problem context for the solver."""
        return lambda engine_params: self._objective_function(
            engine_params,
            parameters,
            structures,
            experiments,
            calculator,
        )
