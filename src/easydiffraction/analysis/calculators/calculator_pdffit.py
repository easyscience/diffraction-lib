from .calculator_base import CalculatorBase
from easydiffraction.utils.formatting import warning

try:
    from diffpy.pdffit2 import pdffit
except ImportError:
    print(warning('"pdffit" module not found. This calculator will not work.'))
    pdffit = None

class PdffitCalculator(CalculatorBase):
    """
    Wrapper for Pdffit library.
    """

    engine_imported = pdffit is not None

    @property
    def name(self):
        return "PdfFit"

    def calculate_structure_factors(self, sample_models, experiments):
        # PDF doesn't compute HKL but we keep interface consistent
        print("[PdfFit] Calculating HKLs (not applicable)...")
        return []

    def _calculate_single_model_pattern(self,
                                        sample_model,
                                        experiment,
                                        called_by_minimizer=False):
        print("[PdfFit] Not implemented yet.")
        return []
