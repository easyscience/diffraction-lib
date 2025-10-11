# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from typeguard import typechecked

from easydiffraction.core.datablocks import DatablockCollection
from easydiffraction.experiments.enums import BeamModeEnum
from easydiffraction.experiments.enums import RadiationProbeEnum
from easydiffraction.experiments.enums import SampleFormEnum
from easydiffraction.experiments.enums import ScatteringTypeEnum
from easydiffraction.experiments.experiment import Experiment
from easydiffraction.utils.formatting import paragraph


class Experiments(DatablockCollection):
    """Collection manager for multiple Experiment instances."""

    def __init__(self) -> None:
        super().__init__(item_type=Experiment)

    # --------------------
    # Add / Remove methods
    # --------------------

    # @typechecked
    # def add(self, experiment: BaseExperiment):
    #    """Add a pre-built experiment instance."""
    #    self[experiment.name] = experiment

    @typechecked
    def add_from_cif_path(self, cif_path: str):
        """Add a new experiment from a CIF file path."""
        experiment = Experiment(cif_path=cif_path)
        self.add(experiment)

    @typechecked
    def add_from_cif_str(self, cif_str: str):
        """Add a new experiment from CIF file content (string)."""
        experiment = Experiment(cif_str=cif_str)
        self.add(experiment)

    @typechecked
    def add_from_data_path(
        self,
        name: str,
        data_path: str,
        sample_form: str = SampleFormEnum.default().value,
        beam_mode: str = BeamModeEnum.default().value,
        radiation_probe: str = RadiationProbeEnum.default().value,
        scattering_type: str = ScatteringTypeEnum.default().value,
    ):
        """Add a new experiment from a data file path."""
        experiment = Experiment(
            name=name,
            data_path=data_path,
            sample_form=sample_form,
            beam_mode=beam_mode,
            radiation_probe=radiation_probe,
            scattering_type=scattering_type,
        )
        self.add(experiment)

    @typechecked
    def add_without_data(
        self,
        name: str,
        sample_form: str = SampleFormEnum.default().value,
        beam_mode: str = BeamModeEnum.default().value,
        radiation_probe: str = RadiationProbeEnum.default().value,
        scattering_type: str = ScatteringTypeEnum.default().value,
    ):
        """Add a new experiment without any data file."""
        experiment = Experiment(
            name=name,
            sample_form=sample_form,
            beam_mode=beam_mode,
            radiation_probe=radiation_probe,
            scattering_type=scattering_type,
        )
        self.add(experiment)

    @typechecked
    def remove(self, name: str) -> None:
        if name in self:
            del self[name]

    # ------------
    # Show methods
    # ------------

    def show_names(self) -> None:
        print(paragraph('Defined experiments' + ' 🔬'))
        print(self.names)

    def show_params(self) -> None:
        for exp in self.values():
            exp.show_params()

    # -----------
    # CIF methods
    # -----------

    # @property
    # def as_cif(self) -> str:
    #    # TODO: It is different from SampleModel.as_cif. Check it.
    #    return '\n\n'.join([exp.as_cif() for exp in self.values()])
