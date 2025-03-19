# factory.py                                          # Manages available calculators and their instantiation

from .calculator_crysfml import CrysfmlCalculator
from .calculator_cryspy import CryspyCalculator
from .calculator_pdffit import PdffitCalculator

class CalculatorFactory:
    """
    Registers and instantiates calculation engines.
    """

    _registry = {
        'crysfml': CrysfmlCalculator,
        'cryspy': CryspyCalculator,
        'pdffit': PdffitCalculator
    }

    @classmethod
    def create_calculator(cls, calculator_type):
        if calculator_type not in cls._registry:
            raise ValueError(
                f"Unknown calculator type '{calculator_type}'. Available: {list(cls._registry.keys())}"
            )
        return cls._registry[calculator_type]()

    @classmethod
    def register_calculator(cls, calculator_type, calculator_cls):
        cls._registry[calculator_type] = calculator_cls

    @classmethod
    def available_calculators(cls):
        return list(cls._registry.keys())

    @classmethod
    def show_available_calculators(cls):
        print("Available calculators:")
        for name in cls.available_calculators():
            print(f" - {name}")