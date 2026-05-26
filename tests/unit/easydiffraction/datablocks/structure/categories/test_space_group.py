# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from easydiffraction.datablocks.structure.categories.space_group import SpaceGroup


def test_space_group_name_updates_it_code():
    sg = SpaceGroup()
    # default name 'P 1' should set code to the first available
    default_code = sg.it_coordinate_system_code.value
    sg.name_h_m = 'P 1'
    assert sg.it_coordinate_system_code.value == sg._it_coordinate_system_code_allowed_values[0]
    # changing name resets the code again
    sg.name_h_m = 'P -1'
    assert sg.it_coordinate_system_code.value == sg._it_coordinate_system_code_allowed_values[0]


def test_space_group_uses_iucr_casing_with_legacy_aliases():
    sg = SpaceGroup()

    assert sg.name_h_m._cif_handler.names == [
        '_space_group.name_H-M_alt',
        '_space_group.name_h_m',
    ]
    assert sg.it_coordinate_system_code._cif_handler.names == [
        '_space_group.IT_coordinate_system_code',
        '_space_group.it_coordinate_system_code',
    ]
