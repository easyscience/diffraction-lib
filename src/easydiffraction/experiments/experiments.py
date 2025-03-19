import numpy as np
from easydiffraction.experiments.factory import ExperimentFactory
from easydiffraction.experiments.base_experiment import BaseExperiment
from easydiffraction.base_collection import BaseCollection


# ==========================================================================
# User-facing Experiment() constructor - exposed for import from __init__.py
# ==========================================================================
def Experiment(
    *,
    id=None,
    diffr_mode=None,
    expt_mode=None,
    radiation_probe=None,
    experiment=None,
    cif_path=None,
    cif_str=None,
    data_path=None
):
    """
    Shorthand to create an Experiment using the factory.
    This keeps the API simple for end-users.

    Parameters:
        id (str): Unique ID of the experiment.
        diffr_mode (str): Diffraction mode, e.g., 'powder' or 'single_crystal'.
        expt_mode (str): Experiment mode, e.g., 'constant_wavelength'.
        radiation_probe (str): Probe type, e.g., 'neutron' or 'xray'.
        experiment (BaseExperiment): Prebuilt experiment object.
        cif_path (str): Path to CIF file for loading the experiment (Not implemented).
        cif_str (str): CIF string for loading the experiment (Not implemented).
        data_path (str): Path to ASCII data file (x, y, sy) (Experimental).

    Returns:
        BaseExperiment: Created experiment instance.
    """

    # Support prebuilt experiment
    if experiment:
        return experiment

    # Support CIF path or string (not implemented yet)
    if cif_path:
        raise NotImplementedError("CIF loading not implemented.")
    if cif_str:
        raise NotImplementedError("CIF loading not implemented.")

    # Support loading from ASCII data (experimental)
    if data_path:
        print(f"Loading Experiment from ASCII data path: {data_path}")
        # Example experiment - user needs to provide modes for context
        if not all([id, diffr_mode, expt_mode, radiation_probe]):
            raise ValueError("To create an experiment from data_path, you must specify id, diffr_mode, expt_mode, and radiation_probe.")

        experiment = ExperimentFactory.create_experiment(
            id=id,
            diffr_mode=diffr_mode,
            expt_mode=expt_mode,
            radiation_probe=radiation_probe
        )

        # Load data and assign to experiment
        _load_ascii_data_to_experiment(experiment, data_path)
        return experiment

    # Support creation by type
    if all([id, diffr_mode, expt_mode, radiation_probe]):
        return ExperimentFactory.create_experiment(
            id=id,
            diffr_mode=diffr_mode,
            expt_mode=expt_mode,
            radiation_probe=radiation_probe
        )

    raise ValueError("You must provide an experiment, type parameters, cif_path, cif_str, or data_path.")


class Experiments(BaseCollection):
    """
    Collection manager for multiple Experiment instances.
    """

    def __init__(self):
        super().__init__()
        self._experiments = self._items  # Alias for legacy support

    def add(
        self,
        experiment=None,
        id=None,
        diffr_mode=None,
        expt_mode=None,
        radiation_probe=None,
        cif_path=None,
        cif_str=None,
        data_path=None
    ):
        """
        Add a new experiment to the collection.
        """
        if experiment:
            self._add_prebuilt_experiment(experiment)
        elif data_path:
            self._add_from_data_path(
                id=id,
                diffr_mode=diffr_mode,
                expt_mode=expt_mode,
                radiation_probe=radiation_probe,
                data_path=data_path
            )
        elif all([id, diffr_mode, expt_mode, radiation_probe]):
            self._add_by_type(id, diffr_mode, expt_mode, radiation_probe)
        elif cif_path:
            self._add_from_cif_path(cif_path)
        elif cif_str:
            self._add_from_cif_string(cif_str)
        else:
            raise ValueError("Provide either experiment, type parameters, cif_path, cif_str, or data_path")

    def _add_prebuilt_experiment(self, experiment):
        if not isinstance(experiment, BaseExperiment):
            raise TypeError("Expected an instance of BaseExperiment or its subclass.")
        self._experiments[experiment.id] = experiment

    def _add_by_type(self, id, diffr_mode, expt_mode, radiation_probe):
        experiment = Experiment(
            id=id,
            diffr_mode=diffr_mode,
            expt_mode=expt_mode,
            radiation_probe=radiation_probe
        )
        self._experiments[experiment.id] = experiment

    def _add_from_cif_path(self, cif_path):
        print(f"Loading Experiment from CIF path: {cif_path}")
        raise NotImplementedError("CIF loading not implemented.")

    def _add_from_cif_string(self, cif_str):
        print("Loading Experiment from CIF string...")
        raise NotImplementedError("CIF loading not implemented.")

    def _add_from_data_path(self, id, diffr_mode, expt_mode, radiation_probe, data_path):
        """
        Load an experiment from raw data ASCII file.
        """
        print(f"Loading Experiment from ASCII data file: {data_path}")
        experiment = Experiment(
            id=id,
            diffr_mode=diffr_mode,
            expt_mode=expt_mode,
            radiation_probe=radiation_probe
        )
        _load_ascii_data_to_experiment(experiment, data_path)
        self._experiments[experiment.id] = experiment

    def remove(self, experiment_id):
        if experiment_id in self._experiments:
            del self._experiments[experiment_id]

    def show_ids(self):
        print("Defined experiments:", list(self._experiments.keys()))

    def show_params(self):
        for exp in self._experiments.values():
            print(exp)

    def as_cif(self):
        return "\n\n".join([exp.as_cif() for exp in self._experiments.values()])

    def __getitem__(self, experiment_id):
        return self._experiments[experiment_id]


# ===========================================================
# Helper Function to Load ASCII Data into Experiment
# ===========================================================
def _load_ascii_data_to_experiment(experiment, data_path):
    """
    Loads x, y, sy values from an ASCII data file into the experiment.

    The file must be structured as:
        x  y  sy
    """
    try:
        data = np.loadtxt(data_path)
    except Exception as e:
        raise IOError(f"Failed to read data from {data_path}: {e}")

    if data.shape[1] < 2:
        raise ValueError("Data file must have at least two columns: x and y.")

    if data.shape[1] < 3:
        print("Warning: No uncertainty (sy) column provided. Defaulting to sqrt(y).")
        sy = np.sqrt(np.abs(data[:, 1]))
    else:
        sy = data[:, 2]

    # Attach the data to the experiment's datastore
    x = data[:, 0]
    y = data[:, 1]
    sy = data[:, 2] if data.shape[1] > 2 else np.sqrt(y)

    # Store in the new structure!
    experiment.datastore.pattern.x = x
    experiment.datastore.pattern.meas = y
    experiment.datastore.pattern.meas_su = sy

    print(f"Loaded data for experiment '{experiment.id}' with {len(x)} points.")