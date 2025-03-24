from abc import ABC, abstractmethod
import tabulate
import time
from ..reliability_factors import (
    calculate_r_factor,
    calculate_r_factor_squared,
    calculate_weighted_r_factor,
    calculate_rb_factor
)
from .chi_square_tracker import ChiSquareTracker

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

    def display_results(self, y_obs=None, y_calc=None, y_err=None, f_obs=None, f_calc=None):
        status_icon = "✅" if self.success else "❌"
        rf = rf2 = wr = br = None
        if y_obs is not None and y_calc is not None:
            rf = calculate_r_factor(y_obs, y_calc) * 100
            rf2 = calculate_r_factor_squared(y_obs, y_calc) * 100
        if y_obs is not None and y_calc is not None and y_err is not None:
            wr = calculate_weighted_r_factor(y_obs, y_calc, y_err) * 100
        if f_obs is not None and f_calc is not None:
            br = calculate_rb_factor(f_obs, f_calc) * 100

        print(f"\nFit results:")
        print(f"{status_icon} Success: {self.success}")
        print(f"⏱️ Fitting time: {self.fitting_time:.2f} seconds")
        print(f"📏 Goodness-of-fit (reduced χ²): {self.reduced_chi_square:.2f}")
        if rf is not None:
            print(f"📏 R-factor (Rf): {rf:.2f}%")
        if rf2 is not None:
            print(f"📏 R-factor squared (Rf²): {rf2:.2f}%")
        if wr is not None:
            print(f"📏 Weighted R-factors (wR): {wr:.2f}%")
        if br is not None:
            print(f"📏 Bragg R-factor (BR): {br:.2f}%")
        print(f"📈 Refined parameters:")

        table_data = []
        headers = ["cif block", "cif parameter", "start", "refined", "error", "units", "change [%]"]

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
                relative_change = f"{abs(change):.1f}% {arrow}"
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
        self._fitting_time = None
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
        success = self._check_success(raw_result)
        self.result = FitResults(
            success=success,
            parameters=parameters,
            reduced_chi_square=self.tracker.best_chi2,
            raw_result=raw_result,
            starting_parameters=parameters,
            fitting_time=self._fitting_time
        )
        return self.result

    @abstractmethod
    def _check_success(self, raw_result):
        """
        Determine whether the fit was successful.
        This must be implemented by concrete minimizers.
        """
        pass

    def fit(self, parameters, objective_function):
        minimizer_name = self.name
        if self.method is not None:
            minimizer_name += f" ({self.method})"

        self.tracker.reset()
        self.tracker.start_tracking(minimizer_name)

        self.parameters = parameters
        start_time = time.perf_counter()

        raw_result = self._run_solver(objective_function, **self._prepare_solver_args(parameters))

        end_time = time.perf_counter()
        self._fitting_time = end_time - start_time

        self.tracker.finish_tracking()

        result = self._finalize_fit(parameters, raw_result)

        return result

    def _objective_function(self, engine_params, parameters, sample_models, experiments, calculator):
        return self._compute_residuals(engine_params, parameters, sample_models, experiments, calculator)

    def _create_objective_function(self, parameters, sample_models, experiments, calculator):
        return lambda engine_params: self._objective_function(
            engine_params, parameters, sample_models, experiments, calculator
        )
