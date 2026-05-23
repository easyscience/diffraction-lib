# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from contextlib import suppress
from itertools import combinations
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

from easydiffraction.analysis.categories.aliases.factory import AliasesFactory
from easydiffraction.analysis.categories.constraints.factory import ConstraintsFactory
from easydiffraction.analysis.categories.fit_parameter_correlations import FitParameterCorrelations
from easydiffraction.analysis.categories.fit_parameters import FitParameters
from easydiffraction.analysis.categories.fit_result import FitResult
from easydiffraction.analysis.categories.joint_fit import JointFitCollection
from easydiffraction.analysis.categories.minimizer import MinimizerCategoryFactory
from easydiffraction.analysis.categories.minimizer.base import MinimizerCategoryBase
from easydiffraction.analysis.categories.minimizer.bayesian_base import BayesianMinimizerBase
from easydiffraction.analysis.categories.sequential_fit import SequentialFit
from easydiffraction.analysis.categories.sequential_fit import SequentialFitFactory
from easydiffraction.analysis.categories.sequential_fit_extract import (
    SequentialFitExtractCollection,
)
from easydiffraction.analysis.enums import FitCorrelationSourceEnum
from easydiffraction.analysis.enums import FitModeEnum
from easydiffraction.analysis.enums import FitResultKindEnum
from easydiffraction.analysis.fit_helpers.bayesian import BayesianFitResults
from easydiffraction.analysis.fit_helpers.bayesian import PosteriorPredictiveSummary
from easydiffraction.analysis.fit_helpers.bayesian import PosteriorSamples
from easydiffraction.analysis.fit_helpers.reporting import FitResults
from easydiffraction.analysis.fitting import Fitter
from easydiffraction.analysis.minimizers.enums import MinimizerTypeEnum
from easydiffraction.core.category_owner import CategoryOwner
from easydiffraction.core.guard import _apply_help_filter
from easydiffraction.core.singleton import ConstraintsHandler
from easydiffraction.core.variable import NumericDescriptor
from easydiffraction.core.variable import Parameter
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.datablocks.experiment.item.base import intensity_category_for
from easydiffraction.display.progress import make_display_handle
from easydiffraction.display.tables import TableRenderer
from easydiffraction.io.cif.serialize import analysis_to_cif
from easydiffraction.utils.enums import VerbosityEnum
from easydiffraction.utils.logging import console
from easydiffraction.utils.logging import log
from easydiffraction.utils.utils import _help_method_rows
from easydiffraction.utils.utils import _help_property_rows
from easydiffraction.utils.utils import render_cif
from easydiffraction.utils.utils import render_object_help
from easydiffraction.utils.utils import render_table

if TYPE_CHECKING:
    from easydiffraction.analysis.categories.minimizer.base import MinimizerCategoryBase
    from easydiffraction.core.posterior import PosteriorParameterSummary

_SUMMARY_HIDDEN_PARAMETER_CATEGORIES = frozenset({'pd_data', 'total_data', 'refln'})
_POSTERIOR_SAMPLE_NDIM = 3
_FLATTENED_POSTERIOR_SAMPLE_NDIM = 2
_CREDIBLE_INTERVAL_LEVEL_COUNT = 2


# LSQ result descriptors default to ``None`` (review-8 F6); the CIF
# restore path calls ``int(...)`` on every result field, which would
# crash for a CIF saved before any fit ran. ``_int_or_none`` lets the
# call site stay terse while preserving ``None`` through the coercion.
def _int_or_none(value: object) -> int | None:
    """Coerce a descriptor value to ``int``; ``None`` passes through."""
    return None if value is None else int(value)


def _discover_property_rows(cls: type) -> list[list[str]]:
    """Return public property rows for analysis help tables."""
    return _help_property_rows(cls)


def _discover_method_rows(cls: type) -> list[list[str]]:
    """Return public method rows for analysis help tables."""
    return _help_method_rows(cls)


class AnalysisDisplay:
    """
    Display helper - parameter tables, CIF, and fit results.

    Accessed via ``analysis.display``.
    """

    def __init__(self, analysis: Analysis) -> None:
        self._analysis = analysis

    def help(self) -> None:
        """Print available analysis-display methods."""
        render_object_help(self)

    def _flush_structure_categories(self) -> None:
        """
        Flush pending category updates so symmetry flags are fresh.
        """
        project = self._analysis.project
        for structure in project.structures:
            structure._need_categories_update = True
            structure._update_categories()

    @staticmethod
    def _summary_parameters(
        params: list[StringDescriptor | NumericDescriptor | Parameter],
    ) -> list[StringDescriptor | NumericDescriptor | Parameter]:
        """Return parameters suitable for compact summary displays."""
        return [
            param
            for param in params
            if param._identity.category_code not in _SUMMARY_HIDDEN_PARAMETER_CATEGORIES
        ]

    def all_params(self) -> None:
        """Print all parameters for structures and experiments."""
        project = self._analysis.project
        self._flush_structure_categories()
        structures_params = self._summary_parameters(project.structures.parameters)
        experiments_params = self._summary_parameters(project.experiments.parameters)

        if not structures_params and not experiments_params:
            log.warning('No parameters found.')
            return

        tabler = TableRenderer.get()

        filtered_headers = [
            'datablock',
            'category',
            'entry',
            'parameter',
            'value',
            'fittable',
        ]

        if structures_params:
            console.paragraph('All parameters for all structures (🧩 data blocks)')
            df = Analysis._get_params_as_dataframe(structures_params)
            filtered_df = df[filtered_headers]
            tabler.render(filtered_df)

        if experiments_params:
            console.paragraph('All parameters for all experiments (🔬 data blocks)')
            df = Analysis._get_params_as_dataframe(experiments_params)
            filtered_df = df[filtered_headers]
            tabler.render(filtered_df)

    def fittable_params(self) -> None:
        """Print all fittable parameters."""
        project = self._analysis.project
        self._flush_structure_categories()
        structures_params = project.structures.fittable_parameters
        experiments_params = project.experiments.fittable_parameters

        if not structures_params and not experiments_params:
            log.warning('No fittable parameters found.')
            return

        tabler = TableRenderer.get()

        filtered_headers = [
            'datablock',
            'category',
            'entry',
            'parameter',
            'value',
            'uncertainty',
            'units',
            'free',
        ]

        if structures_params:
            console.paragraph('Fittable parameters for all structures (🧩 data blocks)')
            df = Analysis._get_params_as_dataframe(structures_params)
            filtered_df = df[filtered_headers]
            tabler.render(filtered_df)

        if experiments_params:
            console.paragraph('Fittable parameters for all experiments (🔬 data blocks)')
            df = Analysis._get_params_as_dataframe(experiments_params)
            filtered_df = df[filtered_headers]
            tabler.render(filtered_df)

    def free_params(self) -> None:
        """Print only currently free (varying) parameters."""
        project = self._analysis.project
        self._flush_structure_categories()
        free_params = getattr(project, 'free_parameters', None)
        if free_params is None:
            structures_params = project.structures.free_parameters
            experiments_params = project.experiments.free_parameters
            free_params = structures_params + experiments_params

        if not free_params:
            log.warning('No free parameters found.')
            return

        tabler = TableRenderer.get()

        filtered_headers = [
            'datablock',
            'category',
            'entry',
            'parameter',
            'value',
            'uncertainty',
            'min',
            'max',
            'units',
        ]

        console.paragraph(
            'Free parameters for both structures (🧩 data blocks) and experiments (🔬 data blocks)'
        )
        df = Analysis._get_params_as_dataframe(free_params)
        filtered_df = df[filtered_headers]
        tabler.render(filtered_df)

    def how_to_access_parameters(self) -> None:
        """
        Show Python access paths for all parameters.

        The output explains how to reference specific parameters in
        code.
        """
        project = self._analysis.project
        structures_params = self._summary_parameters(project.structures.parameters)
        experiments_params = self._summary_parameters(project.experiments.parameters)
        all_params = {
            'structures': structures_params,
            'experiments': experiments_params,
        }

        if not structures_params and not experiments_params:
            log.warning('No parameters found.')
            return

        columns_headers = [
            'datablock',
            'category',
            'entry',
            'parameter',
            'How to Access in Python Code',
        ]

        columns_alignment = [
            'left',
            'left',
            'left',
            'left',
            'left',
        ]

        columns_data = []
        project_varname = project._varname
        for datablock_code, params in all_params.items():
            for param in params:
                if isinstance(param, (StringDescriptor, NumericDescriptor, Parameter)):
                    datablock_entry_name = param._identity.datablock_entry_name
                    category_code = param._identity.category_code
                    category_entry_name = param._identity.category_entry_name or ''
                    param_key = param.name
                    code_variable = (
                        f'{project_varname}.{datablock_code}'
                        f"['{datablock_entry_name}'].{category_code}"
                    )
                    if category_entry_name:
                        code_variable += f"['{category_entry_name}']"
                    code_variable += f'.{param_key}'
                    columns_data.append([
                        datablock_entry_name,
                        category_code,
                        category_entry_name,
                        param_key,
                        code_variable,
                    ])

        console.paragraph('How to access parameters')
        render_table(
            columns_headers=columns_headers,
            columns_alignment=columns_alignment,
            columns_data=columns_data,
        )

    def parameter_cif_uids(self) -> None:
        """
        Show CIF unique IDs for all parameters.

        The output explains which unique identifiers are used when
        creating CIF-based constraints.
        """
        project = self._analysis.project
        structures_params = self._summary_parameters(project.structures.parameters)
        experiments_params = self._summary_parameters(project.experiments.parameters)
        all_params = {
            'structures': structures_params,
            'experiments': experiments_params,
        }

        if not structures_params and not experiments_params:
            log.warning('No parameters found.')
            return

        columns_headers = [
            'datablock',
            'category',
            'entry',
            'parameter',
            'Unique Identifier for CIF Constraints',
        ]

        columns_alignment = [
            'left',
            'left',
            'left',
            'left',
            'left',
        ]

        columns_data = []
        for params in all_params.values():
            for param in params:
                if isinstance(param, (StringDescriptor, NumericDescriptor, Parameter)):
                    datablock_entry_name = param._identity.datablock_entry_name
                    category_code = param._identity.category_code
                    category_entry_name = param._identity.category_entry_name or ''
                    param_key = param.name
                    cif_uid = param._cif_handler.uid
                    columns_data.append([
                        datablock_entry_name,
                        category_code,
                        category_entry_name,
                        param_key,
                        cif_uid,
                    ])

        console.paragraph('Show parameter CIF unique identifiers')
        render_table(
            columns_headers=columns_headers,
            columns_alignment=columns_alignment,
            columns_data=columns_data,
        )

    def constraints(self) -> None:
        """Print a table of all user-defined symbolic constraints."""
        self._analysis.constraints.show()

    def fit_results(self) -> None:
        """
        Display a summary of the fit results.

        Renders the fit quality metrics (reduced χ², R-factors) and a
        table of fitted parameters with their starting values, final
        values, and uncertainties.

        This method should be called after :meth:`Analysis.fit`
        completes. If no fit has been performed yet, a warning is
        logged.
        """
        analysis = self._analysis
        if analysis.fit_results is None:
            log.warning('No fit results available. Run fit() first.')
            return

        structures = analysis.project.structures
        experiments = list(analysis.project.experiments.values())

        analysis.fitter._process_fit_results(structures, experiments)

    def as_cif(self) -> None:
        """Render the analysis section as CIF in console."""
        self._analysis.show_as_cif()


