import lmfit
import numpy as np
from .base import MinimizerBase

class LmfitMinimizer(MinimizerBase):
    """
    Minimizer using the lmfit package.
    """

    def __init__(self):
        self.result = None
        self.minimizer = None

    def prepare_parameters(self, input_parameters):
        engine_parameters = lmfit.Parameters()

        for param in input_parameters:
            lmfit_name = param.id

            engine_parameters.add(
                name=lmfit_name,
                value=param.value,
                vary=param.free,
                min=param.min,
                max=param.max
            )

        return engine_parameters

    def fit(self, sample_models, experiments, calculator):
        """
        Fit function using lmfit.

        :param sample_models: Sample models object.
        :param experiments: Experiments object.
        :param calculator: Calculator instance to compute theoretical patterns.
        """
        parameters = (
            sample_models.get_free_params() +
            experiments.get_free_params()
        )

        if not parameters:
            print("⚠️ No parameters selected for refinement. Aborting fit.")
            return None

        engine_parameters = self.prepare_parameters(parameters)

        # Perform minimization using the new _objective_function
        self.minimizer = lmfit.Minimizer(
            self._objective_function,
            engine_parameters,
            fcn_args=(parameters, sample_models, experiments, calculator)
        )
        self.result = self.minimizer.minimize()
        return self.result

    @staticmethod
    def display_results(result):
        print(lmfit.fit_report(result))

    def _objective_function(self, engine_params, parameters, sample_models, experiments, calculator):
        """Objective function passed to lmfit.Minimizer"""
        # Update the parameter values in models and experiments
        self._sync_parameters(engine_params, parameters)

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
        """Synchronize engine parameter values back to Parameter instances."""
        for param in parameters:
            param_name = param.id  # Use the unique id directly
            param_obj = engine_params[param_name]

            # Update the parameter value directly
            param.value = param_obj.value

    def results(self):
        return self.result