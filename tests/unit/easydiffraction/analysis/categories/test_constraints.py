# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import gemmi

from easydiffraction.analysis.categories.constraints import Constraint
from easydiffraction.analysis.categories.constraints import Constraints


def test_constraint_creation_and_collection():
    c = Constraint()
    c.id = 'constraint_1'
    c.expression = 'a = b + c'
    assert c.id.value == 'constraint_1'
    assert c.lhs_alias == 'a'
    assert c.rhs_expr == 'b + c'

    coll = Constraints()
    coll.create(expression='a = b + c')
    assert 'a' in coll.names
    assert coll['a'].id.value == 'a'
    assert coll['a'].rhs_expr == 'b + c'


def test_constraints_create_uses_explicit_id():
    coll = Constraints()

    coll.create(id='constraint_1', expression='a = b + c')

    assert coll.names == ['constraint_1']
    assert coll['constraint_1'].id.value == 'constraint_1'
    assert coll['constraint_1'].lhs_alias == 'a'
    assert coll['constraint_1'].rhs_expr == 'b + c'


def test_constraints_from_cif_preserves_explicit_id_keys():
    doc = gemmi.cif.read_string(
        'data_constraints\n\n'
        'loop_\n'
        '_constraint.id\n'
        '_constraint.expression\n'
        'constraint_1 "a = b + c"\n',
    )
    coll = Constraints()

    coll.from_cif(doc.sole_block())

    assert coll.names == ['constraint_1']
    assert coll['constraint_1'].id.value == 'constraint_1'
    assert coll['constraint_1'].lhs_alias == 'a'


def test_constraints_from_cif_backfills_missing_id_from_lhs_alias():
    doc = gemmi.cif.read_string(
        'data_constraints\n\nloop_\n_constraint.expression\n"a = b + c"\n',
    )
    coll = Constraints()

    coll.from_cif(doc.sole_block())

    assert coll.names == ['a']
    assert coll['a'].id.value == 'a'
    assert coll['a'].expression.value == 'a = b + c'
