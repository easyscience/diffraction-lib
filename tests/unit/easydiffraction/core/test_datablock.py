# Auto-generated scaffold. Replace TODOs with concrete tests.
import pytest
import numpy as np

# expected vs actual helpers

def _assert_equal(expected, actual):
    assert expected == actual


# Module under test: easydiffraction.core.datablock

# TODO: Replace with real, small tests per class/method.
# Keep names explicit: expected_*, actual_*; compare in a single assert.

def test_module_import():
    import easydiffraction.core.datablock as MUT
    expected_module_name = "easydiffraction.core.datablock"
    actual_module_name = MUT.__name__
    _assert_equal(expected_module_name, actual_module_name)


def test_datablock_collection_add_and_filters():
    from easydiffraction.core.datablock import DatablockCollection, DatablockItem
    from easydiffraction.core.parameters import Parameter
    from easydiffraction.core.identity import Identity

    class DummyParam:
        def __init__(self, name, free=True, constrained=False):
            self.free = free
            self.constrained = constrained
            self._identity = Identity(owner=self, category_entry=lambda: name)

    class Block(DatablockItem):
        def __init__(self, name, params):
            super().__init__()
            self._identity.datablock_entry_name = lambda: name
            self._params = params

        @property
        def parameters(self):
            return self._params

        @property
        def as_cif(self) -> str:
            return ""

    coll = DatablockCollection(item_type=Block)
    a = Block("A", [DummyParam("p1", free=True, constrained=False)])
    b = Block("B", [DummyParam("p2", free=False, constrained=False), DummyParam("p3", free=True, constrained=True)])
    coll.add(a)
    coll.add(b)
    # aggregate
    assert len(coll.parameters) == 3
    # fittable: Parameter subclass and not constrained -> here 0 because DummyParam not Parameter
    assert coll.fittable_parameters == []
    # free: subset of fittable -> empty
    assert coll.free_parameters == []
