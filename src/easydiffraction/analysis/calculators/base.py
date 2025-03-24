# base.py                                            # Abstract calculator base interface

from abc import ABC, abstractmethod

class CalculatorBase(ABC):
    """
    Base API for diffraction calculation engines.
    """

    @property
    @abstractmethod
    def name(self):
        pass

    @abstractmethod
    def calculate_structure_factors(self, sample_model, experiment):
        # Single sample model, single experiment
        pass

    @abstractmethod
    def calculate_pattern(self, sample_models, experiment):
        # Multiple sample models, single experiment
        pass