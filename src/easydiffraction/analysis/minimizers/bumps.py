# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Minimizer using the bumps package."""

from __future__ import annotations

import numpy as np
from bumps.fitproblem import FitProblem
from bumps.fitters import FITTERS
from bumps.fitters import FitDriver
from bumps.fitters import monitor as bumps_monitor
from bumps.parameter import Parameter as BumpsParameter
from scipy.optimize import OptimizeResult

from easydiffraction.analysis.minimizers.base import MinimizerBase
from easydiffraction.analysis.minimizers.enums import MinimizerTypeEnum
from easydiffraction.analysis.minimizers.factory import MinimizerFactory
from easydiffraction.core.metadata import TypeInfo

DEFAULT_METHOD = 'lm'
DEFAULT_MAX_ITERATIONS = 1000
_COVARIANCE_RELATIVE_STEP = 1e-4


class _BumpsEvaluationLimitError(RuntimeError):
    """Raised when the BUMPS residual-evaluation budget is exhausted."""

    def __init__(
        self,
        *,
        evaluation_count: int,
        parameter_values: np.ndarray,
        residuals: np.ndarray | None,
    ) -> None:
        """Record the evaluation count and last residual state."""
        super().__init__('maximum number of residual evaluations reached')
        self.evaluation_count = evaluation_count
        self.parameter_values = parameter_values
        self.residuals = residuals


class _EasyDiffractionFitness:
    """Wrap an EasyDiffraction objective in the BUMPS fitness API."""

    def __init__(
        self,
        bumps_params: list[BumpsParameter],
        objective_function: object,
        max_evaluations: int | None = None,
    ) -> None:
        """Wrap the objective and BUMPS parameters for evaluation."""
        self._bumps_params = bumps_params
        self._objective_function = objective_function
        self._max_evaluations = max_evaluations
        self._numpoints = 0
        self._evaluation_count = 0
        self._count_evaluations = True
        self._last_parameter_values: np.ndarray | None = None
        self._last_residuals: np.ndarray | None = None

    def parameters(self) -> dict[str, BumpsParameter]:
        """Return BUMPS parameters as a name-keyed dictionary."""
        return {p.name: p for p in self._bumps_params}

    def update(self) -> None:
        """Signal that parameters have changed."""

    def residuals(self) -> np.ndarray:
        """Compute residuals for the current BUMPS parameter values."""
        if (
            self._count_evaluations
            and self._max_evaluations is not None
            and self._evaluation_count >= self._max_evaluations
        ):
            last_parameter_values = self._last_parameter_values
            if last_parameter_values is None:
                last_parameter_values = np.array([p.value for p in self._bumps_params])
            raise _BumpsEvaluationLimitError(
                evaluation_count=self._evaluation_count,
                parameter_values=last_parameter_values,
                residuals=self._last_residuals,
            )

        values = np.array([p.value for p in self._bumps_params])
        r = np.asarray(self._objective_function(values), dtype=float)
        self._numpoints = len(r)
        self._last_parameter_values = values.copy()
        self._last_residuals = r.copy()
        if self._count_evaluations:
            self._evaluation_count += 1
        return r

    def nllf(self) -> float:
        """Return half the sum of squared residuals."""
        r = self.residuals()
        return 0.5 * np.sum(r**2)

    def numpoints(self) -> int:
        """Return the number of data points."""
        return self._numpoints

    @property
    def evaluation_count(self) -> int:
        """Return the live residual-evaluation count."""
        return self._evaluation_count

    def reset_evaluation_count(self) -> None:
        """Reset the residual-evaluation counter."""
        self._evaluation_count = 0

    def stop_counting_evaluations(self) -> None:
        """Freeze residual-evaluation counting."""
        self._count_evaluations = False

    @property
    def last_residuals(self) -> np.ndarray | None:
        """Return the last successful residual vector."""
        return self._last_residuals

    def last_reduced_chi_square(self, *, n_parameters: int) -> float | None:
        """Return reduced chi-square for the last residual vector."""
        if self._last_residuals is None:
            return None

        chi_square = float(np.sum(self._last_residuals**2))
        dof = len(self._last_residuals) - n_parameters
        if dof <= 0:
            return chi_square
        return chi_square / dof


