from .minimizers.factory import MinimizerFactory
import lmfit


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

    def _residual_function(self, params, sample_models, experiments, calculator):
        """
        Computes residuals for all experiments.

        :param params: Current parameters for fitting.
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
        print(f"\n🚀 Starting {self.engine.upper()} fitting process...")

        fit_params = (
                sample_models.get_free_params() +  # <<< FIXED HERE
                experiments.get_free_params()  # <<< FIXED HERE
        )

        if not fit_params:
            print("⚠️ No parameters selected for refinement. Aborting fit.")
            return

        # Residual function partial to minimize passing of sample_models etc.
        def residual_func(params):
            return self._residual_function(params, sample_models, experiments, calculator)

        if self.engine == 'lmfit':
            self.results = self.minimizer.fit(
                fit_params,
                sample_models,
                experiments,
                calculator
            )

        elif self.engine == 'bumps':
            self.results = self.minimizer.fit(residual_func, fit_params)

        else:
            raise ValueError(f"Unsupported minimizer engine: {self.engine}")

        print("✅ Fitting complete.\n")
        self._display_results()

    def _display_results(self):
        """
        Prints a summary of the fitting results.
        """
        if self.results is None:
            print("⚠️ No fitting results to display.")
            return

        print("📊 Fitting Results:")
        # Custom result display depending on engine:
        if self.engine == 'lmfit':
            print(lmfit.fit_report(self.results))  # lmfit fit_report is a function, not a method of MinimizerResult
        elif self.engine == 'bumps':
            print(self.results)
        else:
            print(self.results)