class _AnalysisOwnerAccessorsMixin:
    @property
    def project(self) -> object:
        """Project that owns this analysis section."""
        return self._project

    @property
    def aliases(self) -> object:
        """Alias mappings used by symbolic constraints and displays."""
        return self._aliases

    @property
    def constraints(self) -> object:
        """Symbolic constraints owned by this analysis section."""
        return self._constraints

    @property
    def display(self) -> AnalysisDisplay:
        """Display helper for parameter tables, CIF, and fit results."""
        return self._display

    @property
    def fitter(self) -> Fitter:
        """Fitting engine used by this analysis object."""
        return self._fitter

    @fitter.setter
    def fitter(self, value: Fitter) -> None:
        self._fitter = value

    @property
    def fit_results(self) -> object | None:
        """Results from the most recent fit, if any."""
        if self._fit_results is None and self._has_persisted_fit_state():
            self._restore_fit_results_from_projection()
        return self._fit_results

    @fit_results.setter
    def fit_results(self, value: object | None) -> None:
        self._fit_results = value
        self._fitter.results = value


class _AnalysisPersistedCategoryAccessorsMixin:
    @property
    def fit_parameters(self) -> FitParameters:
        """Persisted fit-parameter control snapshots."""
        return self._fit_parameters

    @property
    def fit_result(self) -> FitResult:
        """Persisted common fit-result status metadata."""
        return self._fit_result

    @property
    def fit_parameter_correlations(self) -> FitParameterCorrelations:
        """Persisted fit-parameter correlation summaries."""
        return self._fit_parameter_correlations


