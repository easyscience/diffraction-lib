# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from easydiffraction.datablocks.structure.item.base import Structure


def test_structure_base_str_and_properties():
    m = Structure(name='m1')
    m.name = 'm2'
    assert m.name == 'm2'
    s = str(m)
    assert 'Structure' in s or '<' in s
