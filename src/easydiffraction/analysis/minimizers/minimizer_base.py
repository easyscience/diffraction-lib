import pandas as pd
from abc import ABC, abstractmethod
from tabulate import tabulate

from ..reliability_factors import (
    calculate_r_factor,
    calculate_r_factor_squared,
    calculate_weighted_r_factor,
    calculate_rb_factor
)
from .fitting_progress_tracker import FittingProgressTracker

from easydiffraction.utils.formatting import paragraph

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

        print(paragraph("Fit results"))
        print(f"{status_icon} Success: {self.success}")
        print(f"⏱️ Fitting time: {self.fitting_time:.2f} seconds")
        print(f"📏 Goodness-of-fit (reduced χ²): {self.reduced_chi_square:.2f}")
        if rf is not None:
            print(f"📏 R-factor (Rf): {rf:.2f}%")
        if rf2 is not None:
            print(f"📏 R-factor squared (Rf²): {rf2:.2f}%")
        if wr is not None:
            print(f"📏 Weighted R-factor (wR): {wr:.2f}%")
        if br is not None:
            print(f"📏 Bragg R-factor (BR): {br:.2f}%")
        print(f"📈 Fitted parameters:")

        headers = ["datablock",
                   "category",
                   "entry",
                   "parameter",
                   "start",
                   "fitted",
                   "uncertainty",
                   "units",
                   "change"]

        rows = []
        for param in self.parameters:
            datablock_id = getattr(param, 'datablock_id', 'N/A')  # TODO: Check if 'N/A' is needed
            category_key = getattr(param, 'category_key', 'N/A')
            collection_entry_id = getattr(param, 'collection_entry_id', 'N/A')
            name = getattr(param, 'name', 'N/A')
            start = f"{getattr(param, 'start_value', 'N/A'):.4f}" if param.start_value is not None else "N/A"
            fitted = f"{param.value:.4f}" if param.value is not None else "N/A"
            uncertainty = f"{param.uncertainty:.4f}" if param.uncertainty is not None else "N/A"
            units = getattr(param, 'units', 'N/A')

            if param.start_value and param.value:
                change = ((param.value - param.start_value) / param.start_value) * 100
                arrow = "↑" if change > 0 else "↓"
                relative_change = f"{abs(change):.2f} % {arrow}"
            else:
                relative_change = "N/A"

            rows.append([datablock_id,
                         category_key,
                         collection_entry_id,
                         name,
                         start,
                         fitted,
                         uncertainty,
                         units,
                         relative_change])

        dataframe = pd.DataFrame(rows)
        indices = range(1, len(dataframe) + 1)  # Force starting from 1

        print(tabulate(dataframe,
                       headers=headers,
                       tablefmt="fancy_outline",
                       showindex=indices))


class MinimizerBase(ABC):
    """
    Abstract base class for minimizer implementations.
    Provides shared logic and structure for concrete minimizers.
    """
    def __init__(self,
                 name=None,
                 method=None,
                 max_iterations=None):
        # 'method' is used only by minimizers supporting multiple methods
        # (e.g., lmfit). For minimizers like dfols, pass None.
        self.name = name
        self.method = method
        self.max_iterations = max_iterations
        self.result = None
        self._previous_chi2 = None
        self._iteration = None
        self._best_chi2 = None
        self._best_iteration = None
        self._fitting_time = None
        self.tracker = FittingProgressTracker()

    def _start_tracking(self, minimizer_name):
        self.tracker.reset()
        self.tracker.start_tracking(minimizer_name)
        self.tracker.start_timer()

    def _stop_tracking(self):
        self.tracker.stop_timer()
        self.tracker.finish_tracking()

    @abstractmethod
    def _prepare_solver_args(self, parameters):
        """
        Prepare the solver arguments directly from the list of free parameters.
        """
        pass

    @abstractmethod
    def _run_solver(self,
                    objective_function,
                    engine_parameters):
        pass

    @abstractmethod
    def _sync_result_to_parameters(self,
                                   raw_result,
                                   parameters):
        pass

    def _finalize_fit(self,
                      parameters,
                      raw_result):
        self._sync_result_to_parameters(parameters,
                                        raw_result)
        success = self._check_success(raw_result)
        self.result = FitResults(
            success=success,
            parameters=parameters,
            reduced_chi_square=self.tracker.best_chi2,
            raw_result=raw_result,
            starting_parameters=parameters,
            fitting_time=self.tracker.fitting_time
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

        self._start_tracking(minimizer_name)

        solver_args = self._prepare_solver_args(parameters)
        raw_result = self._run_solver(objective_function,
                                      **solver_args)

        self._stop_tracking()

        result = self._finalize_fit(parameters,
                                    raw_result)

        return result

    def _objective_function(self,
                            engine_params,
                            parameters,
                            sample_models,
                            experiments,
                            calculator):
        return self._compute_residuals(engine_params,
                                       parameters,
                                       sample_models,
                                       experiments,
                                       calculator)

    def _create_objective_function(self,
                                   parameters,
                                   sample_models,
                                   experiments,
                                   calculator):
        return lambda engine_params: self._objective_function(
            engine_params,
            parameters,
            sample_models,
            experiments,
            calculator
        )

