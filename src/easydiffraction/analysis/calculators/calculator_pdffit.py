from .base import CalculatorBase

class PdffitCalculator(CalculatorBase):
    """
    Wrapper for Pdffit library.
    """

    @property
    def name(self):
        return "Pdffit"

    def calculate_structure_factors(self, sample_models, experiments):
        # PDF doesn't compute HKL but we keep interface consistent
        print("[Pdffit] Calculating HKLs (not applicable)...")
        return []

    def calculate_pattern(self, sample_models, experiments):
        print("[Pdffit] Calculating PDF pattern...")
        return []