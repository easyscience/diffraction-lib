# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from easydiffraction.analysis.categories.constraints import Constraint
from easydiffraction.analysis.categories.constraints import Constraints


def test_constraint_creation_and_collection():
    c = Constraint()
    c.expression = 'a = b + c'
    assert c.lhs_alias == 'a'
    assert c.rhs_expr == 'b + c'
    coll = Constraints()
    coll.create(expression='a = b + c')
    assert 'a' in coll.names
    assert coll['a'].rhs_expr == 'b + c'
