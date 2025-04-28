# SPDX-FileCopyrightText: 2025 EasyDiffraction contributors
# SPDX-License-Identifier: BSD-3-Clause
# © 2021-2025 Contributors to the EasyDiffraction project <https://github.com/EasyScience/EasyDiffraction>

import os
import re
import numpy as np
from .calculator_base import CalculatorBase
from easydiffraction.utils.formatting import warning

try:
    from diffpy.pdffit2 import PdfFit as pdffit
    from diffpy.pdffit2 import redirect_stdout
    from diffpy.structure.parsers.p_cif import P_cif as pdffit_cif_parser
    redirect_stdout(open(os.path.devnull, 'w')) # silence the C++ engine output
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
        return "pdffit"

    def calculate_structure_factors(self, sample_models, experiments):
        # PDF doesn't compute HKL but we keep interface consistent
        print("[pdffit] Calculating HKLs (not applicable)...")
        return []

    def _calculate_single_model_pattern(self,
                                        sample_model,
                                        experiment,
                                        called_by_minimizer=False):

        # Create PDF calculator object
        calculator = pdffit()

        # ---------------------------
        # Set sample model parameters
        # ---------------------------

        # TODO: move CIF v2 -> CIF v1 conversion to a separate module
        # Convert the sample model to CIF supported by PDFfit
        v2_cif_string = sample_model.as_cif()
        # convert to version 1 of CIF format
        # this means: replace all dots with underscores for
        # cases where the dot is surrounded by letters on both sides.
        pattern = r"(?<=[a-zA-Z])\.(?=[a-zA-Z])"
        v1_cif_string =  re.sub(pattern, "_", v2_cif_string)

        # Create the PDFit structure
        structure = pdffit_cif_parser().parse(v1_cif_string)

        # Set all model parameters:
        # space group, cell parameters, and atom sites (including ADPs)
        calculator.add_structure(structure)

        # -------------------------
        # Set experiment parameters
        # -------------------------

        # Set some peak-related parameters
        calculator.setvar('pscale', experiment.linked_phases[sample_model.name].scale.value)
        calculator.setvar('delta1', experiment.peak.sharp_delta_1.value)
        calculator.setvar('delta2', experiment.peak.sharp_delta_2.value)
        calculator.setvar('spdiameter', experiment.peak.damp_particle_diameter.value)

        # Data
        pattern = experiment.datastore.pattern
        x = list(pattern.x)
        y_noise = list(np.zeros_like(pattern.x))

        # Assign the data to the PDFfit calculator
        calculator.read_data_lists(stype=experiment.type.radiation_probe.value[0].upper(),
                                   qmax=experiment.peak.cutoff_q.value,
                                   qdamp=experiment.peak.damp_q.value,
                                   r_data=x,
                                   Gr_data=y_noise)

        # qbroad must be set after read_data_string
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
