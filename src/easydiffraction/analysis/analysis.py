# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from contextlib import suppress
from pathlib import Path

import numpy as np
import pandas as pd

from easydiffraction.analysis.categories.aliases.factory import AliasesFactory
from easydiffraction.analysis.categories.bayesian_convergence import BayesianConvergence
from easydiffraction.analysis.categories.bayesian_distribution_caches import (
    BayesianDistributionCaches,
)
from easydiffraction.analysis.categories.bayesian_pair_caches import BayesianPairCaches
from easydiffraction.analysis.categories.bayesian_parameter_posteriors import (
    BayesianParameterPosteriors,
)
from easydiffraction.analysis.categories.bayesian_predictive_datasets import (
    BayesianPredictiveDatasets,
)
from easydiffraction.analysis.categories.bayesian_result import BayesianResult
from easydiffraction.analysis.categories.bayesian_sampler import BayesianSampler
from easydiffraction.analysis.categories.constraints.factory import ConstraintsFactory
from easydiffraction.analysis.categories.deterministic_parameter_results import (
    DeterministicParameterResults,
)
from easydiffraction.analysis.categories.deterministic_result import DeterministicResult
from easydiffraction.analysis.categories.fit_parameter_correlations import FitParameterCorrelations
from easydiffraction.analysis.categories.fit_parameters import FitParameters
from easydiffraction.analysis.categories.fit_result import FitResult
from easydiffraction.analysis.categories.fit_state import FitState
from easydiffraction.analysis.categories.fitting import Fitting
from easydiffraction.analysis.categories.fitting import FittingFactory
from easydiffraction.analysis.categories.joint_fit import JointFitCollection
from easydiffraction.analysis.categories.sequential_fit import SequentialFit
from easydiffraction.analysis.categories.sequential_fit import SequentialFitFactory
from easydiffraction.analysis.categories.sequential_fit_extract import (
    SequentialFitExtractCollection,
)
from easydiffraction.analysis.fit_helpers.bayesian import BayesianFitResults
from easydiffraction.analysis.fit_helpers.reporting import FitResults
from easydiffraction.analysis.enums import FitCorrelationSourceEnum
from easydiffraction.analysis.enums import FitModeEnum
from easydiffraction.analysis.enums import FitResultKindEnum
from easydiffraction.analysis.fitting import Fitter
from easydiffraction.analysis.minimizers.base import BOUNDARY_PROXIMITY_FRACTION
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

_SUMMARY_HIDDEN_PARAMETER_CATEGORIES = frozenset({'pd_data', 'total_data', 'refln'})


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


