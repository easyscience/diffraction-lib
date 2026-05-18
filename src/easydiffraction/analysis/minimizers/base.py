# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from abc import ABC
from abc import abstractmethod
from collections.abc import Callable
from typing import Any

import numpy as np

from easydiffraction.analysis.fit_helpers.reporting import FitResults
from easydiffraction.analysis.fit_helpers.tracking import FitProgressTracker
from easydiffraction.utils.enums import VerbosityEnum
from easydiffraction.utils.logging import log

BOUNDARY_PROXIMITY_FRACTION = 0.01


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
        self.name: str | None = name
        self.method: str | None = method
        self.max_iterations: int | None = max_iterations
        self.result: FitResults | None = None
        self._previous_chi2: float | None = None
        self._iteration: int | None = None
        self._best_chi2: float | None = None
        self._best_iteration: int | None = None
        self._fitting_time: float | None = None
        self._resolved_random_seed: int | None = None
        self.tracker: FitProgressTracker = FitProgressTracker()

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
        self.tracker.start_tracking(minimizer_name, mode=self._tracking_mode())
        self.tracker.start_timer()

    def _stop_tracking(self) -> None:
        """Stop timer and finalize tracking."""
        self.tracker.stop_timer()
        self.tracker.finish_tracking()

    @staticmethod
    def _tracking_mode() -> str:
        """Return the tracker mode for the current minimizer."""
        return 'fit'

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
        use_physical_limits: bool = False,
        random_seed: int | None = None,
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
        use_physical_limits : bool, default=False
            When ``True``, fall back to physical limits from the value
            spec for parameters whose ``fit_min``/``fit_max`` are
            unbounded.
        random_seed : int | None, default=None
            Optional random seed passed to stochastic minimizers.

        Returns
        -------
        FitResults
            FitResults with success flag, best chi2 and timing.
        """
        if use_physical_limits:
            self._apply_physical_limits(parameters)

        resolved_random_seed = self._resolve_random_seed(random_seed)

        minimizer_name = self.name or 'Unnamed Minimizer'
        if self.method is not None and f'({self.method})' not in minimizer_name:
            minimizer_name += f' ({self.method})'

        self._start_tracking(minimizer_name, verbosity=verbosity)

        try:
            solver_args = self._prepare_solver_args(parameters)
            if resolved_random_seed is not None:
                solver_args['random_seed'] = resolved_random_seed
            raw_result = self._run_solver(objective_function, **solver_args)
        except Exception:
            self._stop_tracking()
            raise

        return self._finalize_fit(parameters, raw_result)

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
