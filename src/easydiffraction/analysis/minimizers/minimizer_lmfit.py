import lmfit
from .base import MinimizerBase, FitResults
import numpy as np

DEFAULT_METHOD = 'leastsq'
DEFAULT_MAX_ITERATIONS = 1000

class LmfitMinimizer(MinimizerBase):
    """
    Minimizer using the lmfit package.
    """

    def __init__(self, name='lmfit', method=DEFAULT_METHOD, max_iterations=DEFAULT_MAX_ITERATIONS):
        super().__init__(name=name, method=method, max_iterations=max_iterations)

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
                              #iter_cb=self._iteration_callback,
                              nan_policy='propagate',
                              max_nfev=self.max_iterations)

    def _sync_result_to_parameters(self, parameters, raw_result):
        if hasattr(raw_result, 'params'):
            param_values = raw_result.params
        else:
            param_values = raw_result  # fallback if params attribute is not present

        for param in parameters:
            param_result = param_values.get(param.id)
            if param_result is not None:
                param.value = param_result.value
                param.error = getattr(param_result, 'stderr', None)

    def _iteration_callback(self, params, iter, resid, *args, **kwargs):
        # Temporary do not use this callback, as trying to track both the
        # iteration number and chi-square using _track_chi_square method.
        # Results are a bit different, so need to investigate further.
        # _track_chi_square is used because DFO-LS minimizer seems to
        # not provide the way to call _iteration_callback
        self._iteration = iter
        #red_chi2 = np.sum(resid**2) / (len(resid) - len(self.parameters))
        #print(f"🔄 Iteration {iter}: Reduced Chi-square = {red_chi2:.2f}")
