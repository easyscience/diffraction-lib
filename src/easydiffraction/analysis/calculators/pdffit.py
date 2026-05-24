# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
PDF calculation backend using diffpy.pdffit2 if available.

The class adapts the engine to EasyDiffraction calculator interface and
silences stdio on import to avoid noisy output in notebooks and logs.
"""

import os
import re
from pathlib import Path

import numpy as np

from easydiffraction.analysis.calculators.base import CalculatorBase
from easydiffraction.analysis.calculators.factory import CalculatorFactory
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.datablocks.experiment.item.base import ExperimentBase
from easydiffraction.datablocks.structure.item.base import Structure


def _open_pdffit_devnull() -> object:
    """Open a durable devnull handle for PDFfit stdout redirection."""
    with Path(os.devnull).open('w', encoding='utf-8') as tmp_devnull:
        return os.fdopen(os.dup(tmp_devnull.fileno()), 'w')


try:
    from diffpy.pdffit2 import PdfFit
    from diffpy.pdffit2 import redirect_stdout
    from diffpy.structure.parsers.p_cif import P_cif as pdffit_cif_parser

    _pdffit_devnull = _open_pdffit_devnull()
    redirect_stdout(_pdffit_devnull)
    # TODO: Add the following print to debug mode
    # print("✅ 'pdffit' calculation engine is successfully imported.")
except ImportError:
    # TODO: Add the following print to debug mode
    # print("⚠️ 'pdffit' module not found. This calculation engine will
    # not be available.")
    PdfFit = None
    redirect_stdout = None
    pdffit_cif_parser = None
    _pdffit_devnull = None


@CalculatorFactory.register
class PdffitCalculator(CalculatorBase):
    """Wrapper for Pdffit library."""

    type_info = TypeInfo(
        tag='pdffit',
        description='PDFfit2 for pair distribution function calculations',
    )
    engine_imported: bool = PdfFit is not None

    @property
    def name(self) -> str:
        """Short identifier of this calculator engine."""
        return 'pdffit'

    def calculate_structure_factors(  # noqa: PLR6301
        self,
        structures: object,
        experiments: object,
    ) -> list:
        """
        Return an empty list; PDF does not compute structure factors.

        Parameters
        ----------
        structures : object
            Unused; kept for interface consistency.
        experiments : object
            Unused; kept for interface consistency.

        Returns
        -------
        list
            An empty list.
        """
        # PDF doesn't compute HKL but we keep interface consistent
        # Intentionally unused, required by public API/signature
        del structures, experiments
        print('[pdffit] Calculating HKLs (not applicable)...')
        return []

    def calculate_pattern(  # noqa: PLR6301
        self,
        structure: Structure,
        experiment: ExperimentBase,
        *,
        called_by_minimizer: bool = False,
    ) -> None:
        """
        Calculate the PDF pattern using PDFfit2.

        Parameters
        ----------
        structure : Structure
            The structure object supplying atom sites and cell
            parameters.
        experiment : ExperimentBase
            The experiment object supplying instrument and peak
            parameters.
        called_by_minimizer : bool, default=False
            Unused; kept for interface consistency.
        """
        # Intentionally unused, required by public API/signature
        del called_by_minimizer

        # Create PDF calculator object
        calculator = PdfFit()

        # ---------------------------
        # Set structure parameters
        # ---------------------------

        # TODO: move CIF v2 -> CIF v1 conversion to a separate module
        # Convert the structure to CIF supported by PDFfit
        cif_string_v2 = structure.as_cif
        # convert to version 1 of CIF format
        # this means: replace all dots with underscores for
        # cases where the dot is surrounded by letters on both sides.
        pattern = r'(?<=[a-zA-Z])\.(?=[a-zA-Z])'
        cif_string_v1 = re.sub(pattern, '_', cif_string_v2)

        # Create the PDFit structure
        pdffit_structure = pdffit_cif_parser().parse(cif_string_v1)

        # Set all model parameters:
        # space group, cell parameters, and atom sites (including ADPs)
        calculator.add_structure(pdffit_structure)

        # -------------------------
        # Set experiment parameters
        # -------------------------

        # Set some peak-related parameters
        calculator.setvar('pscale', experiment.linked_phases[structure.name].scale.value)
        calculator.setvar('delta1', experiment.peak.sharp_delta_1.value)
        calculator.setvar('delta2', experiment.peak.sharp_delta_2.value)
        calculator.setvar('spdiameter', experiment.peak.damp_particle_diameter.value)

        # Data
        x = list(experiment.data.x)
        y_noise = list(np.zeros_like(x))

        # Assign the data to the PDFfit calculator
        calculator.read_data_lists(
            stype=experiment.type.radiation_probe.value[0].upper(),
            qmax=experiment.peak.cutoff_q.value,
            qdamp=experiment.peak.damp_q.value,
            r_data=x,
            Gr_data=y_noise,
        )

        # qbroad must be set after read_data_lists
        calculator.setvar('qbroad', experiment.peak.broad_q.value)

        # -----------------
        # Calculate pattern
        # -----------------

        # Calculate the PDF pattern
        calculator.calc()

        # Get the calculated PDF pattern
        pattern = calculator.getpdf_fit()
        return np.array(pattern)
