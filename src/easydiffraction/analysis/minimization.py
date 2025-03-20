from .minimizers.factory import MinimizerFactory


class DiffractionMinimizer:
    """
    Handles the fitting workflow using a pluggable minimizer.
    """

    def __init__(self, engine='lmfit'):
        """
        Initialize the minimizer.

        :param engine: Minimization engine to use ('lmfit', 'bumps', etc.)
        """
        self.engine = engine
        self.minimizer = MinimizerFactory.create_minimizer(engine)
        self.results = None

    def _residual_function(self, sample_models, experiments, calculator):
        """
        Computes residuals for all experiments.

        :param sample_models: SampleModels instance.
        :param experiments: Experiments instance.
        :param calculator: Calculator instance.
        :return: List of residuals.
        """
        residuals = []

        for exp in experiments.list():
            # Calculate the pattern for the current experiment
            calc_pattern = calculator.calculate_pattern(sample_models, exp)

            # Measured pattern
            meas_pattern = exp.datastore.pattern.meas

            # Compute residual (difference between measured and calculated)
            residual = meas_pattern - calc_pattern
            residuals.extend(residual.tolist())

        return residuals


    def fit(self, sample_models, experiments, calculator):
        """
        Run the fitting process.

        :param sample_models: SampleModels instance.
        :param experiments: Experiments instance.
        :param calculator: Calculator instance.
        """
        print(f"\n🚀 Starting fitting process with {self.engine.upper()}...")

        parameters = (
            sample_models.get_free_params() +
            experiments.get_free_params()
        )

        if not parameters:
            print("⚠️ No parameters selected for refinement. Aborting fit.")
            return None

        self.results = self.minimizer.fit(
            sample_models,
            experiments,
            calculator
        )

        print("✅ Fitting complete.\n")
        self._display_results()

    def _display_results(self):
        """
        Prints a summary of the fitting results.
        """
        if self.results is None:
            print("⚠️ No fitting results to display.")
            return

        self.minimizer.display_results(self.results)