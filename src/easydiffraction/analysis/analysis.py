import pandas as pd

from .calculators.factory import CalculatorFactory
from .minimization import DiffractionMinimizer
from .minimizers.minimizer_factory import MinimizerFactory
from easydiffraction.utils.chart_plotter import ChartPlotter, DEFAULT_HEIGHT


class Analysis:
    _calculator = CalculatorFactory.create_calculator('cryspy')

    def __init__(self, project):
        self.project = project
        self.calculator = Analysis._calculator  # Default calculator shared by project
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

        print("\nFree Parameters:")

        if not free_params:
            print("No free parameters found.")
            return

        # Convert Parameter objects to dicts for display
        params_data = [
            {
                'block': param.block_name,
                'cif_name': param.cif_name,
                'value': param.value,
                'error': '' if getattr(param, 'uncertainty', 0.0) == 0.0 else param.uncertainty
            }
            for param in free_params
        ]

        df = pd.DataFrame(params_data)

        if df.empty:
            print("No free parameters found.")
            return

        expected_cols = ["block", "cif_name", "value", "error"]
        valid_cols = [col for col in expected_cols if col in df.columns]

        if not valid_cols:
            print("No valid columns found in free parameters DataFrame.")
            return

        df = df[valid_cols]

        try:
            from tabulate import tabulate
            print(tabulate(df, headers="keys", tablefmt="psql", showindex=False))
        except ImportError:
            print(df.to_string(index=False))

        return free_params

    def show_available_calculators(self):
        CalculatorFactory.show_available_calculators()

    def set_calculator_by_name(self, calculator_name):
        if calculator_name not in CalculatorFactory.available_calculators():
            raise ValueError(
                f"Unknown calculator '{calculator_name}'. Available calculators: {CalculatorFactory.available_calculators()}"
            )

        self.calculator = CalculatorFactory.create_calculator(calculator_name)
        print(f"Calculator switched to: {calculator_name}")

    def calculate_pattern(self, expt_id):
        # Pattern is calculated for the given experiment
        experiment = self.project.experiments[expt_id]
        sample_models = self.project.sample_models
        calculated_pattern = self.calculator.calculate_pattern(sample_models, experiment)
        return calculated_pattern

    def show_calc_chart(self, expt_id, x_min=None, x_max=None):
        experiment = self.project.experiments[expt_id]

        if experiment.datastore.pattern.calc is None:
            print(f"No calculated pattern found for {expt_id}. Running calculation...")
            self.calculate_pattern(expt_id)

        pattern = experiment.datastore.pattern

        plotter = ChartPlotter()
        plotter.plot(
            y_values_list=[pattern.calc],
            x_values=pattern.x,
            x_min=x_min,
            x_max=x_max,
            title=f"Calculated diffraction pattern for {expt_id}",
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
            title=f"Measured vs Calculated diffraction pattern for '{expt_id}':",
            labels=labels
        )

    def fit(self):
        print(f"\nFitting:")

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
        self.fitter.fit(sample_models, experiments, calculator)

        # After fitting, get the results
        self.fit_results = self.fitter.results

    def show_current_minimizer(self):
        print(f"\nCurrent minimizer:\n{self.current_minimizer}")

    @staticmethod
    def show_available_minimizers():
        MinimizerFactory.show_available_minimizers()

    @property
    def current_minimizer(self):
        return self.fitter.selection if self.fitter else None

    @current_minimizer.setter
    def current_minimizer(self, selection):
        self.fitter = DiffractionMinimizer(selection)
        print(f"\nCurrent minimizer changed to:\n{self.current_minimizer}")
