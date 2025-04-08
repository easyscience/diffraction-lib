import os.path

from easydiffraction.utils.formatting import paragraph
from easydiffraction.core.objects import Collection
from easydiffraction.experiments.experiment import (
    BaseExperiment,
    ExperimentFactory
)


class Experiments(Collection):
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
        sample_form=None,
        beam_mode=None,
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
        elif cif_path:
            self._add_from_cif_path(cif_path)
        elif cif_str:
            self._add_from_cif_string(cif_str)
        elif all([id, sample_form, beam_mode, radiation_probe, data_path]):
            self._add_from_data_path(
                id=id,
                sample_form=sample_form,
                beam_mode=beam_mode,
                radiation_probe=radiation_probe,
                data_path=data_path
            )
        else:
            raise ValueError("Provide either experiment, type parameters, cif_path, cif_str, or data_path")

    def _add_prebuilt_experiment(self, experiment):
        if not isinstance(experiment, BaseExperiment):
            raise TypeError("Expected an instance of BaseExperiment or its subclass.")
        self._experiments[experiment.name] = experiment

    def _add_from_cif_path(self, cif_path):
        print(f"Loading Experiment from CIF path...")
        raise NotImplementedError("CIF loading not implemented.")

    def _add_from_cif_string(self, cif_str):
        print("Loading Experiment from CIF string...")
        raise NotImplementedError("CIF loading not implemented.")

    def _add_from_data_path(self,
                            id,
                            sample_form,
                            beam_mode,
                            radiation_probe,
                            data_path):
        """
        Load an experiment from raw data ASCII file.
        """
        # TODO: Move this to the Experiment class
        print(paragraph("Loading measured data from ASCII file"))
        print(os.path.abspath(data_path))
        experiment = ExperimentFactory.create(
            id=id,
            sample_form=sample_form,
            beam_mode=beam_mode,
            radiation_probe=radiation_probe
        )
        experiment._load_ascii_data_to_experiment(data_path)
        self._experiments[experiment.name] = experiment

    def remove(self, experiment_id):
        if experiment_id in self._experiments:
            del self._experiments[experiment_id]

    def show_ids(self):
        print(paragraph("Defined experiments" + " 🔬"))
        print(list(self._experiments.keys()))

    def show_params(self):
        for exp in self._experiments.values():
            print(exp)

    def as_cif(self):
        return "\n\n".join([exp.as_cif() for exp in self._experiments.values()])
