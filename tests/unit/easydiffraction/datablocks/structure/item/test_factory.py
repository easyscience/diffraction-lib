# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from easydiffraction.datablocks.structure.item.factory import StructureFactory


def test_from_scratch():
    m = StructureFactory.from_scratch(name='abc')
    assert m.name == 'abc'
