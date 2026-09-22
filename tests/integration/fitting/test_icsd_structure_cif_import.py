# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Regression coverage for importing an underscore-style ICSD CIF."""

import numpy as np
import pytest

from easydiffraction.analysis.calculators.cryspy import CryspyCalculator
from easydiffraction.datablocks.structure.item.factory import StructureFactory

ZRW2O8_CIF = """\
data_83267-ICSD
_database_code_ICSD                83267
_audit_creation_date               1998-06-26
_chemical_name_systematic
'Zirconium bis(tungstate)'
_chemical_formula_structural
'Zr (W O4)2'
_chemical_formula_sum
'O8 W2 Zr1'
_publ_section_title
'O8 W2 Zr1'
loop_
_citation_id
_citation_journal_abbrev
_citation_year
_citation_journal_volume
_citation_page_first
_citation_page_last
_citation_journal_id_ASTM
primary 'Science' 1996 272 90 92 SCIEAS
loop_
_publ_author_name
Mary, T.A.;Evans, J.S.O.;Vogt, T.;Sleight, A.W.
_cell_length_a                     9.15993(5)
_cell_length_b                     9.15993(5)
_cell_length_c                     9.15993(5)
_cell_angle_alpha                  90.
_cell_angle_beta                   90.
_cell_angle_gamma                  90.
_cell_volume                       768.56
_cell_formula_units_Z              4
_symmetry_space_group_name_H-M     'P 21 3'
_symmetry_Int_Tables_number        198
_refine_ls_R_factor_all            0.024000
loop_
_symmetry_equiv_pos_site_id
_symmetry_equiv_pos_as_xyz
  1     '-z+1/2, -x, y+1/2'
  2     '-y+1/2, -z, x+1/2'
  3     '-x+1/2, -y, z+1/2'
  4     '-z, x+1/2, -y+1/2'
  5     '-y, z+1/2, -x+1/2'
  6     '-x, y+1/2, -z+1/2'
  7     'z+1/2, -x+1/2, -y'
  8     'y+1/2, -z+1/2, -x'
  9     'x+1/2, -y+1/2, -z'
  10     'z, x, y'
  11     'y, z, x'
  12     'x, y, z'
loop_
_atom_type_symbol
_atom_type_oxidation_number
Zr4+     4
W6+     6
O2-     -2
loop_
_atom_site_label
_atom_site_type_symbol
_atom_site_symmetry_multiplicity
_atom_site_Wyckoff_symbol
_atom_site_fract_x
_atom_site_fract_y
_atom_site_fract_z
_atom_site_B_iso_or_equiv
_atom_site_occupancy
Zr1 Zr4+ 4 a 0.0003(4) 0.0003(4) 0.0003(4) 0.010(1) 1.
W1 W6+ 4 a 0.3412(3) 0.3412(3) 0.3412(3) 0.012(1) 1.
W2 W6+ 4 a 0.6008(3) 0.6008(3) 0.6008(3) 0.010(1) 1.
O1 O2- 12 b 0.2071(3) 0.4378(4) 0.4470(3) 0.022(1) 1.
O2 O2- 12 b 0.7876(3) 0.5694(4) 0.5565(3) 0.020(1) 1.
O3 O2- 4 a 0.4916(5) 0.4916(5) 0.4916(5) 0.023(1) 1.
O4 O2- 4 a 0.2336(3) 0.2336(3) 0.2336(3) 0.037(1) 1.
"""


def test_icsd_cif_import_preserves_ions_and_uses_cryspy_fallbacks():
    """Preserve imported ions while replacing unsupported CrysPy symbols."""
    from cryspy.H_functions_global.function_1_cryspy_objects import str_to_globaln

    structure = StructureFactory.from_cif_str(ZRW2O8_CIF)

    assert structure.name == '83267-icsd'
    assert structure.as_cif.startswith('data_83267-icsd\n')
    assert structure.space_group.name_h_m.value == 'P 21 3'
    np.testing.assert_allclose(
        [
            structure.cell.length_a.value,
            structure.cell.length_b.value,
            structure.cell.length_c.value,
            structure.cell.angle_alpha.value,
            structure.cell.angle_beta.value,
            structure.cell.angle_gamma.value,
        ],
        [9.15993, 9.15993, 9.15993, 90.0, 90.0, 90.0],
    )
    np.testing.assert_allclose(
        [
            structure.cell.length_a.uncertainty,
            structure.cell.length_b.uncertainty,
            structure.cell.length_c.uncertainty,
        ],
        [0.00005, 0.00005, 0.00005],
    )

    expected_sites = {
        'Zr1': ('Zr4+', 4, 'a', (0.0003, 0.0003, 0.0003), (0.0004,) * 3, 0.010),
        'W1': ('W6+', 4, 'a', (0.3412, 0.3412, 0.3412), (0.0003,) * 3, 0.012),
        'W2': ('W6+', 4, 'a', (0.6008, 0.6008, 0.6008), (0.0003,) * 3, 0.010),
        'O1': ('O2-', 12, 'b', (0.2071, 0.4378, 0.4470), (0.0003, 0.0004, 0.0003), 0.022),
        'O2': ('O2-', 12, 'b', (0.7876, 0.5694, 0.5565), (0.0003, 0.0004, 0.0003), 0.020),
        'O3': ('O2-', 4, 'a', (0.4916, 0.4916, 0.4916), (0.0005,) * 3, 0.023),
        'O4': ('O2-', 4, 'a', (0.2336, 0.2336, 0.2336), (0.0003,) * 3, 0.037),
    }

    assert structure.atom_sites.names == list(expected_sites)
    for label, expected in expected_sites.items():
        type_symbol, multiplicity, wyckoff, coordinates, coordinate_sus, adp_iso = expected
        site = structure.atom_sites[label]
        assert site.type_symbol.value == type_symbol
        assert site.multiplicity.value == multiplicity
        assert site.wyckoff_letter.value == wyckoff
        assert site.occupancy.value == 1.0
        np.testing.assert_allclose(
            [site.fract_x.value, site.fract_y.value, site.fract_z.value],
            coordinates,
        )
        np.testing.assert_allclose(
            [site.fract_x.uncertainty, site.fract_y.uncertainty, site.fract_z.uncertainty],
            coordinate_sus,
        )
        assert site.adp_iso.value == pytest.approx(adp_iso)
        assert site.adp_iso.uncertainty == pytest.approx(0.001)

    cryspy_cif = CryspyCalculator()._convert_structure_to_cryspy_cif(structure)
    cryspy_structure = str_to_globaln(cryspy_cif).items[0]

    assert cryspy_structure.data_name == '83267-icsd'
    assert [site.type_symbol for site in cryspy_structure.atom_site.items] == [
        'Zr4+',
        'W6+',
        'W6+',
        'O',
        'O',
        'O',
        'O',
    ]
    assert [site.type_symbol.value for site in structure.atom_sites] == [
        expected[0] for expected in expected_sites.values()
    ]
