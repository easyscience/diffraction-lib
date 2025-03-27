import tabulate

from easydiffraction.utils.formatting import paragraph

from .minimizer_lmfit import LmfitMinimizer
from .minimizer_bumps import BumpsMinimizer
from .minimizer_dfols import DfolsMinimizer

class MinimizerFactory:
    _available_minimizers = {
        'lmfit': {
            'engine': 'lmfit',
            'method': 'leastsq',
            'description': 'LMFIT library using the default Levenberg-Marquardt least squares method',
            'class': LmfitMinimizer
        },
        'lmfit (leastsq)': {
            'engine': 'lmfit',
            'method': 'leastsq',
            'description': 'LMFIT library with Levenberg-Marquardt least squares method',
            'class': LmfitMinimizer
        },
        'lmfit (least_squares)': {
            'engine': 'lmfit',
            'method': 'least_squares',
            'description': 'LMFIT library with SciPy’s trust region reflective algorithm',
            'class': LmfitMinimizer
        },
        'dfols': {
            'engine': 'dfols',
            'method': None,
            'description': 'DFO-LS library for derivative-free least-squares optimization',
            'class': DfolsMinimizer
        }
    }

    @classmethod
    def list_available_minimizers(cls):
        return list(cls._available_minimizers.keys())

    @classmethod
    def show_available_minimizers(cls):
        header = ["Minimizer", "Description"]
        table_data = []

        for name, config in cls._available_minimizers.items():
            description = config.get('description', 'No description provided.')
            table_data.append([name, description])

        print(paragraph("Available minimizers"))
        print(tabulate.tabulate(
            table_data,
            headers=header,
            tablefmt="fancy_outline",
            numalign="left",
            stralign="left",
            showindex=False
        ))

    @classmethod
    def create_minimizer(cls, selection: str):
        config = cls._available_minimizers.get(selection)
        if not config:
            raise ValueError(f"Unknown minimizer '{selection}'. Use one of {cls.list_available_minimizers()}")

        minimizer_class = config.get('class')
        method = config.get('method')

        kwargs = {}
        if method is not None:
            kwargs['method'] = method

        return minimizer_class(**kwargs)

    @classmethod
    def register_minimizer(cls, name, minimizer_cls, method=None, description='No description provided.'):
        cls._available_minimizers[name] = {
            'engine': name,
            'method': method,
            'description': description,
            'class': minimizer_cls
        }
