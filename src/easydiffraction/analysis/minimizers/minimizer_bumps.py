import bumps.fitters as bumps_fitters
import bumps.names as bumps_names
import numpy as np
from .base import MinimizerBase

class BumpsMinimizer(MinimizerBase):
    """
    Minimizer using the bumps package.
    """

    def __init__(self):
        self.problem = None
        self.fitter = None
        self.result = None

    def fit(self, parameters, sample_models, experiments, calculator=None):
        """
        Fit function using bumps.

        :param parameters: List of parameters to refine.
        :param sample_models: Sample models object.
        :param experiments: Experiments object.
        :param calculator: Calculator instance to compute theoretical patterns.
        """
        class ResidualsModel(bumps_names.Model):
            def __init__(self):
                # Define bumps Parameters
                self.params = []
                for param in parameters:
                    bumps_param = bumps_names.Parameter(
                        param['value'],
                        name=param['cif_name']
                    )
                    bumps_param.range(param.get('min', -np.inf), param.get('max', np.inf))
                    if not param['free']:
                        bumps_param.fixed = True

                    self.params.append(bumps_param)

            def parameters(self):
                return self.params

            def nllf(self):
                # Assign parameter values to the model
                for bump_param, param in zip(self.params, parameters):
                    param['parameter'].value = bump_param.value

                residuals = []

                for expt_id, experiment in experiments._items.items():
                    y_calc = calculator.calculate_pattern(sample_models, experiment)

                    y_meas = experiment.datastore.pattern.meas
                    y_meas_su = experiment.datastore.pattern.meas_su

                    diff = (y_meas - y_calc) / y_meas_su
                    residuals.extend(diff)

                # Return sum of squared residuals
                return np.sum(np.square(residuals))

        self.problem = bumps_names.FitProblem(ResidualsModel())

        self.fitter = bumps_fitters.DEFit(self.problem)
        self.fitter.solve()

        # Update parameters with refined values
        for bump_param, param in zip(self.problem.model.parameters(), parameters):
            param['parameter'].value = bump_param.value

        self.result = self.problem

    def results(self):
        return self.result