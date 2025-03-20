from .minimizer_lmfit import LmfitMinimizer
from .minimizer_bumps import BumpsMinimizer

class MinimizerFactory:
    @staticmethod
    def create_minimizer(engine: str = 'lmfit'):
        if engine == 'lmfit':
            return LmfitMinimizer()
        elif engine == 'bumps':
            return BumpsMinimizer()
        else:
            raise ValueError(f"Unknown minimizer engine '{engine}'")