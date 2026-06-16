# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Fitter orchestrating model refinement via a pluggable minimizer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import Any

import numpy as np

from easydiffraction.analysis.fit_helpers.metrics import get_reliability_inputs
from easydiffraction.analysis.minimizers.base import MinimizerFitOptions
from easydiffraction.analysis.minimizers.enums import MinimizerTypeEnum
from easydiffraction.analysis.minimizers.factory import MinimizerFactory
from easydiffraction.core.variable import Parameter
from easydiffraction.datablocks.experiment.item.base import intensity_category_for
from easydiffraction.utils.enums import VerbosityEnum
from easydiffraction.utils.logging import log

if TYPE_CHECKING:
    from easydiffraction.analysis.fit_helpers.reporting import FitResults
    from easydiffraction.datablocks.experiment.item.base import ExperimentBase
    from easydiffraction.datablocks.structure.collection import Structures


@dataclass(frozen=True, slots=True)
class FitterFitOptions:
    """Execution options for one fitter run."""

    use_physical_limits: bool = False
    random_seed: int | None = None
    resume: bool = False
    extra_steps: int | None = None

    def as_minimizer_options(self) -> MinimizerFitOptions:
        """Return equivalent minimizer options for this fitter run."""
        return MinimizerFitOptions(
            finalize_tracking=False,
            use_physical_limits=self.use_physical_limits,
            random_seed=self.random_seed,
            resume=self.resume,
            extra_steps=self.extra_steps,
        )


def _resolve_fit_result_message(results: FitResults) -> str:
    """Return a normalized fit-result message."""
    if results.message:
        return results.message

    raw_result = results.engine_result
    message = getattr(raw_result, 'message', '')
    return str(message) if message is not None else ''


def _resolve_fit_result_iterations(results: FitResults) -> int:
    """Return a normalized iteration or evaluation count."""
    if results.iterations:
        return int(results.iterations)

    raw_result = results.engine_result
    for attribute_name in ('nfev', 'nit', 'iterations', 'niter'):
        value = getattr(raw_result, attribute_name, None)
        if value is not None:
            return int(value)
    return 0


def _resolve_fit_result_chi_square(results: FitResults) -> float | None:
    """Return a normalized chi-square-like objective value."""
    if results.chi_square is not None:
        return float(results.chi_square)

    raw_result = results.engine_result
    chisqr = getattr(raw_result, 'chisqr', None)
    if chisqr is not None:
        return float(chisqr)

    fun = getattr(raw_result, 'fun', None)
    if fun is None:
        return None

    if np.isscalar(fun):
        return float(fun)

    fun_array = np.asarray(fun, dtype=float)
    return float(np.sum(fun_array**2))


