from .minimizers.factory import MinimizerFactory

class DiffractionMinimizer:
    """
    Handles the fitting workflow using a pluggable minimizer.
    """

    def __init__(self, engine='lmfit'):
        self.minimizer = MinimizerFactory.create_minimizer(engine)
        self.results = None

    def fit(self, sample_models, experiments, calculator):
        """
        Run the least-squares minimizers.
        Combines experiments and links shared sample model parameters.
        """

        print(f"Starting {self.minimizer.__class__.__name__} fitting process...")

        def residual_func(params):
            """
            Combines residuals from all experiments.
            """
            residuals = []
            for exp in experiments.list():
                calc_pattern = calculator.calculate_pattern(sample_models, exp)
                meas_pattern = exp.datastore.pattern.meas

                # Residual: difference between measured and calculated patterns
                residual = meas_pattern - calc_pattern
                residuals.extend(residual.tolist())

            return residuals

        # Get fit parameters from sample_models and experiments
        fit_params = sample_models.get_refinable_parameters() + experiments.get_refinable_parameters()

        # Convert to lmfit.Parameters if using lmfit
        if isinstance(self.minimizer, MinimizerFactory.create_minimizer('lmfit').__class__):
            from lmfit import Parameters
            lmfit_params = Parameters()
            for param in fit_params:
                lmfit_params.add(param.cif_name, value=param.value, vary=param.vary)
            self.results = self.minimizer.fit(residual_func, lmfit_params)

        # Convert to bumps parameters if using bumps
        elif isinstance(self.minimizer, MinimizerFactory.create_minimizer('bumps').__class__):
            # Bumps typically needs an objective function that returns residual sum of squares.
            # More complex, but can be added here.
            self.results = self.minimizer.fit(residual_func, fit_params)

        print("Fitting complete.")