from unittest.mock import MagicMock
import types
import sys
import pytest

# ---------------------------------------------------------------------------
# Test Isolation Note:
# Importing the top-level 'easydiffraction' package triggers heavy optional
# dependencies (pycrysfml native extension). In this test we only need the
# singleton infrastructure (BaseSingleton, ConstraintsHandler, UidMapHandler)
# and a lightweight parameter-like object. To avoid a failing native extension
# import (SystemError: initialization of crysfml08lib...), we pre-populate
# sys.modules with a minimal stub for 'pycrysfml' before importing anything
# from the package. This keeps the production code untouched per constraints.
# ---------------------------------------------------------------------------
if 'pycrysfml' not in sys.modules:  # only stub if not already provided
    pycrysfml_stub = types.ModuleType('pycrysfml')
    cfml_py_utilities_stub = types.ModuleType('cfml_py_utilities')
    # attach a minimal attribute used defensively in code paths (if any)
    cfml_py_utilities_stub.__dict__.update({})
    pycrysfml_stub.cfml_py_utilities = cfml_py_utilities_stub
    sys.modules['pycrysfml'] = pycrysfml_stub
    sys.modules['pycrysfml.cfml_py_utilities'] = cfml_py_utilities_stub

from easydiffraction.core.singletons import BaseSingleton, ConstraintsHandler, UidMapHandler


@pytest.fixture
def params():
    class DummyParam:
        def __init__(self, value: float, name: str):
            self.value = value
            self.name = name
            self.constrained = False

    return DummyParam(1.0, 'param1'), DummyParam(2.0, 'param2')


@pytest.fixture
def mock_aliases(params):
    param1, param2 = params
    # Inject synthetic UIDs without touching guarded .uid attribute
    uid_map = UidMapHandler.get().get_uid_map()
    uid1 = 'uid_param1'
    uid2 = 'uid_param2'
    uid_map[uid1] = param1
    uid_map[uid2] = param2
    mock = MagicMock()
    mock._items = {
        'alias1': MagicMock(label=MagicMock(value='alias1'), param_uid=MagicMock(value=uid1)),
        'alias2': MagicMock(label=MagicMock(value='alias2'), param_uid=MagicMock(value=uid2)),
    }
    return mock


@pytest.fixture
def mock_constraints():
    mock = MagicMock()
    mock._items = {
        'expr1': MagicMock(
            lhs_alias=MagicMock(value='alias1'), rhs_expr=MagicMock(value='alias2 + 1')
        ),
        'expr2': MagicMock(
            lhs_alias=MagicMock(value='alias2'), rhs_expr=MagicMock(value='alias1 * 2')
        ),
    }
    return mock


def test_base_singleton():
    class TestSingleton(BaseSingleton):
        pass

    instance1 = TestSingleton.get()
    instance2 = TestSingleton.get()

    assert instance1 is instance2  # Ensure only one instance is created


def test_uid_map_handler(params):
    param1, param2 = params
    handler = UidMapHandler.get()
    uid_map = handler.get_uid_map()
    # Populate map manually to simulate registration
    uid_map.clear()
    uid_map['uid_param1'] = param1
    uid_map['uid_param2'] = param2
    assert uid_map['uid_param1'] is param1
    assert uid_map['uid_param2'] is param2


def test_constraints_handler_set_aliases(mock_aliases, params):
    param1, param2 = params
    handler = ConstraintsHandler.get()
    handler.set_aliases(mock_aliases)
    assert handler._alias_to_param['alias1'].param_uid.value == 'uid_param1'
    assert handler._alias_to_param['alias2'].param_uid.value == 'uid_param2'


def test_constraints_handler_set_constraints(mock_constraints):
    handler = ConstraintsHandler.get()
    handler.set_constraints(mock_constraints)

    assert len(handler._parsed_constraints) == 2
    assert handler._parsed_constraints[0] == ('alias1', 'alias2 + 1')
    assert handler._parsed_constraints[1] == ('alias2', 'alias1 * 2')


def test_constraints_handler_apply(mock_aliases, mock_constraints, params):
    param1, _ = params
    handler = ConstraintsHandler.get()
    handler.set_aliases(mock_aliases)
    handler.set_constraints(mock_constraints)
    handler.apply()
    assert param1.value == 3.0
    assert param1.constrained is True
