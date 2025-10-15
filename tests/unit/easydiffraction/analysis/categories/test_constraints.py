from easydiffraction.analysis.categories.constraints import Constraint, Constraints


def test_constraint_creation_and_collection():
    c = Constraint(lhs_alias="a", rhs_expr="b + c")
    assert c.lhs_alias.value == "a"
    coll = Constraints()
    coll.add(c)
    assert "a" in coll.names
    assert coll["a"].rhs_expr.value == "b + c"