class Fitter:
    """Handles the fitting workflow using a pluggable minimizer."""

    def __init__(self, selection: str = MinimizerTypeEnum.default()) -> None:
        """Initialize the fitter with the selected minimizer."""
        self.selection: str = selection
        self.engine: str = selection
        self.minimizer = MinimizerFactory.create(selection)
        self.results: FitResults | None = None

    @staticmethod
    def _collect_fit_parameters(
        structures: Structures,
        experiments: list[ExperimentBase],
    ) -> list[Parameter]:
        """Return free parameters from structures and experiments."""
        expt_free_params: list[Parameter] = []
        for expt in experiments:
            expt_free_params.extend(
                p
                for p in expt.parameters
                if isinstance(p, Parameter) and not p.user_constrained and p.free
            )
        return structures.free_parameters + expt_free_params

    def _build_objective_function(
        self,
        *,
        params: list[Parameter],
        structures: Structures,
        experiments: list[ExperimentBase],
        weights: np.ndarray | None,
        analysis: object,
    ) -> object:
        """Return the residual function for the current fit context."""

        def objective_function(engine_params: dict[str, Any]) -> np.ndarray:
            """Evaluate residuals for the current minimizer state."""
            return self._residual_function(
                engine_params=engine_params,
                parameters=params,
                structures=structures,
                experiments=experiments,
                weights=weights,
                analysis=analysis,
            )

        return objective_function

    def _postprocess_fit_results(
        self,
        *,
        analysis: object,
        experiments: list[ExperimentBase],
        fitted_parameters: list[Parameter],
    ) -> None:
        """Populate result fields and persist fit projections."""
        if self.results is None:
            return

        self.results.message = _resolve_fit_result_message(self.results)
        self.results.iterations = _resolve_fit_result_iterations(self.results)
        self.results.chi_square = _resolve_fit_result_chi_square(self.results)
        self.results.minimizer_type = self.selection

        if analysis is None:
            return

        analysis._store_fit_result_projection(
            self.results,
            experiments=experiments,
            fitted_parameters=fitted_parameters,
        )

    def fit(
        self,
        structures: Structures,
        experiments: list[ExperimentBase],
        weights: np.ndarray | None = None,
        analysis: object = None,
        verbosity: VerbosityEnum = VerbosityEnum.FULL,
        *,
        options: FitterFitOptions | None = None,
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
        options : FitterFitOptions | None, default=None
            Execution options controlling limits, randomness and resume.

        Raises
        ------
        ValueError
            If resume is requested without the same free parameter set
            used by the saved emcee chain, or if the joint-fit *weights*
            are not a 1-D array of one finite, non-negative value per
            experiment whose total is finite and positive.
        """
        fit_options = options or FitterFitOptions()
        self._require_measured_data(experiments)
        self._require_valid_weights(weights, experiments)
        # Enforce symmetry constraints (e.g. ADP) before collecting
        # free parameters so that components fixed by site symmetry are
        # excluded from the minimizer's parameter set.
        for structure in structures:
            structure._need_categories_update = True
            structure._update_categories()

        params = self._collect_fit_parameters(structures, experiments)

        if not params:
            if fit_options.resume:
                msg = 'Resume requires the same free parameters used by the saved emcee chain.'
                raise ValueError(msg)
            if analysis is not None:
                analysis._clear_persisted_fit_state()
                analysis.fit_results = None
            self.results = None
            log.warning('No parameters selected for fitting.')
            return

        if analysis is not None and not fit_options.resume:
            analysis._capture_fit_parameter_state(params)
        if analysis is not None and fit_options.resume:
            self._validate_resume_parameter_set(params=params, analysis=analysis)

        for param in params:
            param._fit_start_value = param.value

        objective_function = self._build_objective_function(
            params=params,
            structures=structures,
            experiments=experiments,
            weights=weights,
            analysis=analysis,
        )

        self._set_minimizer_sidecar_path(analysis)

        try:
            # Keep tracker finalization in this layer so post-processing
            # can run before the live display is closed.
            self.results = self.minimizer.fit(
                params,
                objective_function,
                verbosity=verbosity,
                options=fit_options.as_minimizer_options(),
            )
            self._postprocess_fit_results(
                analysis=analysis,
                experiments=experiments,
                fitted_parameters=params,
            )
            # Keep the timer open through post-processing so the final
            # sampler row and persisted fitting_time include the heavy
            # Bayesian projection/cache work.
            self.minimizer._finalize_timing()
            self._backfill_persisted_fitting_time(analysis)
        finally:
            self.minimizer._stop_tracking()

    @staticmethod
    def _require_measured_data(experiments: list[ExperimentBase]) -> None:
        """
        Reject fitting any experiment that has no measured intensities.

        A calculated-only experiment carries an absent (``NaN``)
        measured array; fitting it would feed all-``NaN`` residuals to
        the minimizer. Fitting requires a measured scan.

        Parameters
        ----------
        experiments : list[ExperimentBase]
            Experiments scheduled for fitting.

        Raises
        ------
        ValueError
            If any experiment lacks measured data.
        """
        for experiment in experiments:
            has_measured = getattr(experiment, '_has_measured_data', None)
            if callable(has_measured) and not has_measured():
                name = getattr(experiment, 'name', '?')
                msg = (
                    f"Cannot fit experiment '{name}': it has no measured data. "
                    'Fitting requires a measured scan; load measured data first. '
                    '(Calculating a pattern without measured data is supported, '
                    'but fitting against it is not.)'
                )
                raise ValueError(msg)

    @staticmethod
    def _require_valid_weights(
        weights: np.ndarray | None,
        experiments: list[ExperimentBase],
    ) -> None:
        """
        Reject joint-fit weights that would corrupt the residuals.

        Joint-fit weights are normalised by their total and applied as
        ``sqrt(weight)`` per experiment. An invalid set (wrong shape,
        negative, non-finite, or summing to a non-positive or
        non-finite total) would feed ``nan`` or division-by-zero
        residuals to the minimizer, so it is rejected up front.

        Parameters
        ----------
        weights : np.ndarray | None
            Per-experiment joint-fit weights, or ``None`` for equal
            weights (always valid).
        experiments : list[ExperimentBase]
            Experiments scheduled for fitting; one weight per
            experiment is required.

        Raises
        ------
        ValueError
            If *weights* is not a 1-D array of one finite, non-negative
            value per experiment whose total is finite and positive.
        """
        if weights is None:
            return
        arr = np.asarray(weights, dtype=np.float64)
        if arr.ndim != 1:
            msg = (
                'Joint-fit weights must be a 1-D array with one weight '
                f'per experiment; got a {arr.ndim}-D array.'
            )
            raise ValueError(msg)
        if arr.size != len(experiments):
            msg = (
                'Joint-fit weights must provide one weight per experiment; '
                f'got {arr.size} weight(s) for {len(experiments)} experiment(s).'
            )
            raise ValueError(msg)
        if not np.isfinite(arr).all():
            msg = f'Joint-fit weights must all be finite numbers; got {arr.tolist()}.'
            raise ValueError(msg)
        if (arr < 0).any():
            msg = f'Joint-fit weights must all be non-negative; got {arr.tolist()}.'
            raise ValueError(msg)
        total = arr.sum(dtype=np.float64)
        if not np.isfinite(total) or total <= 0:
            msg = (
                'Joint-fit weights must sum to a finite positive total; '
                f'got a total of {total} for {arr.tolist()}.'
            )
            raise ValueError(msg)

    def _set_minimizer_sidecar_path(self, analysis: object) -> None:
        """Set the analysis results sidecar path when supported."""
        if analysis is None or not hasattr(self.minimizer, '_sidecar_path'):
            return

        from easydiffraction.io.results_sidecar import SIDECAR_FILE_NAME  # noqa: PLC0415

        project_metadata = getattr(getattr(analysis, 'project', None), 'metadata', None)
        project_path = getattr(project_metadata, 'path', None)
        sidecar_path = (
            None if project_path is None else project_path / 'analysis' / SIDECAR_FILE_NAME
        )
        self.minimizer._sidecar_path = sidecar_path

    def _backfill_persisted_fitting_time(self, analysis: object) -> None:
        """Update persisted fit-result time after post-processing."""
        if analysis is None or self.results is None:
            return
        fit_result = getattr(analysis, 'fit_result', None)
        set_fitting_time = getattr(fit_result, '_set_fitting_time', None)
        if callable(set_fitting_time):
            set_fitting_time(self.results.fitting_time)

    @staticmethod
    def _validate_resume_parameter_set(
        *,
        params: list[Parameter],
        analysis: object,
    ) -> None:
        """Ensure resume uses the same persisted free-parameter set."""
        persisted_names = [
            item.parameter_unique_name.value for item in getattr(analysis, 'fit_parameters', [])
        ]
        if not persisted_names:
            return

        current_names = [param.unique_name for param in params]
        if persisted_names != current_names:
            msg = 'Resume parameter set differs from the saved emcee chain; start a fresh run.'
            raise ValueError(msg)

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
        # then analysis (constraints), then experiments (calculations).
        # Pass called_by_minimizer so the per-iteration Wyckoff snap
        # runs silently (no re-detection or warnings); detection
        # already ran at fit setup.
        for structure in structures:
            structure._update_categories(called_by_minimizer=True)

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
            intensity_category = intensity_category_for(experiment)
            y_calc = intensity_category.intensity_calc
            y_meas = intensity_category.intensity_meas
            y_meas_su = intensity_category.intensity_meas_su
            diff = (y_meas - y_calc) / y_meas_su

            # Residuals are squared before going into reduced
            # chi-squared
            diff *= np.sqrt(weight)

            # Append the residuals for this experiment
            residuals.extend(diff)

        residual_array = np.array(residuals)
        if getattr(self.minimizer, '_tracks_progress_via_solver_monitor', lambda: False)():
            return residual_array
        return self.minimizer.tracker.track(residual_array, parameters)
