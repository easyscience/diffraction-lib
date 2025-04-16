import pytest
import numpy as np
from unittest.mock import MagicMock, patch

from easydiffraction.experiments.experiment import (
    BaseExperiment,
    PowderExperiment,
    SingleCrystalExperiment,
    ExperimentFactory,
    Experiment,
)
from easydiffraction.experiments.components.experiment_type import ExperimentType
from easydiffraction.core.constants import (
    DEFAULT_SAMPLE_FORM,
    DEFAULT_BEAM_MODE,
    DEFAULT_RADIATION_PROBE,
    DEFAULT_PEAK_PROFILE_TYPE,
    DEFAULT_BACKGROUND_TYPE,
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


def test_base_experiment_initialization():
    mock_type = MagicMock()
    mock_type.beam_mode.value = DEFAULT_BEAM_MODE
    mock_type.radiation_probe.value = "xray"
    mock_type.sample_form.value = DEFAULT_SAMPLE_FORM
    experiment = ConcreteBaseExperiment(name="TestExperiment", type=mock_type)
    assert experiment.name == "TestExperiment"
    assert experiment.type == mock_type


def test_base_experiment_as_cif():
    # Mock the type object
    mock_type = MagicMock()
    mock_type.beam_mode.value = DEFAULT_BEAM_MODE
    mock_type.diffraction_type.value = "x-ray"
    mock_type.as_cif.return_value = "type_cif"
    mock_type.sample_form.value = DEFAULT_SAMPLE_FORM
    # Create a concrete instance of BaseExperiment
    experiment = ConcreteBaseExperiment(name="TestExperiment", type=mock_type)

    # Mock the instrument object
    experiment.instrument = MagicMock()
    experiment.instrument.as_cif.return_value = "instrument_cif"

    # Mock other components if necessary
    experiment.peak = MagicMock()
    experiment.peak.as_cif.return_value = "peak_cif"

    experiment.linked_phases = MagicMock()
    experiment.linked_phases.as_cif.return_value = "linked_phases_cif"

    experiment.background = MagicMock()
    experiment.background.as_cif.return_value = "background_cif"

    experiment.datastore.pattern.x = [1.0]
    experiment.datastore.pattern.meas = [2.0]
    experiment.datastore.pattern.meas_su = [0.1]

    # Call the as_cif method and verify the output
    cif_output = experiment.as_cif()
    assert "data_TestExperiment" in cif_output
    assert "type_cif" in cif_output
    assert "instrument_cif" in cif_output
    assert "peak_cif" in cif_output
    assert "linked_phases_cif" in cif_output
    assert "background_cif" in cif_output


def test_powder_experiment_initialization():
    mock_type = MagicMock()
    mock_type.beam_mode.value = DEFAULT_BEAM_MODE
    mock_type.radiation_probe.value = "xray"
    mock_type.sample_form.value = DEFAULT_SAMPLE_FORM
    experiment = PowderExperiment(name="PowderTest", type=mock_type)
    assert experiment.name == "PowderTest"
    assert experiment.type == mock_type
    assert experiment.peak is not None
    assert experiment.background is not None


def test_powder_experiment_load_ascii_data():
    mock_type = MagicMock()
    mock_type.beam_mode.value = DEFAULT_BEAM_MODE
    mock_type.radiation_probe.value = "xray"
    mock_type.sample_form.value = DEFAULT_SAMPLE_FORM
    experiment = PowderExperiment(name="PowderTest", type=mock_type)
    experiment.datastore = MagicMock()
    experiment.datastore.pattern = MagicMock()
    mock_data = np.array([[1.0, 2.0, 0.1], [2.0, 3.0, 0.2]])
    with patch("numpy.loadtxt", return_value=mock_data):
        experiment._load_ascii_data_to_experiment("mock_path")
    assert np.array_equal(experiment.datastore.pattern.x, mock_data[:, 0])
    assert np.array_equal(experiment.datastore.pattern.meas, mock_data[:, 1])
    assert np.array_equal(experiment.datastore.pattern.meas_su, mock_data[:, 2])


def test_powder_experiment_show_meas_chart():
    mock_type = MagicMock()
    mock_type.beam_mode.value = DEFAULT_BEAM_MODE
    mock_type.radiation_probe.value = "xray"
    mock_type.sample_form.value = DEFAULT_SAMPLE_FORM
    experiment = PowderExperiment(name="PowderTest", type=mock_type)
    experiment.datastore = MagicMock()
    experiment.datastore.pattern.x = [1, 2, 3]
    experiment.datastore.pattern.meas = [10, 20, 30]
    with patch("easydiffraction.utils.chart_plotter.ChartPlotter.plot") as mock_plot:
        experiment.show_meas_chart()
        mock_plot.assert_called_once()


def test_single_crystal_experiment_initialization():
    mock_type = MagicMock()
    mock_type.beam_mode.value = DEFAULT_BEAM_MODE
    mock_type.radiation_probe.value = "xray"
    mock_type.sample_form.value = DEFAULT_SAMPLE_FORM
    experiment = ConcreteSingleCrystalExperiment(name="SingleCrystalTest", type=mock_type)
    assert experiment.name == "SingleCrystalTest"
    assert experiment.type == mock_type
    assert experiment.linked_crystal is None


def test_single_crystal_experiment_show_meas_chart():
    mock_type = MagicMock()
    mock_type.beam_mode.value = DEFAULT_BEAM_MODE
    mock_type.radiation_probe.value = "xray"
    mock_type.sample_form.value = DEFAULT_SAMPLE_FORM
    experiment = ConcreteSingleCrystalExperiment(name="SingleCrystalTest", type=mock_type)
    with patch("builtins.print") as mock_print:
        experiment.show_meas_chart()
        mock_print.assert_called_once_with("Showing measured data chart is not implemented yet.")


def test_experiment_factory_create_powder():
    experiment = ExperimentFactory.create(
        name="PowderTest",
        sample_form="powder",
        beam_mode=DEFAULT_BEAM_MODE,
        radiation_probe=DEFAULT_RADIATION_PROBE,
    )
    assert isinstance(experiment, PowderExperiment)
    assert experiment.name == "PowderTest"

# to be added once single crystal works
def no_test_experiment_factory_create_single_crystal():
    experiment = ExperimentFactory.create(
        name="SingleCrystalTest",
        sample_form="single crystal",
        beam_mode=DEFAULT_BEAM_MODE,
        radiation_probe=DEFAULT_RADIATION_PROBE,
    )
    assert isinstance(experiment, SingleCrystalExperiment)
    assert experiment.name == "SingleCrystalTest"


def test_experiment_method():
    mock_data = np.array([[1.0, 2.0, 0.1], [2.0, 3.0, 0.2]])
    with patch("numpy.loadtxt", return_value=mock_data):
        experiment = Experiment(
            name="ExperimentTest",
            sample_form="powder",
            beam_mode=DEFAULT_BEAM_MODE,
            radiation_probe=DEFAULT_RADIATION_PROBE,
            data_path="mock_path",
        )
    assert isinstance(experiment, PowderExperiment)
    assert experiment.name == "ExperimentTest"
    assert np.array_equal(experiment.datastore.pattern.x, mock_data[:, 0])
    assert np.array_equal(experiment.datastore.pattern.meas, mock_data[:, 1])
    assert np.array_equal(experiment.datastore.pattern.meas_su, mock_data[:, 2])
