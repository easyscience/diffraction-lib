import numpy as np
from dfols import solve
from .base import MinimizerBase

class DfolsMinimizer(MinimizerBase):
    """
    Minimizer using the DFO-LS package (Derivative-Free Optimization for Least-Squares).
    """

    def __init__(self, method='leastsq'):
        self.result = None
        self.method = method
        self._previous_chi2 = None
        self._iteration = 0
        self._best_chi2 = None
        self._best_iteration = None

    def fit(self, sample_models, experiments, calculator):
        # Collecting free parameters from models and experiments
        parameters = self._collect_free_parameters(sample_models, experiments)

        if not parameters:
            print("⚠️ No parameters selected for refinement. Aborting fit.")
            return None

        # Preparing initial parameter values and bounds for dfols
        x0, bounds = self._prepare_parameters(parameters)

        # Create the dfols model using the parameters
        dfols_model = self._create_dfols_model(parameters,
                                               sample_models,
                                               experiments,
                                               calculator)

        # Perform minimization using dfols
        result = solve(dfols_model,
                       x0=x0,
                       bounds=bounds,
                       maxfun=1000)

        self.result = result

        print(f"✅ Fitting complete.\n")
        print(f"🔧 Final iteration {self._iteration}: Reduced Chi-square = {self._previous_chi2:.2f}")
        print(f"🏆 Best Reduced Chi-square: {self._best_chi2:.2f} at iteration {self._best_iteration}")

        # Sync the optimized parameters back to the object
        self._sync_result_to_parameters(parameters, result)

        # Store best reduced chi-square in the result for display compatibility
        self.result.redchi = self._best_chi2

        return self.result

    def results(self):
        return self.result

    @staticmethod
    def display_results(result):
        print("DFOLS optimization result:")
        if hasattr(result, "msg"):
            print(f"  message: {result.msg}")
        if hasattr(result, "x"):
            print(f"  solution x: {result.x}")
        if hasattr(result, "obj"):
            print(f"  objective function value (sum of squares): {result.obj}")
        if hasattr(result, "flag"):
            print(f"  exit flag: {result.flag}")
        if hasattr(result, "nf"):
            print(f"  number of function evaluations (nf): {result.nf}")
        if hasattr(result, "nx"):
            print(f"  number of variables (nx): {result.nx}")
        if hasattr(result, "nruns"):
            print(f"  number of runs (nruns): {result.nruns}")

    def _compute_residuals(self, parameters, sample_models, experiments, calculator):
        """
        Computes residuals for current parameter values.
        """
        residuals = []
        for expt_id, experiment in experiments._items.items():
            y_calc = calculator.calculate_pattern(sample_models, experiment)
            y_meas = experiment.datastore.pattern.meas
            y_meas_su = experiment.datastore.pattern.meas_su
            diff = (y_meas - y_calc) / y_meas_su
            residuals.extend(diff)

        return np.array(residuals)

    def _track_chi_square(self, residuals, parameters):
        """
        Tracks and prints Reduced Chi-square improvements.
        """
        chi2 = np.sum(residuals ** 2)
        n_points = len(residuals)
        red_chi2 = chi2 / (n_points - len(parameters))

        if self._previous_chi2 is None:
            self._previous_chi2 = red_chi2
            self._best_chi2 = red_chi2
            self._best_iteration = self._iteration
            print(f"🔧 Iteration {self._iteration}: starting Reduced Chi-square = {red_chi2:.2f}")
        elif (self._previous_chi2 - red_chi2) / self._previous_chi2 > 0.01:
            self._iteration += 1
            print(f"🔧 Iteration {self._iteration}: Reduced Chi-square improved from {self._previous_chi2:.2f} to {red_chi2:.2f}")
            self._previous_chi2 = red_chi2

        if self._best_chi2 is None or red_chi2 < self._best_chi2:
            self._best_chi2 = red_chi2
            self._best_iteration = self._iteration

        return red_chi2

    def _prepare_parameters(self, input_parameters):
        """
        Prepare the starting point and bounds for dfols.
        """
        x0 = []
        bounds_lower = []
        bounds_upper = []

        for param in input_parameters:
            x0.append(param.value)
            bounds_lower.append(param.min if param.min is not None else -np.inf)
            bounds_upper.append(param.max if param.max is not None else np.inf)

        bounds = (np.array(bounds_lower), np.array(bounds_upper))
        return np.array(x0), bounds

    def _create_dfols_model(self, parameters, sample_models, experiments, calculator):
        """
        Returns the objective function for dfols.
        """
        def dfols_model(x):
            # Sync the parameters with the current x values
            for i, param in enumerate(parameters):
                param.value = x[i]

            residuals = []
            for expt_id, experiment in experiments._items.items():
                y_calc = calculator.calculate_pattern(sample_models, experiment)
                y_meas = experiment.datastore.pattern.meas
                y_meas_su = experiment.datastore.pattern.meas_su
                diff = (y_meas - y_calc) / y_meas_su
                residuals.extend(diff)

            residuals_array = np.array(residuals)

            self._track_chi_square(residuals_array, parameters)

            return residuals_array

        return dfols_model

    def _sync_result_to_parameters(self, parameters, result):
        """
        Sync the optimized values back into the parameters.
        """
        for i, param in enumerate(parameters):
            param.value = result.x[i]

    def _objective_function(self, parameters, sample_models, experiments, calculator):
        """
        Required by MinimizerBase. Creates the objective function for dfols.
        """
        return self._create_dfols_model(parameters, sample_models, experiments, calculator)

    def _sync_parameters(self, parameters, result):
        """
        Required by MinimizerBase. Syncs the optimized parameters back to their objects.
        """
        self._sync_result_to_parameters(parameters, result)