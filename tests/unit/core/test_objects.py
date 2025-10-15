from easydiffraction.core.category import CategoryItem
from easydiffraction.core.datablock import DatablockItem
from easydiffraction.core.parameters import Descriptor, Parameter


# filepath: src/easydiffraction/core/test_objects.py


def test_descriptor_initialization():
    desc = Descriptor(
        value=10,
        name='test',
        value_type=int,
        full_cif_names=['_test.tag'],
        default_value=0,
        editable=True,
    )
    assert desc.value == 10
    assert desc.name == 'test'
    assert desc.full_cif_names[0] == '_test.tag'
    assert desc.default_value == 0


def test_descriptor_value_setter():
    desc = Descriptor(
        value=10,
        name='test',
        value_type=int,
        full_cif_names=['_test.tag'],
        default_value=0,
        editable=True,
    )
    desc.value = 20
    assert desc.value == 20

    desc_non_editable = Descriptor(
        value=10,
        name='test_non_edit',
        value_type=int,
        full_cif_names=['_test.tag2'],
        default_value=0,
        editable=False,
    )
    desc_non_editable.value = 30
    assert desc_non_editable.value == 30


def test_parameter_initialization():
    param = Parameter(
        value=5.0,
        name='param',
        full_cif_names=['_param.tag'],
        default_value=5.0,
        uncertainty=0.1,
        free=True,
        constrained=False,
        physical_min=0.0,
        physical_max=10.0,
        fit_min=0.0,
        fit_max=10.0,
    )
    assert param.value == 5.0
    assert param.uncertainty == 0.1
    assert param.free is True
    assert param.constrained is False
    assert param.physical_min == 0.0
    assert param.physical_max == 10.0


def test_component_abstract_methods():
    class TestComponent(CategoryItem):
        @property
        def category_key(self):
            return 'test_category'

    comp = TestComponent()
    assert comp.category_key == 'test_category'


def test_component_attribute_handling():
    class TestComponent(CategoryItem):
        @property
        def category_key(self):
            return 'test_category'

    comp = TestComponent()
    desc = Descriptor(
        value=10,
        name='test',
        value_type=int,
        full_cif_names=['_test.tag'],
        default_value=0,
    )
    comp._parameters = [desc]  # internal test-only association
    assert comp._parameters[0].value == 10


import pytest

@pytest.mark.xfail(reason="Direct parameter attribute injection on CategoryItem now blocked by guards")
def test_datablock_name_propagation():
    class TestComponent(CategoryItem):
        @property
        def category_key(self):
            return 'comp'

        def __init__(self):
            super().__init__()
            self.alpha = Parameter(
                value=1.0,
                name='alpha',
                full_cif_names=['_comp.alpha'],
                default_value=1.0,
            )

    class TestDatablock(DatablockItem):
        def __init__(self):
            super().__init__()
            self.name = 'block1'
            self._components = [TestComponent()]

    db = TestDatablock()
    assert db.comp.alpha.full_name.startswith('block1.comp.alpha')


def test_parameter_string_representation():
    p = Parameter(
        value=2.5,
        name='beta',
        full_cif_names=['_comp.beta'],
        default_value=2.5,
        uncertainty=0.05,
        units='Å',
    )
    s = str(p)
    assert 'Parameter:' in s
    assert 'beta' in s
    assert 'Å' in s


@pytest.mark.xfail(reason="Direct component attribute injection on Datablock now blocked by guards")
def test_datablock_components():
    class TestComponent(CategoryItem):
        @property
        def category_key(self):
            return 'test_category'

    class TestDatablock(DatablockItem):
        def __init__(self):
            super().__init__()
            self.component1 = TestComponent()
            self.component2 = TestComponent()

    datablock = TestDatablock()
    assert len(datablock._components) == 2
    assert all(isinstance(c, TestComponent) for c in datablock._components)
