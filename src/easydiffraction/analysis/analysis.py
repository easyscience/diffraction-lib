from .calculators.factory import CalculatorFactory
from easydiffraction.utils.chart_plotter import ChartPlotter


class Analysis:
    _calculator = CalculatorFactory.create_calculator('cryspy')

    def __init__(self, project):
        self.project = project
        self.calculator = Analysis._calculator  # Default calculator shared by project
        self._refinement_strategy = 'single'

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
        experiment = self.project.experiments[expt_id]
        sample_models = self.project.sample_models

        calculated_pattern = self.calculator.calculate_pattern(sample_models, experiment)
        experiment.datastore.pattern.calc = calculated_pattern

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

    def show_meas_vs_calc_chart(self, expt_id, x_min=None, x_max=None, show_residual=False):
        experiment = self.project.experiments[expt_id]

        if experiment.datastore.pattern.calc is None:
            print(f"No calculated pattern found for {expt_id}. Running calculation...")
            self.calculate_pattern(expt_id)

        pattern = experiment.datastore.pattern

        if pattern.meas is None or pattern.calc is None or pattern.x is None:
            print(f"No data available for {expt_id}. Cannot display chart.")
            return

        # Prepare series for plotting
        series = [pattern.meas, pattern.calc]
        labels = ['meas', 'calc']

        if show_residual:
            residual = pattern.meas - pattern.calc
            series.append(residual)
            labels.append('residual')

        plotter = ChartPlotter()
        plotter.plot(
            y_values_list=series,
            x_values=pattern.x,
            x_min=x_min,
            x_max=x_max,
            title=f"Measured vs Calculated diffraction pattern for {expt_id}",
            labels=labels
        )