class _BumpsProgressMonitor(bumps_monitor.Monitor):
    """Report live BUMPS fit evaluation counts."""

    def __init__(
        self,
        *,
        tracker: object,
        fitness: _EasyDiffractionFitness,
        n_points: int,
        n_parameters: int,
    ) -> None:
        """Store the tracker and fit dimensions for reporting."""
        self._tracker = tracker
        self._fitness = fitness
        self._n_points = n_points
        self._n_parameters = n_parameters

    @staticmethod
    def config_history(history: object) -> None:
        """
        Declare the history fields needed for deterministic progress.
        """
        history.requires(time=1, step=1, value=1)

    def __call__(self, history: object) -> None:
        """Forward deterministic BUMPS progress to the fit tracker."""
        if not history.time or not history.value:
            return

        self._tracker.track_fit_progress(
            iteration=self._reported_iteration(history),
            reduced_chi2=self._reduced_chi_square_from_nllf(float(history.value[0])),
            elapsed_time=float(history.time[0]),
        )

    def final(self, history: object, best: dict[str, object]) -> None:
        """Record the final BUMPS state in the fit tracker."""
        if not history.time or best.get('value') is None:
            return

        self._tracker.track_fit_progress(
            iteration=self._reported_iteration(history),
            reduced_chi2=self._reduced_chi_square_from_nllf(float(best['value'])),
            elapsed_time=float(history.time[0]),
        )

    def _reported_iteration(self, history: object) -> int:
        """Return the live fit evaluation count shown in progress."""
        if self._fitness.evaluation_count > 0:
            return self._fitness.evaluation_count

        step = int(history.step[0]) if history.step else 0
        return max(1, step)

    def _reduced_chi_square_from_nllf(self, nllf: float) -> float:
        """Convert negative log-likelihood to reduced chi-square."""
        dof = self._n_points - self._n_parameters
        chi_square = 2.0 * nllf
        if dof <= 0:
            return chi_square
        return chi_square / dof


