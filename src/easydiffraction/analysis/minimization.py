from .minimizers.minimizer_factory import MinimizerFactory
from ..analysis.reliability_factors import get_reliability_inputs
import numpy as np


class DiffractionMinimizer:
    """
    Handles the fitting workflow using a pluggable minimizer.
    """

    def __init__(self, selection: str = 'lmfit (leastsq)'):
        self.selection = selection
        self.engine = selection.split(' ')[0]  # Extracts 'lmfit' or 'bumps'
        self.minimizer = MinimizerFactory.create_minimizer(selection)
        self.results = None

    def fit(self, sample_models, experiments, calculator):
        """
        Run the fitting process.
        """
        parameters = self._collect_free_parameters(sample_models, experiments)

        if not parameters:
            print("⚠️ No parameters selected for refinement. Aborting fit.")
            return None

        for parameter in parameters:
            parameter.start_value = parameter.value

        objective_function = lambda engine_params: self._residual_function(engine_params, parameters, sample_models, experiments, calculator)

        # Perform fitting
        self.results = self.minimizer.fit(parameters, objective_function)

        # Post-fit processing
        self._process_fit_results(sample_models, experiments, calculator)

    def _process_fit_results(self, sample_models, experiments, calculator):
        """
        Collect reliability inputs and display results after fitting.
        """
        y_obs, y_calc, y_err = get_reliability_inputs(sample_models, experiments, calculator)

        # Placeholder for future f_obs / f_calc retrieval
        f_obs, f_calc = None, None

        if self.results:
            self.results.display_results(y_obs=y_obs, y_calc=y_calc, y_err=y_err, f_obs=f_obs, f_calc=f_calc)

    def _collect_free_parameters(self, sample_models, experiments):
        return sample_models.get_free_params() + experiments.get_free_params()

    def _residual_function(self, engine_params, parameters, sample_models, experiments, calculator):
        """
        Residual function computes the difference between measured and calculated patterns.
        It updates the parameter values according to the optimizer-provided engine_params.
        """
        # Sync parameters back to objects
        self.minimizer._sync_result_to_parameters(parameters, engine_params)

        residuals = []
        for expt_id, experiment in experiments._items.items():
            y_calc = calculator.calculate_pattern(sample_models, experiment)
            y_meas = experiment.datastore.pattern.meas
            y_meas_su = experiment.datastore.pattern.meas_su
            diff = (y_meas - y_calc) / y_meas_su
            residuals.extend(diff)

        residuals = np.array(residuals)
        return self.minimizer.tracker.track(residuals, parameters)
