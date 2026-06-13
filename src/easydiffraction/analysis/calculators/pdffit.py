# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
PDF calculation backend using diffpy.pdffit2 if available.

The class adapts the engine to EasyDiffraction calculator interface and
silences stdio on import to avoid noisy output in notebooks and logs.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

from easydiffraction.analysis.calculators.base import CalculatorBase
from easydiffraction.analysis.calculators.factory import CalculatorFactory
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.utils.logging import log

if TYPE_CHECKING:
    from easydiffraction.datablocks.experiment.item.base import ExperimentBase
    from easydiffraction.datablocks.structure.item.base import Structure


def _open_pdffit_devnull() -> object:
    """Open a durable devnull handle for PDFfit stdout redirection."""
    with Path(os.devnull).open('w', encoding='utf-8') as tmp_devnull:
        return os.fdopen(os.dup(tmp_devnull.fileno()), 'w')


_ANISO_SUFFIXES = ('11', '22', '33', '12', '13', '23')
_B_TO_U_FACTOR = 8.0 * np.pi**2


def _normalize_b_family_adp_to_u(structure: Structure) -> list[tuple]:
    """
    Temporarily convert B-convention ADP values to U notation.

    diffpy reads a single isotropic/anisotropic ADP column, so a
    structure mixing ``Biso``/``Uiso`` (or ``Bani``/``Uani``) atoms must
    be normalized to one convention. B-family values are divided by 8π²
    so every row can be written under the U tags. Returns saved state
    for restoration. ``beta`` atoms keep their stored equivalent values
    unchanged.
    """
    saved: list[tuple] = []
    for atom in structure.atom_sites:
        adp_type = str(atom.adp_type.value).lower()
        if adp_type not in {'biso', 'bani'}:
            continue
        saved.append((atom._adp_iso, atom._adp_iso._value))
        atom._adp_iso._value /= _B_TO_U_FACTOR
        if atom.id.value in structure.atom_site_aniso:
            aniso = structure.atom_site_aniso[atom.id.value]
            for suffix in _ANISO_SUFFIXES:
                param = getattr(aniso, f'_adp_{suffix}')
                saved.append((param, param._value))
                param._value /= _B_TO_U_FACTOR
    return saved


def _restore_adp_values(saved: list[tuple]) -> None:
    """Restore ADP values saved by ``_normalize_b_family_adp_to_u``."""
    for param, value in saved:
        param._value = value


def _structure_cif_for_pdffit(structure: Structure) -> str:
    """
    Return structure CIF using legacy IUCr tags diffpy recognizes.

    EasyDiff persistence renamed several CIF tags (``_atom_site.id``,
    ``_space_group.name_h_m``, type-neutral ``_atom_site.adp_iso``).
    diffpy's CIF parser only understands the legacy IUCr spellings, so
    map them back. All ADP values are normalized to the U convention
    first, so mixed B/U structures are written consistently under the U
    tags rather than mislabeling one family.
    """
    saved = _normalize_b_family_adp_to_u(structure)
    try:
        cif = structure.as_cif
    finally:
        _restore_adp_values(saved)

    replacements = [
        ('_atom_site_aniso.id', '_atom_site_aniso.label'),
        ('_atom_site.id', '_atom_site.label'),
        ('_space_group.name_h_m', '_space_group.name_H-M_alt'),
        ('_space_group.coord_system_code', '_space_group.IT_coordinate_system_code'),
        ('_atom_site.adp_iso', '_atom_site.U_iso_or_equiv'),
        *(
            (f'_atom_site_aniso.adp_{suffix}', f'_atom_site_aniso.U_{suffix}')
            for suffix in _ANISO_SUFFIXES
        ),
    ]
    for easydiff_tag, iucr_tag in replacements:
        cif = cif.replace(easydiff_tag, iucr_tag)
    return cif


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
    url: str = 'https://www.diffpy.org/products/pdffit2.html'

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
        log.debug('[pdffit] Calculating HKLs (not applicable)')
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
        # Convert the structure to CIF supported by PDFfit, mapping
        # EasyDiff tags back to the legacy IUCr spellings diffpy needs.
        cif_string_v2 = _structure_cif_for_pdffit(structure)
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
        calculator.setvar('pscale', experiment.linked_structures[structure.name].scale.value)
        calculator.setvar('delta1', experiment.peak.sharp_delta_1.value)
        calculator.setvar('delta2', experiment.peak.sharp_delta_2.value)
        calculator.setvar('spdiameter', experiment.peak.damp_particle_diameter.value)

        # Data
        x = list(experiment.data.x)
        y_noise = list(np.zeros_like(x))

        # Assign the data to the PDFfit calculator
        calculator.read_data_lists(
            stype=experiment.experiment_type.radiation_probe.value[0].upper(),
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
