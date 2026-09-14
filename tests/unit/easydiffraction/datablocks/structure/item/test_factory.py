# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from easydiffraction.datablocks.structure.item.factory import StructureFactory


def test_from_scratch():
    m = StructureFactory.from_scratch(name='abc')
    assert m.name == 'abc'


def test_from_cif_str_accepts_underscore_style_structure_tags():
    cif = """\
data_legacy
_cell_length_a 9.15993(5)
_cell_length_b 9.15993(5)
_cell_length_c 9.15993(5)
_cell_angle_alpha 90
_cell_angle_beta 90
_cell_angle_gamma 90
_symmetry_space_group_name_H-M 'P 21 3'

loop_
_atom_site_label
_atom_site_type_symbol
_atom_site_symmetry_multiplicity
_atom_site_fract_x
_atom_site_fract_y
_atom_site_fract_z
_atom_site_B_iso_or_equiv
_atom_site_occupancy
Zr1 Zr4+ 4 0.0003(4) 0.0003(4) 0.0003(4) 0.010(1) 1
W1  W6+  4 0.3412(3) 0.3412(3) 0.3412(3) 0.012(1) 1
"""

    structure = StructureFactory.from_cif_str(cif)

    assert structure.cell.length_a.value == 9.15993
    assert structure.space_group.name_h_m.value == 'P 21 3'
    assert structure.atom_sites.names == ['Zr1', 'W1']
    assert structure.atom_sites['Zr1'].type_symbol.value == 'Zr4+'
    assert structure.atom_sites['Zr1'].multiplicity.value == 4
