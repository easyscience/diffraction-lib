import pytest
from easydiffraction.core.singletons import BaseSingleton, UidMapHandler, ConstraintsHandler
from easydiffraction.core.objects import Descriptor, Parameter

# filepath: src/easydiffraction/core/test_singletons.py


def test_base_singleton():
    class TestSingleton(BaseSingleton):
        pass

    instance1 = TestSingleton.get()
    instance2 = TestSingleton.get()

    assert instance1 is instance2  # Ensure only one instance is created


def test_uid_map_handler():
    param1 = Parameter(value=1.0, name="param1", cif_name="param1_cif")
    param2 = Parameter(value=2.0, name="param2", cif_name="param2_cif")

    handler = UidMapHandler.get()
    uid_map = handler.get_uid_map()

    assert uid_map[param1.uid] is param1
    assert uid_map[param2.uid] is param2
    assert uid_map[param1.uid].uid == 'None.param1_cif'
    assert uid_map[param2.uid].uid == 'None.param2_cif'


def test_constraints_handler_set_aliases():
    class MockAlias:
        def __init__(self, param):
            self.param = param

    param1 = Parameter(value=1.0, name="param1", cif_name="param1_cif")
    param2 = Parameter(value=2.0, name="param2", cif_name="param2_cif")

    aliases = {"alias1": MockAlias(param1), "alias2": MockAlias(param2)}

    handler = ConstraintsHandler.get()
    handler.set_aliases(type("MockAliases", (object,), {"_items": aliases}))

    assert handler._alias_to_param["alias1"].param is param1
    assert handler._alias_to_param["alias2"].param is param2


def test_constraints_handler_set_constraints():
    class MockConstraint:
        def __init__(self, lhs_alias, rhs_expr):
            self.lhs_alias = Descriptor(value=lhs_alias, name="lhs", cif_name="lhs_cif")
            self.rhs_expr = Descriptor(value=rhs_expr, name="rhs", cif_name="rhs_cif")

    expressions = {
        "expr1": MockConstraint("alias1", "alias2 + 1"),
        "expr2": MockConstraint("alias2", "alias1 * 2"),
    }

    handler = ConstraintsHandler.get()
    handler.set_constraints(type("MockConstraints", (object,), {"_items": expressions}))

    assert len(handler._parsed_constraints) == 2
    assert handler._parsed_constraints[0] == ("alias1", "alias2 + 1")
    assert handler._parsed_constraints[1] == ("alias2", "alias1 * 2")


def test_constraints_handler_apply():
    class MockAlias:
        def __init__(self, param):
            self.param = param

    # Create parameters
    param1 = Parameter(value=1.0, name="param1", cif_name="param1_cif")
    param2 = Parameter(value=2.0, name="param2", cif_name="param2_cif")

    # Set up aliases
    aliases = {"alias1": MockAlias(param1), "alias2": MockAlias(param2)}

    # Set up ConstraintsHandler
    handler = ConstraintsHandler.get()
    handler.set_aliases(type("MockAliases", (object,), {"_items": aliases}))

    # Define expressions
    constraints = {
        "expr1": type(
            "MockExpression",
            (object,),
            {
                "lhs_alias": Descriptor(value="alias1", name="lhs", cif_name="lhs_cif"),
                "rhs_expr": Descriptor(value="alias2 + 1", name="rhs", cif_name="rhs_cif"),
            },
        )
    }
    handler.set_constraints(type("MockConstraints", (object,), {"_items": constraints}))

    # Apply constraints
    handler.apply()

    # Assert the updated value and constrained status
    assert param1.value == 3.0  # alias2 (2.0) + 1
    assert param1.constrained is True