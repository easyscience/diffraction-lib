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

    def _prepare_lmfit_params(self, fit_params):
        lm_params = lmfit.Parameters()

        for param in fit_params:
            raw_name = param["cif_name"]
            lmfit_name = (
                raw_name.replace("[", "_")
                .replace("]", "")
                .replace(".", "_")
                .replace("'", "")
            )

            lm_params.add(
                name=lmfit_name,
                value=param["value"],
                vary=param["free"],
                min=param.get('min', None),
                max=param.get('max', None)
            )

        return lm_params

    def fit(self, parameters, sample_models, experiments, calculator=None):
        """
        Fit function using lmfit.

        :param parameters: List of parameters to refine. Each parameter dictionary should include a 'parameter' key that holds the actual lmfit Parameter instance.
        :param sample_models: Sample models object.
        :param experiments: Experiments object.
        :param calculator: Calculator instance to compute theoretical patterns.
        """
        lm_params = self._prepare_lmfit_params(parameters)

        def objective_function(lm_params):
            # Update parameter values in models/experiments
            for param in parameters:
                cif_name = param['cif_name']
                lmfit_name = (
                    cif_name.replace("[", "_")
                    .replace("]", "")
                    .replace(".", "_")
                    .replace("'", "")
                )
                param_obj = lm_params[lmfit_name]
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
        self.minimizer = lmfit.Minimizer(objective_function, lm_params)
        self.result = self.minimizer.minimize()
        return self.result

        # Update parameters with refined values
        for param in parameters:
            raw_name = param['cif_name']
            lmfit_name = (
                raw_name.replace("[", "_")
                .replace("]", "")
                .replace(".", "_")
                .replace("'", "")
            )
            lm_params.add(
                name=lmfit_name,
                value=param['value'],
                vary=param['free'],
                min=param.get('min', None),
                max=param.get('max', None)
            )

    def results(self):
        return self.result