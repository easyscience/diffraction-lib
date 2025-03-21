import numpy as np
from dfols import solve
from .base import MinimizerBase, FitResults

DEFAULT_MAX_ITERATIONS = 1000

class DfolsMinimizer(MinimizerBase):
    """
    Minimizer using the DFO-LS package (Derivative-Free Optimization for Least-Squares).
    """

    def __init__(self, max_iterations=DEFAULT_MAX_ITERATIONS, **kwargs):
        super().__init__(method=None, max_iterations=max_iterations)

    def _prepare_solver_args(self, parameters):
        x0 = []
        bounds_lower = []
        bounds_upper = []
        for param in parameters:
            x0.append(param.value)
            bounds_lower.append(param.min if param.min is not None else -np.inf)
            bounds_upper.append(param.max if param.max is not None else np.inf)
        bounds = (np.array(bounds_lower), np.array(bounds_upper))
        return {'x0': np.array(x0), 'bounds': bounds}

    def _run_solver(self, objective_function, **kwargs):
        x0 = kwargs.get('x0')
        bounds = kwargs.get('bounds')
        return solve(objective_function,
                     x0=x0,
                     bounds=bounds,
                     maxfun=self.max_iterations)


    def _sync_result_to_parameters(self, parameters, raw_result):
        # Ensure compatibility with raw_result coming from dfols.solve()
        if hasattr(raw_result, 'x'):
            result_values = raw_result.x
        else:
            result_values = raw_result  # fallback for raw_result being directly a list/array

        for i, param in enumerate(parameters):
            param.value = result_values[i]
            # DFO-LS doesn't provide errors; set to None or calculate later if needed
            param.error = None
