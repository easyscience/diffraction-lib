# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Base classes for experiment datablock items."""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING
from typing import Any
from typing import List

from easydiffraction.core.datablock import DatablockItem
from easydiffraction.datablocks.experiment.categories.data.factory import DataFactory
from easydiffraction.datablocks.experiment.categories.excluded_regions.factory import (
    ExcludedRegionsFactory,
)
from easydiffraction.datablocks.experiment.categories.extinction.factory import ExtinctionFactory
from easydiffraction.datablocks.experiment.categories.instrument.factory import InstrumentFactory
from easydiffraction.datablocks.experiment.categories.linked_crystal.factory import (
    LinkedCrystalFactory,
)
from easydiffraction.datablocks.experiment.categories.linked_phases.factory import (
    LinkedPhasesFactory,
)
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

        Args:     new: New name for this experiment.
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

        Args:     data_path: Path to the ASCII file to load.
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

        Args:     tag: Calculator tag (e.g. ``'cryspy'``, ``'crysfml'``,
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

        self._extinction_type: str = ExtinctionFactory.default_tag()
        self._extinction = ExtinctionFactory.create(self._extinction_type)
        self._linked_crystal_type: str = LinkedCrystalFactory.default_tag()
        self._linked_crystal = LinkedCrystalFactory.create(self._linked_crystal_type)
        self._instrument_type: str = InstrumentFactory.default_tag(
            scattering_type=self.type.scattering_type.value,
            beam_mode=self.type.beam_mode.value,
            sample_form=self.type.sample_form.value,
        )
        self._instrument = InstrumentFactory.create(self._instrument_type)
        self._data_type: str = DataFactory.default_tag(
            sample_form=self.type.sample_form.value,
            beam_mode=self.type.beam_mode.value,
            scattering_type=self.type.scattering_type.value,
        )
        self._data = DataFactory.create(self._data_type)

    @abstractmethod
    def _load_ascii_data_to_experiment(self, data_path: str) -> None:
        """Load single crystal data from an ASCII file.

        Args:     data_path: Path to data file with columns compatible
        with         the beam mode.
        """
        pass

    # ------------------------------------------------------------------
    #  Extinction (switchable-category pattern)
    # ------------------------------------------------------------------

    @property
    def extinction(self):
        """Active extinction correction model."""
        return self._extinction

    @property
    def extinction_type(self) -> str:
        """Tag of the active extinction correction model."""
        return self._extinction_type

    @extinction_type.setter
    def extinction_type(self, new_type: str) -> None:
        """Switch to a different extinction correction model.

        Args:     new_type: Extinction tag (e.g. ``'shelx'``).
        """
        supported_tags = ExtinctionFactory.supported_tags()
        if new_type not in supported_tags:
            log.warning(
                f"Unsupported extinction type '{new_type}'. "
                f'Supported: {supported_tags}. '
                f"For more information, use 'show_supported_extinction_types()'",
            )
            return

        self._extinction = ExtinctionFactory.create(new_type)
        self._extinction_type = new_type
        console.paragraph(f"Extinction type for experiment '{self.name}' changed to")
        console.print(new_type)

    def show_supported_extinction_types(self) -> None:
        """Print a table of supported extinction correction models."""
        ExtinctionFactory.show_supported()

    def show_current_extinction_type(self) -> None:
        """Print the currently used extinction correction model."""
        console.paragraph('Current extinction type')
        console.print(self.extinction_type)

    # ------------------------------------------------------------------
    #  Linked crystal (switchable-category pattern)
    # ------------------------------------------------------------------

    @property
    def linked_crystal(self):
        """Linked crystal model for this experiment."""
        return self._linked_crystal

    @property
    def linked_crystal_type(self) -> str:
        """Tag of the active linked-crystal reference type."""
        return self._linked_crystal_type

    @linked_crystal_type.setter
    def linked_crystal_type(self, new_type: str) -> None:
        """Switch to a different linked-crystal reference type.

        Args:     new_type: Linked-crystal tag (e.g. ``'default'``).
        """
        supported_tags = LinkedCrystalFactory.supported_tags()
        if new_type not in supported_tags:
            log.warning(
                f"Unsupported linked crystal type '{new_type}'. "
                f'Supported: {supported_tags}. '
                f"For more information, use 'show_supported_linked_crystal_types()'",
            )
            return

        self._linked_crystal = LinkedCrystalFactory.create(new_type)
        self._linked_crystal_type = new_type
        console.paragraph(f"Linked crystal type for experiment '{self.name}' changed to")
        console.print(new_type)

    def show_supported_linked_crystal_types(self) -> None:
        """Print a table of supported linked-crystal reference types."""
        LinkedCrystalFactory.show_supported()

    def show_current_linked_crystal_type(self) -> None:
        """Print the currently used linked-crystal reference type."""
        console.paragraph('Current linked crystal type')
        console.print(self.linked_crystal_type)

    # ------------------------------------------------------------------
    #  Instrument (switchable-category pattern)
    # ------------------------------------------------------------------

    @property
    def instrument(self):
        """Active instrument model for this experiment."""
        return self._instrument

    @property
    def instrument_type(self) -> str:
        """Tag of the active instrument type."""
        return self._instrument_type

    @instrument_type.setter
    def instrument_type(self, new_type: str) -> None:
        """Switch to a different instrument type.

        Args:     new_type: Instrument tag (e.g. ``'cwl-sc'``).
        """
        supported = InstrumentFactory.supported_for(
            scattering_type=self.type.scattering_type.value,
            beam_mode=self.type.beam_mode.value,
            sample_form=self.type.sample_form.value,
        )
        supported_tags = [k.type_info.tag for k in supported]
        if new_type not in supported_tags:
            log.warning(
                f"Unsupported instrument type '{new_type}'. "
                f'Supported: {supported_tags}. '
                f"For more information, use 'show_supported_instrument_types()'",
            )
            return
        self._instrument = InstrumentFactory.create(new_type)
        self._instrument_type = new_type
        console.paragraph(f"Instrument type for experiment '{self.name}' changed to")
        console.print(new_type)

    def show_supported_instrument_types(self) -> None:
        """Print a table of supported instrument types."""
        InstrumentFactory.show_supported(
            scattering_type=self.type.scattering_type.value,
            beam_mode=self.type.beam_mode.value,
            sample_form=self.type.sample_form.value,
        )

    def show_current_instrument_type(self) -> None:
        """Print the currently used instrument type."""
        console.paragraph('Current instrument type')
        console.print(self.instrument_type)

    # ------------------------------------------------------------------
    #  Data (switchable-category pattern)
    # ------------------------------------------------------------------

    @property
    def data(self):
        """Data collection for this experiment."""
        return self._data

    @property
    def data_type(self) -> str:
        """Tag of the active data collection type."""
        return self._data_type

    @data_type.setter
    def data_type(self, new_type: str) -> None:
        """Switch to a different data collection type.

        Args:     new_type: Data tag (e.g. ``'bragg-sc'``).
        """
        supported_tags = DataFactory.supported_tags()
        if new_type not in supported_tags:
            log.warning(
                f"Unsupported data type '{new_type}'. "
                f'Supported: {supported_tags}. '
                f"For more information, use 'show_supported_data_types()'",
            )
            return
        self._data = DataFactory.create(new_type)
        self._data_type = new_type
        console.paragraph(f"Data type for experiment '{self.name}' changed to")
        console.print(new_type)

    def show_supported_data_types(self) -> None:
        """Print a table of supported data collection types."""
        DataFactory.show_supported()

    def show_current_data_type(self) -> None:
        """Print the currently used data collection type."""
        console.paragraph('Current data type')
        console.print(self.data_type)


class PdExperimentBase(ExperimentBase):
    """Base class for all powder experiments."""

    def __init__(
        self,
        *,
        name: str,
        type: ExperimentType,
    ) -> None:
        super().__init__(name=name, type=type)

        self._linked_phases_type: str = LinkedPhasesFactory.default_tag()
        self._linked_phases = LinkedPhasesFactory.create(self._linked_phases_type)
        self._excluded_regions_type: str = ExcludedRegionsFactory.default_tag()
        self._excluded_regions = ExcludedRegionsFactory.create(self._excluded_regions_type)
        self._peak_profile_type: str = PeakFactory.default_tag(
            scattering_type=self.type.scattering_type.value,
            beam_mode=self.type.beam_mode.value,
        )
        self._data_type: str = DataFactory.default_tag(
            sample_form=self.type.sample_form.value,
            beam_mode=self.type.beam_mode.value,
            scattering_type=self.type.scattering_type.value,
        )
        self._data = DataFactory.create(self._data_type)
        self._peak = PeakFactory.create(self._peak_profile_type)

    def _get_valid_linked_phases(
        self,
        structures: Structures,
    ) -> List[Any]:
        """Get valid linked phases for this experiment.

        Args:     structures: Collection of structures.

        Returns:     A list of valid linked phases.
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

        Args:     data_path: Path to data file with columns compatible
        with         the beam mode (e.g. 2θ/I/σ for CWL, TOF/I/σ for
        TOF).
        """
        pass

    @property
    def linked_phases(self):
        """Collection of phases linked to this experiment."""
        return self._linked_phases

    @property
    def linked_phases_type(self) -> str:
        """Tag of the active linked-phases collection type."""
        return self._linked_phases_type

    @linked_phases_type.setter
    def linked_phases_type(self, new_type: str) -> None:
        """Switch to a different linked-phases collection type.

        Args:     new_type: Linked-phases tag (e.g. ``'default'``).
        """
        supported_tags = LinkedPhasesFactory.supported_tags()
        if new_type not in supported_tags:
            log.warning(
                f"Unsupported linked phases type '{new_type}'. "
                f'Supported: {supported_tags}. '
                f"For more information, use 'show_supported_linked_phases_types()'",
            )
            return

        self._linked_phases = LinkedPhasesFactory.create(new_type)
        self._linked_phases_type = new_type
        console.paragraph(f"Linked phases type for experiment '{self.name}' changed to")
        console.print(new_type)

    def show_supported_linked_phases_types(self) -> None:
        """Print a table of supported linked-phases collection types."""
        LinkedPhasesFactory.show_supported()

    def show_current_linked_phases_type(self) -> None:
        """Print the currently used linked-phases collection type."""
        console.paragraph('Current linked phases type')
        console.print(self.linked_phases_type)

    @property
    def excluded_regions(self):
        """Collection of excluded regions for the x-grid."""
        return self._excluded_regions

    @property
    def excluded_regions_type(self) -> str:
        """Tag of the active excluded-regions collection type."""
        return self._excluded_regions_type

    @excluded_regions_type.setter
    def excluded_regions_type(self, new_type: str) -> None:
        """Switch to a different excluded-regions collection type.

        Args:     new_type: Excluded-regions tag (e.g. ``'default'``).
        """
        supported_tags = ExcludedRegionsFactory.supported_tags()
        if new_type not in supported_tags:
            log.warning(
                f"Unsupported excluded regions type '{new_type}'. "
                f'Supported: {supported_tags}. '
                f"For more information, use 'show_supported_excluded_regions_types()'",
            )
            return

        self._excluded_regions = ExcludedRegionsFactory.create(new_type)
        self._excluded_regions_type = new_type
        console.paragraph(f"Excluded regions type for experiment '{self.name}' changed to")
        console.print(new_type)

    def show_supported_excluded_regions_types(self) -> None:
        """Print a table of supported excluded-regions collection
        types.
        """
        ExcludedRegionsFactory.show_supported()

    def show_current_excluded_regions_type(self) -> None:
        """Print the currently used excluded-regions collection type."""
        console.paragraph('Current excluded regions type')
        console.print(self.excluded_regions_type)

    # ------------------------------------------------------------------
    #  Data (switchable-category pattern)
    # ------------------------------------------------------------------

    @property
    def data(self):
        """Data collection for this experiment."""
        return self._data

    @property
    def data_type(self) -> str:
        """Tag of the active data collection type."""
        return self._data_type

    @data_type.setter
    def data_type(self, new_type: str) -> None:
        """Switch to a different data collection type.

        Args:     new_type: Data tag (e.g. ``'bragg-pd-cwl'``).
        """
        supported_tags = DataFactory.supported_tags()
        if new_type not in supported_tags:
            log.warning(
                f"Unsupported data type '{new_type}'. "
                f'Supported: {supported_tags}. '
                f"For more information, use 'show_supported_data_types()'",
            )
            return
        self._data = DataFactory.create(new_type)
        self._data_type = new_type
        console.paragraph(f"Data type for experiment '{self.name}' changed to")
        console.print(new_type)

    def show_supported_data_types(self) -> None:
        """Print a table of supported data collection types."""
        DataFactory.show_supported()

    def show_current_data_type(self) -> None:
        """Print the currently used data collection type."""
        console.paragraph('Current data type')
        console.print(self.data_type)

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

        Args:     new_type: New profile type as tag string.
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
