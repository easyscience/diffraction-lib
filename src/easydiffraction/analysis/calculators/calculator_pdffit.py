from typing import Any, List, Union
from .calculator_base import CalculatorBase
from easydiffraction.utils.formatting import warning

from easydiffraction.sample_models.sample_models import SampleModels
from easydiffraction.experiments.experiments import Experiments
from easydiffraction.experiments.experiment import Experiment

try:
    from diffpy.pdffit2 import pdffit
except ImportError:
    print(warning('"pdffit" module not found. This calculator will not work.'))
    pdffit = None


class PdffitCalculator(CalculatorBase):
    """
    Wrapper for Pdffit library.
    """

    engine_imported: bool = pdffit is not None

    @property
    def name(self) -> str:
        return "PdfFit"

    def calculate_structure_factors(self, sample_models: SampleModels, experiments: Experiments) -> List[Any]:
        """
        PDF doesn't compute HKL but we keep the interface consistent.

        Args:
            sample_models: The sample models to calculate structure factors for.
            experiments: The experiments associated with the sample models.

        Returns:
            An empty list, as PDF doesn't compute HKLs.
        """
        print("[PdfFit] Calculating HKLs (not applicable)...")
        return []

    def _calculate_single_model_pattern(
        self,
        sample_model: SampleModels,
        experiment: Experiment,
        called_by_minimizer: bool = False
    ) -> Union[List[float], Any]:
        """
        Calculates the diffraction pattern for a single model using PdfFit.

        Args:
            sample_model: The sample model to calculate the pattern for.
            experiment: The experiment associated with the sample model.
            called_by_minimizer: Whether the calculation is called by a minimizer.

        Returns:
            An empty list or other placeholder, as this is not implemented yet.
        """
        print("[PdfFit] Not implemented yet.")
        return []
