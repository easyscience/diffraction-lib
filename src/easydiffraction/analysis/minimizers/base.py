from abc import ABC, abstractmethod


class MinimizerBase(ABC):
    @abstractmethod
    def prepare_parameters(self, parameters):
        """
        Prepare the parameters for the minimizer engine.
        """
        pass

    @abstractmethod
    def fit(self, sample_models, experiments, calculator):
        pass

    @abstractmethod
    def results(self):
        pass

    @staticmethod
    @abstractmethod
    def display_results(result):
        """
        Display results of the fitting procedure.
        """
        pass
