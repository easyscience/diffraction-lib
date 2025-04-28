import tabulate
from typing import Dict, Type, List, Optional, Union, Any

from easydiffraction.utils.formatting import (
    paragraph,
    error
)
from .calculator_crysfml import CrysfmlCalculator
from .calculator_cryspy import CryspyCalculator
from .calculator_pdffit import PdffitCalculator
from .calculator_base import CalculatorBase


class CalculatorFactory:
    _potential_calculators: Dict[str, Dict[str, Union[str, Type[CalculatorBase]]]] = {
        'crysfml': {
            'description': 'CrysFML library for crystallographic calculations',
            'class': CrysfmlCalculator
        },
        'cryspy': {
            'description': 'CrysPy library for crystallographic calculations',
            'class': CryspyCalculator
        },
        'pdffit': {
            'description': 'PDFfit2 library for pair distribution function calculations',
            'class': PdffitCalculator,
        }
    }

    @classmethod
    def _supported_calculators(cls) -> Dict[str, Dict[str, Union[str, Type[CalculatorBase]]]]:
        return {
            name: cfg
            for name, cfg in cls._potential_calculators.items()
            if cfg['class']().engine_imported  # instantiate and check the @property
        }

    @classmethod
    def list_supported_calculators(cls) -> List[str]:
        return list(cls._supported_calculators().keys())

    @classmethod
    def show_supported_calculators(cls) -> None:
        header: List[str] = ["Calculator", "Description"]
        table_data: List[List[str]] = []

        for name, config in cls._supported_calculators().items():
            description: str = config.get('description', 'No description provided.')
            table_data.append([name, description])

        print(paragraph("Supported calculators"))
        print(tabulate.tabulate(
            table_data,
            headers=header,
            tablefmt="fancy_outline",
            numalign="left",
            stralign="left",
            showindex=False
        ))

    @classmethod
    def create_calculator(cls, calculator_name: str) -> Optional[CalculatorBase]:
        config = cls._supported_calculators().get(calculator_name)
        if not config:
            print(error(f"Unknown calculator '{calculator_name}'"))
            print(f'Supported calculators: {cls.list_supported_calculators()}')
            return None

        return config['class']()

    @classmethod
    def register_calculator(cls, calculator_type: str, calculator_cls: Type[CalculatorBase], description: str = 'No description provided.') -> None:
        cls._potential_calculators[calculator_type] = {
            'class': calculator_cls,
            'description': description
        }

    @classmethod
    def register_minimizer(cls, name: str, minimizer_cls: Type[Any], method: Optional[str] = None, description: str = 'No description provided.') -> None:
        cls._available_minimizers[name] = {
            'engine': name,
            'method': method,
            'description': description,
            'class': minimizer_cls
        }
