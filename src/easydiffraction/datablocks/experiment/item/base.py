# SPDX-FileCopyrightText: 2021-2026 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Base classes for experiment datablock items."""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING
from typing import Any
from typing import List

from easydiffraction.core.datablock import DatablockItem
from easydiffraction.datablocks.experiment.categories.data.factory import DataFactory
from easydiffraction.datablocks.experiment.categories.excluded_regions import ExcludedRegions
from easydiffraction.datablocks.experiment.categories.extinction import Extinction
from easydiffraction.datablocks.experiment.categories.instrument.factory import InstrumentFactory
from easydiffraction.datablocks.experiment.categories.linked_crystal import LinkedCrystal
from easydiffraction.datablocks.experiment.categories.linked_phases import LinkedPhases
from easydiffraction.datablocks.experiment.categories.peak.factory import PeakFactory
from easydiffraction.io.cif.serialize import experiment_to_cif
from easydiffraction.utils.logging import console
from easydiffraction.utils.logging import log
from easydiffraction.utils.utils import render_cif

if TYPE_CHECKING:
    from easydiffraction.datablocks.experiment.categories.experiment_type import ExperimentType
    from easydiffraction.datablocks.structure.collection import Structures


class ExperimentBase(DatablockItem):
    """Base class for all experiment datablock items with only core
    attributes.
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
        self._calculator = None
        self._calculator_type: str | None = None
        self._identity.datablock_entry_name = lambda: self.name

    @property
    def name(self) -> str:
        """Human-readable name of the experiment."""
        return self._name

    @name.setter
    def name(self, new: str) -> None:
        """Rename the experiment.

        Args:
            new: New name for this experiment.
        """
        self._name = new

    @property
    def type(self):  # TODO: Consider another name
        """Experiment type descriptor (sample form, probe, beam
        mode).
        """
        return self._type

    @property
    def as_cif(self) -> str:
        """Serialize this experiment to a CIF fragment."""
        return experiment_to_cif(self)

    def show_as_cif(self) -> None:
        """Pretty-print the experiment as CIF text."""
        experiment_cif = super().as_cif
        paragraph_title: str = f"Experiment 🔬 '{self.name}' as cif"
        console.paragraph(paragraph_title)
        render_cif(experiment_cif)

    @abstractmethod
    def _load_ascii_data_to_experiment(self, data_path: str) -> None:
        """Load ASCII data from file into the experiment data category.

        Args:
            data_path: Path to the ASCII file to load.
        """
        raise NotImplementedError()

    # ------------------------------------------------------------------
    #  Calculator (switchable-category pattern)
    # ------------------------------------------------------------------

    @property
    def calculator(self):
        """The active calculator instance for this experiment.

        Auto-resolved on first access from the experiment's data
        category ``calculator_support`` and
        ``CalculatorFactory._default_rules``.
        """
        if self._calculator is None:
            self._resolve_calculator()
        return self._calculator

    @property
    def calculator_type(self) -> str:
        """Tag of the active calculator backend (e.g. ``'cryspy'``)."""
        if self._calculator_type is None:
            self._resolve_calculator()
        return self._calculator_type

    @calculator_type.setter
    def calculator_type(self, tag: str) -> None:
        """Switch to a different calculator backend.

        Args:
            tag: Calculator tag (e.g. ``'cryspy'``, ``'crysfml'``,
                ``'pdffit'``).
        """
        from easydiffraction.analysis.calculators.factory import CalculatorFactory

        supported = self._supported_calculator_tags()
        if tag not in supported:
            log.warning(
                f"Unsupported calculator '{tag}' for experiment "
                f"'{self.name}'. Supported: {supported}. "
                f"For more information, use 'show_supported_calculator_types()'",
            )
            return
        self._calculator = CalculatorFactory.create(tag)
        self._calculator_type = tag
        console.paragraph(f"Calculator for experiment '{self.name}' changed to")
        console.print(tag)

    def show_supported_calculator_types(self) -> None:
        """Print a table of calculator backends supported by this
        experiment.
        """
        from easydiffraction.analysis.calculators.factory import CalculatorFactory

        supported_tags = self._supported_calculator_tags()
        all_classes = CalculatorFactory._supported_map()
        columns_headers = ['Type', 'Description']
        columns_alignment = ['left', 'left']
        columns_data = [
            [cls.type_info.tag, cls.type_info.description]
            for tag, cls in all_classes.items()
            if tag in supported_tags
        ]
        from easydiffraction.utils.utils import render_table

        console.paragraph('Supported calculator types')
        render_table(
            columns_headers=columns_headers,
            columns_alignment=columns_alignment,
            columns_data=columns_data,
        )

    def show_current_calculator_type(self) -> None:
        """Print the name of the currently active calculator."""
        console.paragraph('Current calculator type')
        console.print(self.calculator_type)

    def _resolve_calculator(self) -> None:
        """Auto-resolve the default calculator from the data category's
        ``calculator_support`` and
        ``CalculatorFactory._default_rules``.
        """
        from easydiffraction.analysis.calculators.factory import CalculatorFactory

        tag = CalculatorFactory.default_tag(
            scattering_type=self.type.scattering_type.value,
        )
        supported = self._supported_calculator_tags()
        if supported and tag not in supported:
            tag = supported[0]
        self._calculator = CalculatorFactory.create(tag)
        self._calculator_type = tag

    def _supported_calculator_tags(self) -> list[str]:
        """Return calculator tags supported by this experiment.

        Intersects the data category's ``calculator_support`` with
        calculators whose engines are importable.
        """
        from easydiffraction.analysis.calculators.factory import CalculatorFactory

        available = CalculatorFactory.supported_tags()
        data = getattr(self, '_data', None)
        if data is not None:
            data_support = getattr(data, 'calculator_support', None)
            if data_support and data_support.calculators:
                return [t for t in available if t in data_support.calculators]
        return available


class ScExperimentBase(ExperimentBase):
    """Base class for all single crystal experiments."""

    def __init__(
        self,
        *,
        name: str,
        type: ExperimentType,
    ) -> None:
        super().__init__(name=name, type=type)

        self._linked_crystal: LinkedCrystal = LinkedCrystal()
        self._extinction: Extinction = Extinction()
        self._instrument = InstrumentFactory.create_default_for(
            scattering_type=self.type.scattering_type.value,
            beam_mode=self.type.beam_mode.value,
            sample_form=self.type.sample_form.value,
        )
        self._data = DataFactory.create_default_for(
            sample_form=self.type.sample_form.value,
            beam_mode=self.type.beam_mode.value,
            scattering_type=self.type.scattering_type.value,
        )

    @abstractmethod
    def _load_ascii_data_to_experiment(self, data_path: str) -> None:
        """Load single crystal data from an ASCII file.

        Args:
            data_path: Path to data file with columns compatible with
                the beam mode.
        """
        pass

    @property
    def linked_crystal(self):
        """Linked crystal model for this experiment."""
        return self._linked_crystal

    @property
    def extinction(self):
        return self._extinction

    @property
    def instrument(self):
        return self._instrument

    @property
    def data(self):
        return self._data


class PdExperimentBase(ExperimentBase):
    """Base class for all powder experiments."""

    def __init__(
        self,
        *,
        name: str,
        type: ExperimentType,
    ) -> None:
        super().__init__(name=name, type=type)

        self._linked_phases: LinkedPhases = LinkedPhases()
        self._excluded_regions: ExcludedRegions = ExcludedRegions()
        self._peak_profile_type: str = PeakFactory.default_tag(
            scattering_type=self.type.scattering_type.value,
            beam_mode=self.type.beam_mode.value,
        )
        self._data = DataFactory.create_default_for(
            sample_form=self.type.sample_form.value,
            beam_mode=self.type.beam_mode.value,
            scattering_type=self.type.scattering_type.value,
        )
        self._peak = PeakFactory.create(self._peak_profile_type)

    def _get_valid_linked_phases(
        self,
        structures: Structures,
    ) -> List[Any]:
        """Get valid linked phases for this experiment.

        Args:
            structures: Collection of structures.

        Returns:
            A list of valid linked phases.
        """
        if not self.linked_phases:
            print('Warning: No linked phases defined. Returning empty pattern.')
            return []

        valid_linked_phases = []
        for linked_phase in self.linked_phases:
            if linked_phase._identity.category_entry_name not in structures.names:
                print(
                    f"Warning: Linked phase '{linked_phase.id.value}' not "
                    f'found in Structures {structures.names}. Skipping it.'
                )
                continue
            valid_linked_phases.append(linked_phase)

        if not valid_linked_phases:
            print(
                'Warning: None of the linked phases found in Structures. Returning empty pattern.'
            )

        return valid_linked_phases

    @abstractmethod
    def _load_ascii_data_to_experiment(self, data_path: str) -> None:
        """Load powder diffraction data from an ASCII file.

        Args:
            data_path: Path to data file with columns compatible with
                the beam mode (e.g. 2θ/I/σ for CWL, TOF/I/σ for TOF).
        """
        pass

    @property
    def linked_phases(self):
        """Collection of phases linked to this experiment."""
        return self._linked_phases

    @property
    def excluded_regions(self):
        """Collection of excluded regions for the x-grid."""
        return self._excluded_regions

    @property
    def data(self):
        return self._data

    @property
    def peak(self):
        """Peak category object with profile parameters and mixins."""
        return self._peak

    @property
    def peak_profile_type(self):
        """Currently selected peak profile type enum."""
        return self._peak_profile_type

    @peak_profile_type.setter
    def peak_profile_type(self, new_type: str):
        """Change the active peak profile type, if supported.

        Args:
            new_type: New profile type as tag string.
        """
        supported = PeakFactory.supported_for(
            scattering_type=self.type.scattering_type.value,
            beam_mode=self.type.beam_mode.value,
        )
        supported_tags = [k.type_info.tag for k in supported]

        if new_type not in supported_tags:
            log.warning(
                f"Unsupported peak profile '{new_type}'. "
                f'Supported peak profiles: {supported_tags}. '
                f"For more information, use 'show_supported_peak_profile_types()'",
            )
            return

        if self._peak is not None:
            log.warning(
                'Switching peak profile type discards existing peak parameters.',
            )

        self._peak = PeakFactory.create(new_type)
        self._peak_profile_type = new_type
        console.paragraph(f"Peak profile type for experiment '{self.name}' changed to")
        console.print(new_type)

    def show_supported_peak_profile_types(self):
        """Print available peak profile types for this experiment."""
        PeakFactory.show_supported(
            scattering_type=self.type.scattering_type.value,
            beam_mode=self.type.beam_mode.value,
        )

    def show_current_peak_profile_type(self):
        """Print the currently selected peak profile type."""
        console.paragraph('Current peak profile type')
        console.print(self.peak_profile_type)
