# SPDX-FileCopyrightText: 2025 EasyDiffraction contributors
# SPDX-License-Identifier: BSD-3-Clause
# © 2021-2025 Contributors to the EasyDiffraction project <https://github.com/EasyScience/EasyDiffraction>
import os
import re
import numpy as np
from .calculator_base import CalculatorBase
from easydiffraction.utils.formatting import warning

try:
    from diffpy.pdffit2 import PdfFit as pdf_calc
    from diffpy.pdffit2 import redirect_stdout
    from diffpy.structure.parsers.p_cif import P_cif as cif_parser
    # silence the C++ engine output
    redirect_stdout(open(os.path.devnull, 'w'))
except ImportError:
    print(warning('"pdffit" module not found. This calculator will not work.'))
    pdf_calc = None

class PdffitCalculator(CalculatorBase):
    """
    Wrapper for Pdffit library.
    """

    engine_imported = pdf_calc is not None

    @property
    def name(self):
        return "PDFFit"

    def calculate_structure_factors(self, sample_models, experiments):
        # PDF doesn't compute HKL but we keep interface consistent
        print("[PdfFit] Calculating HKLs (not applicable)...")
        return []

    def _calculate_single_model_pattern(self,
                                        sample_model,
                                        experiment,
                                        called_by_minimizer=False):
        P = pdf_calc()

        v2_cif_string = sample_model.as_cif()
        # convert to version 1 of CIF format
        # this means: replace all dots with underscores for
        # cases where the dot is surrounded by letters on both sides.
        pattern = r"(?<=[a-zA-Z])\.(?=[a-zA-Z])"
        v1_cif_string =  re.sub(pattern, "_", v2_cif_string)

        structure = cif_parser().parse(v1_cif_string)
        P.add_structure(structure)

        # extract conditions from the model
        qmax = experiment.instrument.qmax.value
        qdamp = experiment.instrument.qdamp.value
        delta1 = experiment.instrument.delta1.value
        delta2 = experiment.instrument.delta2.value
        qbroad = experiment.instrument.qbroad.value
        spdiameter = experiment.instrument.spdiameter.value

        stype = "N" if experiment.type.radiation_probe.value == "neutron" else "X"

        # scale
        id = sample_model.name
        scale = experiment.linked_phases[id].scale.value
        P.setvar('pscale', scale)
        P.setvar('delta1', delta1)
        P.setvar('delta2', delta2)
        P.setvar('spdiameter', spdiameter)

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
                P.setvar(u_str, Biso)

        # Errors
        pattern = experiment.datastore.pattern
        noise_array = np.zeros(len(pattern.x))

        # Assign the data to the pdf calculator
        P.read_data_lists(stype, qmax, qdamp, list(pattern.x), list(noise_array))
        # qbroad must be set after read_data_string
        P.setvar('qbroad', qbroad)

        P.calc()

        pdf = np.array(P.getpdf_fit())

        return pdf
