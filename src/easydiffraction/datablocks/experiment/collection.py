# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Collection of experiment data blocks."""

from typeguard import typechecked

from easydiffraction.core.datablock import DatablockCollection
from easydiffraction.datablocks.experiment.item.base import ExperimentBase
from easydiffraction.datablocks.experiment.item.factory import ExperimentFactory
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
        experiment = ExperimentFactory.from_data_path(
            name=name,
            data_path=data_path,
            sample_form=sample_form,
            beam_mode=beam_mode,
            radiation_probe=radiation_probe,
            scattering_type=scattering_type,
        )
        self.add(experiment)

    @typechecked
    def add_from_zip_path(
        self,
        *,
        name_prefix: str,
        zip_path: str,
        sample_form: str | None = None,
        beam_mode: str | None = None,
        radiation_probe: str | None = None,
        scattering_type: str | None = None,
    ) -> None:
        """
        Add experiments from data files inside a ZIP archive.

        Each file in the archive becomes a separate experiment named
        ``'{name_prefix}_{i}'`` where *i* is a one-based index matching
        the lexicographic file order.

        Parameters
        ----------
        name_prefix : str
            Common prefix for generated experiment names.
        zip_path : str
            Path to the ZIP archive containing data files.
        sample_form : str | None, default=None
            Sample form (e.g. ``'powder'``).
        beam_mode : str | None, default=None
            Beam mode (e.g. ``'constant wavelength'``).
        radiation_probe : str | None, default=None
            Radiation probe (e.g. ``'neutron'``).
        scattering_type : str | None, default=None
            Scattering type (e.g. ``'bragg'``).
        """
        experiments = ExperimentFactory.from_zip_path(
            name_prefix=name_prefix,
            zip_path=zip_path,
            sample_form=sample_form,
            beam_mode=beam_mode,
            radiation_probe=radiation_probe,
            scattering_type=scattering_type,
        )
        for experiment in experiments:
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
