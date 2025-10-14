# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING

from easydiffraction.core.datablocks import DatablockItem
from easydiffraction.experiments.categories.excluded_regions import ExcludedRegions
from easydiffraction.experiments.categories.linked_phases import LinkedPhases
from easydiffraction.experiments.categories.peak.factory import PeakFactory
from easydiffraction.experiments.categories.peak.factory import PeakProfileTypeEnum
from easydiffraction.experiments.datastore.factory import DatastoreFactory
from easydiffraction.io.cif.serialize import experiment_to_cif
from easydiffraction.utils.formatting import paragraph
from easydiffraction.utils.formatting import warning
from easydiffraction.utils.utils import render_cif
from easydiffraction.utils.utils import render_table

if TYPE_CHECKING:
    from easydiffraction.experiments.categories.experiment_type import ExperimentType


class ExperimentBase(DatablockItem):
    """Base class for all experiments with only core attributes.

    Wraps experiment type, instrument and datastore.
    """

    def __init__(
        self,
        *,
        name: str,
        type: ExperimentType,
    ):
        super().__init__()
        self._name = name
        self._type = type
        self._datastore = DatastoreFactory.create(
            sample_form=self.type.sample_form.value,
            beam_mode=self.type.beam_mode.value,
        )
        self._identity.datablock_entry_name = lambda: self.name

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, new: str) -> None:
        self._name = new

    @property
    def type(self):  # TODO: Consider another name
        return self._type

    @property
    def datastore(self):
        return self._datastore

    @property
    def as_cif(self) -> str:
        return experiment_to_cif(self)

    def show_as_cif(self) -> None:
        experiment_cif = super().as_cif
        datastore_cif = self.datastore.as_truncated_cif
        cif_text: str = f'{experiment_cif}\n\n{datastore_cif}'
        paragraph_title: str = paragraph(f"Experiment 🔬 '{self.name}' as cif")
        render_cif(cif_text, paragraph_title)

    @abstractmethod
    def _load_ascii_data_to_experiment(self, data_path: str) -> None:
        raise NotImplementedError()


class PdExperimentBase(ExperimentBase):
    """Base class for all powder experiments."""

    def __init__(
        self,
        *,
        name: str,
        type: ExperimentType,
    ) -> None:
        super().__init__(name=name, type=type)

        self._peak_profile_type: PeakProfileTypeEnum = PeakProfileTypeEnum.default(
            self.type.scattering_type.value,
            self.type.beam_mode.value,
        )
        self._peak = PeakFactory.create(
            scattering_type=self.type.scattering_type.value,
            beam_mode=self.type.beam_mode.value,
            profile_type=self._peak_profile_type,
        )

        self._linked_phases: LinkedPhases = LinkedPhases()
        self._excluded_regions: ExcludedRegions = ExcludedRegions()

    @abstractmethod
    def _load_ascii_data_to_experiment(self, data_path: str) -> None:
        pass

    @property
    def peak(self) -> str:
        return self._peak

    @peak.setter
    def peak(self, value):
        self._peak = value

    @property
    def linked_phases(self) -> str:
        return self._linked_phases

    @property
    def excluded_regions(self) -> str:
        return self._excluded_regions

    @property
    def peak_profile_type(self):
        return self._peak_profile_type

    @peak_profile_type.setter
    def peak_profile_type(self, new_type: str | PeakProfileTypeEnum):
        if isinstance(new_type, str):
            try:
                new_type = PeakProfileTypeEnum(new_type)
            except ValueError:
                print(warning(f"Unknown peak profile type '{new_type}'"))
                return

        supported_types = list(
            PeakFactory._supported[self.type.scattering_type.value][
                self.type.beam_mode.value
            ].keys()
        )

        if new_type not in supported_types:
            print(warning(f"Unsupported peak profile '{new_type.value}'"))
            print(f'Supported peak profiles: {supported_types}')
            print("For more information, use 'show_supported_peak_profile_types()'")
            return

        self._peak = PeakFactory.create(
            scattering_type=self.type.scattering_type.value,
            beam_mode=self.type.beam_mode.value,
            profile_type=new_type,
        )
        self._peak_profile_type = new_type
        print(paragraph(f"Peak profile type for experiment '{self.name}' changed to"))
        print(new_type.value)

    def show_supported_peak_profile_types(self):
        columns_headers = ['Peak profile type', 'Description']
        columns_alignment = ['left', 'left']
        columns_data = []

        scattering_type = self.type.scattering_type.value
        beam_mode = self.type.beam_mode.value

        for profile_type in PeakFactory._supported[scattering_type][beam_mode]:
            columns_data.append([profile_type.value, profile_type.description()])

        print(paragraph('Supported peak profile types'))
        render_table(
            columns_headers=columns_headers,
            columns_alignment=columns_alignment,
            columns_data=columns_data,
        )

    def show_current_peak_profile_type(self):
        print(paragraph('Current peak profile type'))
        print(self.peak_profile_type)
