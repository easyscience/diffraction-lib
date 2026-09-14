# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from easydiffraction.datablocks.structure.item.factory import StructureFactory


def test_from_scratch():
    m = StructureFactory.from_scratch(name='abc')
    assert m.name == 'abc'


def test_from_cif_str_normalizes_datablock_name():
    structure = StructureFactory.from_cif_str('data_83267-ICSD\n')

    assert structure.name == '83267-icsd'
    assert structure.as_cif.startswith('data_83267-icsd\n')
