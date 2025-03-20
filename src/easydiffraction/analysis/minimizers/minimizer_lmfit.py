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

        # Create the lmfit model using the parameters
        lmfit_model = self._create_lmfit_model(parameters,
                                               sample_models,
                                               experiments,
                                               calculator)

        # Perform minimization using lmfit
        print(f"🔧 [DEBUG] Running lmfit minimize with method: {self.method}")
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
        """
        Create the lmfit model function based on the parameters and models.
        """
        def lmfit_model(params):
            residuals = self._objective_function(params, parameters, sample_models, experiments, calculator)
            return residuals

        return lmfit_model

    def _objective_function(self, engine_params, parameters, sample_models, experiments, calculator):
        """
        Objective function for lmfit minimizer to compute residuals.
        """
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
        """
        Synchronize parameters for LMFIT engine.
        engine_params: lmfit.Parameters (dict-like)
        parameters: list of Parameter objects
        """
        for param in parameters:
            param_name = param.id
            param_obj = engine_params[param_name]
            param.value = param_obj.value
            param.error = param_obj.stderr  # Assuming the error is in stderr of lmfit