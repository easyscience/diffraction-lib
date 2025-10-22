# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from typing import List
from typing import Optional
from typing import Union

import pandas as pd

from easydiffraction import console
from easydiffraction import log
from easydiffraction.analysis.calculators.factory import CalculatorFactory
from easydiffraction.analysis.categories.aliases import Aliases
from easydiffraction.analysis.categories.constraints import Constraints
from easydiffraction.analysis.categories.joint_fit_experiments import JointFitExperiments
from easydiffraction.analysis.fitting import Fitter
from easydiffraction.analysis.minimizers.factory import MinimizerFactory
from easydiffraction.core.parameters import NumericDescriptor
from easydiffraction.core.parameters import Parameter
from easydiffraction.core.singletons import ConstraintsHandler
from easydiffraction.experiments.experiments import Experiments
from easydiffraction.utils.utils import render_cif
from easydiffraction.utils.utils import render_table


class Analysis:
    """High-level orchestration of analysis tasks for a Project.

    This class wires calculators and minimizers, exposes a compact
    interface for parameters, constraints and results, and coordinates
    computations across the project's sample models and experiments.

    Typical usage:

    - Display or filter parameters to fit.
    - Select a calculator/minimizer implementation.
    - Calculate patterns and run single or joint fits.

    Attributes:
    project: The parent Project object.
        aliases: A registry of human-friendly aliases for parameters.
        constraints: Symbolic constraints between parameters.
    calculator: Active calculator used for computations.
        fitter: Active fitter/minimizer driver.
    """

    _calculator = CalculatorFactory.create_calculator('cryspy')

    def __init__(self, project) -> None:
        """Create a new Analysis instance bound to a project.

        Args:
            project: The project that owns models and experiments.
        """
        self.project = project
        self.aliases = Aliases()
        self.constraints = Constraints()
        self.constraints_handler = ConstraintsHandler.get()
        self.calculator = Analysis._calculator  # Default calculator shared by project
        self._calculator_key: str = 'cryspy'  # Added to track the current calculator
        self._fit_mode: str = 'single'
        self.fitter = Fitter('lmfit (leastsq)')

    def _get_params_as_dataframe(
        self,
        params: List[Union[NumericDescriptor, Parameter]],
    ) -> pd.DataFrame:
        """Convert a list of parameters to a DataFrame.

        Args:
            params: List of DescriptorFloat or Parameter objects.

        Returns:
            A pandas DataFrame containing parameter information.
        """
        rows = []
        for param in params:
            common_attrs = {}
            # TODO: Merge into one. Add field if attr exists
            if isinstance(param, (NumericDescriptor, Parameter)):  # TODO: StringDescriptor?
                common_attrs = {
                    'datablock': param._identity.datablock_entry_name,
                    'category': param._identity.category_code,
                    'entry': param._identity.category_entry_name
                    or '',  # TODO: 'entry' if not None?
                    'parameter': param.name,
                    'value': param.value,  # TODO: f'{param.value!r}' for StringDescriptor?
                    'units': param.units,
                    'fittable': False,
                }
            param_attrs = {}
            if isinstance(param, Parameter):
                param_attrs = {
                    'fittable': True,
                    'free': param.free,
                    'min': param.fit_min,
                    'max': param.fit_max,
                    # 'uncertainty': f'{param.uncertainty:.4f}'
                    # if param.uncertainty else '',
                    'uncertainty': f'{param.uncertainty:.4f}' if param.uncertainty else '',
                    # 'value': f'{param.value:.4f}', # TODO: Needed?
                    # 'units': param.units,
                }
            row = common_attrs | param_attrs
            rows.append(row)

        dataframe = pd.DataFrame(rows)
        return dataframe

    def show_all_params(self) -> None:
        """Print a table with all parameters for sample models and
        experiments.
        """
        sample_models_params = self.project.sample_models.parameters
        experiments_params = self.project.experiments.parameters

        if not sample_models_params and not experiments_params:
            log.warning('No parameters found.')
            return

        columns_headers = [
            'datablock',
            'category',
            'entry',
            'parameter',
            'value',
            'fittable',
        ]
        columns_alignment = [
            'left',
            'left',
            'left',
            'left',
            'right',
            'left',
        ]

        sample_models_dataframe = self._get_params_as_dataframe(sample_models_params)
        sample_models_dataframe = sample_models_dataframe[columns_headers]

        console.paragraph('All parameters for all sample models (🧩 data blocks)')
        render_table(
            columns_headers=columns_headers,
            columns_alignment=columns_alignment,
            columns_data=sample_models_dataframe,
        )

        experiments_dataframe = self._get_params_as_dataframe(experiments_params)
        experiments_dataframe = experiments_dataframe[columns_headers]

        console.paragraph('All parameters for all experiments (🔬 data blocks)')
        render_table(
            columns_headers=columns_headers,
            columns_alignment=columns_alignment,
            columns_data=experiments_dataframe,
        )

    def show_fittable_params(self) -> None:
        """Print a table with parameters that can be included in
        fitting.
        """
        sample_models_params = self.project.sample_models.fittable_parameters
        experiments_params = self.project.experiments.fittable_parameters

        if not sample_models_params and not experiments_params:
            log.warning('No fittable parameters found.')
            return

        columns_headers = [
            'datablock',
            'category',
            'entry',
            'parameter',
            'value',
            'uncertainty',
            'units',
            'free',
        ]
        columns_alignment = [
            'left',
            'left',
            'left',
            'left',
            'right',
            'right',
            'left',
            'left',
        ]

        sample_models_dataframe = self._get_params_as_dataframe(sample_models_params)
        sample_models_dataframe = sample_models_dataframe[columns_headers]

        console.paragraph('Fittable parameters for all sample models (🧩 data blocks)')
        render_table(
            columns_headers=columns_headers,
            columns_alignment=columns_alignment,
            columns_data=sample_models_dataframe,
        )

        experiments_dataframe = self._get_params_as_dataframe(experiments_params)
        experiments_dataframe = experiments_dataframe[columns_headers]

        console.paragraph('Fittable parameters for all experiments (🔬 data blocks)')
        render_table(
            columns_headers=columns_headers,
            columns_alignment=columns_alignment,
            columns_data=experiments_dataframe,
        )

    def show_free_params(self) -> None:
        """Print a table with only currently-free (varying)
        parameters.
        """
        console.paragraph(
            'Free parameters for both sample models (🧩 data blocks) '
            'and experiments (🔬 data blocks)'
        )

        sample_models_params = self.project.sample_models.free_parameters
        experiments_params = self.project.experiments.free_parameters
        free_params = sample_models_params + experiments_params

        if not free_params:
            log.warning('No free parameters found.')
            return

        columns_headers = [
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
        columns_alignment = [
            'left',
            'left',
            'left',
            'left',
            'right',
            'right',
            'right',
            'right',
            'left',
        ]

        dataframe = self._get_params_as_dataframe(free_params)
        dataframe = dataframe[columns_headers]
        columns_data = dataframe[columns_headers].to_numpy()

        render_table(
            columns_headers=columns_headers,
            columns_alignment=columns_alignment,
            columns_data=columns_data,
        )

    def how_to_access_parameters(self) -> None:
        """Show Python access paths for all parameters.

        The output explains how to reference specific parameters in
        code.
        """
        sample_models_params = self.project.sample_models.parameters
        experiments_params = self.project.experiments.parameters
        all_params = {
            'sample_models': sample_models_params,
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
            'CIF uid',
        ]

        columns_alignment = [
            'left',
            'left',
            'left',
            'left',
            'left',
            'left',
        ]

        columns_data = []
        project_varname = self.project._varname
        for datablock_type, params in all_params.items():
            for param in params:
                if isinstance(param, (NumericDescriptor, Parameter)):
                    datablock_entry_name = param._identity.datablock_entry_name
                    category_code = param._identity.category_code
                    category_entry_name = param._identity.category_entry_name or ''
                    param_key = param.name
                    code_variable = (
                        f'{project_varname}.{datablock_type}'
                        f"['{datablock_entry_name}'].{category_code}"
                    )
                    if category_entry_name:
                        code_variable += f"['{category_entry_name}']"
                    code_variable += f'.{param_key}'
                    uid = (
                        f'{datablock_entry_name}.{category_code}.'
                        f'{category_entry_name + "." if category_entry_name else ""}{param_key}'
                    )
                    columns_data.append([
                        datablock_entry_name,
                        category_code,
                        category_entry_name,
                        param_key,
                        code_variable,
                        uid,
                    ])

        console.paragraph('How to access parameters')
        render_table(
            columns_headers=columns_headers,
            columns_alignment=columns_alignment,
            columns_data=columns_data,
        )

    def show_parameter_cif_uids(self) -> None:
        """Show CIF unique IDs for all parameters.

        The output explains which unique identifiers are used when
        creating CIF-based constraints.
        """
        sample_models_params = self.project.sample_models.parameters
        experiments_params = self.project.experiments.parameters
        all_params = {
            'sample_models': sample_models_params,
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
        for _datablock_type, params in all_params.items():
            for param in params:
                if isinstance(param, (NumericDescriptor, Parameter)):
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

    def show_current_calculator(self) -> None:
        """Print the name of the currently selected calculator
        engine.
        """
        console.paragraph('Current calculator')
        console.print(self.current_calculator)

    @staticmethod
    def show_supported_calculators() -> None:
        """Print a table of available calculator backends on this
        system.
        """
        CalculatorFactory.show_supported_calculators()

    @property
    def current_calculator(self) -> str:
        """The key/name of the active calculator backend."""
        return self._calculator_key

    @current_calculator.setter
    def current_calculator(self, calculator_name: str) -> None:
        """Switch to a different calculator backend.

        Args:
            calculator_name: Calculator key to use (e.g. 'cryspy').
        """
        calculator = CalculatorFactory.create_calculator(calculator_name)
        if calculator is None:
            return
        self.calculator = calculator
        self._calculator_key = calculator_name
        console.paragraph('Current calculator changed to')
        console.print(self.current_calculator)

    def show_current_minimizer(self) -> None:
        """Print the name of the currently selected minimizer."""
        console.paragraph('Current minimizer')
        console.print(self.current_minimizer)

    @staticmethod
    def show_available_minimizers() -> None:
        """Print a table of available minimizer drivers on this
        system.
        """
        MinimizerFactory.show_available_minimizers()

    @property
    def current_minimizer(self) -> Optional[str]:
        """The identifier of the active minimizer, if any."""
        return self.fitter.selection if self.fitter else None

    @current_minimizer.setter
    def current_minimizer(self, selection: str) -> None:
        """Switch to a different minimizer implementation.

        Args:
            selection: Minimizer selection string, e.g.
                'lmfit (leastsq)'.
        """
        self.fitter = Fitter(selection)
        console.paragraph('Current minimizer changed to')
        console.print(self.current_minimizer)

    @property
    def fit_mode(self) -> str:
        """Current fitting strategy: either 'single' or 'joint'."""
        return self._fit_mode

    @fit_mode.setter
    def fit_mode(self, strategy: str) -> None:
        """Set the fitting strategy.

        When set to 'joint', all experiments get default weights and
        are used together in a single optimization.

        Args:
                strategy: Either 'single' or 'joint'.

        Raises:
            ValueError: If an unsupported strategy value is
                provided.
        """
        if strategy not in ['single', 'joint']:
            raise ValueError("Fit mode must be either 'single' or 'joint'")
        self._fit_mode = strategy
        if strategy == 'joint' and not hasattr(self, 'joint_fit_experiments'):
            # Pre-populate all experiments with weight 0.5
            self.joint_fit_experiments = JointFitExperiments()
            for id in self.project.experiments.names:
                self.joint_fit_experiments.add_from_args(id=id, weight=0.5)
        console.paragraph('Current fit mode changed to')
        console.print(self._fit_mode)

    def show_available_fit_modes(self) -> None:
        """Print all supported fitting strategies and their
        descriptions.
        """
        strategies = [
            {
                'Strategy': 'single',
                'Description': 'Independent fitting of each experiment; no shared parameters',
            },
            {
                'Strategy': 'joint',
                'Description': 'Simultaneous fitting of all experiments; '
                'some parameters are shared',
            },
        ]

        columns_headers = ['Strategy', 'Description']
        columns_alignment = ['left', 'left']
        columns_data = []
        for item in strategies:
            strategy = item['Strategy']
            description = item['Description']
            columns_data.append([strategy, description])

        console.paragraph('Available fit modes')
        render_table(
            columns_headers=columns_headers,
            columns_alignment=columns_alignment,
            columns_data=columns_data,
        )

    def show_current_fit_mode(self) -> None:
        """Print the currently active fitting strategy."""
        console.paragraph('Current fit mode')
        console.print(self.fit_mode)

    def calculate_pattern(self, expt_name: str) -> None:
        """Calculate and store the diffraction pattern for an
        experiment.

        The pattern is stored in the target experiment's datastore.

        Args:
                expt_name: The identifier of the experiment to compute.
        """
        experiment = self.project.experiments[expt_name]
        sample_models = self.project.sample_models
        self.calculator.calculate_pattern(sample_models, experiment)

    def show_constraints(self) -> None:
        """Print a table of all user-defined symbolic constraints."""
        constraints_dict = dict(self.constraints)

        if not self.constraints._items:
            log.warning('No constraints defined.')
            return

        rows = []
        for constraint in constraints_dict.values():
            row = {
                'lhs_alias': constraint.lhs_alias.value,
                'rhs_expr': constraint.rhs_expr.value,
                'full expression': f'{constraint.lhs_alias.value} = {constraint.rhs_expr.value}',
            }
            rows.append(row)

        headers = ['lhs_alias', 'rhs_expr', 'full expression']
        alignments = ['left', 'left', 'left']
        rows = [[row[header] for header in headers] for row in rows]

        console.paragraph('User defined constraints')
        render_table(
            columns_headers=headers,
            columns_alignment=alignments,
            columns_data=rows,
        )

    def apply_constraints(self):
        """Apply the currently defined constraints to the active
        project.
        """
        if not self.constraints._items:
            log.warning('No constraints defined.')
            return

        self.constraints_handler.set_aliases(self.aliases)
        self.constraints_handler.set_constraints(self.constraints)
        self.constraints_handler.apply()

    def fit(self):
        """Execute fitting using the selected mode, calculator and
        minimizer.

        In 'single' mode, fits each experiment independently. In
        'joint' mode, performs a simultaneous fit across experiments
        with weights.
            Sets :attr:`fit_results` on success.
        """
        sample_models = self.project.sample_models
        if not sample_models:
            log.warning('No sample models found in the project. Cannot run fit.')
            return

        experiments = self.project.experiments
        if not experiments:
            log.warning('No experiments found in the project. Cannot run fit.')
            return

        calculator = self.calculator
        if not calculator:
            log.warning('No calculator is set. Cannot run fit.')
            return

        # Run the fitting process
        if self.fit_mode == 'joint':
            console.paragraph(
                f"Using all experiments 🔬 {experiments.names} for '{self.fit_mode}' fitting"
            )
            self.fitter.fit(
                sample_models,
                experiments,
                calculator,
                weights=self.joint_fit_experiments,
            )
        elif self.fit_mode == 'single':
            for expt_name in experiments.names:
                console.paragraph(
                    f"Using experiment 🔬 '{expt_name}' for '{self.fit_mode}' fitting"
                )
                experiment = experiments[expt_name]
                dummy_experiments = Experiments()  # TODO: Find a better name
                dummy_experiments.add(experiment)
                self.fitter.fit(sample_models, dummy_experiments, calculator)
        else:
            raise NotImplementedError(f'Fit mode {self.fit_mode} not implemented yet.')

        # After fitting, get the results
        self.fit_results = self.fitter.results

    def as_cif(self):
        """Serialize the analysis section to a CIF string.

        Returns:
            The analysis section represented as a CIF document string.
        """
        from easydiffraction.io.cif.serialize import analysis_to_cif

        return analysis_to_cif(self)

    def show_as_cif(self) -> None:
        """Render the analysis section as CIF in a formatted console
        view.
        """
        cif_text: str = self.as_cif()
        paragraph_title: str = 'Analysis 🧮 info as cif'
        console.paragraph(paragraph_title)
        render_cif(cif_text)
