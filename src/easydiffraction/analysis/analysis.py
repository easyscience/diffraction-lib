# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from contextlib import suppress

import numpy as np
import pandas as pd

from easydiffraction.analysis.categories.aliases.factory import AliasesFactory
from easydiffraction.analysis.categories.constraints.factory import ConstraintsFactory
from easydiffraction.analysis.categories.fit_mode import FitModeEnum
from easydiffraction.analysis.categories.fit_mode import FitModeFactory
from easydiffraction.analysis.categories.joint_fit_experiments import JointFitExperiments
from easydiffraction.analysis.fit_helpers.tracking import _make_display_handle
from easydiffraction.analysis.fitting import Fitter
from easydiffraction.analysis.minimizers.factory import MinimizerFactory
from easydiffraction.core.guard import GuardedBase
from easydiffraction.core.singleton import ConstraintsHandler
from easydiffraction.core.variable import NumericDescriptor
from easydiffraction.core.variable import Parameter
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.display.tables import TableRenderer
from easydiffraction.io.cif.serialize import analysis_to_cif
from easydiffraction.utils.enums import VerbosityEnum
from easydiffraction.utils.logging import console
from easydiffraction.utils.logging import log
from easydiffraction.utils.utils import render_cif
from easydiffraction.utils.utils import render_table


def _discover_property_rows(cls: type) -> list[list[str]]:
    """
    Discover public properties from the class MRO.

    Parameters
    ----------
    cls : type
        The class to inspect.

    Returns
    -------
    list[list[str]]
        Table rows with ``[index, name, writable, description]``.
    """
    seen: dict = {}
    for base in cls.mro():
        for key, attr in base.__dict__.items():
            if key.startswith('_') or not isinstance(attr, property):
                continue
            if key not in seen:
                seen[key] = attr

    rows = []
    for i, key in enumerate(sorted(seen), 1):
        prop = seen[key]
        writable = '✓' if prop.fset else '✗'
        doc = GuardedBase._first_sentence(prop.fget.__doc__ if prop.fget else None)
        rows.append([str(i), key, writable, doc])
    return rows


def _discover_method_rows(cls: type) -> list[list[str]]:
    """
    Discover public methods from the class MRO.

    Parameters
    ----------
    cls : type
        The class to inspect.

    Returns
    -------
    list[list[str]]
        Table rows with ``[index, name(), description]``.
    """
    seen_methods: set = set()
    methods_list: list = []
    for base in cls.mro():
        for key, attr in base.__dict__.items():
            if key.startswith('_') or key in seen_methods:
                continue
            if isinstance(attr, property):
                continue
            raw = attr
            if isinstance(raw, (staticmethod, classmethod)):
                raw = raw.__func__
            if callable(raw):
                seen_methods.add(key)
                methods_list.append((key, raw))

    rows = []
    for i, (key, method) in enumerate(sorted(methods_list), 1):
        doc = GuardedBase._first_sentence(getattr(method, '__doc__', None))
        rows.append([str(i), f'{key}()', doc])
    return rows


class AnalysisDisplay:
    """
    Display helper - parameter tables, CIF, and fit results.

    Accessed via ``analysis.display``.
    """

    def __init__(self, analysis: 'Analysis') -> None:
        self._analysis = analysis

    def all_params(self) -> None:
        """Print all parameters for structures and experiments."""
        project = self._analysis.project
        structures_params = project.structures.parameters
        experiments_params = project.experiments.parameters

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

        console.paragraph('All parameters for all structures (🧩 data blocks)')
        df = Analysis._get_params_as_dataframe(structures_params)
        filtered_df = df[filtered_headers]
        tabler.render(filtered_df)

        console.paragraph('All parameters for all experiments (🔬 data blocks)')
        df = Analysis._get_params_as_dataframe(experiments_params)
        filtered_df = df[filtered_headers]
        tabler.render(filtered_df)

    def fittable_params(self) -> None:
        """Print all fittable parameters."""
        project = self._analysis.project
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

        console.paragraph('Fittable parameters for all structures (🧩 data blocks)')
        df = Analysis._get_params_as_dataframe(structures_params)
        filtered_df = df[filtered_headers]
        tabler.render(filtered_df)

        console.paragraph('Fittable parameters for all experiments (🔬 data blocks)')
        df = Analysis._get_params_as_dataframe(experiments_params)
        filtered_df = df[filtered_headers]
        tabler.render(filtered_df)

    def free_params(self) -> None:
        """Print only currently free (varying) parameters."""
        project = self._analysis.project
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
        structures_params = project.structures.parameters
        experiments_params = project.experiments.parameters
        all_params = {
            'structures': structures_params,
            'experiments': experiments_params,
        }

        if not all_params:
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
        structures_params = project.structures.parameters
        experiments_params = project.experiments.parameters
        all_params = {
            'structures': structures_params,
            'experiments': experiments_params,
        }

        if not all_params:
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
        analysis = self._analysis
        if not analysis.constraints._items:
            log.warning('No constraints defined.')
            return

        rows = [[constraint.expression.value] for constraint in analysis.constraints]

        console.paragraph('User defined constraints')
        render_table(
            columns_headers=['expression'],
            columns_alignment=['left'],
            columns_data=rows,
        )
        console.print(f'Constraints enabled: {analysis.constraints.enabled}')

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
        cif_text: str = self._analysis.as_cif()
        paragraph_title: str = 'Analysis 🧮 info as cif'
        console.paragraph(paragraph_title)
        render_cif(cif_text)


