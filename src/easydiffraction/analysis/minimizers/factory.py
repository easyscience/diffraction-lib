from .minimizer_lmfit import LmfitMinimizer
from .minimizer_bumps import BumpsMinimizer
from .minimizer_dfols import DfolsMinimizer  # NEW IMPORT

class MinimizerFactory:
    _available_minimizers = {
        'lmfit (leastsq)': {'engine': 'lmfit', 'method': 'leastsq'},
        'lmfit (least_squares)': {'engine': 'lmfit', 'method': 'least_squares'},
        'bumps (lm)': {'engine': 'bumps', 'method': 'lm'},
        'dfols (leastsq)': {'engine': 'dfols', 'method': 'leastsq'}
    }

    @staticmethod
    def list_available_minimizers():
        return list(MinimizerFactory._available_minimizers.keys())

    @staticmethod
    def show_available_minimizers():
        for name in MinimizerFactory.list_available_minimizers():
            print(name)

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
            return DfolsMinimizer(method=config['method'])  # NEW BLOCK

        raise ValueError(f"Unsupported minimizer engine '{config['engine']}'")