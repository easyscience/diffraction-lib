# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from easydiffraction.datablocks.structure.item.base import Structure


def test_structure_base_str_and_properties():
    m = Structure(name='m1')
    m.name = 'm2'
    assert m.name == 'm2'
    s = str(m)
    assert 'Structure' in s or '<' in s


def test_structure_name_rejects_uppercase_on_creation_and_rename():
    import pytest

    with pytest.raises(
        ValueError,
        match=r"Invalid structure name 'LaM7O3'.*Use 'lam7o3' instead",
    ):
        Structure(name='LaM7O3')

    structure = Structure(name='lam7o3')
    with pytest.raises(
        ValueError,
        match=r"Invalid structure name 'LMO'.*Use 'lmo' instead",
    ):
        structure.name = 'LMO'

    assert structure.name == 'lam7o3'
