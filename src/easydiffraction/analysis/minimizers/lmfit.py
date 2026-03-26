# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from typing import Dict
from typing import List

import lmfit

from easydiffraction.analysis.minimizers.base import MinimizerBase
from easydiffraction.analysis.minimizers.factory import MinimizerFactory
from easydiffraction.core.metadata import TypeInfo

DEFAULT_METHOD = 'leastsq'
DEFAULT_MAX_ITERATIONS = 1000


@MinimizerFactory.register
class LmfitMinimizer(MinimizerBase):
    """Minimizer using the lmfit package."""

    type_info = TypeInfo(
        tag='lmfit',
        description='LMFIT with Levenberg-Marquardt least squares',
    )

    def __init__(
        self,
        name: str = 'lmfit',
        method: str = DEFAULT_METHOD,
        max_iterations: int = DEFAULT_MAX_ITERATIONS,
    ) -> None:
        super().__init__(
            name=name,
            method=method,
            max_iterations=max_iterations,
        )

    def _prepare_solver_args(
        self,
        parameters: List[object],
    ) -> Dict[str, object]:
        """
        Prepare the solver arguments for the lmfit minimizer.

        Parameters
        ----------
        parameters : List[object]
            List of parameters to be optimized.

        Returns
        -------
        Dict[str, object]
            A dictionary containing the prepared lmfit. Parameters
            object.
        """
        engine_parameters = lmfit.Parameters()
        for param in parameters:
            engine_parameters.add(
                name=param._minimizer_uid,
                value=param.value,
                vary=param.free,
                min=param.fit_min,
                max=param.fit_max,
            )
        return {'engine_parameters': engine_parameters}

    def _run_solver(self, objective_function: object, **kwargs: object) -> object:
        """
        Run the lmfit solver.

        Parameters
        ----------
        objective_function : object
            The objective function to minimize.
        **kwargs : object
            Additional arguments for the solver.

        Returns
        -------
        object
            The result of the lmfit minimization.
        """
        engine_parameters = kwargs.get('engine_parameters')

        return lmfit.minimize(
            objective_function,
            params=engine_parameters,
            method=self.method,
            nan_policy='propagate',
            max_nfev=self.max_iterations,
        )

    def _sync_result_to_parameters(
        self,
        parameters: List[object],
        raw_result: object,
    ) -> None:
        """
        Synchronize the result from the solver to the parameters.

        Parameters
        ----------
        parameters : List[object]
            List of parameters being optimized.
        raw_result : object
            The result object returned by the solver.
        """
        param_values = raw_result.params if hasattr(raw_result, 'params') else raw_result

        for param in parameters:
            param_result = param_values.get(param._minimizer_uid)
            if param_result is not None:
                # Bypass validation but set the dirty flag so
                # _update_categories() knows work is needed.
                param._set_value_from_minimizer(param_result.value)
                param.uncertainty = getattr(param_result, 'stderr', None)

    def _check_success(self, raw_result: object) -> bool:
        """
        Determine success from lmfit MinimizerResult.

        Parameters
        ----------
        raw_result : object
            The result object returned by the solver.

        Returns
        -------
        bool
            True if the optimization was successful, False otherwise.
        """
        return getattr(raw_result, 'success', False)

    def _iteration_callback(
        self,
        params: lmfit.Parameters,
        iter: int,
        resid: object,
        *args: object,
        **kwargs: object,
    ) -> None:
        """
        Handle each iteration callback of the minimizer.

        Parameters
        ----------
        params : lmfit.Parameters
            The current parameters.
        iter : int
            The current iteration number.
        resid : object
            The residuals.
        *args : object
            Additional positional arguments.
        **kwargs : object
            Additional keyword arguments.
        """
        # Intentionally unused, required by callback signature
        del params, resid, args, kwargs
        self._iteration = iter
