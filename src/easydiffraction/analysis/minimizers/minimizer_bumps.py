from .base import BaseMinimizer
import bumps.names as bump
from bumps.fitters import FitDriver

class BumpsMinimizer(BaseMinimizer):
    def __init__(self):
        self.results = None

    def fit(self, residual_func, fit_params):
        """
        Performs least-squares fitting using bumps.
        :param residual_func: Function that returns residuals.
        :param fit_params: bumps.Parameter objects list.
        :return: FitDriver result
        """
        print("Running BUMPS Minimizer...")

        # Define problem
        problem = bump.FitProblem(residual_func)

        # Setup fitter
        driver = FitDriver(problem, method='lm')  # Levenberg-Marquardt
        driver.fit()

        self.results = driver
        print("BUMPS Minimization complete.")
        return driver