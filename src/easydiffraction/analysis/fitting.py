# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from typing import TYPE_CHECKING
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import numpy as np

from easydiffraction.analysis.fit_helpers.metrics import get_reliability_inputs
from easydiffraction.analysis.minimizers.factory import MinimizerFactory
from easydiffraction.core.variable import Parameter
from easydiffraction.datablocks.experiment.collection import Experiments
from easydiffraction.datablocks.structure.collection import Structures

if TYPE_CHECKING:
    from easydiffraction.analysis.fit_helpers.reporting import FitResults


class Fitter:
    """Handles the fitting workflow using a pluggable minimizer."""

    def __init__(self, selection: str = 'lmfit') -> None:
        self.selection: str = selection
        self.engine: str = selection
        self.minimizer = MinimizerFactory.create(selection)
        self.results: Optional[FitResults] = None

    def fit(
        self,
        structures: Structures,
        experiments: Experiments,
        weights: Optional[np.array] = None,
        analysis: object = None,
    ) -> None:
        """
        Run the fitting process.

        This method performs the optimization but does not display results. Use
        :meth:`show_fit_results` on the Analysis object to display the fit
        results after fitting is complete.

        Parameters
        ----------
        structures
            Collection of structures.
        experiments
            Collection of experiments.
        weights
            Optional weights for joint fitting.
        analysis
            Optional Analysis object to update its categories during
            fitting.
        """
        params = structures.free_parameters + experiments.free_parameters

        if not params:
            print('⚠️ No parameters selected for fitting.')
            return None

        for param in params:
            param._fit_start_value = param.value

        def objective_function(engine_params: Dict[str, Any]) -> np.ndarray:
            return self._residual_function(
                engine_params=engine_params,
                parameters=params,
                structures=structures,
                experiments=experiments,
                weights=weights,
                analysis=analysis,
            )

        # Perform fitting
        self.results = self.minimizer.fit(params, objective_function)

    def _process_fit_results(
        self,
        structures: Structures,
        experiments: Experiments,
    ) -> None:
        """
        Collect reliability inputs and display fit results.

        This method is typically called by :meth:`Analysis.show_fit_results`
        rather than directly. It calculates R-factors and other metrics, then
        renders them to the console.

        Parameters
        ----------
        structures
            Collection of structures.
        experiments
            Collection of experiments.
        """
        y_obs, y_calc, y_err = get_reliability_inputs(
            structures,
            experiments,
        )

        # Placeholder for future f_obs / f_calc retrieval
        f_obs, f_calc = None, None

        if self.results:
            self.results.display_results(
                y_obs=y_obs,
                y_calc=y_calc,
                y_err=y_err,
                f_obs=f_obs,
                f_calc=f_calc,
            )

    def _collect_free_parameters(
        self,
        structures: Structures,
        experiments: Experiments,
    ) -> List[Parameter]:
        """
        Collect free parameters from structures and experiments.

        Parameters
        ----------
        structures
            Collection of structures.
        experiments
            Collection of experiments.

        Returns
        -------
            List of free parameters.
        """
        free_params: List[Parameter] = structures.free_parameters + experiments.free_parameters
        return free_params

    def _residual_function(
        self,
        engine_params: Dict[str, Any],
        parameters: List[Parameter],
        structures: Structures,
        experiments: Experiments,
        weights: Optional[np.array] = None,
        analysis: object = None,
    ) -> np.ndarray:
        """
        Residual function computes the difference between measured and
        calculated patterns. It updates the parameter values according to the
        optimizer-provided engine_params.

        Parameters
        ----------
        engine_params
            Engine-specific parameter dict.
        parameters
            List of parameters being optimized.
        structures
            Collection of structures.
        experiments
            Collection of experiments.
        weights
            Optional weights for joint fitting.
        analysis
            Optional Analysis object to update its categories during
            fitting.

        Returns
        -------
            Array of weighted residuals.
        """
        # Sync parameters back to objects
        self.minimizer._sync_result_to_parameters(parameters, engine_params)

        # Update categories to reflect new parameter values
        # Order matters: structures first (symmetry, structure),
        # then analysis (constraints), then experiments (calculations)
        for structure in structures:
            structure._update_categories()

        if analysis is not None:
            analysis._update_categories(called_by_minimizer=True)

        # Prepare weights for joint fitting
        num_expts: int = len(experiments.names)
        if weights is None:
            _weights = np.ones(num_expts)
        else:
            _weights_list: List[float] = []
            for name in experiments.names:
                _weight = weights[name].weight.value
                _weights_list.append(_weight)
            _weights = np.array(_weights_list, dtype=np.float64)

        # Normalize weights so they sum to num_expts
        # We should obtain the same reduced chi_squared when a single
        # dataset is split into two parts and fit together. If weights
        # sum to one, then reduced chi_squared will be half as large as
        # expected.
        _weights *= num_expts / np.sum(_weights)
        residuals: List[float] = []

        for experiment, weight in zip(experiments.values(), _weights, strict=True):
            # Update experiment-specific calculations
            experiment._update_categories(called_by_minimizer=True)

            # Calculate the difference between measured and calculated
            # patterns
            y_calc: np.ndarray = experiment.data.intensity_calc
            y_meas: np.ndarray = experiment.data.intensity_meas
            y_meas_su: np.ndarray = experiment.data.intensity_meas_su
            diff = (y_meas - y_calc) / y_meas_su

            # Residuals are squared before going into reduced
            # chi-squared
            diff *= np.sqrt(weight)

            # Append the residuals for this experiment
            residuals.extend(diff)

        return self.minimizer.tracker.track(np.array(residuals), parameters)
