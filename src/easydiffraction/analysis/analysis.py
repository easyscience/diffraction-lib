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
        self.fitter = Fitter('lmfit')
        self.fit_results = None
        self._parameter_snapshots: dict[str, dict[str, dict]] = {}

    def help(self) -> None:
        """Print a summary of analysis properties and methods."""
        console.paragraph("Help for 'Analysis'")

        cls = type(self)

        # Auto-discover properties from MRO
        seen_props: dict = {}
        for base in cls.mro():
            for key, attr in base.__dict__.items():
                if key.startswith('_') or not isinstance(attr, property):
                    continue
                if key not in seen_props:
                    seen_props[key] = attr

        prop_rows = []
        for i, key in enumerate(sorted(seen_props), 1):
            prop = seen_props[key]
            writable = '✓' if prop.fset else '✗'
            doc = GuardedBase._first_sentence(prop.fget.__doc__ if prop.fget else None)
            prop_rows.append([str(i), key, writable, doc])

        if prop_rows:
            console.paragraph('Properties')
            render_table(
                columns_headers=['#', 'Name', 'Writable', 'Description'],
                columns_alignment=['right', 'left', 'center', 'left'],
                columns_data=prop_rows,
            )

        # Auto-discover methods from MRO
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

        method_rows = []
        for i, (key, method) in enumerate(sorted(methods_list), 1):
            doc = GuardedBase._first_sentence(getattr(method, '__doc__', None))
            method_rows.append([str(i), f'{key}()', doc])

        if method_rows:
            console.paragraph('Methods')
            render_table(
                columns_headers=['#', 'Name', 'Description'],
                columns_alignment=['right', 'left', 'left'],
                columns_data=method_rows,
            )

    # ------------------------------------------------------------------
    #  Aliases (switchable-category pattern)
    # ------------------------------------------------------------------

    @property
    def aliases_type(self) -> str:
        """Tag of the active aliases collection type."""
        return self._aliases_type

    @aliases_type.setter
    def aliases_type(self, new_type: str) -> None:
        """
        Switch to a different aliases collection type.

        Parameters
        ----------
        new_type : str
            Aliases tag (e.g. ``'default'``).
        """
        supported_tags = AliasesFactory.supported_tags()
        if new_type not in supported_tags:
            log.warning(
                f"Unsupported aliases type '{new_type}'. "
                f'Supported: {supported_tags}. '
                f"For more information, use 'show_supported_aliases_types()'",
            )
            return
        self.aliases = AliasesFactory.create(new_type)
        self._aliases_type = new_type
        console.paragraph('Aliases type changed to')
        console.print(new_type)

    def show_supported_aliases_types(self) -> None:
        """Print a table of supported aliases collection types."""
        AliasesFactory.show_supported()

    def show_current_aliases_type(self) -> None:
        """Print the currently used aliases collection type."""
        console.paragraph('Current aliases type')
        console.print(self._aliases_type)

    # ------------------------------------------------------------------
    #  Constraints (switchable-category pattern)
    # ------------------------------------------------------------------

    @property
    def constraints_type(self) -> str:
        """Tag of the active constraints collection type."""
        return self._constraints_type

    @constraints_type.setter
    def constraints_type(self, new_type: str) -> None:
        """
        Switch to a different constraints collection type.

        Parameters
        ----------
        new_type : str
            Constraints tag (e.g. ``'default'``).
        """
        supported_tags = ConstraintsFactory.supported_tags()
        if new_type not in supported_tags:
            log.warning(
                f"Unsupported constraints type '{new_type}'. "
                f'Supported: {supported_tags}. '
                f"For more information, use 'show_supported_constraints_types()'",
            )
            return
        self.constraints = ConstraintsFactory.create(new_type)
        self._constraints_type = new_type
        console.paragraph('Constraints type changed to')
        console.print(new_type)

    def show_supported_constraints_types(self) -> None:
        """Print a table of supported constraints collection types."""
        ConstraintsFactory.show_supported()

    def show_current_constraints_type(self) -> None:
        """Print the currently used constraints collection type."""
        console.paragraph('Current constraints type')
        console.print(self._constraints_type)

    def _get_params_as_dataframe(
        self,
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

    def show_all_params(self) -> None:
        """Print all parameters for structures and experiments."""
        structures_params = self.project.structures.parameters
        experiments_params = self.project.experiments.parameters

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
        df = self._get_params_as_dataframe(structures_params)
        filtered_df = df[filtered_headers]
        tabler.render(filtered_df)

        console.paragraph('All parameters for all experiments (🔬 data blocks)')
        df = self._get_params_as_dataframe(experiments_params)
        filtered_df = df[filtered_headers]
        tabler.render(filtered_df)

    def show_fittable_params(self) -> None:
        """Print all fittable parameters."""
        structures_params = self.project.structures.fittable_parameters
        experiments_params = self.project.experiments.fittable_parameters

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
        df = self._get_params_as_dataframe(structures_params)
        filtered_df = df[filtered_headers]
        tabler.render(filtered_df)

        console.paragraph('Fittable parameters for all experiments (🔬 data blocks)')
        df = self._get_params_as_dataframe(experiments_params)
        filtered_df = df[filtered_headers]
        tabler.render(filtered_df)

    def show_free_params(self) -> None:
        """Print only currently free (varying) parameters."""
        structures_params = self.project.structures.free_parameters
        experiments_params = self.project.experiments.free_parameters
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
        df = self._get_params_as_dataframe(free_params)
        filtered_df = df[filtered_headers]
        tabler.render(filtered_df)

    def how_to_access_parameters(self) -> None:
        """
        Show Python access paths for all parameters.

        The output explains how to reference specific parameters in
        code.
        """
        structures_params = self.project.structures.parameters
        experiments_params = self.project.experiments.parameters
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
        project_varname = self.project._varname
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

    def show_parameter_cif_uids(self) -> None:
        """
        Show CIF unique IDs for all parameters.

        The output explains which unique identifiers are used when
        creating CIF-based constraints.
        """
        structures_params = self.project.structures.parameters
        experiments_params = self.project.experiments.parameters
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

    def show_current_minimizer(self) -> None:
        """Print the name of the currently selected minimizer."""
        console.paragraph('Current minimizer')
        console.print(self.current_minimizer)

    @staticmethod
    def show_available_minimizers() -> None:
        """Print available minimizer drivers on this system."""
        MinimizerFactory.show_supported()

    @property
    def current_minimizer(self) -> str | None:
        """The identifier of the active minimizer, if any."""
        return self.fitter.selection if self.fitter else None

    @current_minimizer.setter
    def current_minimizer(self, selection: str) -> None:
        """
        Switch to a different minimizer implementation.

        Parameters
        ----------
        selection : str
            Minimizer selection string, e.g. 'lmfit'.
        """
        self.fitter = Fitter(selection)
        console.paragraph('Current minimizer changed to')
        console.print(self.current_minimizer)

    # ------------------------------------------------------------------
    #  Fit mode (switchable-category pattern)
    # ------------------------------------------------------------------

    @property
    def fit_mode(self) -> object:
        """Fit-mode category item holding the active strategy."""
        return self._fit_mode

    @property
    def fit_mode_type(self) -> str:
        """Tag of the active fit-mode category type."""
        return self._fit_mode_type

    @fit_mode_type.setter
    def fit_mode_type(self, new_type: str) -> None:
        """
        Switch to a different fit-mode category type.

        Parameters
        ----------
        new_type : str
            Fit-mode tag (e.g. ``'default'``).
        """
        supported_tags = FitModeFactory.supported_tags()
        if new_type not in supported_tags:
            log.warning(
                f"Unsupported fit-mode type '{new_type}'. "
                f'Supported: {supported_tags}. '
                f"For more information, use 'show_supported_fit_mode_types()'",
            )
            return
        self._fit_mode = FitModeFactory.create(new_type)
        self._fit_mode_type = new_type
        console.paragraph('Fit-mode type changed to')
        console.print(new_type)

    def show_supported_fit_mode_types(self) -> None:
        """Print a table of supported fit-mode category types."""
        FitModeFactory.show_supported()

    def show_current_fit_mode_type(self) -> None:
        """Print the currently used fit-mode category type."""
        console.paragraph('Current fit-mode type')
        console.print(self._fit_mode_type)

    # ------------------------------------------------------------------
    #  Joint-fit experiments (category)
    # ------------------------------------------------------------------

    @property
    def joint_fit_experiments(self) -> object:
        """Per-experiment weight collection for joint fitting."""
        return self._joint_fit_experiments

    def show_constraints(self) -> None:
        """Print a table of all user-defined symbolic constraints."""
        if not self.constraints._items:
            log.warning('No constraints defined.')
            return

        rows = [[constraint.expression.value] for constraint in self.constraints]

        console.paragraph('User defined constraints')
        render_table(
            columns_headers=['expression'],
            columns_alignment=['left'],
            columns_data=rows,
        )

    def apply_constraints(self) -> None:
        """Apply currently defined constraints to the project."""
        if not self.constraints._items:
            log.warning('No constraints defined.')
            return

        self.constraints_handler.set_aliases(self.aliases)
        self.constraints_handler.set_constraints(self.constraints)
        self.constraints_handler.apply()

    def fit(self, verbosity: str | None = None) -> None:
        """
        Execute fitting for all experiments.

        This method performs the optimization but does not display
        results automatically. Call :meth:`show_fit_results` after
        fitting to see a summary of the fit quality and parameter
        values.

        In 'single' mode, fits each experiment independently. In 'joint'
        mode, performs a simultaneous fit across experiments with
        weights.

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

        Raises
        ------
        NotImplementedError
            If the fit mode is not ``'single'`` or ``'joint'``.
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

        # Run the fitting process
        mode = FitModeEnum(self._fit_mode.mode.value)
        if mode is FitModeEnum.JOINT:
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
            )

            # After fitting, get the results
            self.fit_results = self.fitter.results

        elif mode is FitModeEnum.SINGLE:
            expt_names = experiments.names
            num_expts = len(expt_names)

            # Short mode: print header and create display handle once
            short_headers = ['experiment', 'χ²', 'iterations', 'status']
            short_alignments = ['left', 'right', 'right', 'center']
            short_rows: list[list[str]] = []
            short_display_handle: object | None = None
            if verb is VerbosityEnum.SHORT:
                first = expt_names[0]
                last = expt_names[-1]
                minimizer_name = self.fitter.selection
                console.paragraph(
                    f"Using {num_expts} experiments 🔬 from '{first}' to "
                    f"'{last}' for '{mode.value}' fitting"
                )
                console.print(f"🚀 Starting fit process with '{minimizer_name}'...")
                console.print('📈 Goodness-of-fit (reduced χ²) per experiment:')
                short_display_handle = _make_display_handle()

            for _idx, expt_name in enumerate(expt_names, start=1):
                if verb is VerbosityEnum.FULL:
                    console.paragraph(
                        f"Using experiment 🔬 '{expt_name}' for '{mode.value}' fitting"
                    )

                experiment = experiments[expt_name]
                experiments_list = [experiment]
                self.fitter.fit(
                    structures,
                    experiments_list,
                    analysis=self,
                    verbosity=verb,
                )

                # After fitting, snapshot parameter values before
                # they get overwritten by the next experiment's fit
                results = self.fitter.results
                snapshot: dict[str, dict] = {}
                for param in results.parameters:
                    snapshot[param.unique_name] = {
                        'value': param.value,
                        'uncertainty': param.uncertainty,
                        'units': param.units,
                    }
                self._parameter_snapshots[expt_name] = snapshot
                self.fit_results = results

                # Short mode: append one summary row and update in-place
                if verb is VerbosityEnum.SHORT:
                    chi2_str = (
                        f'{results.reduced_chi_square:.2f}'
                        if results.reduced_chi_square is not None
                        else '—'
                    )
                    iters = str(self.fitter.minimizer.tracker.best_iteration or 0)
                    status = '✅' if results.success else '❌'
                    short_rows.append([expt_name, chi2_str, iters, status])
                    render_table(
                        columns_headers=short_headers,
                        columns_alignment=short_alignments,
                        columns_data=short_rows,
                        display_handle=short_display_handle,
                    )

            # Short mode: close the display handle
            if short_display_handle is not None and hasattr(short_display_handle, 'close'):
                with suppress(Exception):
                    short_display_handle.close()

        else:
            msg = f'Fit mode {mode.value} not implemented yet.'
            raise NotImplementedError(msg)

        # After fitting, save the project
        # TODO: Consider saving individual data during sequential
        #  (single) fitting, instead of waiting until the end and save
        #  only the last one
        if self.project.info.path is not None:
            self.project.save()

    def show_fit_results(self) -> None:
        """
        Display a summary of the fit results.

        Renders the fit quality metrics (reduced χ², R-factors) and a
        table of fitted parameters with their starting values, final
        values, and uncertainties.

        This method should be called after :meth:`fit` completes. If no
        fit has been performed yet, a warning is logged.

        Example::

        project.analysis.fit() project.analysis.show_fit_results()
        """
        if self.fit_results is None:
            log.warning('No fit results available. Run fit() first.')
            return

        structures = self.project.structures
        experiments = list(self.project.experiments.values())

        self.fitter._process_fit_results(structures, experiments)

    def _update_categories(self, called_by_minimizer: bool = False) -> None:
        """
        Update all categories owned by Analysis.

        This ensures aliases and constraints are up-to-date before
        serialization or after parameter changes.

        Parameters
        ----------
        called_by_minimizer : bool, default=False
            Whether this is called during fitting.
        """
        # Apply constraints to sync dependent parameters
        if self.constraints._items:
            self.constraints_handler.apply()

        # Update category-specific logic
        # TODO: Need self.categories as in the case of datablock.py
        for category in [self.aliases, self.constraints]:
            if hasattr(category, '_update'):
                category._update(called_by_minimizer=called_by_minimizer)

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
        """Render the analysis section as CIF in console."""
        cif_text: str = self.as_cif()
        paragraph_title: str = 'Analysis 🧮 info as cif'
        console.paragraph(paragraph_title)
        render_cif(cif_text)