class Analysis(
    _AnalysisOwnerAccessorsMixin,
    _AnalysisPersistedCategoryAccessorsMixin,
    CategoryOwner,
):
    """
    High-level orchestration of analysis tasks for a Project.

    This class wires calculators and minimizers, exposes a compact
    interface for parameters, constraints and results, and coordinates
    computations across the project's structures and experiments.
    """

    def __init__(self, project: object) -> None:
        """
        Create a new Analysis instance bound to a project.

        Parameters
        ----------
        project : object
            The project that owns models and experiments.
        """
        super().__init__()
        self._project = project
        self._aliases_type: str = AliasesFactory.default_tag()
        self._aliases = AliasesFactory.create(self._aliases_type)
        self._constraints_type: str = ConstraintsFactory.default_tag()
        self._constraints = ConstraintsFactory.create(self._constraints_type)
        self._constraints_handler = ConstraintsHandler.get()
        self._minimizer: MinimizerCategoryBase = MinimizerCategoryFactory.create(
            MinimizerTypeEnum.default().value
        )
        self._fitting_mode_type: FitModeEnum = FitModeEnum.default()
        self._joint_fit: JointFitCollection = JointFitCollection()
        self._sequential_fit: SequentialFit = SequentialFitFactory.create(
            SequentialFitFactory.default_tag()
        )
        self._sequential_fit_extract = SequentialFitExtractCollection()
        self._fit_parameters = FitParameters()
        self._fit_result = FitResult()
        self._fit_parameter_correlations = FitParameterCorrelations()
        self._has_persisted_fit_state_data = False
        self._persisted_fit_state_sidecar: dict[str, object] = {}
        self._fitter = Fitter(self.minimizer_type)
        self._fit_results = None
        self._parameter_snapshots: dict[str, dict[str, dict]] = {}
        self._display = AnalysisDisplay(self)
        self._attach_category_parents()

    def _attach_category_parents(self) -> None:
        """Link owned categories back to this analysis object."""
        self._aliases._parent = self
        self._constraints._parent = self
        self._minimizer._parent = self
        self._joint_fit._parent = self
        self._sequential_fit._parent = self
        self._sequential_fit_extract._parent = self
        self._fit_parameters._parent = self
        self._fit_result._parent = self
        self._fit_parameter_correlations._parent = self

    def _supported_filters_for(self, category: object) -> dict[str, object]:
        """Return owner context filters for a switchable category."""
        del category
        return {}

    def _swap_minimizer(self, new_type: str) -> None:
        """Switch the active minimizer category."""
        self._replace_minimizer(new_type, announce=True)

    def _swap_fitting_mode(self, new_type: str) -> None:
        """Switch the active fitting-mode category."""
        msg = f"Switching fitting mode to '{new_type}' is not wired yet."
        raise NotImplementedError(msg)

    @staticmethod
    def _predictive_cache_key(
        experiment_name: str,
        x_axis_name: str,
        *,
        include_draws: bool = True,
    ) -> str:
        """Return the runtime cache key for one predictive summary."""
        key_suffix = 'draws' if include_draws else 'band'
        return f'{experiment_name}:{x_axis_name}:{key_suffix}'

    def _live_parameter_map(self) -> dict[str, Parameter]:
        """Return live parameters keyed by unique name."""
        all_parameters = self.project.structures.parameters + self.project.experiments.parameters
        return {
            param.unique_name: param
            for param in all_parameters
            if isinstance(param, Parameter) and hasattr(param, 'unique_name')
        }

    def _ordered_restored_parameter_names(self) -> list[str]:
        """
        Return persisted parameter names in display and array order.
        """
        return [row.param_unique_name.value for row in self.fit_parameters]

    def _restore_live_parameter_state(self, param_map: dict[str, Parameter]) -> None:
        """Restore saved fit metadata onto live parameter objects."""
        for row in self.fit_parameters:
            parameter = param_map.get(row.param_unique_name.value)
            if parameter is None:
                log.warning(
                    'Persisted fit-state references unknown parameter '
                    f'{row.param_unique_name.value!r}.'
                )
                continue

            parameter.fit_min = row.fit_min.value
            parameter.fit_max = row.fit_max.value
            parameter._set_fit_bounds_uncertainty_multiplier(
                row.fit_bounds_uncertainty_multiplier.value
            )
            parameter._fit_start_value = row.start_value.value
            parameter._fit_start_uncertainty = row.start_uncertainty.value
            posterior = row.posterior_summary(display_name=parameter.name)
            parameter._set_posterior(posterior)
            if posterior is not None and np.isfinite(posterior.standard_deviation):
                parameter.uncertainty = posterior.standard_deviation

    def _restored_fit_parameters(self, param_map: dict[str, Parameter]) -> list[Parameter]:
        """Return live parameters in the persisted fit-result order."""
        restored_parameters: list[Parameter] = []
        for unique_name in self._ordered_restored_parameter_names():
            parameter = param_map.get(unique_name)
            if parameter is not None:
                restored_parameters.append(parameter)
        return restored_parameters

    def _restored_posterior_samples(self) -> PosteriorSamples | None:
        """Return restored posterior samples from the HDF5 sidecar."""
        posterior_data = self._persisted_fit_state_sidecar.get('posterior', {})
        parameter_samples = posterior_data.get('parameter_samples')
        if parameter_samples is None:
            return None

        posterior_rows = [row for row in self.fit_parameters if row.has_posterior_summary()]
        parameter_names = [row.param_unique_name.value for row in posterior_rows]

        parameter_sample_array = np.asarray(parameter_samples, dtype=float)
        if parameter_sample_array.ndim != _POSTERIOR_SAMPLE_NDIM:
            log.warning('Persisted posterior samples have an invalid shape for restore.')
            return None
        if parameter_sample_array.shape[2] != len(parameter_names):
            log.warning(
                'Persisted posterior samples do not match restored posterior parameter names.'
            )
            return None

        log_posterior = posterior_data.get('log_posterior')
        draw_index = posterior_data.get('draw_index')
        return PosteriorSamples(
            parameter_names=parameter_names,
            parameter_samples=parameter_sample_array,
            log_posterior=(
                None if log_posterior is None else np.asarray(log_posterior, dtype=float)
            ),
            draw_index=None if draw_index is None else np.asarray(draw_index),
        )

    def _restored_posterior_summaries(self) -> list[PosteriorParameterSummary]:
        """Return posterior summary rows as runtime summary objects."""
        param_map = self._live_parameter_map()
        summaries: list[PosteriorParameterSummary] = []
        for row in self.fit_parameters:
            parameter = param_map.get(row.param_unique_name.value)
            display_name = row.param_unique_name.value if parameter is None else parameter.name
            summary = row.posterior_summary(display_name=display_name)
            if summary is not None:
                summaries.append(summary)
        return summaries

    def _restored_predictive_summaries(self) -> dict[str, PosteriorPredictiveSummary]:
        """Return restored predictive summaries for runtime reuse."""
        restored_predictive: dict[str, PosteriorPredictiveSummary] = {}
        predictive_data = self._persisted_fit_state_sidecar.get('predictive_datasets', {})
        for item_id, dataset in predictive_data.items():
            experiment_name = str(item_id)
            x_axis_name = str(dataset.get('x_axis_name', ''))
            summary = PosteriorPredictiveSummary(
                experiment_name=experiment_name,
                x_axis_name=x_axis_name,
                x=np.asarray(dataset['x'], dtype=float),
                best_sample_prediction=np.asarray(
                    dataset['best_sample_prediction'],
                    dtype=float,
                ),
                lower_95=(
                    None
                    if dataset.get('lower_95') is None
                    else np.asarray(dataset['lower_95'], dtype=float)
                ),
                upper_95=(
                    None
                    if dataset.get('upper_95') is None
                    else np.asarray(dataset['upper_95'], dtype=float)
                ),
                lower_68=(
                    None
                    if dataset.get('lower_68') is None
                    else np.asarray(dataset['lower_68'], dtype=float)
                ),
                upper_68=(
                    None
                    if dataset.get('upper_68') is None
                    else np.asarray(dataset['upper_68'], dtype=float)
                ),
                draws=(
                    None
                    if dataset.get('draws') is None
                    else np.asarray(dataset['draws'], dtype=float)
                ),
            )
            restored_predictive[experiment_name] = summary
            restored_predictive[
                self._predictive_cache_key(
                    experiment_name,
                    x_axis_name,
                    include_draws=False,
                )
            ] = summary
            if summary.draws is not None:
                restored_predictive[
                    self._predictive_cache_key(
                        experiment_name,
                        x_axis_name,
                        include_draws=True,
                    )
                ] = summary
        return restored_predictive

    def _restore_fit_results_from_projection(self) -> object | None:
        """Rebuild a runtime fit-result object from saved state."""
        if not self._has_persisted_fit_state():
            return None

        # Validate the (result_kind, minimizer family) pair before
        # touching any live parameters or posterior arrays, so a CIF
        # whose tags disagree fails fast with a clear error rather than
        # crashing deep inside the Bayesian restore (review-8 F5).
        if (
            self.fit_result.result_kind.value == FitResultKindEnum.BAYESIAN.value
            and not isinstance(self.minimizer, BayesianMinimizerBase)
        ):
            bayesian_kind = FitResultKindEnum.BAYESIAN.value
            deterministic_kind = FitResultKindEnum.DETERMINISTIC.value
            msg = (
                'CIF restore mismatch: '
                f"_fit_result.result_kind = '{bayesian_kind}' "
                f"but _minimizer.type = '{self.minimizer_type}' "
                'is not a Bayesian minimizer. Either set '
                '_minimizer.type to a Bayesian sampler '
                '(e.g. bumps (dream)), or set _fit_result.result_kind '
                f"to '{deterministic_kind}'."
            )
            raise ValueError(msg)

        param_map = self._live_parameter_map()
        self._restore_live_parameter_state(param_map)
        restored_parameters = self._restored_fit_parameters(param_map)
        fitting_time = self.fit_result.fitting_time.value
        reduced_chi_square = self.fit_result.reduced_chi_square.value

        if self.fit_result.result_kind.value == FitResultKindEnum.BAYESIAN.value:
            posterior_samples = self._restored_posterior_samples()
            sample_shape = (
                np.asarray(posterior_samples.parameter_samples).shape
                if posterior_samples is not None
                else (0, 0, 0)
            )
            sampler_settings = self.minimizer._native_kwargs()
            sampler_name = (
                'dream'
                if self.minimizer_type == MinimizerTypeEnum.BUMPS_DREAM.value
                else str(self.minimizer_type)
            )
            restored_results = BayesianFitResults(
                success=bool(self.fit_result.success.value),
                parameters=restored_parameters,
                reduced_chi_square=reduced_chi_square,
                starting_parameters=list(restored_parameters),
                fitting_time=fitting_time,
                sampler_name=sampler_name,
                point_estimate_name=self.minimizer.point_estimate_name.value,
                posterior_samples=posterior_samples,
                posterior_parameter_summaries=self._restored_posterior_summaries(),
                posterior_predictive=self._restored_predictive_summaries(),
                credible_interval_levels=(
                    float(self.minimizer.credible_interval_inner.value),
                    float(self.minimizer.credible_interval_outer.value),
                ),
                sampler_settings={
                    'steps': int(sampler_settings.get('steps', 0)),
                    'burn': int(sampler_settings.get('burn', 0)),
                    'thin': int(sampler_settings.get('thin', 0)),
                    'pop': int(sampler_settings.get('pop', 0)),
                    'parallel': int(sampler_settings.get('parallel', 0)),
                    'init': str(sampler_settings.get('init', '')),
                    'random_seed': sampler_settings.get('random_seed'),
                },
                convergence_diagnostics={
                    'converged': False,
                    'max_r_hat': self.minimizer.gelman_rubin_max.value,
                    'min_ess_bulk': self.minimizer.effective_sample_size_min.value,
                    'n_draws': int(sample_shape[0]),
                    'n_chains': int(sample_shape[1]),
                    'n_parameters': int(sample_shape[2]),
                },
                sampler_completed=bool(self.minimizer.sampler_completed.value),
                best_log_posterior=self.minimizer.best_log_posterior.value,
            )
            restored_results.message = self.fit_result.message.value
            restored_results.iterations = int(self.fit_result.iterations.value)
            self.fit_results = restored_results
            return restored_results

        restored_results = FitResults(
            success=bool(self.fit_result.success.value),
            parameters=restored_parameters,
            reduced_chi_square=reduced_chi_square,
            starting_parameters=list(restored_parameters),
            fitting_time=fitting_time,
            optimizer_name=self.minimizer.optimizer_name.value,
            method_name=self.minimizer.method_name.value,
            objective_name=self.minimizer.objective_name.value,
            objective_value=self.minimizer.objective_value.value,
            n_data_points=_int_or_none(self.minimizer.n_data_points.value),
            n_parameters=_int_or_none(self.minimizer.n_parameters.value),
            n_free_parameters=_int_or_none(self.minimizer.n_free_parameters.value),
            degrees_of_freedom=_int_or_none(self.minimizer.degrees_of_freedom.value),
            covariance_available=self.minimizer.covariance_available.value,
            correlation_available=self.minimizer.correlation_available.value,
            runtime_seconds=self.minimizer.runtime_seconds.value,
            iterations_performed=_int_or_none(self.minimizer.iterations_performed.value),
            exit_reason=self.minimizer.exit_reason.value,
        )
        restored_results.message = self.fit_result.message.value
        restored_results.iterations = int(self.fit_result.iterations.value)
        restored_results.chi_square = self.minimizer.objective_value.value
        self.fit_results = restored_results
        return restored_results

    def help(self) -> None:
        """Print a summary of analysis properties and methods."""
        cls = type(self)
        console.paragraph(f"Help for '{cls.__name__}'")

        property_rows = _discover_property_rows(cls)
        method_rows = _discover_method_rows(cls)
        property_names = [row[1] for row in property_rows]
        method_names = [row[1][:-2] for row in method_rows]
        property_names, method_names = _apply_help_filter(self, property_names, method_names)

        filtered_property_names = set(property_names)
        filtered_method_names = set(method_names)
        filtered_property_rows = []
        for row in property_rows:
            if row[1] in filtered_property_names:
                filtered_property_rows.append([
                    str(len(filtered_property_rows) + 1),
                    row[1],
                    row[2],
                    row[3],
                ])

        filtered_method_rows = []
        for row in method_rows:
            method_name = row[1][:-2]
            if method_name in filtered_method_names:
                filtered_method_rows.append([str(len(filtered_method_rows) + 1), row[1], row[2]])

        if filtered_property_rows:
            console.paragraph('Properties')
            render_table(
                columns_headers=['#', 'Name', 'Writable', 'Description'],
                columns_alignment=['right', 'left', 'center', 'left'],
                columns_data=filtered_property_rows,
            )

        if filtered_method_rows:
            console.paragraph('Methods')
            render_table(
                columns_headers=['#', 'Name', 'Description'],
                columns_alignment=['right', 'left', 'left'],
                columns_data=filtered_method_rows,
            )

    def _help_filter(
        self,
        properties: list[str],
        methods: list[str],
    ) -> tuple[list[str], list[str]]:
        """Hide inactive mode-specific categories from analysis help."""
        hidden_properties: set[str]
        if self._fitting_mode_type is FitModeEnum.SINGLE:
            hidden_properties = {'joint_fit', 'sequential_fit', 'sequential_fit_extract'}
        elif self._fitting_mode_type is FitModeEnum.JOINT:
            hidden_properties = {'sequential_fit', 'sequential_fit_extract'}
        elif self._fitting_mode_type is FitModeEnum.SEQUENTIAL:
            hidden_properties = {'joint_fit'}
        else:  # pragma: no cover
            hidden_properties = set()

        filtered_properties = [name for name in properties if name not in hidden_properties]
        return filtered_properties, methods

    def _serializable_categories(self) -> list:
        """Serializable analysis categories for the active fit mode."""
        categories = [
            self.minimizer,
            self.aliases,
            self.constraints,
        ]

        if self._fitting_mode_type is FitModeEnum.JOINT:
            categories.append(self.joint_fit)
        elif self._fitting_mode_type is FitModeEnum.SEQUENTIAL:
            categories.extend([
                self.sequential_fit,
                self.sequential_fit_extract,
            ])

        if self._has_persisted_fit_state():
            categories.extend(self._fit_state_categories())

        return categories

    # ------------------------------------------------------------------
    #  Parameter helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_params_as_dataframe(
        params: list[NumericDescriptor | Parameter],
    ) -> pd.DataFrame:
        """
        Convert a list of parameters to a DataFrame.

        Parameters
        ----------
        params : list[NumericDescriptor | Parameter]
            List of DescriptorFloat or Parameter objects.

        Returns
        -------
        pd.DataFrame
            A pandas DataFrame containing parameter information.
        """
        records = []
        for param in params:
            record = {}
            # TODO: Merge into one. Add field if attr exists
            # TODO: f'{param.value!r}' for StringDescriptor?
            if isinstance(param, (StringDescriptor, NumericDescriptor, Parameter)):
                record = {
                    ('fittable', 'left'): False,
                    ('datablock', 'left'): param._identity.datablock_entry_name,
                    ('category', 'left'): param._identity.category_code,
                    ('entry', 'left'): param._identity.category_entry_name or '',
                    ('parameter', 'left'): param.name,
                    ('value', 'right'): param.value,
                }
            if isinstance(param, (NumericDescriptor, Parameter)):
                record |= {
                    ('units', 'left'): param.units,
                }
            if isinstance(param, Parameter):
                record |= {
                    ('fittable', 'left'): not param.user_constrained
                    and not param.symmetry_constrained,
                    ('free', 'left'): param.free,
                    ('min', 'right'): param.fit_min,
                    ('max', 'right'): param.fit_max,
                    ('uncertainty', 'right'): param.uncertainty or '',
                }
            records.append(record)

        df = pd.DataFrame.from_records(records)
        df.columns = pd.MultiIndex.from_tuples(df.columns)
        return df

    def fit(self) -> None:
        """Execute fitting for the currently selected fitting mode."""
        mode = self._fitting_mode_type
        if mode is FitModeEnum.SINGLE:
            self._run_single()
        elif mode is FitModeEnum.JOINT:
            self._prepare_joint_fit()
            self._run_joint()
        elif mode is FitModeEnum.SEQUENTIAL:
            self._run_sequential()
        else:  # pragma: no cover
            msg = f'Unknown fit mode: {mode!r}'
            raise ValueError(msg)

    def _warn_results_sidecar_overwrite(self) -> None:
        """Warn before persisted sidecar arrays are overwritten."""
        project_path = self.project.info.path
        if project_path is None:
            return

        from easydiffraction.io.results_sidecar import (  # noqa: PLC0415
            warn_analysis_results_sidecar_overwrite,
        )

        warn_analysis_results_sidecar_overwrite(analysis_dir=project_path / 'analysis')

    def _prepare_joint_fit(self) -> None:
        """
        Auto-populate and validate joint-fit rows before execution.
        """
        experiments = self.project.experiments
        minimum_joint_experiments = 2
        if len(experiments) < minimum_joint_experiments:
            msg = (
                'Joint fitting requires at least '
                f'{minimum_joint_experiments} experiments, found {len(experiments)}.'
            )
            raise ValueError(msg)

        experiment_names = list(experiments.names)
        experiment_name_set = set(experiment_names)
        existing_ids = [item.experiment_id.value for item in self._joint_fit]

        unexpected_ids = sorted({name for name in existing_ids if name not in experiment_name_set})
        if unexpected_ids:
            msg = (
                'joint_fit contains experiment_id values not present in the project: '
                f'{unexpected_ids}.'
            )
            raise ValueError(msg)

        existing_id_set = set(existing_ids)
        for experiment_id in experiment_names:
            if experiment_id not in existing_id_set:
                self._joint_fit.create(experiment_id=experiment_id, weight=1.0)
                existing_id_set.add(experiment_id)

        missing_ids = [name for name in experiment_names if name not in existing_id_set]
        if missing_ids:
            msg = f'joint_fit is missing rows for project experiments: {missing_ids}.'
            raise ValueError(msg)

    @property
    def fitting_mode_type(self) -> str:
        """Currently selected fitting mode."""
        return self._fitting_mode_type.value

    @fitting_mode_type.setter
    def fitting_mode_type(self, value: str) -> None:
        supported = [mode.value for mode in FitModeEnum]

        try:
            new_mode = FitModeEnum(value)
        except ValueError:
            log.warning(
                f"Unsupported fitting mode '{value}'. "
                f'Supported fitting modes: {supported}. '
                f"For more information, use 'show_supported_fitting_mode_types()'",
            )
            return

        self._fitting_mode_type = new_mode
        console.paragraph('Fitting mode changed to')
        console.print(self._fitting_mode_type.value)

    def show_supported_fitting_mode_types(self) -> None:
        """Print supported fitting modes and mark the current type."""
        columns_data = [
            [
                '*' if mode is self._fitting_mode_type else '',
                mode.value,
                mode.description(),
            ]
            for mode in FitModeEnum
        ]
        console.paragraph('Fitting mode types')
        render_table(
            columns_headers=['', 'Type', 'Description'],
            columns_alignment=['left', 'left', 'left'],
            columns_data=columns_data,
        )

    def show_current_fitting_mode_type(self) -> None:
        """Print the currently selected fitting mode."""
        console.paragraph('Current fitting mode type')
        console.print(self._fitting_mode_type.value)

    def _set_fitting_mode_type(self, value: str) -> None:
        """Set the fitting mode without console output."""
        supported = [mode.value for mode in FitModeEnum]

        try:
            self._fitting_mode_type = FitModeEnum(value)
        except ValueError:
            log.warning(
                f"Unsupported fitting mode '{value}' in CIF. "
                f'Supported: {supported}. Keeping default.',
            )

    @property
    def minimizer(self) -> MinimizerCategoryBase:
        """Active minimizer settings and result category."""
        return self._minimizer

    @property
    def minimizer_type(self) -> str:
        """Currently selected minimizer type."""
        return self.minimizer.type

    @minimizer_type.setter
    def minimizer_type(self, value: str) -> None:
        self._replace_minimizer(value, announce=True)

    def _replace_minimizer(self, value: str, *, announce: bool) -> None:
        """Replace the active minimizer category."""
        supported = [str(tag) for tag in MinimizerCategoryFactory.supported_tags()]
        if value not in supported:
            log.warning(
                f"Unsupported minimizer type '{value}'. "
                f'Supported minimizer types: {supported}. '
                f"For more information, use 'show_supported_minimizer_types()'",
            )
            return

        if value == self.minimizer_type:
            if announce:
                console.paragraph('Current minimizer already set to')
                console.print(value)
            return

        old_minimizer = self._minimizer
        new_minimizer = MinimizerCategoryFactory.create(value)
        old_defaults = MinimizerCategoryFactory.create(self.minimizer_type)
        self._warn_about_minimizer_swap_defaults(old_defaults, new_minimizer)

        old_minimizer._parent = None
        self._minimizer = new_minimizer
        self._minimizer._parent = self
        self._fitter = Fitter(value)
        if announce:
            console.paragraph('Current minimizer changed to')
            console.print(value)

    def _set_minimizer_type(self, value: str) -> None:
        """Set the minimizer type without console output."""
        self._replace_minimizer(value, announce=False)

    @staticmethod
    def _minimizer_swap_diff(
        old_minimizer: MinimizerCategoryBase,
        new_minimizer: MinimizerCategoryBase,
    ) -> tuple[list[str], list[str], list[str]]:
        """
        Return (removed, added, changed) setting-name lists for a swap.

        ``removed`` lists settings present on ``old_minimizer`` but not
        on ``new_minimizer`` (a value the user previously customised is
        no longer applicable). ``added`` lists settings introduced by
        the new minimizer with their default value. ``changed`` lists
        settings shared by both whose default value differs, in the
        ``'{name}={old!r}->{new!r}'`` form.
        """
        old_values = old_minimizer._descriptor_values(old_minimizer._setting_descriptor_names)
        new_values = new_minimizer._descriptor_values(new_minimizer._setting_descriptor_names)
        old_keys = set(old_values)
        new_keys = set(new_values)
        removed = sorted(old_keys - new_keys)
        added = sorted(f'{name}={new_values[name]!r}' for name in (new_keys - old_keys))
        changed = sorted(
            f'{name}={old_values[name]!r}->{new_values[name]!r}'
            for name in (old_keys & new_keys)
            if old_values[name] != new_values[name]
        )
        return removed, added, changed

    @classmethod
    def _warn_about_minimizer_swap_defaults(
        cls,
        old_minimizer: MinimizerCategoryBase,
        new_minimizer: MinimizerCategoryBase,
    ) -> None:
        """
        Emit human-readable warnings about a minimizer swap.

        Splits the diff into "removed", "added", "changed" lines so the
        message stays legible for scientists when an inter-family swap
        replaces the whole setting surface (e.g. ``lmfit`` → ``bumps
        (dream)``). Same-family swaps still see the per-field
        ``old->new`` line for actual default differences.
        """
        removed, added, changed = cls._minimizer_swap_diff(old_minimizer, new_minimizer)
        if removed:
            log.warning(f'Switching minimizer type removes these settings: {", ".join(removed)}.')
        if added:
            log.warning(
                f'Switching minimizer type adds these settings with defaults: {", ".join(added)}.'
            )
        if changed:
            log.warning(
                f'Switching minimizer type changes these default values: {", ".join(changed)}.'
            )

    def show_supported_minimizer_types(self) -> None:
        """Print supported minimizer types and mark the current type."""
        current = self.minimizer_type
        columns_data = [
            [
                '*' if str(klass.type_info.tag) == current else '',
                str(klass.type_info.tag),
                klass.type_info.description,
            ]
            for klass in MinimizerCategoryFactory.supported_for()
        ]
        console.paragraph('Minimizer types')
        render_table(
            columns_headers=['', 'Type', 'Description'],
            columns_alignment=['left', 'left', 'left'],
            columns_data=columns_data,
        )

    def show_current_minimizer_type(self) -> None:
        """Print the currently selected minimizer type."""
        console.paragraph('Current minimizer type')
        console.print(self.minimizer_type)

    def _sync_engine_from_minimizer_category(self) -> None:
        """Apply minimizer category settings to the live engine."""
        engine = self.fitter.minimizer
        for key, value in self.minimizer._native_kwargs().items():
            if key == 'random_seed':
                continue
            if not hasattr(engine, key):
                log.warning(
                    f"Minimizer setting '{key}' is not supported by "
                    f"engine '{self.minimizer_type}'."
                )
                continue
            setattr(engine, key, value)

    def _resolved_fit_random_seed(self, random_seed: int | None) -> int | None:
        """Return call-time or minimizer-category random seed."""
        if random_seed is not None:
            return random_seed
        seed = self.minimizer._native_kwargs().get('random_seed')
        return None if seed is None else int(seed)

    # ------------------------------------------------------------------
    #  Joint-fit weights (category)
    # ------------------------------------------------------------------

    @property
    def joint_fit(self) -> object:
        """Per-experiment weight collection for joint fitting."""
        return self._joint_fit

    @property
    def sequential_fit(self) -> SequentialFit:
        """Persisted settings for sequential fitting."""
        return self._sequential_fit

    @property
    def sequential_fit_extract(self) -> SequentialFitExtractCollection:
        """Persisted extract rules for sequential fitting."""
        return self._sequential_fit_extract

    def _has_persisted_fit_state(self) -> bool:
        """
        Return whether a persisted fit-state projection is present.
        """
        return self._has_persisted_fit_state_data

    def _set_has_persisted_fit_state(self, *, value: bool) -> None:
        """Set the persisted fit-state presence flag."""
        self._has_persisted_fit_state_data = value

    def _fit_state_categories(self) -> list[object]:
        """Return fit-state categories for the current result kind."""
        categories: list[object] = [
            self.fit_parameters,
            self.fit_result,
            self.fit_parameter_correlations,
        ]

        try:
            result_kind = FitResultKindEnum(self.fit_result.result_kind.value)
        except ValueError:
            log.warning(
                'Unsupported fit_result.result_kind while serializing analysis CIF: '
                f'{self.fit_result.result_kind.value!r}. '
                'Saving only common fit-state categories.',
            )
            return categories

        if result_kind is FitResultKindEnum.DETERMINISTIC:
            return categories

        return categories

    def _clear_persisted_fit_state(self) -> None:
        """Reset all persisted fit-state categories before a new fit."""
        self._clear_minimizer_result_projection()
        self._fit_parameters = FitParameters()
        self._fit_result = FitResult()
        self._fit_parameter_correlations = FitParameterCorrelations()
        self._set_has_persisted_fit_state(value=False)
        self._persisted_fit_state_sidecar = {}

    def _clear_minimizer_result_projection(self) -> None:
        """Reset result-only fields on the active minimizer category."""
        self.minimizer._reset_result_descriptors()

    def _capture_fit_parameter_state(self, parameters: list[Parameter]) -> None:
        """Capture pre-fit parameter state."""
        self._clear_persisted_fit_state()

        for param in parameters:
            self.fit_parameters.create(
                param_unique_name=param.unique_name,
                fit_min=param.fit_min,
                fit_max=param.fit_max,
                fit_bounds_uncertainty_multiplier=param.fit_bounds_uncertainty_multiplier,
                start_value=param.value,
                start_uncertainty=param.uncertainty,
            )

        self._set_has_persisted_fit_state(value=True)

    def _selected_parameters_for_fit(self, experiments: list[object]) -> list[Parameter]:
        """
        Return unique live parameters involved in the current fit slice.
        """
        selected_parameters: list[Parameter] = []
        seen_unique_names: set[str] = set()

        for param in self.project.structures.parameters:
            if not isinstance(param, Parameter):
                continue
            if param.unique_name in seen_unique_names:
                continue
            selected_parameters.append(param)
            seen_unique_names.add(param.unique_name)

        for experiment in experiments:
            for param in experiment.parameters:
                if not isinstance(param, Parameter):
                    continue
                if param.unique_name in seen_unique_names:
                    continue
                selected_parameters.append(param)
                seen_unique_names.add(param.unique_name)

        return selected_parameters

    @staticmethod
    def _fit_data_point_count(experiments: list[object]) -> int:
        """Return observed data-point count for one fit slice."""
        total = 0
        for experiment in experiments:
            intensity_category = intensity_category_for(experiment)
            total += int(np.asarray(intensity_category.intensity_meas).size)
        return total

    @staticmethod
    def _resolve_covariance_matrix(results: FitResults) -> np.ndarray | None:
        """
        Return a covariance matrix when the raw fit result exposes one.
        """
        raw_result = results.engine_result
        for attribute_name in ('covar', 'covariance_matrix'):
            covariance = getattr(raw_result, attribute_name, None)
            if covariance is None:
                continue

            covariance_array = np.asarray(covariance, dtype=float)
            if covariance_array.ndim != _FLATTENED_POSTERIOR_SAMPLE_NDIM:
                continue
            if covariance_array.shape[0] != covariance_array.shape[1]:
                continue
            return covariance_array

        return None

    @staticmethod
    def _correlation_matrix_from_covariance(covariance: np.ndarray) -> np.ndarray | None:
        """
        Return a correlation matrix derived from a covariance matrix.
        """
        diagonal = np.diag(covariance)
        if np.any(diagonal <= 0):
            return None

        scales = np.sqrt(diagonal)
        denominator = np.outer(scales, scales)
        with np.errstate(invalid='ignore', divide='ignore'):
            correlation = covariance / denominator

        if not np.all(np.isfinite(correlation)):
            return None
        return correlation

    @staticmethod
    def _resolve_objective_value(results: FitResults) -> float | None:
        """Return the objective value stored for a fit result."""
        if results.chi_square is None:
            return None
        return float(results.chi_square)

    def _store_common_fit_result_projection(
        self,
        results: FitResults,
        *,
        result_kind: FitResultKindEnum,
    ) -> None:
        """
        Store fields shared by deterministic and Bayesian fit results.
        """
        self.fit_result._set_result_kind(result_kind.value)
        self.fit_result._set_success(value=results.success)
        self.fit_result._set_message(results.message)
        self.fit_result._set_iterations(results.iterations)
        self.fit_result._set_fitting_time(results.fitting_time)
        self.fit_result._set_reduced_chi_square(results.reduced_chi_square)
        self._set_has_persisted_fit_state(value=True)

    def _store_correlation_projection(
        self,
        *,
        unique_names: list[str],
        correlation_matrix: np.ndarray,
        source_kind: FitCorrelationSourceEnum,
    ) -> None:
        """Store upper-triangle correlations from one matrix."""
        if len(unique_names) <= 1:
            return
        if correlation_matrix.shape != (len(unique_names), len(unique_names)):
            return

        for row_index, unique_name_i in enumerate(unique_names[:-1]):
            for column_index in range(row_index + 1, len(unique_names)):
                correlation = correlation_matrix[row_index, column_index]
                if not np.isfinite(correlation):
                    continue
                self.fit_parameter_correlations.create(
                    source_kind=source_kind.value,
                    param_unique_name_i=unique_name_i,
                    param_unique_name_j=unique_names[column_index],
                    correlation=float(np.clip(correlation, -1.0, 1.0)),
                )

    def _store_least_squares_result_projection(
        self,
        results: FitResults,
        *,
        experiments: list[object],
        fitted_parameters: list[Parameter],
    ) -> None:
        """Store least-squares result fields."""
        selected_parameters = self._selected_parameters_for_fit(experiments)
        n_parameters = len(selected_parameters)
        n_free_parameters = len(fitted_parameters)
        n_data_points = self._fit_data_point_count(experiments)
        degrees_of_freedom = max(n_data_points - n_free_parameters, 0)
        covariance = self._resolve_covariance_matrix(results)
        correlation_matrix = (
            self._correlation_matrix_from_covariance(covariance)
            if covariance is not None
            else None
        )

        self.minimizer._set_optimizer_name(
            str(self.fitter.minimizer.name or self.fitter.selection)
        )
        self.minimizer._set_method_name(str(self.fitter.minimizer.method or ''))
        self.minimizer._set_objective_name('chi_square')
        self.minimizer._set_objective_value(self._resolve_objective_value(results))
        self.minimizer._set_n_data_points(n_data_points)
        self.minimizer._set_n_parameters(n_parameters)
        self.minimizer._set_n_free_parameters(n_free_parameters)
        self.minimizer._set_degrees_of_freedom(degrees_of_freedom)
        self.minimizer._set_covariance_available(value=covariance is not None)
        self.minimizer._set_correlation_available(value=correlation_matrix is not None)
        self.minimizer._set_runtime_seconds(results.fitting_time)
        self.minimizer._set_iterations_performed(results.iterations)
        self.minimizer._set_exit_reason(results.message)

        if correlation_matrix is not None:
            self._store_correlation_projection(
                unique_names=[param.unique_name for param in fitted_parameters],
                correlation_matrix=correlation_matrix,
                source_kind=FitCorrelationSourceEnum.DETERMINISTIC,
            )

    @staticmethod
    def _store_posterior_distribution_cache_projection(
        *,
        plotter: object,
        results: BayesianFitResults,
        flattened_samples: np.ndarray,
        parameter_names: list[str],
    ) -> dict[str, dict[str, np.ndarray]]:
        """
        Store cached posterior density curves into persisted manifests.
        """
        payload: dict[str, dict[str, np.ndarray]] = {}
        for parameter_index, parameter_name in enumerate(parameter_names):
            lower_bound, upper_bound = plotter._posterior_parameter_bounds(
                fit_results=results,
                parameter_name=parameter_name,
            )
            density_curve = plotter._posterior_density_curve(
                flattened_samples[:, parameter_index],
                lower_bound=lower_bound,
                upper_bound=upper_bound,
            )
            if density_curve is None:
                continue

            x_values, density_values = density_curve
            x_array = np.asarray(x_values, dtype=float)
            density_array = np.asarray(density_values, dtype=float)
            payload[parameter_name] = {
                'x': x_array,
                'density': density_array,
            }
        return payload

    @staticmethod
    def _posterior_pair_contour_levels(density: np.ndarray) -> np.ndarray:
        """Return default contour levels for one cached pair."""
        density_max = float(np.max(density))
        if not np.isfinite(density_max) or density_max <= 0:
            return np.asarray([], dtype=float)
        return density_max * np.asarray([0.20, 0.35, 0.50, 0.65, 0.80, 0.95], dtype=float)

    @staticmethod
    def _ordered_pair_metadata(
        parameter_names: list[str],
        first_index: int,
        second_index: int,
    ) -> tuple[int, int, str, str]:
        """Return ordered pair indices and parameter names."""
        x_index = first_index
        y_index = second_index
        x_name = parameter_names[x_index]
        y_name = parameter_names[y_index]
        if x_name > y_name:
            x_index, y_index = y_index, x_index
            x_name, y_name = y_name, x_name
        return x_index, y_index, x_name, y_name

    def _store_one_posterior_pair_cache_projection(
        self,
        *,
        plotter: object,
        results: BayesianFitResults,
        density_samples: np.ndarray,
        pair_metadata: tuple[int, int, str, str],
        contour_grid_size: int,
        pair_id: str,
    ) -> tuple[str, dict[str, object]] | None:
        """Store one cached pair surface and return its payload."""
        x_index, y_index, x_name, y_name = pair_metadata

        x_values = density_samples[:, x_index]
        y_values = density_samples[:, y_index]
        x_bounds, y_bounds = plotter._posterior_pair_bounds(
            fit_results=results,
            x_parameter_name=x_name,
            y_parameter_name=y_name,
            x_values=x_values,
            y_values=y_values,
        )
        density_surface = plotter._posterior_pair_density_surface(
            x_values=x_values,
            y_values=y_values,
            x_bounds=x_bounds,
            y_bounds=y_bounds,
            grid_size=contour_grid_size,
        )
        if density_surface is None:
            return None

        x_grid_array = np.asarray(density_surface[0], dtype=float)
        y_grid_array = np.asarray(density_surface[1], dtype=float)
        density_array = np.asarray(density_surface[2], dtype=float)
        contour_levels = self._posterior_pair_contour_levels(density_array)
        return pair_id, {
            'param_unique_name_x': x_name,
            'param_unique_name_y': y_name,
            'x': x_grid_array,
            'y': y_grid_array,
            'density': density_array,
            'contour_levels': contour_levels,
        }

    def _store_posterior_pair_cache_projection(
        self,
        *,
        plotter: object,
        results: BayesianFitResults,
        flattened_samples: np.ndarray,
        parameter_names: list[str],
    ) -> dict[str, dict[str, object]]:
        """Store cached pair-density surfaces in manifests."""
        n_parameters = len(parameter_names)
        if n_parameters <= 1:
            return {}

        density_samples = plotter._thin_posterior_samples(
            flattened_samples,
            max_points=plotter._posterior_pair_density_max_points(n_parameters),
        )
        contour_grid_size = plotter._posterior_pair_contour_grid_size(n_parameters)
        payload: dict[str, dict[str, object]] = {}
        for first_index, second_index in combinations(range(n_parameters), 2):
            pair_id = str(len(payload) + 1)
            cache_projection = self._store_one_posterior_pair_cache_projection(
                plotter=plotter,
                results=results,
                density_samples=density_samples,
                pair_metadata=self._ordered_pair_metadata(
                    parameter_names,
                    first_index,
                    second_index,
                ),
                contour_grid_size=contour_grid_size,
                pair_id=pair_id,
            )
            if cache_projection is None:
                continue

            pair_id, pair_payload = cache_projection
            payload[pair_id] = pair_payload
        return payload

    @staticmethod
    def _predictive_dataset_payload(
        summary: PosteriorPredictiveSummary,
    ) -> dict[str, object]:
        """Return persisted predictive arrays for one summary."""
        payload: dict[str, object] = {
            'x_axis_name': summary.x_axis_name,
            'x': np.asarray(summary.x, dtype=float),
            'best_sample_prediction': np.asarray(summary.best_sample_prediction, dtype=float),
        }
        if summary.lower_95 is not None:
            payload['lower_95'] = np.asarray(summary.lower_95, dtype=float)
        if summary.upper_95 is not None:
            payload['upper_95'] = np.asarray(summary.upper_95, dtype=float)
        if summary.lower_68 is not None:
            payload['lower_68'] = np.asarray(summary.lower_68, dtype=float)
        if summary.upper_68 is not None:
            payload['upper_68'] = np.asarray(summary.upper_68, dtype=float)
        if summary.draws is not None:
            payload['draws'] = np.asarray(summary.draws, dtype=float)
        return payload

    def _store_posterior_predictive_projection(
        self,
        *,
        plotter: object,
        results: BayesianFitResults,
    ) -> dict[str, dict[str, object]]:
        """
        Store posterior predictive summaries into persisted manifests.
        """
        predictive_payload: dict[str, dict[str, object]] = {}
        for experiment_name in self.project.experiments.names:
            experiment = self.project.experiments[experiment_name]
            x_axis, x_axis_name, _, _, _ = plotter._resolve_x_axis(experiment.type, None)
            summary = plotter._build_posterior_predictive_summary(
                fit_results=results,
                experiment=experiment,
                expt_name=experiment_name,
                x_axis=x_axis,
                include_draws=False,
            )
            if summary is None:
                continue

            results.posterior_predictive[summary.experiment_name] = summary
            results.posterior_predictive[
                self._predictive_cache_key(
                    summary.experiment_name,
                    str(x_axis_name),
                    include_draws=False,
                )
            ] = summary
            predictive_payload[summary.experiment_name] = self._predictive_dataset_payload(
                summary,
            )
        return predictive_payload

    def _store_posterior_plot_cache_projection(self, results: BayesianFitResults) -> None:
        """Populate persisted Bayesian plot caches."""
        posterior_samples = results.posterior_samples
        if posterior_samples is None:
            results.posterior_distribution_caches = {}
            results.posterior_pair_caches = {}
            self._persisted_fit_state_sidecar['distribution_caches'] = {}
            self._persisted_fit_state_sidecar['pair_caches'] = {}
            self._persisted_fit_state_sidecar['predictive_datasets'] = {}
            return

        flattened_samples = np.asarray(posterior_samples.flattened(), dtype=float)
        parameter_names = list(posterior_samples.parameter_names)
        if (
            flattened_samples.ndim != _FLATTENED_POSTERIOR_SAMPLE_NDIM
            or not parameter_names
            or flattened_samples.shape[1] != len(parameter_names)
        ):
            results.posterior_distribution_caches = {}
            results.posterior_pair_caches = {}
            self._persisted_fit_state_sidecar['distribution_caches'] = {}
            self._persisted_fit_state_sidecar['pair_caches'] = {}
            self._persisted_fit_state_sidecar['predictive_datasets'] = {}
            return

        plotter = self.project.chart.plotter
        distribution_payload = self._store_posterior_distribution_cache_projection(
            plotter=plotter,
            results=results,
            flattened_samples=flattened_samples,
            parameter_names=parameter_names,
        )
        pair_payload = self._store_posterior_pair_cache_projection(
            plotter=plotter,
            results=results,
            flattened_samples=flattened_samples,
            parameter_names=parameter_names,
        )
        predictive_payload = self._store_posterior_predictive_projection(
            plotter=plotter,
            results=results,
        )

        self._persisted_fit_state_sidecar['distribution_caches'] = distribution_payload
        self._persisted_fit_state_sidecar['pair_caches'] = pair_payload
        self._persisted_fit_state_sidecar['predictive_datasets'] = predictive_payload
        results.posterior_distribution_caches = distribution_payload
        results.posterior_pair_caches = pair_payload

    def _store_posterior_samples_sidecar_projection(
        self,
        results: BayesianFitResults,
    ) -> None:
        """Persist posterior arrays while live samples exist."""
        posterior_samples = results.posterior_samples
        if posterior_samples is None:
            self._persisted_fit_state_sidecar['posterior'] = {}
            return

        self._persisted_fit_state_sidecar['posterior'] = {
            'parameter_samples': np.asarray(
                posterior_samples.parameter_samples,
                dtype=float,
            ),
            'log_posterior': (
                None
                if posterior_samples.log_posterior is None
                else np.asarray(posterior_samples.log_posterior, dtype=float)
            ),
            'draw_index': (
                None
                if posterior_samples.draw_index is None
                else np.asarray(posterior_samples.draw_index)
            ),
        }

    def _store_posterior_fit_projection(self, results: BayesianFitResults) -> None:
        """Store Bayesian result fields."""
        credible_interval_inner = 0.68
        credible_interval_outer = 0.95
        if len(results.credible_interval_levels) >= _CREDIBLE_INTERVAL_LEVEL_COUNT:
            credible_interval_inner = float(results.credible_interval_levels[0])
            credible_interval_outer = float(results.credible_interval_levels[1])

        point_estimate_name = results.point_estimate_name or 'best_sample'
        convergence = results.convergence_diagnostics

        self.minimizer._set_runtime_seconds(results.fitting_time)
        self.minimizer._set_point_estimate_name(point_estimate_name)
        self.minimizer._set_sampler_completed(value=results.sampler_completed)
        self.minimizer._set_best_log_posterior(results.best_log_posterior)
        self.minimizer._set_credible_interval_inner(credible_interval_inner)
        self.minimizer._set_credible_interval_outer(credible_interval_outer)
        self.minimizer._set_gelman_rubin_max(convergence.get('max_r_hat'))
        self.minimizer._set_effective_sample_size_min(convergence.get('min_ess_bulk'))
        self.minimizer._set_acceptance_rate_mean(convergence.get('acceptance_rate_mean'))
        self._store_posterior_samples_sidecar_projection(results)

        live_parameters = {
            parameter.unique_name: parameter
            for parameter in results.parameters
            if isinstance(parameter, Parameter)
        }
        for summary in results.posterior_parameter_summaries:
            self.fit_parameters.set_posterior_summary(summary)
            parameter = live_parameters.get(summary.unique_name)
            if parameter is not None:
                parameter._set_posterior(summary)

        posterior_samples = results.posterior_samples
        if posterior_samples is None:
            return

        self._store_posterior_plot_cache_projection(results)
        if len(posterior_samples.parameter_names) <= 1:
            return

        flattened = posterior_samples.flattened()
        correlation_matrix = np.corrcoef(flattened, rowvar=False)
        self._store_correlation_projection(
            unique_names=list(posterior_samples.parameter_names),
            correlation_matrix=correlation_matrix,
            source_kind=FitCorrelationSourceEnum.POSTERIOR,
        )

    def _store_fit_result_projection(
        self,
        results: FitResults,
        *,
        experiments: list[object],
        fitted_parameters: list[Parameter],
    ) -> None:
        """
        Store the latest fit result into persisted fit-state categories.
        """
        if isinstance(results, BayesianFitResults):
            self._store_common_fit_result_projection(
                results,
                result_kind=FitResultKindEnum.BAYESIAN,
            )
            self._store_posterior_fit_projection(results)
            return

        self._store_common_fit_result_projection(
            results,
            result_kind=FitResultKindEnum.DETERMINISTIC,
        )
        self._store_least_squares_result_projection(
            results,
            experiments=experiments,
            fitted_parameters=fitted_parameters,
        )

    def _resolve_sequential_data_dir(self) -> Path:
        """
        Resolve the sequential-fit data directory to an absolute path.
        """
        data_dir = Path(self._sequential_fit.data_dir.value)
        if data_dir.is_absolute():
            return data_dir

        project_path = self.project.info.path
        if project_path is None:
            msg = (
                'Project must be saved before resolving a relative '
                'sequential_fit.data_dir. Call save_as() first.'
            )
            raise ValueError(msg)

        return project_path / data_dir

    def _prepare_fit_run(self) -> tuple[VerbosityEnum, object, object] | None:
        """Resolve common inputs for single and joint fitting."""
        verb = VerbosityEnum(self.project.verbosity.fit.value)
        structures = self.project.structures
        if not structures:
            log.warning('No structures found in the project. Cannot run fit.')
            return None

        experiments = self.project.experiments
        if not experiments:
            log.warning('No experiments found in the project. Cannot run fit.')
            return None

        self._warn_results_sidecar_overwrite()

        # Apply constraints before fitting so that user-constrained
        # parameters are marked and excluded from the free parameter
        # list built by the fitter.
        self._sync_engine_from_minimizer_category()
        self._update_categories()

        return verb, structures, experiments

    def _run_single(self) -> None:
        """
        Execute single-mode fitting with current project verbosity.
        """
        prepared = self._prepare_fit_run()
        if prepared is None:
            return

        verb, structures, experiments = prepared
        self._fit_single(
            verb,
            structures,
            experiments,
            use_physical_limits=False,
            random_seed=None,
        )

        if self.project.info.path is not None:
            self.project.save()

    def _run_joint(self) -> None:
        """Execute joint-mode fitting with current project verbosity."""
        prepared = self._prepare_fit_run()
        if prepared is None:
            return

        verb, structures, experiments = prepared
        self._fit_joint(
            verb,
            structures,
            experiments,
            use_physical_limits=False,
            random_seed=None,
        )

        if self.project.info.path is not None:
            self.project.save()

    def _run_sequential(self) -> None:
        """
        Execute sequential fitting from persisted sequential settings.
        """
        from easydiffraction.analysis.sequential import fit_sequential as _fit_seq  # noqa: PLC0415

        self._set_fitting_mode_type(FitModeEnum.SEQUENTIAL.value)
        self._update_categories()
        self._warn_results_sidecar_overwrite()
        self._clear_persisted_fit_state()

        max_workers_value = self._sequential_fit.max_workers.value
        max_workers = max_workers_value if max_workers_value == 'auto' else int(max_workers_value)

        chunk_size_value = self._sequential_fit.chunk_size.value
        chunk_size = None if chunk_size_value == '.' else int(chunk_size_value)

        self.fit_results = None
        self.fitter.results = None

        try:
            _fit_seq(
                analysis=self,
                data_dir=str(self._resolve_sequential_data_dir()),
                max_workers=max_workers,
                chunk_size=chunk_size,
                file_pattern=self._sequential_fit.file_pattern.value,
                reverse=self._sequential_fit.reverse.value,
            )
        finally:
            self.fit_results = None
            self.fitter.results = None
            self._clear_persisted_fit_state()

        if self.project.info.path is not None:
            self.project.save()

    def _fit_joint(
        self,
        verb: VerbosityEnum,
        structures: object,
        experiments: object,
        *,
        use_physical_limits: bool,
        random_seed: int | None,
    ) -> None:
        """
        Run joint fitting across all experiments with weights.

        Parameters
        ----------
        verb : VerbosityEnum
            Output verbosity.
        structures : object
            Project structures collection.
        experiments : object
            Project experiments collection.
        use_physical_limits : bool
            Whether to use physical limits as fit bounds.
        random_seed : int | None
            Optional random seed passed to stochastic minimizers.
        """
        mode = FitModeEnum.JOINT
        # Auto-populate joint_fit if empty
        if not len(self._joint_fit):
            for experiment_id in experiments.names:
                self._joint_fit.create(experiment_id=experiment_id, weight=0.5)
        if verb is not VerbosityEnum.SILENT:
            console.paragraph(
                f"Using all experiments 🔬 {experiments.names} for '{mode.value}' fitting"
            )
        # Resolve weights to a plain numpy array
        experiments_list = list(experiments.values())
        weights_list = [self._joint_fit[name].weight.value for name in experiments.names]
        weights_array = np.array(weights_list, dtype=np.float64)
        self.fitter.fit(
            structures,
            experiments_list,
            weights=weights_array,
            analysis=self,
            verbosity=verb,
            use_physical_limits=use_physical_limits,
            random_seed=self._resolved_fit_random_seed(random_seed),
        )

        # After fitting, get the results
        self.fit_results = self.fitter.results

    def _fit_single(
        self,
        verb: VerbosityEnum,
        structures: object,
        experiments: object,
        *,
        use_physical_limits: bool,
        random_seed: int | None,
    ) -> None:
        """
        Run single-mode fitting for each experiment independently.

        Parameters
        ----------
        verb : VerbosityEnum
            Output verbosity.
        structures : object
            Project structures collection.
        experiments : object
            Project experiments collection.
        use_physical_limits : bool
            Whether to use physical limits as fit bounds.
        random_seed : int | None
            Optional random seed passed to stochastic minimizers.
        """
        mode = FitModeEnum.SINGLE
        expt_names = experiments.names

        short_display_handle = self._fit_single_print_header(verb, expt_names, mode)
        short_rows: list[list[str]] = []
        self.fitter.minimizer.tracker._set_shared_display_handle(short_display_handle)

        try:
            for expt_name in expt_names:
                if verb is VerbosityEnum.FULL:
                    console.print(
                        f"📋 Using experiment 🔬 '{expt_name}' for '{mode.value}' fitting"
                    )

                experiment = experiments[expt_name]
                self.fitter.fit(
                    structures,
                    [experiment],
                    analysis=self,
                    verbosity=verb,
                    use_physical_limits=use_physical_limits,
                    random_seed=self._resolved_fit_random_seed(random_seed),
                )

                # After fitting, snapshot parameter values before
                # they get overwritten by the next experiment's fit
                results = self.fitter.results
                self._snapshot_params(expt_name, results)
                self.fit_results = results

                # Short mode: append one summary row and update in-place
                if verb is VerbosityEnum.SHORT:
                    self._fit_single_update_short_table(
                        short_rows, expt_name, results, short_display_handle
                    )
        finally:
            self.fitter.minimizer.tracker._set_shared_display_handle(None)

            # Short mode: close the display handle
            if short_display_handle is not None and hasattr(short_display_handle, 'close'):
                with suppress(Exception):
                    short_display_handle.close()

    @staticmethod
    def _fit_single_print_header(
        verb: VerbosityEnum,
        expt_names: list[str],
        mode: FitModeEnum,
    ) -> object | None:
        """
        Print the header for single-mode fitting.

        Parameters
        ----------
        verb : VerbosityEnum
            Output verbosity.
        expt_names : list[str]
            Experiment names.
        mode : FitModeEnum
            The fit mode enum.

        Returns
        -------
        object | None
            Display handle for short mode, or ``None``.
        """
        if verb is not VerbosityEnum.SILENT:
            console.paragraph('Standard fitting')
        if verb is not VerbosityEnum.SHORT:
            return None
        num_expts = len(expt_names)
        console.print(
            f"📋 Using {num_expts} experiments 🔬 from '{expt_names[0]}' to "
            f"'{expt_names[-1]}' for '{mode.value}' fitting"
        )
        console.print("🚀 Starting fit process with 'lmfit'...")
        console.print('📈 Goodness-of-fit (reduced χ²) per experiment:')
        return make_display_handle()

    def _snapshot_params(self, expt_name: str, results: object) -> None:
        """
        Snapshot parameter values for a single experiment.

        Parameters
        ----------
        expt_name : str
            Experiment name key for the snapshot dict.
        results : object
            Fit results with ``.parameters`` list.
        """
        snapshot: dict[str, dict] = {}
        for param in results.parameters:
            snapshot[param.unique_name] = {
                'value': param.value,
                'uncertainty': param.uncertainty,
                'units': param.units,
            }
        self._parameter_snapshots[expt_name] = snapshot

    def _fit_single_update_short_table(
        self,
        short_rows: list[list[str]],
        expt_name: str,
        results: object,
        display_handle: object | None,
    ) -> None:
        """
        Append a summary row for short-mode display.

        Parameters
        ----------
        short_rows : list[list[str]]
            Accumulated rows (mutated in place).
        expt_name : str
            Experiment name.
        results : object
            Fit results.
        display_handle : object | None
            Display handle for in-place table update.
        """
        chi2_str = (
            f'{results.reduced_chi_square:.2f}' if results.reduced_chi_square is not None else '—'
        )
        iters = str(self.fitter.minimizer.tracker.best_iteration or 0)
        status = '✅' if results.success else '❌'
        short_rows.append([expt_name, chi2_str, iters, status])
        render_table(
            columns_headers=['experiment', 'χ²', 'iterations', 'status'],
            columns_alignment=['left', 'right', 'right', 'center'],
            columns_data=short_rows,
            display_handle=display_handle,
        )

    def _update_categories(
        self,
        *,
        called_by_minimizer: bool = False,
    ) -> None:
        """
        Update all categories owned by Analysis.

        This ensures aliases and constraints are up-to-date before
        serialization or after parameter changes.

        Parameters
        ----------
        called_by_minimizer : bool, default=False
            Whether this is called during fitting.
        """
        super()._update_categories(called_by_minimizer=called_by_minimizer)

        # Apply constraints to sync dependent parameters
        if self.constraints.enabled and self.constraints._items:
            self._constraints_handler.set_aliases(self.aliases)
            self._constraints_handler.set_constraints(self.constraints)
            self._constraints_handler.apply()

    @property
    def as_cif(self) -> str:
        """
        Serialize the analysis section to a CIF string.

        Returns
        -------
        str
            The analysis section represented as a CIF document string.
        """
        self._update_categories()
        return analysis_to_cif(self)

    def show_as_cif(self) -> None:
        """Pretty-print the analysis section as CIF text."""
        console.paragraph('Analysis info as CIF')
        render_cif(self.as_cif)
