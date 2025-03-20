import lmfit
from .base import MinimizerBase

class LmfitMinimizer(MinimizerBase):
    """
    Minimizer using the lmfit package.
    """

    def __init__(self, method='leastsq'):
        self.result = None
        self.minimizer = None
        self.method = method

    def fit(self, sample_models, experiments, calculator):
        parameters = self._collect_free_parameters(sample_models, experiments)

        if not parameters:
            print("⚠️ No parameters selected for refinement. Aborting fit.")
            return None

        engine_parameters = self._prepare_parameters(parameters)

        # Perform minimization using the base objective function
        self.minimizer = lmfit.Minimizer(
            self._objective_function,
            engine_parameters,
            fcn_args=(parameters, sample_models, experiments, calculator)
        )
        self.result = self.minimizer.minimize(method=self.method)
        return self.result

    def results(self):
        return self.result

    @staticmethod
    def display_results(result):
        print(lmfit.fit_report(result))

    def _prepare_parameters(self, input_parameters):
        engine_parameters = lmfit.Parameters()

        for param in input_parameters:
            engine_parameters.add(
                name=param.id,
                value=param.value,
                vary=param.free,
                min=param.min,
                max=param.max
            )

        return engine_parameters