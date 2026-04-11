# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Minimizer using the bumps package."""

from __future__ import annotations

import numpy as np
from bumps.fitproblem import FitProblem
from bumps.fitters import FITTERS
from bumps.fitters import FitDriver
from bumps.parameter import Parameter as BumpsParameter
from scipy.optimize import OptimizeResult

from easydiffraction.analysis.minimizers.base import MinimizerBase
from easydiffraction.analysis.minimizers.enums import MinimizerTypeEnum
from easydiffraction.analysis.minimizers.factory import MinimizerFactory
from easydiffraction.core.metadata import TypeInfo

DEFAULT_METHOD = 'lm'
DEFAULT_MAX_ITERATIONS = 1000


class _EasyDiffractionFitness:
    """
    Adaptor wrapping an EasyDiffraction objective into bumps Fitness.
    """

    def __init__(
        self,
        bumps_params: list[BumpsParameter],
        objective_function: object,
    ) -> None:
        self._bumps_params = bumps_params
        self._objective_function = objective_function
        self._numpoints = 0

    def parameters(self) -> dict[str, BumpsParameter]:
        """Return bumps parameters as a name-keyed dictionary."""
        return {p.name: p for p in self._bumps_params}

    def update(self) -> None:
        """Signal that parameters have changed (no-op)."""

    def residuals(self) -> np.ndarray:
        """Compute residuals using current bumps parameter values."""
        values = np.array([p.value for p in self._bumps_params])
        r = self._objective_function(values)
        self._numpoints = len(r)
        return r

    def nllf(self) -> float:
        """
        Negative log-likelihood as half the sum of squared residuals.
        """
        r = self.residuals()
        return 0.5 * np.sum(r**2)

    def numpoints(self) -> int:
        """Return the number of data points."""
        return self._numpoints


@MinimizerFactory.register
class BumpsMinimizer(MinimizerBase):
    """Minimizer using the bumps package."""

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
        super().__init__(
            name=name,
            method=method,
            max_iterations=max_iterations,
        )

    def _prepare_solver_args(  # noqa: PLR6301
        self,
        parameters: list[object],
    ) -> dict[str, object]:
        """
        Prepare bumps parameters from EasyDiffraction parameters.

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
        Run the bumps solver.

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
        fitness = _EasyDiffractionFitness(bumps_params, objective_function)
        fitness.nllf()  # pre-compute so numpoints() is valid
        problem = FitProblem(fitness)

        fitclass = next(cls for cls in FITTERS if cls.id == self.method)
        driver = FitDriver(
            fitclass=fitclass,
            problem=problem,
            monitors=[],
            steps=self.max_iterations,
        )
        driver.clip()
        x, fx = driver.fit()

        success = x is not None
        if success:
            problem.setp(x)

        # Read values back from bumps Parameters in our original order.
        # FitProblem sorts parameters alphabetically, so x from
        # driver.fit() uses that sorted order — not ours.
        result_x = np.array([p.value for p in bumps_params])

        covar, stderr = (
            self._compute_covariance(bumps_params, fitness) if success else (None, None)
        )
        var_names = [p.name for p in bumps_params]

        return OptimizeResult(
            x=result_x,
            dx=stderr,
            fun=fx,
            success=success,
            status=0 if success else -1,
            message='successful termination' if success else 'fit failed',
            covar=covar,
            var_names=var_names,
        )

    def _compute_covariance(  # noqa: PLR6301
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

        step = np.sqrt(np.finfo(float).eps)
        jacobian = np.empty((n_points, n_params))
        for j in range(n_params):
            orig = bumps_params[j].value
            h = step * max(abs(orig), 1.0)
            bumps_params[j].value = orig + h
            jacobian[:, j] = (fitness.residuals() - r0) / h
            bumps_params[j].value = orig

        chi2_reduced = np.sum(r0**2) / (n_points - n_params)
        try:
            cov = np.linalg.inv(jacobian.T @ jacobian) * chi2_reduced
        except np.linalg.LinAlgError:
            return None, None

        stderr = np.sqrt(np.abs(np.diag(cov)))
        return cov, stderr

    def _sync_result_to_parameters(  # noqa: PLR6301
        self,
        parameters: list[object],
        raw_result: object,
    ) -> None:
        """
        Synchronize the result from the solver to the parameters.

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
        Determine success from bumps OptimizeResult.

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
