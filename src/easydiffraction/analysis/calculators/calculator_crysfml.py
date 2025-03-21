try:
    from pycrysfml import cfml_py_utilities
except ImportError:
    cryspy = None
    print('Warning: pycrysfml module not found. This calculator will not work.')

from .base import CalculatorBase


class CrysfmlCalculator(CalculatorBase):
    """
    Adapter for Crysfml library.
    """

    @property
    def name(self):
        return "Crysfml"

    def calculate_hkl(self, sample_models, experiments):
        # Call Crysfml to calculate structure factors
        raise NotImplementedError("HKL calculation is not implemented for CryspyCalculator.")

    def calculate_pattern(self, sample_models, experiments):
        # Call Crysfml to calculate diffraction pattern
        crysfml_dict = self._crysfml_dict(sample_models, experiments)
        _, y = cfml_py_utilities.cw_powder_pattern_from_dict(crysfml_dict)
        return y

    def _crysfml_dict(self, sample_models, experiments):
        # Convert EasyDiffraction sample_models and experiments into Crysfml dict
        pass

    def _convert_sample_models_to_dict(self, sample_models):
        pass

    def _convert_experiment_to_dict(self, experiment):
        pass