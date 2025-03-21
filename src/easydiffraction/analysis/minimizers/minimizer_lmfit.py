import lmfit
from .base import MinimizerBase, FitResults

DEFAULT_METHOD = 'leastsq'
DEFAULT_MAX_ITERATIONS = 1000

class LmfitMinimizer(MinimizerBase):
    """
    Minimizer using the lmfit package.
    """

    def __init__(self, method=DEFAULT_METHOD, max_iterations=DEFAULT_MAX_ITERATIONS):
        super().__init__(method=method, maxfun=max_iterations)

    def _prepare_solver_args(self, parameters):
        engine_parameters = lmfit.Parameters()
        for param in parameters:
            engine_parameters.add(
                name=param.id,
                value=param.value,
                vary=param.free,
                min=param.min,
                max=param.max
            )
        return {'engine_parameters': engine_parameters}

    def _run_solver(self, objective_function, **kwargs):
        engine_parameters = kwargs.get('engine_parameters')
        return lmfit.minimize(objective_function,
                              params=engine_parameters,
                              method=self.method,
                              max_nfev=self.maxfun)

    @staticmethod
    def _sync_parameters(engine_params, parameters):
        for param in parameters:
            param_result = engine_params.get(param.id)
            if param_result is not None:
                param.value = param_result.value

    def _sync_result_to_parameters(self, parameters, raw_result):
        for param in parameters:
            param_result = raw_result.params.get(param.id)
            if param_result is not None:
                param.value = param_result.value
                param.error = param_result.stderr
