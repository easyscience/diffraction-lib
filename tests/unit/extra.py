import pytest

from easydiffraction.sample_models.components.cell import Cell
from easydiffraction.sample_models.components.space_group import SpaceGroup
from easydiffraction.sample_models.collections.atom_sites import AtomSites
from easydiffraction.core.objects import Descriptor, Parameter
from easydiffraction import SampleModel, SampleModels

# DatablockCollection


def test_datablock_collection_get_invalid_attribute():
    models = SampleModels()
    with pytest.raises(AttributeError):
        getattr(models, 'dummy_attr')


def test_datablock_collection_set_invalid_attribute():
    models = SampleModels()
    with pytest.raises(AttributeError):
        setattr(models, 'dummy_attr', 'dummy_value')


# Datablock


def test_datablock_get_invalid_attribute():
    m = SampleModel(name='mdl')
    with pytest.raises(AttributeError):
        getattr(m, 'dummy_attr')


def test_datablock_set_invalid_attribute():
    m = SampleModel(name='mdl')
    with pytest.raises(AttributeError):
        setattr(m, 'dummy_attr', 'dummy_value')


def test_datablock_invalid_float_type_warning():
    m = SampleModel(name='mdl')
    with pytest.warns(UserWarning, match='Allowed: str'):
        m.name = 33.3


# CategoryCollection


def test_category_collection_get_invalid_attribute():
    sites = AtomSites()
    with pytest.raises(AttributeError):
        getattr(sites, 'dummy_attr')


def test_category_collection_set_invalid_attribute():
    sites = AtomSites()
    with pytest.raises(AttributeError):
        setattr(sites, 'dummy_attr', 'dummy_value')


# CategoryItem


def test_category_item_get_invalid_attribute():
    sg = SpaceGroup()
    with pytest.raises(AttributeError):
        getattr(sg, 'dummy_attr')


def test_category_item_set_invalid_attribute():
    sg = SpaceGroup()
    with pytest.raises(AttributeError):
        setattr(sg, 'dummy_attr', 'dummy_value')


# Descriptor


def test_descriptor_set_invalid_attribute():
    sg = SpaceGroup()
    with pytest.raises(AttributeError):
        setattr(sg.name_h_m, 'dummy_attr', 'dummy_value')


@pytest.mark.parametrize('attr', Descriptor._readonly_attributes)
def test_descriptor_set_readonly_attributes(attr):
    sg = SpaceGroup()
    with pytest.raises(AttributeError):
        setattr(sg.name_h_m, attr, 'something')


def test_descriptor_default():
    sg = SpaceGroup()
    assert sg.name_h_m.value == 'P 1'


def test_descriptor_set():
    sg = SpaceGroup()
    sg.name_h_m = 'P n m a'
    assert sg.name_h_m.value == 'P n m a'


def test_descriptor_invalid_float_type_warning():
    sg = SpaceGroup()
    with pytest.warns(UserWarning, match='Allowed: str'):
        sg.name_h_m.value = 33.3


def test_descriptor_invalid_value_warning():
    sg = SpaceGroup()
    with pytest.warns(UserWarning, match='Allowed:'):
        sg.name_h_m.value = 'P m-3m'


# Parameter


def test_parameter_set_invalid_attribute():
    cell = Cell()
    with pytest.raises(AttributeError):
        setattr(cell.length_a, 'dummy_attr', 'dummy_value')


@pytest.mark.parametrize('attr', Parameter._readonly_attributes)
def test_parameter_set_read_only_attributes(attr):
    cell = Cell()
    with pytest.raises(AttributeError):
        setattr(cell.length_a, attr, 'something')


def test_parameter_invalid_str_type_warning():
    cell = Cell()
    with pytest.warns(UserWarning, match='Allowed:'):
        cell.length_a = '5'


def test_parameter_invalid_float_range_warning():
    cell = Cell()
    with pytest.warns(UserWarning, match='is outside'):
        cell.length_a = -5.5
