from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from easydiffraction.sample_models.sample_model import SampleModel
from easydiffraction.sample_models.sample_model_types.base import BaseSampleModel
from easydiffraction.sample_models.sample_models import SampleModels


@pytest.fixture
def mock_sample_model():
    with (
        patch('easydiffraction.sample_models.category_items.space_group.SpaceGroup') as mock_space_group,
        patch('easydiffraction.sample_models.category_items.cell.Cell') as mock_cell,
        patch('easydiffraction.sample_models.collections.atom_sites.AtomSites') as mock_atom_sites,
    ):
        space_group = mock_space_group.return_value
        cell = mock_cell.return_value
        atom_sites = mock_atom_sites.return_value

        # Mock attributes
        space_group.name_h_m.value = 'P 1'
        space_group.it_coordinate_system_code.value = 1
        cell.length_a.value = 1.0
        cell.length_b.value = 2.0
        cell.length_c.value = 3.0
        cell.angle_alpha.value = 90.0
        cell.angle_beta.value = 90.0
        cell.angle_gamma.value = 90.0
        atom_sites.__iter__.return_value = []

        return SampleModel(name='test_model')


@pytest.fixture
def mock_sample_models():
    return SampleModels()


def test_sample_models_add(mock_sample_models, mock_sample_model):
    mock_sample_models.add(mock_sample_model)

    # Assertions
    assert 'test_model' in mock_sample_models.names


def test_sample_models_remove(mock_sample_models, mock_sample_model):
    mock_sample_models.add(mock_sample_model)
    mock_sample_models.remove('test_model')

    # Assertions
    assert 'test_model' not in mock_sample_models.names


def test_sample_models_as_cif(mock_sample_models, mock_sample_model):
    mock_sample_models.add(mock_sample_model)
    cif = mock_sample_models.as_cif
    assert 'data_test_model' in cif or 'test_model' in cif


@patch('builtins.print')
def test_sample_models_show_names(mock_print, mock_sample_models, mock_sample_model):
    mock_sample_models.add(mock_sample_model)
    mock_sample_models.show_names()

    # Assertions
    mock_print.assert_called_with(['test_model'])


@patch.object(BaseSampleModel, 'show_params', autospec=True)
def test_sample_models_show_params(mock_show_params, mock_sample_models, mock_sample_model):
    mock_sample_models.add(mock_sample_model)
    mock_sample_models.show_params()

    # Assertions
    mock_show_params.assert_called_once_with(mock_sample_model)


def test_sample_models_add_minimal(monkeypatch):
    sm = SampleModels()
    # Patch SampleModel to avoid heavy init
    class DummyModel(SampleModel):
        def __init__(self, name, cif_path=None, cif_str=None):  # type: ignore[no-untyped-def]
            # Do not call super().__init__ to keep it light
            self._name = name

    monkeypatch.setattr('easydiffraction.sample_models.sample_models.SampleModel', DummyModel)
    sm.add_minimal('m1')
    assert 'm1' in sm.names


def test_sample_models_add_from_cif_path(monkeypatch):
    sm = SampleModels()
    created = {}

    def fake_create(**kwargs):  # type: ignore[no-untyped-def]
        created['kwargs'] = kwargs
        return BaseSampleModel(name='dummy_from_path')

    monkeypatch.setattr(
        'easydiffraction.sample_models.sample_model_factory.SampleModelFactory.create',
        staticmethod(fake_create),
    )

    sm.add_from_cif_path('/path/to/file.cif')
    assert 'dummy_from_path' in sm.names
    assert created['kwargs']['cif_path'] == '/path/to/file.cif'


def test_sample_models_add_from_cif_str(monkeypatch):
    sm = SampleModels()
    created = {}

    def fake_create(**kwargs):  # type: ignore[no-untyped-def]
        created['kwargs'] = kwargs
        return BaseSampleModel(name='dummy_from_str')

    monkeypatch.setattr(
        'easydiffraction.sample_models.sample_model_factory.SampleModelFactory.create',
        staticmethod(fake_create),
    )

    sm.add_from_cif_str('data_cif')
    assert 'dummy_from_str' in sm.names
    assert created['kwargs']['cif_str'] == 'data_cif'
