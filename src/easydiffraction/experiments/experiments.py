# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction Python Library contributors <https://github.com/easyscience/diffraction-lib>
# SPDX-License-Identifier: BSD-3-Clause

from typing import Dict
from typing import List

from easydiffraction.core.objects import Collection
from easydiffraction.experiments.components.experiment_type import BeamModeEnum
from easydiffraction.experiments.components.experiment_type import RadiationProbeEnum
from easydiffraction.experiments.components.experiment_type import SampleFormEnum
from easydiffraction.experiments.components.experiment_type import ScatteringTypeEnum
from easydiffraction.experiments.experiment import BaseExperiment
from easydiffraction.experiments.experiment import Experiment
from easydiffraction.utils.decorators import enforce_type
from easydiffraction.utils.formatting import paragraph


class Experiments(Collection):
    """
    Collection manager for multiple Experiment instances.
    """

    @property
    def _child_class(self):
        return BaseExperiment

    def __init__(self) -> None:
        super().__init__()
        self._experiments: Dict[str, BaseExperiment] = self._items  # Alias for legacy support

    def add(self, experiment: BaseExperiment):
        """
        Add a pre-built experiment instance.
        """
        self._add_prebuilt_experiment(experiment)

    def add_from_cif_path(self, cif_path: str):
        """
        Add a new experiment from a CIF file path.
        """
        experiment = Experiment(cif_path=cif_path)
        self._add_prebuilt_experiment(experiment)

    def add_from_cif_str(self, cif_str: str):
        """
        Add a new experiment from CIF file content (string).
        """
        experiment = Experiment(cif_str=cif_str)
        self._add_prebuilt_experiment(experiment)

    def add_from_data_path(
        self,
        name: str,
        data_path: str,
        sample_form: str = SampleFormEnum.default().value,
        beam_mode: str = BeamModeEnum.default().value,
        radiation_probe: str = RadiationProbeEnum.default().value,
        scattering_type: str = ScatteringTypeEnum.default().value,
    ):
        """
        Add a new experiment from a data file path.
        """
        experiment = Experiment(
            name=name,
            data_path=data_path,
            sample_form=sample_form,
            beam_mode=beam_mode,
            radiation_probe=radiation_probe,
            scattering_type=scattering_type,
        )
        self._add_prebuilt_experiment(experiment)

    def add_without_data(
        self,
        name: str,
        sample_form: str = SampleFormEnum.default().value,
        beam_mode: str = BeamModeEnum.default().value,
        radiation_probe: str = RadiationProbeEnum.default().value,
        scattering_type: str = ScatteringTypeEnum.default().value,
    ):
        """
        Add a new experiment without any data file.
        """
        experiment = Experiment(
            name=name,
            sample_form=sample_form,
            beam_mode=beam_mode,
            radiation_probe=radiation_probe,
            scattering_type=scattering_type,
        )
        self._add_prebuilt_experiment(experiment)

    @enforce_type
    def _add_prebuilt_experiment(self, experiment: BaseExperiment):
        self._experiments[experiment.name] = experiment

    def remove(self, experiment_id: str) -> None:
        if experiment_id in self._experiments:
            del self._experiments[experiment_id]

    def show_names(self) -> None:
        print(paragraph('Defined experiments' + ' 🔬'))
        print(self.ids)

    @property
    def ids(self) -> List[str]:
        return list(self._experiments.keys())

    def show_params(self) -> None:
        for exp in self._experiments.values():
            print(exp)

    def as_cif(self) -> str:
        return '\n\n'.join([exp.as_cif() for exp in self._experiments.values()])
