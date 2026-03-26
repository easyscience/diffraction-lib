# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""PDF calculation backend using diffpy.pdffit2 if available.

The class adapts the engine to EasyDiffraction calculator interface and
silences stdio on import to avoid noisy output in notebooks and logs.
"""

import os
import re
from pathlib import Path
from typing import Optional

import numpy as np

from easydiffraction.analysis.calculators.base import CalculatorBase
from easydiffraction.analysis.calculators.factory import CalculatorFactory
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.datablocks.experiment.item.base import ExperimentBase
from easydiffraction.datablocks.structure.item.base import Structure

try:
    from diffpy.pdffit2 import PdfFit
    from diffpy.pdffit2 import redirect_stdout
    from diffpy.structure.parsers.p_cif import P_cif as pdffit_cif_parser

    # Silence the C++ engine output while keeping the handle open
    _pdffit_devnull: Optional[object]
    with Path(os.devnull).open('w') as _tmp_devnull:
        # Duplicate file descriptor so the handle remains
        # valid after the context
        _pdffit_devnull = os.fdopen(os.dup(_tmp_devnull.fileno()), 'w')
    redirect_stdout(_pdffit_devnull)
    # TODO: Add the following print to debug mode
    # print("✅ 'pdffit' calculation engine is successfully imported.")
except ImportError:
    # TODO: Add the following print to debug mode
    # print("⚠️ 'pdffit' module not found. This calculation engine will
    # not be available.")
    PdfFit = None


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
        return 'pdffit'

    def calculate_structure_factors(self, structures: object, experiments: object) -> list:
        # PDF doesn't compute HKL but we keep interface consistent
        # Intentionally unused, required by public API/signature
        del structures, experiments
        print('[pdffit] Calculating HKLs (not applicable)...')
        return []

    def calculate_pattern(
        self,
        structure: Structure,
        experiment: ExperimentBase,
        called_by_minimizer: bool = False,
    ) -> None:
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
        pattern = np.array(pattern)

        return pattern
