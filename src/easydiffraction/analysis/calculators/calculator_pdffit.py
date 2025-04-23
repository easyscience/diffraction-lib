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

        # Convert the sample model to CIF supported by PDFfit
        v2_cif_string = sample_model.as_cif()
        # convert to version 1 of CIF format
        # this means: replace all dots with underscores for
        # cases where the dot is surrounded by letters on both sides.
        pattern = r"(?<=[a-zA-Z])\.(?=[a-zA-Z])"
        v1_cif_string =  re.sub(pattern, "_", v2_cif_string)

        # Create the PDFit structure
        structure = pdffit_cif_parser().parse(v1_cif_string)

        # Set space group, cell parameters, and atom site coordinates
        calculator.add_structure(structure)

        # Set ADP parameters
        for i_atom, atom in enumerate(sample_model.atom_sites):
            if not hasattr(atom, 'adp_type'):
                continue
            # TODO: the following should be Uiso, so needs changing
            # once the model has Uiso implemented
            if not atom.adp_type.value == 'Biso':
                continue
            Biso = atom.b_iso.value
            for i in range(1, 4):
                u_str = 'u{}{}({})'.format(i, i, i_atom + 1)
                calculator.setvar(u_str, Biso)

        # -------------------------
        # Set experiment parameters
        # -------------------------

        # Set the radiation probe for PDFfit
        radiation_probe = experiment.type.radiation_probe.value[0].upper()

        # Set instrument parameters
        calculator.setvar('pscale', experiment.linked_phases[sample_model.name].scale.value)
        calculator.setvar('delta1', experiment.instrument.delta1.value)
        calculator.setvar('delta2', experiment.instrument.delta2.value)
        calculator.setvar('spdiameter', experiment.instrument.spdiameter.value)

        # Extract other experiment-related parameters
        qmax = experiment.instrument.qmax.value
        qdamp = experiment.instrument.qdamp.value
        qbroad = experiment.instrument.qbroad.value

        # Data
        pattern = experiment.datastore.pattern
        x = list(pattern.x)
        y_noise = list(np.zeros_like(pattern.x))

        # Assign the data to the PDFfit calculator
        calculator.read_data_lists(radiation_probe,
                                   qmax,
                                   qdamp,
                                   x,
                                   y_noise)

        # qbroad must be set after read_data_string
        calculator.setvar('qbroad', qbroad)

        # -----------------
        # Calculate pattern
        # -----------------

        # Calculate the PDF pattern?
        calculator.calc()

        # Get the calculated PDF pattern?
        pattern = calculator.getpdf_fit()
        pattern = np.array(pattern)

        return pattern
