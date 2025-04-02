import pandas as pd
from tabulate import tabulate

from easydiffraction.utils.formatting import paragraph, info, error
from easydiffraction.utils.chart_plotter import ChartPlotter, DEFAULT_HEIGHT
from easydiffraction.experiments.experiments import Experiments

from .calculators.calculator_factory import CalculatorFactory
from .minimization import DiffractionMinimizer
from .minimizers.minimizer_factory import MinimizerFactory


class Analysis:
    _calculator = CalculatorFactory.create_calculator('cryspy')

    def __init__(self, project):
        self.project = project
        self.calculator = Analysis._calculator  # Default calculator shared by project
        self._calculator_key = 'cryspy'  # Added to track the current calculator
        self._fit_mode = 'single'
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
    def show_supported_calculators():
        CalculatorFactory.show_supported_calculators()

    @property
    def current_calculator(self):
        return self._calculator_key

    @current_calculator.setter
    def current_calculator(self, calculator_name):
        calculator = CalculatorFactory.create_calculator(calculator_name)
        if calculator is None:
            return
        self.calculator = calculator
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
    def fit_mode(self):
        return self._fit_mode

    @fit_mode.setter
    def fit_mode(self, strategy):
        if strategy not in ['single', 'joint']:
            raise ValueError("Fit mode must be either 'single' or 'joint'")
        self._fit_mode = strategy
        if strategy == 'joint':
            self.joint_fit = {}
        print(paragraph("Current ffit mode changed to"))
        print(self._fit_mode)

    def show_available_fit_modes(self):
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

    def show_current_fit_mode(self):
        print(paragraph("Current ffit mode"))
        print(self.fit_mode)

    def calculate_pattern(self, expt_id):
        # Pattern is calculated for the given experiment
        experiment = self.project.experiments[expt_id]
        sample_models = self.project.sample_models
        calculated_pattern = self.calculator.calculate_pattern(sample_models, experiment)
        return calculated_pattern

    def show_calc_chart(self, expt_id, x_min=None, x_max=None):
        self.calculate_pattern(expt_id)

        experiment = self.project.experiments[expt_id]
        pattern = experiment.datastore.pattern

        plotter = ChartPlotter()
        plotter.plot(
            y_values_list=[pattern.calc],
            x_values=pattern.x,
            x_min=x_min,
            x_max=x_max,
            title=paragraph(f"Calculated data for experiment 🔬 '{expt_id}'"),
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
            title=paragraph(f"Measured vs Calculated data for experiment 🔬 '{expt_id}'"),
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
        experiment_ids = list(experiments._items.keys())

        if self.fit_mode == 'joint':
            print(paragraph(f"Using all experiments 🔬 {experiment_ids} for '{self.fit_mode}' fitting"))
            self.fitter.fit(sample_models, experiments, calculator, weights=self.joint_fit)
        elif self.fit_mode == 'single':
            for expt_id in list(experiments._items.keys()):
                print(paragraph(f"Using experiment 🔬 '{expt_id}' for '{self.fit_mode}' fitting"))
                experiment = experiments[expt_id]
                dummy_experiments = Experiments()
                dummy_experiments.add(experiment)
                self.fitter.fit(sample_models, dummy_experiments, calculator)
        else:
            raise NotImplementedError(f"Fit mode {self.fit_mode} not implemented yet.")

        # After fitting, get the results
        self.fit_results = self.fitter.results

    def as_cif(self):
        lines = []
        lines.append(f"_analysis.calculator_engine  {self.current_calculator}")
        lines.append(f"_analysis.fitting_engine  {self.current_minimizer}")
        lines.append(f"_analysis.fit_mode  {self.fit_mode}")

        return "\n".join(lines)

    def show_as_cif(self):
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
