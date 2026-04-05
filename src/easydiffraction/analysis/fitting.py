# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any

import numpy as np

from easydiffraction.analysis.fit_helpers.metrics import get_reliability_inputs
from easydiffraction.analysis.minimizers.factory import MinimizerFactory
from easydiffraction.core.variable import Parameter
from easydiffraction.utils.enums import VerbosityEnum

if TYPE_CHECKING:
    from easydiffraction.analysis.fit_helpers.reporting import FitResults
    from easydiffraction.datablocks.experiment.item.base import ExperimentBase
    from easydiffraction.datablocks.structure.collection import Structures


class Fitter:
    """Handles the fitting workflow using a pluggable minimizer."""

    def __init__(self, selection: str = 'lmfit') -> None:
        self.selection: str = selection
        self.engine: str = selection
        self.minimizer = MinimizerFactory.create(selection)
        self.results: FitResults | None = None

    def fit(
        self,
        structures: Structures,
        experiments: list[ExperimentBase],
        weights: np.ndarray | None = None,
        analysis: object = None,
        verbosity: VerbosityEnum = VerbosityEnum.FULL,
    ) -> None:
        """
        Run the fitting process.

        This method performs the optimization but does not display
        results. Use :meth:`show_fit_results` on the Analysis object to
        display the fit results after fitting is complete.

        Parameters
        ----------
        structures : Structures
            Collection of structures.
        experiments : list[ExperimentBase]
            List of experiments to fit.
        weights : np.ndarray | None, default=None
            Per-experiment weights as a 1-D array (length must match
            *experiments*). When ``None``, equal weights are used.
        analysis : object, default=None
            Optional Analysis object to update its categories during
            fitting.
        verbosity : VerbosityEnum, default=VerbosityEnum.FULL
            Console output verbosity.
        """
        expt_free_params: list[Parameter] = []
        for expt in experiments:
            expt_free_params.extend(
                p
                for p in expt.parameters
                if isinstance(p, Parameter) and not p.constrained and p.free
            )
        params = structures.free_parameters + expt_free_params

        if not params:
            print('⚠️ No parameters selected for fitting.')
            return

        for param in params:
            param._fit_start_value = param.value

        def objective_function(engine_params: dict[str, Any]) -> np.ndarray:
            """
            Evaluate the residual for the current minimizer parameters.

            Parameters
            ----------
            engine_params : dict[str, Any]
                Parameter values provided by the minimizer engine.

            Returns
            -------
            np.ndarray
                Residual array passed back to the minimizer.
            """
            return self._residual_function(
                engine_params=engine_params,
                parameters=params,
                structures=structures,
                experiments=experiments,
                weights=weights,
                analysis=analysis,
            )

        # Perform fitting
        self.results = self.minimizer.fit(params, objective_function, verbosity=verbosity)

    def _process_fit_results(
        self,
        structures: Structures,
        experiments: list[ExperimentBase],
    ) -> None:
        """
        Collect reliability inputs and display fit results.

        This method is typically called by
        :meth:`Analysis.show_fit_results` rather than directly. It
        calculates R-factors and other metrics, then renders them to the
        console.

        Parameters
        ----------
        structures : Structures
            Collection of structures.
        experiments : list[ExperimentBase]
            List of experiments.
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

    def _residual_function(
        self,
        engine_params: dict[str, Any],
        parameters: list[Parameter],
        structures: Structures,
        experiments: list[ExperimentBase],
        weights: np.ndarray | None = None,
        analysis: object = None,
    ) -> np.ndarray:
        """
        Compute residuals between measured and calculated patterns.

        It updates the parameter values according to the
        optimizer-provided engine_params.

        Parameters
        ----------
        engine_params : dict[str, Any]
            Engine-specific parameter dict.
        parameters : list[Parameter]
            List of parameters being optimized.
        structures : Structures
            Collection of structures.
        experiments : list[ExperimentBase]
            List of experiments.
        weights : np.ndarray | None, default=None
            Per-experiment weights as a 1-D array. When ``None``, equal
            weights are used.
        analysis : object, default=None
            Optional Analysis object to update its categories during
            fitting.

        Returns
        -------
        np.ndarray
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
        num_expts: int = len(experiments)
        norm_weights = (
            np.ones(num_expts) if weights is None else np.asarray(weights, dtype=np.float64)
        )

        # Normalize weights so they sum to num_expts
        # We should obtain the same reduced chi_squared when a single
        # dataset is split into two parts and fit together. If weights
        # sum to one, then reduced chi_squared will be half as large as
        # expected.
        norm_weights *= num_expts / np.sum(norm_weights)
        residuals: list[float] = []

        for experiment, weight in zip(experiments, norm_weights, strict=True):
            # Update experiment-specific calculations
            experiment._update_categories(called_by_minimizer=True)

            # Calculate the difference between measured and calculated
            # patterns
            y_calc = experiment.data.intensity_calc
            y_meas = experiment.data.intensity_meas
            y_meas_su = experiment.data.intensity_meas_su
            diff = (y_meas - y_calc) / y_meas_su

            # Residuals are squared before going into reduced
            # chi-squared
            diff *= np.sqrt(weight)

            # Append the residuals for this experiment
            residuals.extend(diff)

        return self.minimizer.tracker.track(np.array(residuals), parameters)
