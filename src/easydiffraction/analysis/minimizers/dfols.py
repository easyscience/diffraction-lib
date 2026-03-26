# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from typing import Dict
from typing import List

import numpy as np
from dfols import solve

from easydiffraction.analysis.minimizers.base import MinimizerBase
from easydiffraction.analysis.minimizers.factory import MinimizerFactory
from easydiffraction.core.metadata import TypeInfo

DEFAULT_MAX_ITERATIONS = 1000


@MinimizerFactory.register
class DfolsMinimizer(MinimizerBase):
    """
    Minimizer using the DFO-LS package (Derivative-Free Optimization for
    Least-Squares).
    """

    type_info = TypeInfo(
        tag='dfols',
        description='DFO-LS derivative-free least-squares optimization',
    )

    def __init__(
        self,
        name: str = 'dfols',
        max_iterations: int = DEFAULT_MAX_ITERATIONS,
        **kwargs: object,
    ) -> None:
        super().__init__(name=name, method=None, max_iterations=max_iterations)
        # Intentionally unused, accepted for API compatibility
        del kwargs

    def _prepare_solver_args(self, parameters: List[object]) -> Dict[str, object]:
        x0 = []
        bounds_lower = []
        bounds_upper = []
        for param in parameters:
            x0.append(param.value)
            bounds_lower.append(param.fit_min)
            bounds_upper.append(param.fit_max)
        bounds = (np.array(bounds_lower), np.array(bounds_upper))
        return {'x0': np.array(x0), 'bounds': bounds}

    def _run_solver(self, objective_function: object, **kwargs: object) -> object:
        x0 = kwargs.get('x0')
        bounds = kwargs.get('bounds')
        return solve(objective_function, x0=x0, bounds=bounds, maxfun=self.max_iterations)

    def _sync_result_to_parameters(
        self,
        parameters: List[object],
        raw_result: object,
    ) -> None:
        """
        Synchronizes the result from the solver to the parameters.

        Parameters
        ----------
        parameters : List[object]
            List of parameters being optimized.
        raw_result : object
            The result object returned by the solver.
        """
        # Ensure compatibility with raw_result coming from dfols.solve()
        result_values = raw_result.x if hasattr(raw_result, 'x') else raw_result

        for i, param in enumerate(parameters):
            # Bypass validation but set the dirty flag so
            # _update_categories() knows work is needed.
            param._set_value_from_minimizer(result_values[i])
            # DFO-LS doesn't provide uncertainties; set to None or
            # calculate later if needed
            param.uncertainty = None

    def _check_success(self, raw_result: object) -> bool:
        """
        Determines success from DFO-LS result dictionary.

        Parameters
        ----------
        raw_result : object
            The result object returned by the solver.

        Returns
        -------
        bool
            True if the optimization was successful, False otherwise.
        """
        return raw_result.flag == raw_result.EXIT_SUCCESS
