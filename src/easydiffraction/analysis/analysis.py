import pandas as pd
import numpy as np
from tabulate import tabulate
from typing import List, Optional, Union, Any

from easydiffraction.utils.formatting import (
    paragraph,
    warning
)
from easydiffraction.utils.chart_plotter import (
    ChartPlotter,
    DEFAULT_HEIGHT
)
from easydiffraction.experiments.experiments import Experiments
from easydiffraction.core.objects import (
    Descriptor,
    Parameter
)
from easydiffraction.core.singletons import (
    ConstraintsHandler,
    UidMapHandler
)

from .collections.aliases import ConstraintAliases
from .collections.constraints import ConstraintExpressions
from .calculators.calculator_factory import CalculatorFactory
from .minimization import DiffractionMinimizer
from .minimizers.minimizer_factory import MinimizerFactory
from easydiffraction.analysis.collections.joint_fit_experiments import JointFitExperiments


class Analysis:
    _calculator = CalculatorFactory.create_calculator('cryspy')

    def __init__(self, project: Any) -> None:
        self.project = project
        self.aliases = ConstraintAliases()
        self.constraints = ConstraintExpressions()
        self.constraints_handler = ConstraintsHandler.get()
        self.calculator = Analysis._calculator  # Default calculator shared by project
        self._calculator_key: str = 'cryspy'  # Added to track the current calculator
        self._fit_mode: str = 'single'
        self.fitter = DiffractionMinimizer('lmfit (leastsq)')

    def _get_params_as_dataframe(self, params: List[Union[Descriptor, Parameter]]) -> pd.DataFrame:
        """
        Convert a list of parameters to a DataFrame.

        Args:
            params: List of Descriptor or Parameter objects.

        Returns:
            A pandas DataFrame containing parameter information.
        """
        rows = []
        for param in params:
            common_attrs = {}
            if isinstance(param, (Descriptor, Parameter)):
                common_attrs = {
                    'datablock': param.datablock_id,
                    'category': param.category_key,
                    'entry': param.collection_entry_id,
                    'parameter': param.name,
                    'value': param.value,
                    'units': param.units,
                    'fittable': False
                }
            param_attrs = {}
            if isinstance(param, Parameter):
                param_attrs = {
                    'fittable': True,
                    'free': param.free,
                    'min': param.min,
                    'max': param.max,
                    'uncertainty': f"{param.uncertainty:.4f}" if param.uncertainty else "",
                    'value': f"{param.value:.4f}",
                    'units': param.units,
                }
            row = common_attrs | param_attrs
            rows.append(row)

        dataframe = pd.DataFrame(rows)

        return dataframe

    def _show_params(self, dataframe: pd.DataFrame, column_headers: List[str]) -> None:
        """
        Display parameters in a tabular format.

        Args:
            dataframe: The pandas DataFrame containing parameter information.
            column_headers: List of column headers to display.
        """
        dataframe = dataframe[column_headers]
        indices = range(1, len(dataframe) + 1)  # Force starting from 1

        print(tabulate(dataframe,
                       headers=column_headers,
                       tablefmt="fancy_outline",
                       showindex=indices))

    def show_all_params(self) -> None:
        sample_models_params = self.project.sample_models.get_all_params()
        experiments_params = self.project.experiments.get_all_params()

        if not sample_models_params and not experiments_params:
            print(warning(f"No parameters found."))
            return

        column_headers = ['datablock',
                          'category',
                          'entry',
                          'parameter',
                          'value',
                          'fittable']

        print(paragraph("All parameters for all sample models (🧩 data blocks)"))
        sample_models_dataframe = self._get_params_as_dataframe(sample_models_params)
        self._show_params(sample_models_dataframe, column_headers=column_headers)

        print(paragraph("All parameters for all experiments (🔬 data blocks)"))
        experiments_dataframe = self._get_params_as_dataframe(experiments_params)
        self._show_params(experiments_dataframe, column_headers=column_headers)

    def show_fittable_params(self) -> None:
        sample_models_params = self.project.sample_models.get_fittable_params()
        experiments_params = self.project.experiments.get_fittable_params()

        if not sample_models_params and not experiments_params:
            print(warning(f"No fittable parameters found."))
            return

        column_headers = ['datablock',
                          'category',
                          'entry',
                          'parameter',
                          'value',
                          'uncertainty',
                          'units',
                          'free']

        print(paragraph("Fittable parameters for all sample models (🧩 data blocks)"))
        sample_models_dataframe = self._get_params_as_dataframe(sample_models_params)
        self._show_params(sample_models_dataframe, column_headers=column_headers)

        print(paragraph("Fittable parameters for all experiments (🔬 data blocks)"))
        experiments_dataframe = self._get_params_as_dataframe(experiments_params)
        self._show_params(experiments_dataframe, column_headers=column_headers)

    def show_free_params(self) -> None:
        sample_models_params = self.project.sample_models.get_free_params()
        experiments_params = self.project.experiments.get_free_params()
        free_params = sample_models_params + experiments_params

        if not free_params:
            print(warning(f"No free parameters found."))
            return

        column_headers = ['datablock',
                          'category',
                          'entry',
                          'parameter',
                          'value',
                          'uncertainty',
                          'min',
                          'max',
                          'units']

        print(paragraph("Free parameters for both sample models (🧩 data blocks) and experiments (🔬 data blocks)"))
        dataframe = self._get_params_as_dataframe(free_params)
        self._show_params(dataframe, column_headers=column_headers)

    def how_to_access_parameters(self, show_description: bool = False) -> None:
        sample_models_params = self.project.sample_models.get_all_params()
        experiments_params = self.project.experiments.get_all_params()
        params = {'sample_models': sample_models_params,
                  'experiments': experiments_params}

        if not params:
            print(warning(f"No parameters found."))
            return

        project_varname = self.project._varname

        rows = []
        for datablock_type, params in params.items():
            for param in params:
                if isinstance(param, (Descriptor, Parameter)):
                    datablock_id = param.datablock_id
                    category_key = param.category_key
                    entry_id = param.collection_entry_id
                    param_key = param.name
                    description = param.description
                    variable = f"{project_varname}.{datablock_type}['{datablock_id}'].{category_key}"
                    if entry_id:
                        variable += f"['{entry_id}']"
                    variable += f".{param_key}"
                    rows.append({'variable': variable,
                                 'description': description})

        dataframe = pd.DataFrame(rows)

        column_headers = ['variable']
        if show_description:
            column_headers = ['variable', 'description']
        dataframe = dataframe[column_headers]

        indices = range(1, len(dataframe) + 1)  # Force starting from 1

        print(paragraph("How to access parameters"))
        print("You can access parameters using the following syntax. "
              "Just copy and paste it from the table below:")

        print(tabulate(dataframe,
                       headers=column_headers,
                       tablefmt="fancy_outline",
                       showindex=indices))

    def show_current_calculator(self) -> None:
        print(paragraph("Current calculator"))
        print(self.current_calculator)

    @staticmethod
    def show_supported_calculators() -> None:
        CalculatorFactory.show_supported_calculators()

    @property
    def current_calculator(self) -> str:
        return self._calculator_key

    @current_calculator.setter
    def current_calculator(self, calculator_name: str) -> None:
        calculator = CalculatorFactory.create_calculator(calculator_name)
        if calculator is None:
            return
        self.calculator = calculator
        self._calculator_key = calculator_name
        print(paragraph("Current calculator changed to"))
        print(self.current_calculator)

    def show_current_minimizer(self) -> None:
        print(paragraph("Current minimizer"))
        print(self.current_minimizer)

    @staticmethod
    def show_available_minimizers() -> None:
        MinimizerFactory.show_available_minimizers()

    @property
    def current_minimizer(self) -> Optional[str]:
        return self.fitter.selection if self.fitter else None

    @current_minimizer.setter
    def current_minimizer(self, selection: str) -> None:
        self.fitter = DiffractionMinimizer(selection)
        print(paragraph(f"Current minimizer changed to"))
        print(self.current_minimizer)

    @property
    def fit_mode(self) -> str:
        return self._fit_mode

    @fit_mode.setter
    def fit_mode(self, strategy: str) -> None:
        if strategy not in ['single', 'joint']:
            raise ValueError("Fit mode must be either 'single' or 'joint'")
        self._fit_mode = strategy
        if strategy == 'joint':
            if not hasattr(self, 'joint_fit_experiments'):
                # Pre-populate all experiments with weight 0.5
                self.joint_fit_experiments = JointFitExperiments()
                for id in self.project.experiments.ids:
                    self.joint_fit_experiments.add(id, weight=0.5)
        print(paragraph("Current fit mode changed to"))
        print(self._fit_mode)

    def show_available_fit_modes(self) -> None:
        strategies = [
            {
                "Strategy": "single",
                "Description": "Independent fitting of each experiment; no shared parameters"},
            {
                "Strategy": "joint",
                "Description": "Simultaneous fitting of all experiments; some parameters are shared"
            },
        ]
        print(paragraph("Available fit modes"))
        print(tabulate(strategies, headers="keys", tablefmt="fancy_outline", showindex=False))

    def show_current_fit_mode(self) -> None:
        print(paragraph("Current fit mode"))
        print(self.fit_mode)

    def calculate_pattern(self, expt_name: str) -> Optional[np.ndarray]:
        """
        Calculate the diffraction pattern for a given experiment.

        Args:
            expt_name: The name of the experiment.

        Returns:
            The calculated pattern as a pandas DataFrame.
        """
        experiment = self.project.experiments[expt_name]
        sample_models = self.project.sample_models
        calculated_pattern = self.calculator.calculate_pattern(sample_models, experiment)
        return calculated_pattern

    def show_constraints(self) -> None:
        constraints_dict = self.constraints._items

        if not self.constraints._items:
            print(warning(f"No constraints defined."))
            return

        rows = []
        for id, constraint in constraints_dict.items():
            row = {
                'id': id,
                'lhs_alias': constraint.lhs_alias.value,
                'rhs_expr': constraint.rhs_expr.value,
                'full expression': f'{constraint.lhs_alias.value} = {constraint.rhs_expr.value}'
            }
            rows.append(row)

        dataframe = pd.DataFrame(rows)

        print(paragraph(f"User defined constraints"))
        print(tabulate(dataframe,
                       headers=dataframe.columns,
                       tablefmt="fancy_outline",
                       showindex=False))

    def _update_uid_map(self) -> None:
        """
        Update the UID map for accessing parameters by UID.
        This is needed for adding or removing constraints.
        """
        sample_models_params = self.project.sample_models.get_all_params()
        experiments_params = self.project.experiments.get_all_params()
        params = sample_models_params + experiments_params

        UidMapHandler.get().set_uid_map(params)

    def apply_constraints(self) -> None:
        if not self.constraints._items:
            print(warning(f"No constraints defined."))
            return

        sample_models_params = self.project.sample_models.get_fittable_params()
        experiments_params = self.project.experiments.get_fittable_params()
        fittable_params = sample_models_params + experiments_params

        self._update_uid_map()
        self.constraints_handler.set_aliases(self.aliases)
        self.constraints_handler.set_expressions(self.constraints)
        self.constraints_handler.apply(parameters=fittable_params)

    def show_calc_chart(self, expt_name: str, x_min: Optional[float] = None, x_max: Optional[float] = None) -> None:
        self.calculate_pattern(expt_name)

        experiment = self.project.experiments[expt_name]
        pattern = experiment.datastore.pattern

        plotter = ChartPlotter()
        plotter.plot(
            y_values_list=[pattern.calc],
            x_values=pattern.x,
            x_min=x_min,
            x_max=x_max,
            title=paragraph(f"Calculated data for experiment 🔬 '{expt_name}'"),
            labels=['calc']
        )

    def show_meas_vs_calc_chart(self,
                                expt_name: str,
                                x_min: Optional[float] = None,
                                x_max: Optional[float] = None,
                                show_residual: bool = False,
                                chart_height: int = DEFAULT_HEIGHT) -> None:
        experiment = self.project.experiments[expt_name]

        self.calculate_pattern(expt_name)

        pattern = experiment.datastore.pattern

        if pattern.meas is None or pattern.calc is None or pattern.x is None:
            print(f"No data available for {expt_name}. Cannot display chart.")
            return

        series = [pattern.meas, pattern.calc]
        labels = ['meas', 'calc']

        if show_residual:
            residual = pattern.meas - pattern.calc
            series.append(residual)
            labels.append('residual')

        plotter = ChartPlotter(height=chart_height)
        plotter.plot(
            y_values_list=series,
            x_values=pattern.x,
            x_min=x_min,
            x_max=x_max,
            title=paragraph(f"Measured vs Calculated data for experiment 🔬 '{expt_name}'"),
            labels=labels
        )

    def fit(self) -> None:
        sample_models = self.project.sample_models
        if not sample_models:
            print("No sample models found in the project. Cannot run fit.")
            return

        experiments = self.project.experiments
        if not experiments:
            print("No experiments found in the project. Cannot run fit.")
            return

        calculator = self.calculator
        if not calculator:
            print("No calculator is set. Cannot run fit.")
            return

        # Run the fitting process
        experiment_ids = experiments.ids

        if self.fit_mode == 'joint':
            print(paragraph(f"Using all experiments 🔬 {experiment_ids} for '{self.fit_mode}' fitting"))
            self.fitter.fit(sample_models, experiments, calculator, weights=self.joint_fit_experiments)
        elif self.fit_mode == 'single':
            for expt_name in experiments.ids:
                print(paragraph(f"Using experiment 🔬 '{expt_name}' for '{self.fit_mode}' fitting"))
                experiment = experiments[expt_name]
                dummy_experiments = Experiments()  # TODO: Find a better name
                dummy_experiments.add(experiment)
                self.fitter.fit(sample_models, dummy_experiments, calculator)
        else:
            raise NotImplementedError(f"Fit mode {self.fit_mode} not implemented yet.")

        # After fitting, get the results
        self.fit_results = self.fitter.results

    def as_cif(self) -> str:
        lines = []
        lines.append(f"_analysis.calculator_engine  {self.current_calculator}")
        lines.append(f"_analysis.fitting_engine  {self.current_minimizer}")
        lines.append(f"_analysis.fit_mode  {self.fit_mode}")

        return "\n".join(lines)

    def show_as_cif(self) -> None:
        cif_text = self.as_cif()
        lines = cif_text.splitlines()
        max_width = max(len(line) for line in lines)
        padded_lines = [f"│ {line.ljust(max_width)} │" for line in lines]
        top = f"╒{'═' * (max_width + 2)}╕"
        bottom = f"╘{'═' * (max_width + 2)}╛"

        print(paragraph(f"Analysis 🧮 info as cif"))
        print(top)
        print("\n".join(padded_lines))
        print(bottom)
