import tabulate

from .calculator_crysfml import CrysfmlCalculator
from .calculator_cryspy import CryspyCalculator
from .calculator_pdffit import PdffitCalculator
from ...utils.utils import paragraph


class CalculatorFactory:
    _available_calculators = {
        'crysfml': {
            'description': 'CrysFML library for crystallographic calculations.',
            'class': CrysfmlCalculator
        },
        'cryspy': {
            'description': 'CrysPy library for crystallographic calculations.',
            'class': CryspyCalculator
        },
        'pdffit': {
            'description': 'PDFfit2 library for pair distribution function calculations.',
            'class': PdffitCalculator,
        }
    }

    @classmethod
    def list_available_calculators(cls):
        return list(cls._available_calculators.keys())

    @classmethod
    def show_available_calculators(cls):
        header = ["Calculator", "Description"]
        table_data = []

        for name, config in cls._available_calculators.items():
            description = config.get('description', 'No description provided.')
            table_data.append([name, description])

        print(paragraph("Available calculators"))
        print(tabulate.tabulate(
            table_data,
            headers=header,
            tablefmt="fancy_outline",
            numalign="left",
            stralign="left",
            showindex=False
        ))

    @classmethod
    def create_calculator(cls, selection):
        config = cls._available_calculators.get(selection)
        if not config:
            raise ValueError(f"Unknown calculator type '{selection}'. Available: {cls.list_available_calculators()}")

        calculator_class = config.get('class')

        return calculator_class()

    @classmethod
    def register_calculator(cls, calculator_type, calculator_cls, description='No description provided.'):
        cls._available_calculators[calculator_type] = {
            'class': calculator_cls,
            'description': description
        }

    @classmethod
    def register_minimizer(cls, name, minimizer_cls, method=None, description='No description provided.'):
        cls._available_minimizers[name] = {
            'engine': name,
            'method': method,
            'description': description,
            'class': minimizer_cls
        }
