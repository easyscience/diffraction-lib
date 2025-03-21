from abc import ABC, abstractmethod
import numpy as np
import tabulate

class FitResults:
    def __init__(self, success=False, parameters=None, chi_square=None,
                 reduced_chi_square=None, message='', iterations=0, engine_result=None, starting_parameters=None, **kwargs):
        self.success = success
        self.parameters = parameters if parameters is not None else []
        self.chi_square = chi_square
        self.reduced_chi_square = reduced_chi_square
        self.message = message
        self.iterations = iterations
        self.engine_result = engine_result
        self.result = None
        self.starting_parameters = starting_parameters if starting_parameters is not None else []

        if 'redchi' in kwargs and self.reduced_chi_square is None:
            self.reduced_chi_square = kwargs.get('redchi')

        for key, value in kwargs.items():
            setattr(self, key, value)

    def display_results(self):
        print(f"\nFit results:")
        print(f"✅ Success: {self.success}")
        print(f"🔧 Reduced Chi-square: {self.reduced_chi_square:.2f}")
        print(f"📈 Parameters:")

        table_data = []
        headers = ["block", "cif_name", "start", "refined", "error", "units", "change [%]"]

        for param in self.parameters:
            block_name = getattr(param, 'block_name', 'N/A')
            cif_name = getattr(param, 'cif_name', 'N/A')
            start = f"{getattr(param, 'start_value', 'N/A'):.4f}" if param.start_value is not None else "N/A"
            refined = f"{param.value:.4f}" if param.value is not None else "N/A"
            error = f"{param.error:.4f}" if param.error is not None else "N/A"
            units = getattr(param, 'units', 'N/A')

            if param.start_value and param.value:
                change = ((param.value - param.start_value) / param.start_value) * 100
                arrow = "↑" if change > 0 else "↓"
                relative_change = f"{arrow} {abs(change):.1f}%"
            else:
                relative_change = "N/A"

            table_data.append([block_name, cif_name, start, refined, error, units, relative_change])

        print(tabulate.tabulate(table_data, headers=headers, tablefmt="grid"))


class MinimizerBase(ABC):
    """
    Abstract base class for minimizer implementations.
    Provides shared logic and structure for concrete minimizers.
    """
    def __init__(self, name=None, method=None, max_iterations=None):
        # 'method' is used only by minimizers supporting multiple methods (e.g., lmfit). For minimizers like dfols, pass None.
        self.name = name
        self.method = method
        self.max_iterations = max_iterations
        self.result = None
        self._previous_chi2 = None
        self._iteration = 0
        self._best_chi2 = None
        self._best_iteration = None

    @abstractmethod
    def _prepare_solver_args(self, parameters):
        """
        Prepare the solver arguments directly from the list of free parameters.
        """
        pass

    @abstractmethod
    def _run_solver(self, objective_function, engine_parameters):
        pass


    @abstractmethod
    def _sync_result_to_parameters(self, raw_result, parameters):
        pass

    def _finalize_fit(self, parameters, raw_result):
        self._sync_result_to_parameters(parameters, raw_result)
        self.result = FitResults(
            parameters=parameters,
            redchi=self._best_chi2,
            raw_result=raw_result,
            starting_parameters=parameters  # Pass starting parameters to the results
        )
        return self.result

    @staticmethod
    def _collect_free_parameters(sample_models, experiments):
        return sample_models.get_free_params() + experiments.get_free_params()

    def _track_chi_square(self, residuals, parameters):
        chi2 = np.sum(residuals ** 2)
        n_points = len(residuals)
        red_chi2 = chi2 / (n_points - len(parameters))

        row = []
        # Add initial row to print
        if self._previous_chi2 is None:
            self._previous_chi2 = red_chi2
            self._best_chi2 = red_chi2
            self._best_iteration = self._iteration
            row = [self._iteration,
                   f"{red_chi2:<12.2f}",
                   "-".ljust(12),
                   "-".ljust(12)]
        # Check for improvement and append new row to print
        elif (self._previous_chi2 - red_chi2) / self._previous_chi2 > 0.01:
            change_percent = (self._previous_chi2 - red_chi2) / self._previous_chi2 * 100
            self._iteration += 1
            row = [self._iteration,
                   f"{self._previous_chi2:<12.2f}",
                   f"{red_chi2:<12.2f}",
                   f"↓ {change_percent:.1f}%".ljust(10)]
            self._previous_chi2 = red_chi2
        if len(row):
            print(f"| {row[0]:<11} | {row[1]:<12} | {row[2]:<12} | {row[3]:<12} |")

        if self._best_chi2 is None or red_chi2 < self._best_chi2:
            self._best_chi2 = red_chi2
            self._best_iteration = self._iteration

        return residuals

    def _compute_residuals(self, engine_params, parameters, sample_models, experiments, calculator):
        self._sync_result_to_parameters(parameters, engine_params)

        residuals = []
        for expt_id, experiment in experiments._items.items():
            y_calc = calculator.calculate_pattern(sample_models, experiment)
            y_meas = experiment.datastore.pattern.meas
            y_meas_su = experiment.datastore.pattern.meas_su
            diff = (y_meas - y_calc) / y_meas_su
            residuals.extend(diff)

        residuals = np.array(residuals)
        return self._track_chi_square(residuals, parameters)

    def fit(self, sample_models, experiments, calculator):
        minimizer_name = self.name
        if self.method is not None:
            minimizer_name += f" ({self.method})"

        print(f"🚀 Starting fitting process with {minimizer_name}...")

        self.parameters = self._collect_free_parameters(sample_models, experiments)

        for parameter in self.parameters:
            parameter.start_value = parameter.value

        solver_args = self._prepare_solver_args(self.parameters)
        objective_function = self._create_objective_function(self.parameters, sample_models, experiments, calculator)

        print("📈 Reduced Chi-square change:")
        print("+-------------+--------------+--------------+--------------+")
        print(f"| {'iteration':<11} | {'start':<12} | {'improved':<12} | {'change [%]':<12} |")
        print("+=============+==============+==============+==============+")

        raw_result = self._run_solver(objective_function, **solver_args)
        result = self._finalize_fit(self.parameters, raw_result)

        print("+-------------+--------------+--------------+--------------+")
        print(f"🔧 Final iteration {self._iteration}: Reduced Chi-square = {self._previous_chi2:.2f}")
        print(f"🏆 Best Reduced Chi-square: {self._best_chi2:.2f} at iteration {self._best_iteration}")
        print("✅ Fitting complete.")

        return result

    def results(self):
        return self.result

    @staticmethod
    def display_results(result):
        result.display_results()

    def _objective_function(self, engine_params, parameters, sample_models, experiments, calculator):
        return self._compute_residuals(engine_params, parameters, sample_models, experiments, calculator)

    def _create_objective_function(self, parameters, sample_models, experiments, calculator):
        return lambda engine_params: self._objective_function(
            engine_params, parameters, sample_models, experiments, calculator
        )