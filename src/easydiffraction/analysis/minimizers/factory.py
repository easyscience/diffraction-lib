import tabulate

from .minimizer_lmfit import LmfitMinimizer
from .minimizer_bumps import BumpsMinimizer
from .minimizer_dfols import DfolsMinimizer  # NEW IMPORT

class MinimizerFactory:
    _available_minimizers = {
        'lmfit': {
            'engine': 'lmfit',
            'method': 'leastsq',
            'description': 'LMFIT library using the default Levenberg-Marquardt least squares method.'
        },
        'lmfit (leastsq)': {
            'engine': 'lmfit',
            'method': 'leastsq',
            'description': 'LMFIT library with Levenberg-Marquardt least squares method.'
        },
        'lmfit (least_squares)': {
            'engine': 'lmfit',
            'method': 'least_squares',
            'description': 'LMFIT library with SciPy’s trust region reflective algorithm.'
        },
        'dfols': {
            'engine': 'dfols',
            'method': None,
            'description': 'DFOLS library for derivative-free least-squares optimization.'
        }
    }

    @staticmethod
    def list_available_minimizers():
        return list(MinimizerFactory._available_minimizers.keys())

    @staticmethod
    def show_available_minimizers():
        header = ["Minimizer", "Description"]
        table_data = []

        for name, config in MinimizerFactory._available_minimizers.items():
            description = config.get('description', 'No description provided.')
            table_data.append([name, description])

        print("\nAvailable Minimizers:\n")
        print(tabulate.tabulate(
            table_data,
            headers=header,
            tablefmt="fancy_outline",
            numalign="left",
            stralign="left",
            showindex=False
        ))

    @staticmethod
    def create_minimizer(selection: str):
        config = MinimizerFactory._available_minimizers.get(selection)
        if not config:
            raise ValueError(f"Unknown minimizer '{selection}'. Use one of {MinimizerFactory.list_available_minimizers()}")

        if config['engine'] == 'lmfit':
            return LmfitMinimizer(method=config['method'])
        elif config['engine'] == 'bumps':
            return BumpsMinimizer(method=config['method'])
        elif config['engine'] == 'dfols':
            return DfolsMinimizer()  # no method passed

        raise ValueError(f"Unsupported minimizer engine '{config['engine']}'")