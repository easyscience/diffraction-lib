# Auto-generated scaffold. Replace TODOs with concrete tests.
import pytest
import numpy as np

# expected vs actual helpers

def _assert_equal(expected, actual):
    assert expected == actual


# Module under test: easydiffraction.core.identity

# TODO: Replace with real, small tests per class/method.
# Keep names explicit: expected_*, actual_*; compare in a single assert.

def test_module_import():
    import easydiffraction.core.identity as MUT
    expected_module_name = "easydiffraction.core.identity"
    actual_module_name = MUT.__name__
    _assert_equal(expected_module_name, actual_module_name)


def test_identity_direct_and_parent_resolution():
    from easydiffraction.core.identity import Identity

    class Node:
        def __init__(self, name=None, parent=None):
            self._identity = Identity(owner=self, category_code=name)
            if parent is not None:
                self._parent = parent

    # leaf with no direct category_code, inherits from parent
    parent = Node(name="cat")
    child = Node(parent=parent)

    expected_parent_code = "cat"
    actual_parent_code = parent._identity.category_code
    assert expected_parent_code == actual_parent_code

    expected_child_code = "cat"
    actual_child_code = child._identity.category_code
    assert expected_child_code == actual_child_code


def test_identity_cycle_safe_resolution():
    from easydiffraction.core.identity import Identity

    class Node:
        def __init__(self):
            self._identity = Identity(owner=self)

    a = Node()
    b = Node()
    # create cycle
    a._parent = b
    b._parent = a
    # resolution should not raise and should return None
    assert a._identity.category_code is None
