# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Collection of experiment data blocks."""

import pathlib

from typeguard import typechecked

from easydiffraction.core.datablock import DatablockCollection
from easydiffraction.datablocks.experiment.item.base import ExperimentBase
from easydiffraction.datablocks.experiment.item.factory import ExperimentFactory
from easydiffraction.io.edstar import edstar_body_from_text
from easydiffraction.utils.enums import VerbosityEnum
from easydiffraction.utils.logging import console


class Experiments(DatablockCollection):
    """
    Collection of Experiment data blocks.

    Provides convenience constructors for common creation patterns and
    helper methods for simple presentation of collection contents.
    """

    def __init__(self) -> None:
        super().__init__(item_type=ExperimentBase)

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    # TODO: Make abstract in DatablockCollection?
    @typechecked
    def create(
        self,
        *,
        name: str,
        sample_form: str | None = None,
        beam_mode: str | None = None,
        radiation_probe: str | None = None,
        scattering_type: str | None = None,
    ) -> None:
        """
        Add an experiment without associating a data file.

        Parameters
        ----------
        name : str
            Experiment identifier.
        sample_form : str | None, default=None
            Sample form (e.g. ``'powder'``).
        beam_mode : str | None, default=None
            Beam mode (e.g. ``'constant wavelength'``).
        radiation_probe : str | None, default=None
            Radiation probe (e.g. ``'neutron'``).
        scattering_type : str | None, default=None
            Scattering type (e.g. ``'bragg'``).
        """
        experiment = ExperimentFactory.from_scratch(
            name=name,
            sample_form=sample_form,
            beam_mode=beam_mode,
            radiation_probe=radiation_probe,
            scattering_type=scattering_type,
        )
        self.add(experiment)

    # TODO: Move to DatablockCollection?
    @typechecked
    def add_from_cif_str(
        self,
        cif_str: str,
    ) -> None:
        """
        Add an experiment from a CIF string.

        Parameters
        ----------
        cif_str : str
            Full CIF document as a string.
        """
        experiment = ExperimentFactory.from_cif_str(cif_str)
        self.add(experiment)

    # TODO: Move to DatablockCollection?
    @typechecked
    def add_from_cif_path(
        self,
        cif_path: str,
    ) -> None:
        """
        Add an experiment from a CIF file path.

        Parameters
        ----------
        cif_path : str
            Path to a CIF document.
        """
        experiment = ExperimentFactory.from_cif_path(cif_path)
        self.add(experiment)

    @typechecked
    def add_from_edstar_path(
        self,
        edstar_path: str,
    ) -> None:
        """
        Add an experiment from an EdSTAR file.

        Parameters
        ----------
        edstar_path : str
            Path to an EdSTAR experiment file.
        """
        body = edstar_body_from_text(pathlib.Path(edstar_path).read_text(encoding='utf-8'))
        experiment = ExperimentFactory.from_cif_str(body)
        self.add(experiment)

    @typechecked
    def add_from_data_path(
        self,
        *,
        name: str,
        data_path: str,
        sample_form: str | None = None,
        beam_mode: str | None = None,
        radiation_probe: str | None = None,
        scattering_type: str | None = None,
    ) -> None:
        """
        Add an experiment from a data file path.

        Parameters
        ----------
        name : str
            Experiment identifier.
        data_path : str
            Path to the measured data file.
        sample_form : str | None, default=None
            Sample form (e.g. ``'powder'``).
        beam_mode : str | None, default=None
            Beam mode (e.g. ``'constant wavelength'``).
        radiation_probe : str | None, default=None
            Radiation probe (e.g. ``'neutron'``).
        scattering_type : str | None, default=None
            Scattering type (e.g. ``'bragg'``).
        """
        verbosity = self._parent.verbosity.fit.value if self._parent is not None else None
        verb = VerbosityEnum(verbosity) if verbosity is not None else VerbosityEnum.FULL
        experiment = ExperimentFactory.from_scratch(
            name=name,
            sample_form=sample_form,
            beam_mode=beam_mode,
            radiation_probe=radiation_probe,
            scattering_type=scattering_type,
        )
        num_points = experiment._load_ascii_data_to_experiment(data_path)
        if verb is VerbosityEnum.FULL:
            console.paragraph('Data loaded successfully')
            console.print(f"Experiment 🔬 '{name}'. Number of data points: {num_points}.")
        elif verb is VerbosityEnum.SHORT:
            console.print(f"✅ Data loaded: Experiment 🔬 '{name}'. {num_points} points.")
        self.add(experiment)

    # TODO: Move to DatablockCollection?
    def show_names(self) -> None:
        """List all experiment names in the collection."""
        console.paragraph('Defined experiments' + ' 🔬')
        console.print(self.names)

    # TODO: Move to DatablockCollection?
    def show_params(self) -> None:
        """Show parameters of all experiments in the collection."""
        for experiment in self.values():
            experiment.show_params()
