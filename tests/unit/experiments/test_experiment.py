from unittest.mock import MagicMock
from unittest.mock import patch

import numpy as np
import pytest

from easydiffraction.experiments.components.experiment_type import BeamModeEnum
from easydiffraction.experiments.components.experiment_type import ExperimentType
from easydiffraction.experiments.components.experiment_type import RadiationProbeEnum
from easydiffraction.experiments.components.experiment_type import SampleFormEnum
from easydiffraction.experiments.components.experiment_type import ScatteringTypeEnum
from easydiffraction.experiments.experiment import BaseExperiment
from easydiffraction.experiments.experiment import Experiment
from easydiffraction.experiments.experiment import ExperimentFactory
from easydiffraction.experiments.experiment import PowderExperiment
from easydiffraction.experiments.experiment import SingleCrystalExperiment


@pytest.fixture
def expt_type():
    return ExperimentType(
        sample_form=SampleFormEnum.default(),
        beam_mode=BeamModeEnum.default(),
        radiation_probe='xray',
        scattering_type='bragg',
    )


class ConcreteBaseExperiment(BaseExperiment):
    """Concrete implementation of BaseExperiment for testing."""

    def _load_ascii_data_to_experiment(self, data_path):
        pass

    def show_meas_chart(self, x_min=None, x_max=None):
        pass


class ConcreteSingleCrystalExperiment(SingleCrystalExperiment):
    """Concrete implementation of SingleCrystalExperiment for testing."""

    def _load_ascii_data_to_experiment(self, data_path):
        pass


def test_base_experiment_initialization(expt_type):
    experiment = ConcreteBaseExperiment(name='TestExperiment', type=expt_type)
    assert experiment.name == 'TestExperiment'
    assert experiment.type == expt_type


def test_powder_experiment_initialization(expt_type):
    experiment = PowderExperiment(name='PowderTest', type=expt_type)
    assert experiment.name == 'PowderTest'
    assert experiment.type == expt_type
    assert experiment.background is not None
    assert experiment.peak is not None
    assert experiment.linked_phases is not None


def test_powder_experiment_load_ascii_data(expt_type):
    experiment = PowderExperiment(name='PowderTest', type=expt_type)
    experiment.datastore = MagicMock()
    mock_data = np.array([[1.0, 2.0, 0.1], [2.0, 3.0, 0.2]])
    with patch('numpy.loadtxt', return_value=mock_data):
        experiment._load_ascii_data_to_experiment('mock_path')
    assert np.array_equal(experiment.datastore.x, mock_data[:, 0])
    assert np.array_equal(experiment.datastore.meas, mock_data[:, 1])
    assert np.array_equal(experiment.datastore.meas_su, mock_data[:, 2])


def test_single_crystal_experiment_initialization(expt_type):
    experiment = ConcreteSingleCrystalExperiment(name='SingleCrystalTest', type=expt_type)
    assert experiment.name == 'SingleCrystalTest'
    assert experiment.type == expt_type
    assert experiment.linked_crystal is None


def test_single_crystal_experiment_show_meas_chart(expt_type):
    experiment = ConcreteSingleCrystalExperiment(name='SingleCrystalTest', type=expt_type)
    with patch('builtins.print') as mock_print:
        experiment.show_meas_chart()
        mock_print.assert_called_once_with('Showing measured data chart is not implemented yet.')


def test_experiment_factory_create_powder():
    experiment = ExperimentFactory.create(
        name='PowderTest',
        sample_form=SampleFormEnum.POWDER.value,
        beam_mode=BeamModeEnum.default().value,
        radiation_probe=RadiationProbeEnum.default().value,
        scattering_type=ScatteringTypeEnum.default().value,
    )
    assert isinstance(experiment, PowderExperiment)
    assert experiment.name == 'PowderTest'


# to be added once single crystal works
def no_test_experiment_factory_create_single_crystal():
    experiment = ExperimentFactory.create(
        name='SingleCrystalTest',
        sample_form=SampleFormEnum.SINGLE_CRYSTAL.value,
        beam_mode=BeamModeEnum.default().value,
        radiation_probe=RadiationProbeEnum.default().value,
    )
    assert isinstance(experiment, SingleCrystalExperiment)
    assert experiment.name == 'SingleCrystalTest'


def test_experiment_method():
    mock_data = np.array([[1.0, 2.0, 0.1], [2.0, 3.0, 0.2]])
    with patch('numpy.loadtxt', return_value=mock_data):
        experiment = Experiment(
            name='ExperimentTest',
            sample_form='powder',
            beam_mode=BeamModeEnum.default().value,
            radiation_probe=RadiationProbeEnum.default().value,
            data_path='mock_path',
        )
    assert isinstance(experiment, PowderExperiment)
    assert experiment.name == 'ExperimentTest'
    assert np.array_equal(experiment.datastore.x, mock_data[:, 0])
    assert np.array_equal(experiment.datastore.meas, mock_data[:, 1])
    assert np.array_equal(experiment.datastore.meas_su, mock_data[:, 2])


def test_experiment_factory_invalid_args_missing_required():
    # Missing required 'name'
    with pytest.raises(ValueError, match='Invalid argument combination'):
        ExperimentFactory.create(
            sample_form=SampleFormEnum.POWDER.value,
            beam_mode=BeamModeEnum.default().value,
            radiation_probe=RadiationProbeEnum.default().value,
            scattering_type=ScatteringTypeEnum.default().value,
        )


def test_experiment_factory_conflicting_args_cif_and_name():
    # Conflicting: 'cif_path' with 'name'
    with pytest.raises(ValueError, match='Invalid argument combination'):
        ExperimentFactory.create(name='ConflictTest', cif_path='path/to/file.cif')


def test_experiment_factory_conflicting_args_data_and_cif():
    # Conflicting: multiple conflicting input sources
    with pytest.raises(ValueError, match='Invalid argument combination'):
        ExperimentFactory.create(name='ConflictTest', data_path='mock_path', cif_str='cif content')


def test_experiment_factory_invalid_args_unsupported_key():
    # Unsupported keyword
    with pytest.raises(ValueError, match='Invalid argument combination'):
        ExperimentFactory.create(foo='bar')