@MinimizerFactory.register
class BumpsMinimizer(MinimizerBase):
    """Minimizer using the BUMPS package."""

    type_info = TypeInfo(
        tag=MinimizerTypeEnum.BUMPS,
        description='Bumps library using the default Levenberg-Marquardt method',
    )

    def __init__(
        self,
        name: str = MinimizerTypeEnum.BUMPS,
        method: str = DEFAULT_METHOD,
        max_iterations: int = DEFAULT_MAX_ITERATIONS,
    ) -> None:
        """Initialize the BUMPS minimizer with default settings."""
        super().__init__(
            name=name,
            method=method,
            max_iterations=max_iterations,
        )

    @staticmethod
    def _tracks_progress_via_solver_monitor() -> bool:
        """
        Use BUMPS monitor callbacks for live deterministic progress.
        """
        return True

    def _prepare_solver_args(  # noqa: PLR6301
        self,
        parameters: list[object],
    ) -> dict[str, object]:
        """
        Prepare BUMPS parameters from EasyDiffraction parameters.

        Parameters
        ----------
        parameters : list[object]
            List of parameters to be optimized.

        Returns
        -------
        dict[str, object]
            Dictionary containing the bumps parameter list.
        """
        bumps_params = []
        for param in parameters:
            bp = BumpsParameter(
                value=param.value,
                name=param._minimizer_uid,
            )
            lo = param.fit_min
            hi = param.fit_max
            bp.range(lo, hi)
            bumps_params.append(bp)
        return {'bumps_params': bumps_params}

    def _run_solver(
        self,
        objective_function: object,
        **kwargs: object,
    ) -> object:
        """
        Run the BUMPS solver.

        Uses FitDriver directly instead of bumps.fitters.fit() to skip
        the expensive post-fit stderr/Jacobian computation that would
        trigger extra objective-function evaluations.

        Parameters
        ----------
        objective_function : object
            The objective function to minimize.
        **kwargs : object
            Additional arguments for the solver.

        Returns
        -------
        object
            A scipy OptimizeResult with the optimized values.
        """
        bumps_params = kwargs.get('bumps_params')
        fitness = _EasyDiffractionFitness(
            bumps_params,
            objective_function,
            max_evaluations=self.max_iterations,
        )
        fitness.nllf()  # pre-compute so numpoints() is valid
        fitness.reset_evaluation_count()
        problem = FitProblem(fitness)
        progress_monitor = _BumpsProgressMonitor(
            tracker=self.tracker,
            fitness=fitness,
            n_points=fitness.numpoints(),
            n_parameters=len(bumps_params),
        )

        fitclass = next(cls for cls in FITTERS if cls.id == self.method)
        driver = FitDriver(
            fitclass=fitclass,
            problem=problem,
            monitors=[progress_monitor],
            steps=self.max_iterations,
        )
        driver.clip()
        try:
            x, fx = driver.fit()
            evaluation_limit_reached = False
            evaluation_limit_message = 'successful termination'
        except _BumpsEvaluationLimitError as exc:
            x, fx, evaluation_limit_message = self._handle_evaluation_limit(
                exc=exc,
                fitness=fitness,
                n_parameters=len(bumps_params),
            )
            evaluation_limit_reached = True
        finally:
            fitness.stop_counting_evaluations()

        success = x is not None and not evaluation_limit_reached
        if success:
            problem.setp(x)

        return self._build_optimize_result(
            bumps_params=bumps_params,
            fitness=fitness,
            success=success,
            evaluation_limit_reached=evaluation_limit_reached,
            evaluation_limit_message=evaluation_limit_message,
            function_value=fx,
        )

    def _handle_evaluation_limit(
        self,
        *,
        exc: _BumpsEvaluationLimitError,
        fitness: _EasyDiffractionFitness,
        n_parameters: int,
    ) -> tuple[np.ndarray, None, str]:
        """
        Build a partial result when the evaluation budget is exhausted.
        """
        reduced_chi2 = self._reduced_chi_square_from_limit(
            exc=exc,
            fitness=fitness,
            n_parameters=n_parameters,
        )
        if reduced_chi2 is not None:
            elapsed_time = self.tracker._current_elapsed_time()
            self.tracker.track_fit_progress(
                iteration=exc.evaluation_count,
                reduced_chi2=reduced_chi2,
                elapsed_time=0.0 if elapsed_time is None else elapsed_time,
            )
        return exc.parameter_values.copy(), None, str(exc)

    @staticmethod
    def _reduced_chi_square_from_limit(
        *,
        exc: _BumpsEvaluationLimitError,
        fitness: _EasyDiffractionFitness,
        n_parameters: int,
    ) -> float | None:
        """Return reduced chi-square at the evaluation cutoff."""
        if exc.residuals is not None:
            chi_square = float(np.sum(exc.residuals**2))
            dof = len(exc.residuals) - n_parameters
            return chi_square if dof <= 0 else chi_square / dof
        if fitness.last_residuals is None:
            return None
        return fitness.last_reduced_chi_square(n_parameters=n_parameters)

    def _build_optimize_result(
        self,
        *,
        bumps_params: list[BumpsParameter],
        fitness: _EasyDiffractionFitness,
        success: bool,
        evaluation_limit_reached: bool,
        evaluation_limit_message: str,
        function_value: float | None,
    ) -> OptimizeResult:
        """Convert the BUMPS solver outcome into an OptimizeResult."""
        # Read values back from bumps Parameters in our original order.
        # FitProblem sorts parameters alphabetically, so x from
        # driver.fit() uses that sorted order — not ours.
        result_x = np.array([p.value for p in bumps_params])
        covariance, stderr = (
            self._compute_covariance(bumps_params, fitness) if success else (None, None)
        )
        return OptimizeResult(
            x=result_x,
            dx=stderr,
            fun=function_value,
            success=success,
            status=0 if success else 5 if evaluation_limit_reached else -1,
            message='successful termination' if success else evaluation_limit_message,
            covar=covariance,
            var_names=[p.name for p in bumps_params],
        )

    def _compute_covariance(  # ruff: ignore[no-self-use, too-many-locals]
        self,
        bumps_params: list[BumpsParameter],
        fitness: _EasyDiffractionFitness,
    ) -> tuple[np.ndarray | None, np.ndarray | None]:
        """
        Compute covariance matrix and standard errors from a Jacobian.

        Parameters
        ----------
        bumps_params : list[BumpsParameter]
            Bumps parameters at their optimal values.
        fitness : _EasyDiffractionFitness
            Fitness object used to evaluate residuals.

        Returns
        -------
        tuple[np.ndarray | None, np.ndarray | None]
            ``(covariance_matrix, standard_errors)`` or ``(None, None)``
            when the computation fails.
        """
        r0 = fitness.residuals()
        n_points = len(r0)
        n_params = len(bumps_params)
        if n_points <= n_params:
            return None, None

        jacobian = np.empty((n_points, n_params))
        for j in range(n_params):
            orig = bumps_params[j].value
            h = _COVARIANCE_RELATIVE_STEP * max(abs(orig), 1.0)
            try:
                bumps_params[j].value = orig + h
                residuals_upper = fitness.residuals()
                bumps_params[j].value = orig - h
                residuals_lower = fitness.residuals()
            finally:
                bumps_params[j].value = orig
            jacobian[:, j] = (residuals_upper - residuals_lower) / (2.0 * h)

        chi2_reduced = np.sum(r0**2) / (n_points - n_params)
        try:
            _u, singular_values, vh = np.linalg.svd(jacobian, full_matrices=False)
        except np.linalg.LinAlgError:
            return None, None

        tolerance = max(jacobian.shape) * np.finfo(float).eps * singular_values[0]
        if len(singular_values) < n_params or singular_values[-1] <= tolerance:
            return None, None

        inverse_squared = 1.0 / singular_values**2
        cov = (vh.T * inverse_squared) @ vh * chi2_reduced
        cov = (cov + cov.T) / 2.0

        stderr = np.sqrt(np.clip(np.diag(cov), 0.0, None))
        return cov, stderr

    def _sync_result_to_parameters(  # noqa: PLR6301
        self,
        parameters: list[object],
        raw_result: object,
    ) -> None:
        """
        Synchronize the solver result back to the parameters.

        Parameters
        ----------
        parameters : list[object]
            List of parameters being optimized.
        raw_result : object
            The result object returned by the solver, or a numpy array
            during optimization.
        """
        if hasattr(raw_result, 'x'):
            values = raw_result.x
            uncertainties = getattr(raw_result, 'dx', None)
        else:
            values = raw_result
            uncertainties = None

        for i, param in enumerate(parameters):
            param._set_value_from_minimizer(float(values[i]))
            if uncertainties is not None and i < len(uncertainties):
                param.uncertainty = float(uncertainties[i])
            else:
                param.uncertainty = None

    def _check_success(self, raw_result: object) -> bool:  # noqa: PLR6301
        """
        Determine success from a BUMPS OptimizeResult.

        Parameters
        ----------
        raw_result : object
            The result object returned by the solver.

        Returns
        -------
        bool
            True if the optimization was successful.
        """
        return getattr(raw_result, 'success', False)
