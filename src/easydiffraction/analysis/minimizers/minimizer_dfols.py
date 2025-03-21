import numpy as np
from dfols import solve
from .base import MinimizerBase, FitResults

DEFAULT_METHOD = 'leastsq'
DEFAULT_MAX_ITERATIONS = 1000

class DfolsMinimizer(MinimizerBase):
    """
    Minimizer using the DFO-LS package (Derivative-Free Optimization for Least-Squares).
    """

    def __init__(self, method=DEFAULT_METHOD, max_iterations=DEFAULT_MAX_ITERATIONS):
        super().__init__(method=method, maxfun=max_iterations)

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
                     maxfun=self.maxfun)

    @staticmethod
    def _sync_parameters(engine_params, parameters):
        for i, param in enumerate(parameters):
            param.value = engine_params[i]

    def _sync_result_to_parameters(self, parameters, result):
        for i, param in enumerate(parameters):
            param.value = result.x[i]
