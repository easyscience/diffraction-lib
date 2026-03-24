# SPDX-FileCopyrightText: 2021-2026 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from typing import Any
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
    """Minimizer using the DFO-LS package (Derivative-Free Optimization
    for Least-Squares).
    """

    type_info = TypeInfo(
        tag='dfols',
        description='DFO-LS derivative-free least-squares optimization',
    )

    def __init__(
        self,
        name: str = 'dfols',
        max_iterations: int = DEFAULT_MAX_ITERATIONS,
        **kwargs: Any,
    ) -> None:
        super().__init__(name=name, method=None, max_iterations=max_iterations)
        # Intentionally unused, accepted for API compatibility
        del kwargs

    def _prepare_solver_args(self, parameters: List[Any]) -> Dict[str, Any]:
        x0 = []
        bounds_lower = []
        bounds_upper = []
        for param in parameters:
            x0.append(param.value)
            bounds_lower.append(param.fit_min)
            bounds_upper.append(param.fit_max)
        bounds = (np.array(bounds_lower), np.array(bounds_upper))
        return {'x0': np.array(x0), 'bounds': bounds}

    def _run_solver(self, objective_function: Any, **kwargs: Any) -> Any:
        x0 = kwargs.get('x0')
        bounds = kwargs.get('bounds')
        return solve(objective_function, x0=x0, bounds=bounds, maxfun=self.max_iterations)

    def _sync_result_to_parameters(
        self,
        parameters: List[Any],
        raw_result: Any,
    ) -> None:
        """Synchronizes the result from the solver to the parameters.

        Args:
            parameters: List of parameters being optimized.
            raw_result: The result object returned by the solver.
        """
        # Ensure compatibility with raw_result coming from dfols.solve()
        result_values = raw_result.x if hasattr(raw_result, 'x') else raw_result

        for i, param in enumerate(parameters):
            # Write _value directly, bypassing the value setter.
            # See lmfit.py for rationale (validators block trial values,
            # and validation is a performance overhead during fitting).
            param._value = result_values[i]
            # DFO-LS doesn't provide uncertainties; set to None or
            # calculate later if needed
            param.uncertainty = None

    def _check_success(self, raw_result: Any) -> bool:
        """Determines success from DFO-LS result dictionary.

        Args:
            raw_result: The result object returned by the solver.

        Returns:
            True if the optimization was successful, False otherwise.
        """
        return raw_result.flag == raw_result.EXIT_SUCCESS
