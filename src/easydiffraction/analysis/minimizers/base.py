from abc import ABC, abstractmethod
import numpy as np
import tabulate
import time  # Add at the top of the file

class FitResults:
    def __init__(self, success=False, parameters=None, chi_square=None,
                 reduced_chi_square=None, message='', iterations=0, engine_result=None, starting_parameters=None, fitting_time=None, **kwargs):
        self.success = success
        self.parameters = parameters if parameters is not None else []
        self.chi_square = chi_square
        self.reduced_chi_square = reduced_chi_square
        self.message = message
        self.iterations = iterations
        self.engine_result = engine_result
        self.result = None
        self.starting_parameters = starting_parameters if starting_parameters is not None else []
        self.fitting_time = fitting_time  # Store fitting time

        if 'redchi' in kwargs and self.reduced_chi_square is None:
            self.reduced_chi_square = kwargs.get('redchi')

        for key, value in kwargs.items():
            setattr(self, key, value)

    def display_results(self):
        print(f"\nFit results:")
        print(f"✅ Success: {self.success}")
        red_chi_str = f"{self.reduced_chi_square:.2f}" if self.reduced_chi_square is not None else "N/A"
        print(f"🔧 Reduced Chi-square: {red_chi_str}")
        print(f"⏱️ Fitting time: {self.fitting_time:.2f} seconds")
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

        print(tabulate.tabulate(table_data,
                                headers=headers,
                                tablefmt="fancy_outline",
                                numalign="center",
                                stralign="center",
                                showindex=False))


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
        self._iteration = None
        self._best_chi2 = None
        self._best_iteration = None
        self._fitting_time = None  # New attribute to store fitting time
        from .chi_square_tracker import ChiSquareTracker
        self.tracker = ChiSquareTracker()

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
            starting_parameters=parameters,  # Pass starting parameters to the results
            fitting_time=self._fitting_time  # Pass fitting time
        )
        return self.result

    def fit(self, parameters, objective_function):
        minimizer_name = self.name
        if self.method is not None:
            minimizer_name += f" ({self.method})"

        self.tracker.reset()
        self.tracker.start_tracking(minimizer_name)
        self.parameters = parameters

        start_time = time.time()

        raw_result = self._run_solver(objective_function, **self._prepare_solver_args(parameters))

        end_time = time.time()
        self._fitting_time = end_time - start_time

        result = self._finalize_fit(parameters, raw_result)

        self.tracker.finish_tracking(self._fitting_time)

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
