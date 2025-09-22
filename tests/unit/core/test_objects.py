from easydiffraction.core.objects import CategoryItem
from easydiffraction.core.objects import Datablock
from easydiffraction.core.objects import Descriptor
from easydiffraction.core.objects import Parameter

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
    # The first CIF tag alias should be stored
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
    # Attempting to change non-editable value should be ignored
    desc_non_editable.value = 30
    assert desc_non_editable.value == 10


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
    comp.test_attr = desc
    assert comp.test_attr.value == 10  # Access Descriptor value directly


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

    class TestDatablock(Datablock):
        def __init__(self):
            super().__init__()
            self.name = 'block1'
            self.comp = TestComponent()

    db = TestDatablock()
    # Parameter full name should include datablock prefix now
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


def test_datablock_components():
    class TestComponent(CategoryItem):
        @property
        def category_key(self):
            return 'test_category'

    class TestDatablock(Datablock):
        def __init__(self):
            super().__init__()
            self.component1 = TestComponent()
            self.component2 = TestComponent()

    datablock = TestDatablock()
    comps = datablock.categories
    assert len(comps) == 2
    assert all(isinstance(c, TestComponent) for c in comps)
