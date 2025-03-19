from easyscience.fitting.multi_fitter import MultiFitter

class DiffractionMinimizer:
    """
    Optimization handler for fitting workflows.
    """

    def __init__(self):
        self.fitter = MultiFitter()
        self.results = None

    def fit(self, fit_params, sample_models, experiments, calculator):
        """
        Run the minimization process using the selected fitter.
        """
        print("Starting fitting process...")

        def resid_func(params):
            # Example of residuals calculation
            residuals = []
            for exp in experiments.list():
                calc_pattern = calculator.calculate_pattern(sample_models, exp)
                meas_pattern = exp.meas_data
                residual = meas_pattern - calc_pattern
                residuals.extend(residual)
            return residuals

        self.results = self.fitter.fit(resid_func, fit_params)

        print("Fitting complete.")