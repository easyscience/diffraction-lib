from abc import ABC, abstractmethod

class BaseMinimizer(ABC):
    @abstractmethod
    def fit(self, residual_func, fit_params):
        pass