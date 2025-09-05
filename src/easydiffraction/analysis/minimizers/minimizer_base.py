# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction Python Library contributors <https://github.com/easyscience/diffraction-lib>
# SPDX-License-Identifier: BSD-3-Clause

from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional

import numpy as np

from easydiffraction.analysis.fitting.progress_tracker import FittingProgressTracker
from easydiffraction.analysis.fitting.results import FitResults


class MinimizerBase(ABC):
    """
    Abstract base class for minimizer implementations.
    Provides shared logic and structure for concrete minimizers.
    """

    def __init__(
        self,
        name: Optional[str] = None,
        method: Optional[str] = None,
        max_iterations: Optional[int] = None,
    ) -> None:
        self.name: Optional[str] = name
        self.method: Optional[str] = method
        self.max_iterations: Optional[int] = max_iterations
        self.result: Optional[FitResults] = None
        self._previous_chi2: Optional[float] = None
        self._iteration: Optional[int] = None
        self._best_chi2: Optional[float] = None
        self._best_iteration: Optional[int] = None
        self._fitting_time: Optional[float] = None
        self.tracker: FittingProgressTracker = FittingProgressTracker()

    def _start_tracking(self, minimizer_name: str) -> None:
        self.tracker.reset()
        self.tracker.start_tracking(minimizer_name)
        self.tracker.start_timer()

    def _stop_tracking(self) -> None:
        self.tracker.stop_timer()
        self.tracker.finish_tracking()

    @abstractmethod
    def _prepare_solver_args(self, parameters: List[Any]) -> Dict[str, Any]:
        """
        Prepare the solver arguments directly from the list of free parameters.
        """
        pass

    @abstractmethod
    def _run_solver(
        self,
        objective_function: Callable[..., Any],
        engine_parameters: Dict[str, Any],
    ) -> Any:
        pass

    @abstractmethod
    def _sync_result_to_parameters(
        self,
        raw_result: Any,
        parameters: List[Any],
    ) -> None:
        pass

    def _finalize_fit(
        self,
        parameters: List[Any],
        raw_result: Any,
    ) -> FitResults:
        self._sync_result_to_parameters(parameters, raw_result)
        success = self._check_success(raw_result)
        self.result = FitResults(
            success=success,
            parameters=parameters,
            reduced_chi_square=self.tracker.best_chi2,
            engine_result=raw_result,
            starting_parameters=parameters,
            fitting_time=self.tracker.fitting_time,
        )
        return self.result

    @abstractmethod
    def _check_success(self, raw_result: Any) -> bool:
        """
        Determine whether the fit was successful.
        This must be implemented by concrete minimizers.
        """
        pass

    def fit(
        self,
        parameters: List[Any],
        objective_function: Callable[..., Any],
    ) -> FitResults:
        minimizer_name = self.name or 'Unnamed Minimizer'
        if self.method is not None:
            minimizer_name += f' ({self.method})'

        self._start_tracking(minimizer_name)

        solver_args = self._prepare_solver_args(parameters)
        raw_result = self._run_solver(objective_function, **solver_args)

        self._stop_tracking()

        result = self._finalize_fit(parameters, raw_result)

        return result

    def _objective_function(
        self,
        engine_params: Dict[str, Any],
        parameters: List[Any],
        sample_models: Any,
        experiments: Any,
        calculator: Any,
    ) -> np.ndarray:
        return self._compute_residuals(
            engine_params,
            parameters,
            sample_models,
            experiments,
            calculator,
        )

    def _create_objective_function(
        self,
        parameters: List[Any],
        sample_models: Any,
        experiments: Any,
        calculator: Any,
    ) -> Callable[[Dict[str, Any]], np.ndarray]:
        return lambda engine_params: self._objective_function(
            engine_params,
            parameters,
            sample_models,
            experiments,
            calculator,
        )
