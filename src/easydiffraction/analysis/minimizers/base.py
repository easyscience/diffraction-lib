from abc import ABC, abstractmethod

class MinimizerBase(ABC):
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

    @abstractmethod
    def _prepare_parameters(self, parameters):
        """
        Prepare the parameters for the minimizer engine.
        """
        pass

    @staticmethod
    @abstractmethod
    def _sync_parameters(engine_params, parameters):
        """
        Synchronize engine parameter values back to Parameter instances.
        """
        pass

    @abstractmethod
    def _objective_function(self, engine_params, parameters, sample_models, experiments, calculator):
        """
        Objective function to be minimized.
        """
        pass

    def _collect_free_parameters(self, sample_models, experiments):
        """
        Collect free parameters from sample models and experiments.
        """
        return sample_models.get_free_params() + experiments.get_free_params()
