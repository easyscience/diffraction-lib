import numpy as np
from scipy.interpolate import interp1d

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

        # Get x-values from measured pattern
        x_points = experiment.datastore.pattern.x

        # Interpolate background from control points (experiment.background)
        if experiment.background.points:
            background_points = np.array(experiment.background.points)
            bg_x, bg_y = background_points[:, 0], background_points[:, 1]

            # Create interpolation function
            interp_func = interp1d(
                bg_x, bg_y,
                kind='linear',
                bounds_error=False,
                fill_value=(bg_y[0], bg_y[-1])
            )
            interpolated_bkg = interp_func(x_points)

            # Save background to datastore
            experiment.datastore.pattern.bkg = interpolated_bkg
        else:
            interpolated_bkg = 0
            experiment.datastore.pattern.bkg = np.zeros_like(x_points)

        # Calculate diffraction pattern (without background)
        calculated_pattern = self.calculator.calculate_pattern(sample_models, experiment)

        # Add background to calculated pattern
        calculated_pattern_with_bkg = calculated_pattern + interpolated_bkg

        # Store the final calculated pattern
        experiment.datastore.pattern.calc = calculated_pattern_with_bkg

        return calculated_pattern_with_bkg

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

        #if experiment.datastore.pattern.calc is None:
        #    print(f"No calculated pattern found for {expt_id}. Running calculation...")
        #    self.calculate_pattern(expt_id)
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

def fit(self):
    """
    Run the fitting process.
    """
    print("Starting the fitting process...")

    sample_models = self.project.sample_models
    experiments = self.project.experiments

    if not sample_models or not experiments:
        print("No sample models or experiments found in the project. Fit aborted.")
        return

    # Ensure the calculator is set
    if not self.calculator:
        raise ValueError("No calculator is set. Cannot run fit.")

    # Placeholder for actual fitting logic
    # In a real implementation, you would pass sample_models, experiments, and possibly a calculator to the optimizer
    print("Fitting algorithm would execute here...")
    print("Fit completed.")

    # Store dummy results for demonstration
    self.fit_results = {
        'rwp': 10.5,
        'chi2': 1.2,
        'params': {
            'lattice_a': 5.431,
            'lattice_c': 10.12
        }
    }

def show_fit_results(self):
    """
    Show fitting results after the fit.
    """
    if not hasattr(self, 'fit_results') or not self.fit_results:
        print("No fit results found. Run fit() first.")
        return

    print("\nFitting Results:")
    print(f"Rwp: {self.fit_results['rwp']:.2f}%")
    print(f"Chi^2: {self.fit_results['chi2']:.2f}")
    print("Refined Parameters:")
    for param, value in self.fit_results['params'].items():
        print(f"  {param}: {value}")