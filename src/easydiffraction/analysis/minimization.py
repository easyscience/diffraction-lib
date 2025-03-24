from .minimizers.factory import MinimizerFactory
from .minimizers.chi_square_tracker import ChiSquareTracker
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

        self.results = self.minimizer.fit(parameters, objective_function)

        self._display_results()

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

    def _display_results(self):
        """
        Prints a summary of the fitting results.
        """
        if self.results is None:
            print("⚠️ No fitting results to display.")
            return

        self.minimizer.display_results(self.results)