import pandas as pd
from tabulate import tabulate

from easydiffraction.utils.utils import paragraph, info
from easydiffraction.utils.chart_plotter import ChartPlotter, DEFAULT_HEIGHT
from easydiffraction.experiments import Experiments

from .calculators.calculator_factory import CalculatorFactory
from .minimization import DiffractionMinimizer
from .minimizers.minimizer_factory import MinimizerFactory


class Analysis:
    _calculator = CalculatorFactory.create_calculator('cryspy')

    def __init__(self, project):
        self.project = project
        self.calculator = Analysis._calculator  # Default calculator shared by project
        self._calculator_key = 'cryspy'  # Added to track the current calculator
        self._refinement_strategy = 'single'
        self.fitter = DiffractionMinimizer('lmfit (leastsq)')

    def show_refinable_params(self):
        self.project.sample_models.show_all_parameters_table()
        self.project.experiments.show_all_parameters_table()

    def show_free_params(self):
        """
        Displays only the parameters that are free to refine.
        """
        free_params = self.project.sample_models.get_free_params() + \
                      self.project.experiments.get_free_params()

        print(paragraph("Free Parameters"))

        if not free_params:
            print("No free parameters found.")
            return

        # Convert a list of parameters to custom dictionaries
        params = [
            {
                'cif block': param.block_name,
                'cif parameter': param.cif_name,
                'value': param.value,
                'error': '' if getattr(param, 'uncertainty', 0.0) == 0.0 else param.uncertainty,
                'units': param.units,
            }
            for param in free_params
        ]

        df = pd.DataFrame(params)

        # Ensure columns exist
        expected_cols = ["cif block", "cif parameter", "value", "error", "units"]
        valid_cols = [col for col in expected_cols if col in df.columns]

        if not valid_cols:
            print("No valid columns found in free parameters DataFrame.")
            return

        df = df[valid_cols]

        try:
            print(tabulate(df, headers="keys", tablefmt="fancy_outline", showindex=False))
        except ImportError:
            print(df.to_string(index=False))

        return free_params

    def show_current_calculator(self):
        print(paragraph("Current calculator"))
        print(self.current_calculator)

    @staticmethod
    def show_available_calculators():
        CalculatorFactory.show_available_calculators()

    @property
    def current_calculator(self):
        return self._calculator_key

    @current_calculator.setter
    def current_calculator(self, calculator_name):
        if calculator_name not in CalculatorFactory.list_available_calculators():
            raise ValueError(
                f"Unknown calculator '{calculator_name}'. Available calculators: {CalculatorFactory.list_available_calculators()}"
            )
        self.calculator = CalculatorFactory.create_calculator(calculator_name)
        self._calculator_key = calculator_name
        print(paragraph("Current calculator changed to"))
        print(self.current_calculator)

    def show_current_minimizer(self):
        print(paragraph("Current minimizer"))
        print(self.current_minimizer)

    @staticmethod
    def show_available_minimizers():
        MinimizerFactory.show_available_minimizers()

    @property
    def current_minimizer(self):
        return self.fitter.selection if self.fitter else None

    @current_minimizer.setter
    def current_minimizer(self, selection):
        self.fitter = DiffractionMinimizer(selection)
        print(paragraph(f"Current minimizer changed to"))
        print(self.current_minimizer)

    @property
    def refinement_strategy(self):
        return self._refinement_strategy

    @refinement_strategy.setter
    def refinement_strategy(self, strategy):
        if strategy not in ['single', 'combined']:
            raise ValueError("Refinement strategy must be either 'single' or 'combined'")
        self._refinement_strategy = strategy
        print(paragraph("Current refinement strategy changed to"))
        print(self._refinement_strategy)

    def show_available_refinement_strategies(self):
        strategies = [
            {"Strategy": "single", "Description": "Refine each experiment separately"},
            {"Strategy": "combined", "Description": "Perform joint refinement of all experiments"},
            {"Strategy": "sequential*", "Description": "Refine experiments one after another"},
            {"Strategy": "decoupled*", "Description": "Refine all experiments independently"},
        ]
        print(paragraph("Available refinement strategies"))
        print(tabulate(strategies, headers="keys", tablefmt="fancy_outline", showindex=False))
        print("* Strategies marked with an asterisk are not implemented yet.")

    def show_current_refinement_strategy(self):
        print(paragraph("Current refinement strategy"))
        print(self.refinement_strategy)

    def calculate_pattern(self, expt_id):
        # Pattern is calculated for the given experiment
        experiment = self.project.experiments[expt_id]
        sample_models = self.project.sample_models
        calculated_pattern = self.calculator.calculate_pattern(sample_models, experiment)
        return calculated_pattern

    def show_calc_chart(self, expt_id, x_min=None, x_max=None):
        experiment = self.project.experiments[expt_id]

        if experiment.datastore.pattern.calc is None:
            print(info(f"No calculated pattern found for '{expt_id}'. Calculating."))
            self.calculate_pattern(expt_id)

        pattern = experiment.datastore.pattern

        plotter = ChartPlotter()
        plotter.plot(
            y_values_list=[pattern.calc],
            x_values=pattern.x,
            x_min=x_min,
            x_max=x_max,
            title=paragraph(f"Calculated data for experiment '{expt_id}'"),
            labels=['calc']
        )

    def show_meas_vs_calc_chart(self,
                                expt_id,
                                x_min=None,
                                x_max=None,
                                show_residual=False,
                                chart_height=DEFAULT_HEIGHT):
        experiment = self.project.experiments[expt_id]

        self.calculate_pattern(expt_id)

        pattern = experiment.datastore.pattern

        if pattern.meas is None or pattern.calc is None or pattern.x is None:
            print(f"No data available for {expt_id}. Cannot display chart.")
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
            title=paragraph(f"Measured vs Calculated data for experiment '{expt_id}'"),
            labels=labels
        )

    def fit(self):
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
        print(paragraph(f"Fitting using refinement strategy '{self.refinement_strategy}'"))
        experiment_ids = list(experiments._items.keys())

        if self.refinement_strategy == 'combined':
            print(paragraph(f"Using all experiments {experiment_ids} for joint refinement."))
            self.fitter.fit(sample_models, experiments, calculator)
        elif self.refinement_strategy == 'single':
            for expt_id in list(experiments._items.keys()):
                print(paragraph(f"Using experiment '{expt_id}' for decoupled refinement."))
                experiment = experiments[expt_id]
                dummy_experiments = Experiments()
                dummy_experiments.add(experiment)
                self.fitter.fit(sample_models, dummy_experiments, calculator)
        else:
            raise NotImplementedError(f"Refinement strategy {self.refinement_strategy} not implemented yet.")

        # After fitting, get the results
        self.fit_results = self.fitter.results
