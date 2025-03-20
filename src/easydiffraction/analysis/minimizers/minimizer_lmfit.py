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
            raw_name = param["cif_name"]
            lmfit_name = (
                raw_name.replace("[", "_")
                .replace("]", "")
                .replace(".", "_")
                .replace("'", "")
            )

            engine_parameters.add(
                name=lmfit_name,
                value=param["value"],
                vary=param["free"],
                min=param.get('min', None),
                max=param.get('max', None)
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

        def objective_function(engine_parameters):
            # Update parameter values in models/experiments
            for param in parameters:
                cif_name = param['cif_name']
                lmfit_name = (
                    cif_name.replace("[", "_")
                    .replace("]", "")
                    .replace(".", "_")
                    .replace("'", "")
                )
                param_obj = engine_parameters[lmfit_name]
                if 'parameter' in param:
                    param['parameter'].value = param_obj.value
                else:
                    param['value'] = param_obj.value

            residuals = []

            for expt_id, experiment in experiments._items.items():
                y_calc = calculator.calculate_pattern(sample_models, experiment)

                y_meas = experiment.datastore.pattern.meas
                y_meas_su = experiment.datastore.pattern.meas_su

                diff = (y_meas - y_calc) / y_meas_su
                residuals.extend(diff)

            return np.array(residuals)

        # Perform minimization
        self.minimizer = lmfit.Minimizer(objective_function, engine_parameters)
        self.result = self.minimizer.minimize()
        return self.result

    @staticmethod
    def display_results(result):
        print(lmfit.fit_report(result))

    def results(self):
        return self.result