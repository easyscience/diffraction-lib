from .minimizers.minimizer_factory import MinimizerFactory
from ..analysis.reliability_factors import get_reliability_inputs
import numpy as np


class DiffractionMinimizer:
    """
    Handles the fitting workflow using a pluggable minimizer.
    """

    def __init__(self, selection: str = 'lmfit (leastsq)'):
        self.selection = selection
        self.engine = selection.split(' ')[0]  # Extracts 'lmfit' or 'dfols'
        self.minimizer = MinimizerFactory.create_minimizer(selection)
        self.results = None

    def fit(self, sample_models, experiments, calculator, weights=None):
        """
        Run the fitting process.
        """
        parameters = self._collect_free_parameters(sample_models, experiments)

        if not parameters:
            print("⚠️ No parameters selected for refinement. Aborting fit.")
            return None

        for parameter in parameters:
            parameter.start_value = parameter.value

        objective_function = lambda engine_params: self._residual_function(engine_params, parameters, sample_models, experiments, calculator, weights)

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

    def _residual_function(self, engine_params, parameters, sample_models, experiments, calculator, weights=None):
        """
        Residual function computes the difference between measured and calculated patterns.
        It updates the parameter values according to the optimizer-provided engine_params.
        """
        # Sync parameters back to objects
        self.minimizer._sync_result_to_parameters(parameters, engine_params)
        
        # Prepare weights for joint fitting
        N_experiments = len(experiments.ids)
        weights = np.ones(N_experiments) if weights is None else np.array([getattr(weights, id, 1.0) for id in experiments.ids], dtype=np.float64)
        weights *= N_experiments / np.sum(weights)  # Normalize weights so they sum to N, where N is the number of experiments

        residuals = []
        for (expt_id, experiment), weight in zip(experiments._items.items(), weights):
            y_calc = calculator.calculate_pattern(sample_models, experiment)
            y_meas = experiment.datastore.pattern.meas
            y_meas_su = experiment.datastore.pattern.meas_su
            diff = (y_meas - y_calc) / y_meas_su
            diff *= np.sqrt(weight)  # Residuls are squared before going into reduced chi-squared
            residuals.extend(diff)

        residuals = np.array(residuals)
        return self.minimizer.tracker.track(residuals, parameters)
