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
    def calculate_hkl(self, sample_models, experiments):
        pass

    @abstractmethod
    def calculate_pattern(self, sample_models, experiments):
        pass