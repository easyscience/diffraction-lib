# Auto-generated scaffold. Replace TODOs with concrete tests.
import pytest
import numpy as np

# expected vs actual helpers

def _assert_equal(expected, actual):
    assert expected == actual


# Module under test: easydiffraction.core.collection

# TODO: Replace with real, small tests per class/method.
# Keep names explicit: expected_*, actual_*; compare in a single assert.

def test_module_import():
    import easydiffraction.core.collection as MUT
    expected_module_name = "easydiffraction.core.collection"
    actual_module_name = MUT.__name__
    _assert_equal(expected_module_name, actual_module_name)


def test_collection_add_get_delete_and_names():
    from easydiffraction.core.collection import CollectionBase
    from easydiffraction.core.identity import Identity

    class Item:
        def __init__(self, name):
            self._identity = Identity(owner=self, category_entry=lambda: name)

    class MyCollection(CollectionBase):
        @property
        def parameters(self):
            return []

        @property
        def as_cif(self) -> str:
            return ""

    c = MyCollection(item_type=Item)
    # add two items
    a = Item("a")
    b = Item("b")
    c["a"] = a
    c["b"] = b
    # get
    assert c["a"] is a and c["b"] is b
    # overwrite existing key
    a2 = Item("a")
    c["a"] = a2
    assert c["a"] is a2 and len(list(c.keys())) == 2
    # delete
    del c["b"]
    assert list(c.names) == ["a"]