class Analysis:
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
        self.project = project
        self._aliases_type: str = AliasesFactory.default_tag()
        self.aliases = AliasesFactory.create(self._aliases_type)
        self._constraints_type: str = ConstraintsFactory.default_tag()
        self.constraints = ConstraintsFactory.create(self._constraints_type)
        self.constraints_handler = ConstraintsHandler.get()
        self._fit_mode_type: str = FitModeFactory.default_tag()
        self._fit_mode = FitModeFactory.create(self._fit_mode_type)
        self._joint_fit_experiments = JointFitExperiments()
        self.fitter = Fitter()
        self.fit_results = None
        self._parameter_snapshots: dict[str, dict[str, dict]] = {}
        self._display = AnalysisDisplay(self)

    @property
    def display(self) -> AnalysisDisplay:
        """Display helper for parameter tables, CIF, and fit results."""
        return self._display

    def help(self) -> None:
        """Print a summary of analysis properties and methods."""
        console.paragraph("Help for 'Analysis'")

        cls = type(self)

        prop_rows = _discover_property_rows(cls)
        if prop_rows:
            console.paragraph('Properties')
            render_table(
                columns_headers=['#', 'Name', 'Writable', 'Description'],
                columns_alignment=['right', 'left', 'center', 'left'],
                columns_data=prop_rows,
            )

        method_rows = _discover_method_rows(cls)
        if method_rows:
            console.paragraph('Methods')
            render_table(
                columns_headers=['#', 'Name', 'Description'],
                columns_alignment=['right', 'left', 'left'],
                columns_data=method_rows,
            )

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
                    ('fittable', 'left'): True,
                    ('free', 'left'): param.free,
                    ('min', 'right'): param.fit_min,
                    ('max', 'right'): param.fit_max,
                    ('uncertainty', 'right'): param.uncertainty or '',
                }
            records.append(record)

        df = pd.DataFrame.from_records(records)
        df.columns = pd.MultiIndex.from_tuples(df.columns)
        return df

    def show_minimizer_types(self) -> None:
        """Print supported minimizers and mark the current selection."""
        current = self.minimizer_type
        supported = MinimizerFactory.supported_tags()
        all_classes = MinimizerFactory._supported_map()
        columns_data = [
            ['*' if tag == current else '', tag, cls.type_info.description]
            for tag, cls in all_classes.items()
            if tag in supported
        ]
        console.paragraph('Minimizer types')
        render_table(
            columns_headers=['Current', 'Type', 'Description'],
            columns_alignment=['left', 'left', 'left'],
            columns_data=columns_data,
        )

    @staticmethod
    def show_available_minimizers() -> None:
        """Print available minimizer drivers on this system."""
        MinimizerFactory.show_supported()

    @property
    def minimizer_type(self) -> str | None:
        """The identifier of the active minimizer, if any."""
        return self.fitter.selection if self.fitter else None

    @minimizer_type.setter
    def minimizer_type(self, selection: str) -> None:
        """
        Switch to a different minimizer implementation.

        Parameters
        ----------
        selection : str
            Minimizer selection string, e.g. 'lmfit'.
        """
        self.fitter = Fitter(selection)
        console.paragraph('Current minimizer changed to')
        console.print(self.minimizer_type)

    @property
    def current_minimizer(self) -> str | None:
        """Backward-compatible alias for :attr:`minimizer_type`."""
        return self.minimizer_type

    @current_minimizer.setter
    def current_minimizer(self, selection: str) -> None:
        self.minimizer_type = selection

    # ------------------------------------------------------------------
    #  Fit mode (single type, with show methods)
    # ------------------------------------------------------------------

    @property
    def fit_mode(self) -> object:
        """Fit-mode category item holding the active strategy."""
        return self._fit_mode

    def show_fit_mode_types(self) -> None:
        """Print supported fit modes and mark the current selection."""
        num_expts = len(self.project.experiments) if self.project.experiments else 0
        if num_expts <= 1:
            modes = [FitModeEnum.SINGLE]
        else:
            modes = [FitModeEnum.SINGLE, FitModeEnum.JOINT, FitModeEnum.SEQUENTIAL]
        current = self.fit_mode_type
        columns_data = [
            ['*' if mode.value == current else '', mode.value, mode.description()]
            for mode in modes
        ]
        console.paragraph('Fit mode types')
        render_table(
            columns_headers=['Current', 'Type', 'Description'],
            columns_alignment=['left', 'left', 'left'],
            columns_data=columns_data,
        )

    @property
    def fit_mode_type(self) -> str:
        """Current fit-mode type string (single, joint, sequential)."""
        return self._fit_mode.mode.value

    @fit_mode_type.setter
    def fit_mode_type(self, value: str) -> None:
        self._fit_mode.mode = value

    def show_supported_fit_mode_types(self) -> None:
        """Backward-compatible alias for :meth:`show_fit_mode_types`."""
        self.show_fit_mode_types()

    # ------------------------------------------------------------------
    #  Joint-fit experiments (category)
    # ------------------------------------------------------------------

    @property
    def joint_fit_experiments(self) -> object:
        """Per-experiment weight collection for joint fitting."""
        return self._joint_fit_experiments

    def fit(self, verbosity: str | None = None, *, use_physical_limits: bool = False) -> None:
        """
        Execute fitting for all experiments.

        This method performs the optimization but does not display
        results automatically. Call :meth:`display.fit_results` after
        fitting to see a summary of the fit quality and parameter
        values.

        In 'single' mode, fits each experiment independently. In 'joint'
        mode, performs a simultaneous fit across experiments with
        weights. If mode is 'sequential', logs an error directing the
        user to :meth:`fit_sequential` instead.

        Sets :attr:`fit_results` on success, which can be accessed
        programmatically (e.g.,
        ``analysis.fit_results.reduced_chi_square``).

        Parameters
        ----------
        verbosity : str | None, default=None
            Console output verbosity: ``'full'`` for detailed per-
            experiment progress, ``'short'`` for a
            one-row-per-experiment summary table, or ``'silent'`` for no
            output. When ``None``, uses ``project.verbosity``.
        use_physical_limits : bool, default=False
            When ``True``, fall back to physical limits from the value
            spec for parameters whose ``fit_min``/``fit_max`` are
            unbounded.
        """
        verb = VerbosityEnum(verbosity if verbosity is not None else self.project.verbosity)

        structures = self.project.structures
        if not structures:
            log.warning('No structures found in the project. Cannot run fit.')
            return

        experiments = self.project.experiments
        if not experiments:
            log.warning('No experiments found in the project. Cannot run fit.')
            return

        # Apply constraints before fitting so that constrained
        # parameters are marked and excluded from the free parameter
        # list built by the fitter.
        self._update_categories()

        # Run the fitting process
        mode = FitModeEnum(self._fit_mode.mode.value)
        if mode is FitModeEnum.JOINT:
            self._fit_joint(verb, structures, experiments, use_physical_limits=use_physical_limits)
        elif mode is FitModeEnum.SINGLE:
            self._fit_single(
                verb, structures, experiments, use_physical_limits=use_physical_limits
            )
        elif mode is FitModeEnum.SEQUENTIAL:
            log.error(
                "fit_mode is 'sequential'. Use fit_sequential(data_dir=...) instead of fit()."
            )
            return

        # After fitting, save the project
        if self.project.info.path is not None:
            self.project.save()

    def _fit_joint(
        self,
        verb: VerbosityEnum,
        structures: object,
        experiments: object,
        *,
        use_physical_limits: bool,
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
        """
        mode = FitModeEnum.JOINT
        # Auto-populate joint_fit_experiments if empty
        if not len(self._joint_fit_experiments):
            for id in experiments.names:
                self._joint_fit_experiments.create(id=id, weight=0.5)
        if verb is not VerbosityEnum.SILENT:
            console.paragraph(
                f"Using all experiments 🔬 {experiments.names} for '{mode.value}' fitting"
            )
        # Resolve weights to a plain numpy array
        experiments_list = list(experiments.values())
        weights_list = [
            self._joint_fit_experiments[name].weight.value for name in experiments.names
        ]
        weights_array = np.array(weights_list, dtype=np.float64)
        self.fitter.fit(
            structures,
            experiments_list,
            weights=weights_array,
            analysis=self,
            verbosity=verb,
            use_physical_limits=use_physical_limits,
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
        """
        mode = FitModeEnum.SINGLE
        expt_names = experiments.names

        short_display_handle = self._fit_single_print_header(verb, expt_names, mode)
        short_rows: list[list[str]] = []

        for expt_name in expt_names:
            if verb is VerbosityEnum.FULL:
                console.print(f"📋 Using experiment 🔬 '{expt_name}' for '{mode.value}' fitting")

            experiment = experiments[expt_name]
            self.fitter.fit(
                structures,
                [experiment],
                analysis=self,
                verbosity=verb,
                use_physical_limits=use_physical_limits,
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
        return _make_display_handle()

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

    def fit_sequential(
        self,
        data_dir: str,
        max_workers: int | str = 1,
        chunk_size: int | None = None,
        file_pattern: str = '*',
        extract_diffrn: object = None,
        verbosity: str | None = None,
        *,
        reverse: bool = False,
    ) -> None:
        """
        Run sequential fitting over all data files in a directory.

        Fits each dataset independently using the current structure and
        experiment as a template.  Results are written incrementally to
        ``analysis/results.csv`` in the project directory.

        The project must contain exactly one structure and one
        experiment (the template), and must have been saved
        (``save_as()``) before calling this method.

        Parameters
        ----------
        data_dir : str
            Path to directory containing data files.
        max_workers : int | str, default=1
            Number of parallel worker processes. ``1`` = sequential.
            ``'auto'`` = physical CPU count. Uses
            ``ProcessPoolExecutor`` with ``spawn`` context when > 1.
        chunk_size : int | None, default=None
            Files per chunk. Default ``None`` uses *max_workers*.
        file_pattern : str, default='*'
            Glob pattern to filter files in *data_dir*.
        extract_diffrn : object, default=None
            User callback ``f(file_path) → {diffrn_field: value}``.
            Called per file after fitting. ``None`` = no diffrn
            metadata.
        verbosity : str | None, default=None
            ``'full'``, ``'short'``, or ``'silent'``. Default: project
            verbosity.
        reverse : bool, default=False
            When ``True``, process data files in reverse order.  Useful
            when starting values are better matched to the last file
            (e.g. highest-temperature dataset in a cooling scan).
        """
        from easydiffraction.analysis.sequential import fit_sequential as _fit_seq  # noqa: PLC0415

        # Record the fit mode for CIF serialization
        self._fit_mode.mode = FitModeEnum.SEQUENTIAL.value

        # Apply constraints before building the template
        self._update_categories()

        # Temporarily override project verbosity if caller provided one
        original_verbosity = None
        if verbosity is not None:
            original_verbosity = self.project.verbosity
            self.project.verbosity = verbosity
        try:
            _fit_seq(
                analysis=self,
                data_dir=data_dir,
                max_workers=max_workers,
                chunk_size=chunk_size,
                file_pattern=file_pattern,
                extract_diffrn=extract_diffrn,
                reverse=reverse,
            )
        finally:
            if original_verbosity is not None:
                self.project.verbosity = original_verbosity

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
        del called_by_minimizer

        # Apply constraints to sync dependent parameters
        if self.constraints.enabled and self.constraints._items:
            self.constraints_handler.set_aliases(self.aliases)
            self.constraints_handler.set_constraints(self.constraints)
            self.constraints_handler.apply()

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
