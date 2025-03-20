import lmfit
import numpy as np
from .base import MinimizerBase

class LmfitMinimizer(MinimizerBase):
    """
    Minimizer using the lmfit package.
    """

    def __init__(self, method='leastsq'):
        self.result = None
        self.method = method

    def fit(self, sample_models, experiments, calculator):
        # Collecting free parameters from models and experiments
        parameters = self._collect_free_parameters(sample_models, experiments)

        if not parameters:
            print("⚠️ No parameters selected for refinement. Aborting fit.")
            return None

        # Preparing parameters for lmfit engine
        engine_parameters = self._prepare_parameters(parameters)
        print(f"🔧 [DEBUG] Engine parameters: {engine_parameters}")

        # Create the lmfit model using the parameters
        lmfit_model = self._create_lmfit_model(parameters,
                                               sample_models,
                                               experiments,
                                               calculator)

        # Perform minimization using lmfit
        fit_result = lmfit.minimize(lmfit_model,
                                    params=engine_parameters,
                                    method=self.method)
        self.result = fit_result

        # Return fit results
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

    def _create_lmfit_model(self, parameters, sample_models, experiments, calculator):
        def lmfit_model(params):
            residuals = self._objective_function(params, parameters, sample_models, experiments, calculator)
            return residuals

        return lmfit_model

    def _objective_function(self, engine_params, parameters, sample_models, experiments, calculator):
        LmfitMinimizer._sync_parameters(engine_params, parameters)

        residuals = []
        for expt_id, experiment in experiments._items.items():
            y_calc = calculator.calculate_pattern(sample_models, experiment)
            y_meas = experiment.datastore.pattern.meas
            y_meas_su = experiment.datastore.pattern.meas_su
            diff = (y_meas - y_calc) / y_meas_su
            residuals.extend(diff)

        return np.array(residuals)

    @staticmethod
    def _sync_parameters(engine_params, parameters):
        print(f"🔧 [DEBUG] Syncing parameters with engine_params: {engine_params}")
        # engine_params is a list of floats representing parameter values
        for idx, param in enumerate(parameters):
            new_value = engine_params[idx]
            print(f"🔧 [DEBUG] Updating parameter '{param.id}' from {param.value} to {new_value}")
            param.value = new_value
