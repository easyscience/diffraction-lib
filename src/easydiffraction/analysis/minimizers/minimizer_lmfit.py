from .base import BaseMinimizer
from lmfit import minimize, Parameters

class LmfitMinimizer(BaseMinimizer):
    def __init__(self):
        self.results = None

    def fit(self, residual_func, fit_params):
        """
        Performs least-squares fitting using lmfit.
        :param residual_func: Function that returns residuals.
        :param fit_params: lmfit.Parameters object.
        :return: Minimizer result
        """
        print("Running LMFIT Minimizer...")
        result = minimize(residual_func, fit_params)
        self.results = result
        print("LMFIT Minimization complete.")
        return result