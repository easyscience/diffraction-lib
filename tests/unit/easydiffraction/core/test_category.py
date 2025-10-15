from easydiffraction.core.category import CategoryCollection, CategoryItem
from easydiffraction.core.parameters import GenericDescriptorBase
from easydiffraction.core.validation import AttributeSpec, DataTypes
from easydiffraction.io.cif.serialize import category_item_to_cif


class SimpleDescriptor(GenericDescriptorBase):
    _value_type = DataTypes.STRING
    def __init__(self, name, value):
        super().__init__(
            name=name,
            description='',
            value_spec=AttributeSpec(value=value, type_=DataTypes.STRING, default=''),
        )


class SimpleItem(CategoryItem):
    def __init__(self, entry_name):
        super().__init__()
        self._identity.category_code = 'simple'
        self._identity.category_entry_name = entry_name
        # Assign as private attributes to bypass GuardedBase writable checks,
        # and expose via properties below.
        object.__setattr__(self, '_a', SimpleDescriptor('a', 'x'))
        object.__setattr__(self, '_b', SimpleDescriptor('b', 'y'))

    @property
    def a(self):
        return self._a

    @property
    def b(self):
        return self._b


class SimpleCollection(CategoryCollection):
    def __init__(self):
        super().__init__(item_type=SimpleItem)


def test_category_item_str_and_properties():
    it = SimpleItem('name1')
    s = str(it)
    assert '<' in s and 'a=' in s and 'b=' in s
    assert it.unique_name.endswith('.simple.name1') or it.unique_name == 'simple.name1'
    assert len(it.parameters) == 2


def test_category_collection_str_and_cif_calls():
    c = SimpleCollection()
    c.add(SimpleItem('n1'))
    c.add(SimpleItem('n2'))
    s = str(c)
    assert 'collection' in s and '2 items' in s
    # as_cif delegates to serializer; calling it ensures code path executed
    _ = c.as_cif# Auto-generated scaffold. Replace TODOs with concrete tests.
import pytest
import numpy as np

# expected vs actual helpers

def _assert_equal(expected, actual):
    assert expected == actual


# Module under test: easydiffraction.core.category

# TODO: Replace with real, small tests per class/method.
# Keep names explicit: expected_*, actual_*; compare in a single assert.

def test_module_import():
    import easydiffraction.core.category as MUT
    expected_module_name = "easydiffraction.core.category"
    actual_module_name = MUT.__name__
    _assert_equal(expected_module_name, actual_module_name)
