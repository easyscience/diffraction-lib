# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from easydiffraction.analysis.categories.aliases import Alias
from easydiffraction.analysis.categories.aliases import Aliases
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.variable import Parameter
from easydiffraction.io.cif.handler import CifHandler


def test_alias_creation_and_collection():
    p1 = Parameter(
        name='adp_iso',
        value_spec=AttributeSpec(default=0.5),
        cif_handler=CifHandler(names=['_atom_site.adp_iso']),
    )
    a = Alias()
    a.id = 'x'
    a._set_param(p1)
    assert a.id.value == 'x'
    assert a.param is p1
    coll = Aliases()
    coll.create(id='x', param=p1)
    # Collections index by entry name; check via names or direct indexing
    assert 'x' in coll.names
    assert coll['x'].param is p1
    assert coll['x'].parameter_unique_name.value == p1.unique_name
