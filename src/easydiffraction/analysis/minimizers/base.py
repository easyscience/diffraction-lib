from abc import ABC, abstractmethod

class MinimizerBase(ABC):
    @abstractmethod
    def fit(self, parameters, sample_models, experiments, calculator=None):
        pass

    @abstractmethod
    def results(self):
        pass