class Analysis(CategoryOwner):
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
        self._fitting: Fitting = FittingFactory.create(FittingFactory.default_tag())
        self._fitting_mode_type: FitModeEnum = FitModeEnum.default()
        self._joint_fit: JointFitCollection = JointFitCollection()
        self._sequential_fit: SequentialFit = SequentialFitFactory.create(
            SequentialFitFactory.default_tag()
        )
        self._sequential_fit_extract = SequentialFitExtractCollection()
        self._fit_state = FitState()
        self._fit_parameters = FitParameters()
        self._fit_result = FitResult()
        self._fit_parameter_correlations = FitParameterCorrelations()
        self._deterministic_result = DeterministicResult()
        self._deterministic_parameter_results = DeterministicParameterResults()
        self._bayesian_result = BayesianResult()
        self._bayesian_sampler = BayesianSampler()
        self._bayesian_convergence = BayesianConvergence()
        self._bayesian_parameter_posteriors = BayesianParameterPosteriors()
        self._bayesian_distribution_caches = BayesianDistributionCaches()
        self._bayesian_pair_caches = BayesianPairCaches()
        self._bayesian_predictive_datasets = BayesianPredictiveDatasets()
        self._has_persisted_fit_state_data = False
        self._persisted_fit_state_sidecar: dict[str, object] = {}
        self._fitter = Fitter(self._fitting.minimizer_type.value)
        self._fit_results = None
        self._parameter_snapshots: dict[str, dict[str, dict]] = {}
        self._display = AnalysisDisplay(self)

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
        return self._fit_results

    @fit_results.setter
    def fit_results(self, value: object | None) -> None:
        self._fit_results = value

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
            self.fitting,
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
    def fitting(self) -> Fitting:
        """Fitting configuration category."""
        return self._fitting

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
                f"For more information, use 'show_fitting_mode_types()'",
            )
            return

        self._fitting_mode_type = new_mode
        console.paragraph('Fitting mode changed to')
        console.print(self._fitting_mode_type.value)

    def show_fitting_mode_types(self) -> None:
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

    @property
    def fit_state(self) -> FitState:
        """Persisted fit-state schema metadata."""
        return self._fit_state

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

    @property
    def deterministic_result(self) -> DeterministicResult:
        """Persisted deterministic fit-result metadata."""
        return self._deterministic_result

    @property
    def deterministic_parameter_results(self) -> DeterministicParameterResults:
        """Persisted deterministic parameter-result summaries."""
        return self._deterministic_parameter_results

    @property
    def bayesian_result(self) -> BayesianResult:
        """Persisted Bayesian fit-result metadata."""
        return self._bayesian_result

    @property
    def bayesian_sampler(self) -> BayesianSampler:
        """Persisted Bayesian sampler settings."""
        return self._bayesian_sampler

    @property
    def bayesian_convergence(self) -> BayesianConvergence:
        """Persisted Bayesian convergence diagnostics."""
        return self._bayesian_convergence

    @property
    def bayesian_parameter_posteriors(self) -> BayesianParameterPosteriors:
        """Persisted Bayesian parameter posterior summaries."""
        return self._bayesian_parameter_posteriors

    @property
    def bayesian_distribution_caches(self) -> BayesianDistributionCaches:
        """Persisted Bayesian distribution-cache manifests."""
        return self._bayesian_distribution_caches

    @property
    def bayesian_pair_caches(self) -> BayesianPairCaches:
        """Persisted Bayesian pair-cache manifests."""
        return self._bayesian_pair_caches

    @property
    def bayesian_predictive_datasets(self) -> BayesianPredictiveDatasets:
        """Persisted Bayesian predictive-dataset manifests."""
        return self._bayesian_predictive_datasets

    def _has_persisted_fit_state(self) -> bool:
        """
        Return whether a persisted fit-state projection is present.
        """
        return self._has_persisted_fit_state_data

    def _set_has_persisted_fit_state(self, value: bool) -> None:
        """
        Set the persisted fit-state presence flag for internal callers.
        """
        self._has_persisted_fit_state_data = value

    def _fit_state_categories(self) -> list[object]:
        """
        Return fit-state categories for the current persisted result
        kind.
        """
        categories: list[object] = [
            self.fit_state,
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
            categories.extend([
                self.deterministic_result,
                self.deterministic_parameter_results,
            ])
            return categories

        categories.extend([
            self.bayesian_result,
            self.bayesian_sampler,
            self.bayesian_convergence,
            self.bayesian_parameter_posteriors,
            self.bayesian_distribution_caches,
            self.bayesian_pair_caches,
            self.bayesian_predictive_datasets,
        ])
        return categories

    def _clear_persisted_fit_state(self) -> None:
        """Reset all persisted fit-state categories before a new fit."""
        self._fit_state = FitState()
        self._fit_parameters = FitParameters()
        self._fit_result = FitResult()
        self._fit_parameter_correlations = FitParameterCorrelations()
        self._deterministic_result = DeterministicResult()
        self._deterministic_parameter_results = DeterministicParameterResults()
        self._bayesian_result = BayesianResult()
        self._bayesian_sampler = BayesianSampler()
        self._bayesian_convergence = BayesianConvergence()
        self._bayesian_parameter_posteriors = BayesianParameterPosteriors()
        self._bayesian_distribution_caches = BayesianDistributionCaches()
        self._bayesian_pair_caches = BayesianPairCaches()
        self._bayesian_predictive_datasets = BayesianPredictiveDatasets()
        self._set_has_persisted_fit_state(False)
        self._persisted_fit_state_sidecar = {}

    def _capture_fit_parameter_state(self, parameters: list[Parameter]) -> None:
        """Capture pre-fit parameter state into persisted fit-state categories."""
        self._clear_persisted_fit_state()
        self.fit_state._set_schema_version(1)

        for param in parameters:
            self.fit_parameters.create(
                param_unique_name=param.unique_name,
                fit_min=param.fit_min,
                fit_max=param.fit_max,
                fit_bounds_uncertainty_multiplier=param.fit_bounds_uncertainty_multiplier,
                start_value=param.value,
                start_uncertainty=param.uncertainty,
            )

        self._set_has_persisted_fit_state(True)

    @staticmethod
    def _parameter_is_at_fit_bound(
        param: Parameter,
        *,
        use_upper_bound: bool,
    ) -> bool:
        """Return whether a parameter finished within tolerance of a fit bound."""
        value = param.value
        if value is None:
            return False

        bound = param.fit_max if use_upper_bound else param.fit_min
        if not np.isfinite(bound):
            return False

        span = param.fit_max - param.fit_min
        if np.isfinite(span) and span > 0:
            tolerance = BOUNDARY_PROXIMITY_FRACTION * span
        else:
            tolerance = BOUNDARY_PROXIMITY_FRACTION * max(abs(bound), 1.0)
        return abs(value - bound) <= tolerance

    def _selected_parameters_for_fit(self, experiments: list[object]) -> list[Parameter]:
        """Return unique live parameters involved in the current fit slice."""
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
        """Return the total number of observed data points in the fit slice."""
        total = 0
        for experiment in experiments:
            intensity_category = intensity_category_for(experiment)
            total += int(np.asarray(intensity_category.intensity_meas).size)
        return total

    @staticmethod
    def _resolve_covariance_matrix(results: FitResults) -> np.ndarray | None:
        """Return a covariance matrix when the raw fit result exposes one."""
        raw_result = results.engine_result
        for attribute_name in ('covar', 'covariance_matrix'):
            covariance = getattr(raw_result, attribute_name, None)
            if covariance is None:
                continue

            covariance_array = np.asarray(covariance, dtype=float)
            if covariance_array.ndim != 2:
                continue
            if covariance_array.shape[0] != covariance_array.shape[1]:
                continue
            return covariance_array

        return None

    @staticmethod
    def _correlation_matrix_from_covariance(covariance: np.ndarray) -> np.ndarray | None:
        """Return a correlation matrix derived from a covariance matrix."""
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
        """Store fields shared by deterministic and Bayesian fit results."""
        self.fit_state._set_schema_version(1)
        self.fit_result._set_result_kind(result_kind.value)
        self.fit_result._set_success(results.success)
        self.fit_result._set_message(results.message)
        self.fit_result._set_iterations(results.iterations)
        self.fit_result._set_fitting_time(results.fitting_time)
        self.fit_result._set_reduced_chi_square(results.reduced_chi_square)
        self._set_has_persisted_fit_state(True)

    def _store_correlation_projection(
        self,
        *,
        unique_names: list[str],
        correlation_matrix: np.ndarray,
        source_kind: FitCorrelationSourceEnum,
    ) -> None:
        """Store upper-triangle parameter correlations from a correlation matrix."""
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

    def _store_deterministic_result_projection(
        self,
        results: FitResults,
        *,
        experiments: list[object],
        fitted_parameters: list[Parameter],
    ) -> None:
        """Store deterministic fit-result projections into persisted categories."""
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

        self.deterministic_result._set_optimizer_name(
            str(self.fitter.minimizer.name or self.fitter.selection)
        )
        self.deterministic_result._set_method_name(str(self.fitter.minimizer.method or ''))
        self.deterministic_result._set_objective_name('chi_square')
        self.deterministic_result._set_objective_value(self._resolve_objective_value(results))
        self.deterministic_result._set_n_data_points(n_data_points)
        self.deterministic_result._set_n_parameters(n_parameters)
        self.deterministic_result._set_n_free_parameters(n_free_parameters)
        self.deterministic_result._set_degrees_of_freedom(degrees_of_freedom)
        self.deterministic_result._set_covariance_available(covariance is not None)
        self.deterministic_result._set_correlation_available(correlation_matrix is not None)

        for order_index, param in enumerate(fitted_parameters):
            self.deterministic_parameter_results.create(
                order_index=order_index,
                param_unique_name=param.unique_name,
                final_value=param.value,
                final_uncertainty=param.uncertainty,
                at_lower_bound=self._parameter_is_at_fit_bound(
                    param,
                    use_upper_bound=False,
                ),
                at_upper_bound=self._parameter_is_at_fit_bound(
                    param,
                    use_upper_bound=True,
                ),
            )

        if correlation_matrix is not None:
            self._store_correlation_projection(
                unique_names=[param.unique_name for param in fitted_parameters],
                correlation_matrix=correlation_matrix,
                source_kind=FitCorrelationSourceEnum.DETERMINISTIC,
            )

    def _store_bayesian_result_projection(self, results: BayesianFitResults) -> None:
        """Store Bayesian fit-result projections into persisted categories."""
        credible_interval_inner = 0.68
        credible_interval_outer = 0.95
        if len(results.credible_interval_levels) >= 2:
            credible_interval_inner = float(results.credible_interval_levels[0])
            credible_interval_outer = float(results.credible_interval_levels[1])

        point_estimate_name = results.point_estimate_name or 'best_sample'
        sampler_settings = results.sampler_settings
        convergence = results.convergence_diagnostics

        self.bayesian_result._set_sampler_name(results.sampler_name)
        self.bayesian_result._set_point_estimate_name(point_estimate_name)
        self.bayesian_result._set_success(results.success)
        self.bayesian_result._set_sampler_completed(results.sampler_completed)
        self.bayesian_result._set_best_log_posterior(results.best_log_posterior)
        self.bayesian_result._set_credible_interval_inner(credible_interval_inner)
        self.bayesian_result._set_credible_interval_outer(credible_interval_outer)
        self.bayesian_result._set_has_posterior_samples(results.posterior_samples is not None)
        self.bayesian_result._set_has_distribution_cache(False)
        self.bayesian_result._set_has_pair_cache(False)
        self.bayesian_result._set_has_posterior_predictive(bool(results.posterior_predictive))
        self.bayesian_result._set_sidecar_file('results.h5')

        self.bayesian_sampler._set_steps(int(sampler_settings.get('steps', 0)))
        self.bayesian_sampler._set_burn(int(sampler_settings.get('burn', 0)))
        self.bayesian_sampler._set_thin(int(sampler_settings.get('thin', 0)))
        self.bayesian_sampler._set_pop(int(sampler_settings.get('pop', 0)))
        self.bayesian_sampler._set_parallel(bool(sampler_settings.get('parallel', False)))
        self.bayesian_sampler._set_init(str(sampler_settings.get('init', '')))
        random_seed = sampler_settings.get('random_seed')
        self.bayesian_sampler._set_random_seed(
            None if random_seed is None else int(random_seed)
        )

        self.bayesian_convergence._set_converged(bool(convergence.get('converged', False)))
        self.bayesian_convergence._set_max_r_hat(convergence.get('max_r_hat'))
        self.bayesian_convergence._set_min_ess_bulk(convergence.get('min_ess_bulk'))
        self.bayesian_convergence._set_n_draws(int(convergence.get('n_draws', 0)))
        self.bayesian_convergence._set_n_chains(int(convergence.get('n_chains', 0)))
        self.bayesian_convergence._set_n_parameters(int(convergence.get('n_parameters', 0)))

        for order_index, summary in enumerate(results.posterior_parameter_summaries):
            self.bayesian_parameter_posteriors.create(
                order_index=order_index,
                unique_name=summary.unique_name,
                display_name=summary.display_name,
                best_sample_value=summary.best_sample_value,
                median=summary.median,
                uncertainty=summary.standard_deviation,
                interval_68_lower=summary.interval_68[0],
                interval_68_upper=summary.interval_68[1],
                interval_95_lower=summary.interval_95[0],
                interval_95_upper=summary.interval_95[1],
                ess_bulk=summary.ess_bulk,
                r_hat=summary.r_hat,
            )

        posterior_samples = results.posterior_samples
        if posterior_samples is None:
            return
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
        """Store the latest fit result into persisted fit-state categories."""
        if isinstance(results, BayesianFitResults):
            self._store_common_fit_result_projection(
                results,
                result_kind=FitResultKindEnum.BAYESIAN,
            )
            self._store_bayesian_result_projection(results)
            return

        self._store_common_fit_result_projection(
            results,
            result_kind=FitResultKindEnum.DETERMINISTIC,
        )
        self._store_deterministic_result_projection(
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

        # Apply constraints before fitting so that user-constrained
        # parameters are marked and excluded from the free parameter
        # list built by the fitter.
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
            random_seed=random_seed,
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
                    random_seed=random_seed,
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
