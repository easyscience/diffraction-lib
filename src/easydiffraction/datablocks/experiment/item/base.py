# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Base classes for experiment datablock items."""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING
from typing import Any

from easydiffraction.core.datablock import DatablockItem
from easydiffraction.datablocks.experiment.categories.calculation import CalculationFactory
from easydiffraction.datablocks.experiment.categories.data.factory import DataFactory
from easydiffraction.datablocks.experiment.categories.diffrn.factory import DiffrnFactory
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
from easydiffraction.datablocks.experiment.categories.refln.factory import ReflnFactory
from easydiffraction.io.cif.parse import read_cif_str
from easydiffraction.io.cif.serialize import experiment_to_cif
from easydiffraction.utils.logging import console
from easydiffraction.utils.logging import log
from easydiffraction.utils.utils import render_cif
from easydiffraction.utils.utils import render_table

if TYPE_CHECKING:
    from easydiffraction.datablocks.experiment.categories.experiment_type import ExperimentType
    from easydiffraction.datablocks.structure.collection import Structures


def intensity_category_for(experiment: object) -> object:
    """Return the category exposing measured and calculated values."""
    resolver = getattr(experiment, '_intensity_category', None)
    if callable(resolver):
        return resolver()

    data = getattr(experiment, 'data', None)
    if data is not None:
        return data

    refln = getattr(experiment, 'refln', None)
    if refln is not None:
        return refln

    name = getattr(experiment, 'name', type(experiment).__name__)
    msg = f"Experiment '{name}' has no intensity category."
    raise AttributeError(msg)


class ExperimentBase(DatablockItem):
    """Base class for all experiment datablock items."""

    def __init__(
        self,
        *,
        name: str,
        type: ExperimentType,
    ) -> None:
        super().__init__()
        self._name = name
        self._type = type
        self._calculator = None
        self._calculator_type: str | None = None
        self._identity.datablock_entry_name = lambda: self.name

        self._diffrn_type: str = DiffrnFactory.default_tag()
        self._diffrn = DiffrnFactory.create(self._diffrn_type)
        self._calculation = CalculationFactory.create(
            'default',
            calculator_type=self._default_calculator_tag(),
        )
        self._calculation._parent = self

    @property
    def name(self) -> str:
        """Human-readable name of the experiment."""
        return self._name

    @name.setter
    def name(self, new: str) -> None:
        """
        Rename the experiment.

        Parameters
        ----------
        new : str
            New name for this experiment.
        """
        self._name = new

    @property
    def type(self) -> object:  # TODO: Consider another name
        """Experiment type: sample form, probe, beam mode."""
        return self._type

    # ------------------------------------------------------------------
    #  Diffrn conditions (read-only, single type)
    # ------------------------------------------------------------------

    @property
    def diffrn(self) -> object:
        """Ambient conditions recorded during measurement."""
        return self._diffrn

    def _restore_switchable_types(self, block: object) -> None:
        """
        Restore switchable category types from a parsed CIF block.

        Called by the factory immediately after the experiment object is
        created and before any category parameters are loaded from CIF.
        Subclasses with switchable categories must override this method
        and call their ``_set_<type>`` private setter for each category
        whose active implementation is identified by a CIF type tag.

        Parameters
        ----------
        block : object
            Parsed ``gemmi.cif.Block`` to read type tags from.
        """
        calculator_type = read_cif_str(block, '_calculation.calculator_type')
        if calculator_type is not None:
            self._set_calculator_type(calculator_type, announce=False)

    def _normalize_switchable_type_descriptors(self) -> None:
        """
        Normalize switchable category descriptors after CIF loading.
        """
        if self._calculator_type is not None:
            self.calculation.calculator_type.value = self._calculator_type

    @property
    def as_cif(self) -> str:
        """Serialize this experiment to a CIF fragment."""
        return experiment_to_cif(self)

    def show_as_cif(self) -> None:
        """Pretty-print the experiment as CIF text."""
        paragraph_title: str = f"Experiment 🔬 '{self.name}' as cif"
        console.paragraph(paragraph_title)
        render_cif(self._cif_for_display())

    @abstractmethod
    def _load_ascii_data_to_experiment(self, data_path: str) -> None:
        """
        Load ASCII data from file into the experiment data category.

        Parameters
        ----------
        data_path : str
            Path to the ASCII file to load.

        Raises
        ------
        NotImplementedError
            Subclasses must implement this method.
        """
        raise NotImplementedError

    # ------------------------------------------------------------------
    #  Calculation (switchable-category pattern)
    # ------------------------------------------------------------------

    @property
    def calculation(self) -> object:
        """
        The active calculation category for this experiment.

        Holds the selected calculator type and provides access to the
        live calculator backend instance.
        """
        if self._calculator is None:
            self._resolve_calculation()
        return self._calculation

    def _default_calculator_tag(self) -> str:
        """Return the default calculator tag for this experiment."""
        from easydiffraction.analysis.calculators.factory import CalculatorFactory  # noqa: PLC0415

        return CalculatorFactory.default_tag(
            scattering_type=self.type.scattering_type.value,
        )

    def _set_calculator_type(
        self,
        tag: str,
        *,
        announce: bool = True,
    ) -> None:
        """Switch to a different calculator backend."""
        from easydiffraction.analysis.calculators.factory import CalculatorFactory  # noqa: PLC0415

        supported = self._supported_calculator_tags()
        if tag not in supported:
            log.warning(
                f"Unsupported calculator '{tag}' for experiment "
                f"'{self.name}'. Supported: {supported}. "
                f"For more information, use 'calculation.show_calculator_types()'",
            )
            return
        if self._calculator_type == tag and self._calculator is not None:
            if announce:
                console.paragraph(f"Calculator for experiment '{self.name}' already set to")
                console.print(tag)
            return
        self._calculator = CalculatorFactory.create(tag)
        self._calculator_type = tag
        self.calculation.calculator_type.value = tag
        if announce:
            console.paragraph(f"Calculator for experiment '{self.name}' changed to")
            console.print(tag)

    def _resolve_calculation(self) -> None:
        """Auto-resolve the default calculator from category support."""
        from easydiffraction.analysis.calculators.factory import CalculatorFactory  # noqa: PLC0415

        tag = self._default_calculator_tag()
        supported = self._supported_calculator_tags()
        if supported and tag not in supported:
            tag = supported[0]
        self._calculator = CalculatorFactory.create(tag)
        self._calculator_type = tag
        self.calculation.calculator_type.value = tag

    def _supported_calculator_tags(self) -> list[str]:
        """
        Return calculator tags supported by this experiment.

        Intersects the active support category's ``calculator_support``
        with calculators whose engines are importable.
        """
        from easydiffraction.analysis.calculators.factory import CalculatorFactory  # noqa: PLC0415

        available = CalculatorFactory.supported_tags()
        support_category = self._calculator_support_category()
        if support_category is not None:
            data_support = getattr(support_category, 'calculator_support', None)
            if data_support and data_support.calculators:
                return [t for t in available if t in data_support.calculators]
        return available

    def _calculator_support_category(self) -> object | None:
        """
        Return the category that constrains calculator availability.
        """
        return getattr(self, '_data', None) or getattr(self, '_refln', None)

    def _intensity_category(self) -> object:
        """Return the experiment category exposing intensity arrays."""
        msg = f"Experiment '{self.name}' has no intensity category."
        raise AttributeError(msg)


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
        self._refln_type: str = ReflnFactory.default_tag(
            sample_form=self.type.sample_form.value,
            beam_mode=self.type.beam_mode.value,
            scattering_type=self.type.scattering_type.value,
        )
        self._refln = ReflnFactory.create(self._refln_type)
        self._resolve_calculation()

    @abstractmethod
    def _load_ascii_data_to_experiment(self, data_path: str) -> None:
        """
        Load single crystal data from an ASCII file.

        Parameters
        ----------
        data_path : str
            Path to data file with columns compatible with the beam
            mode.
        """

    # ------------------------------------------------------------------
    #  Extinction (switchable-category pattern)
    # ------------------------------------------------------------------

    @property
    def extinction(self) -> object:
        """Active extinction correction model."""
        return self._extinction

    @property
    def extinction_type(self) -> str:
        """Tag of the active extinction correction model."""
        return self._extinction_type

    @extinction_type.setter
    def extinction_type(self, new_type: str) -> None:
        """
        Switch to a different extinction correction model.

        Parameters
        ----------
        new_type : str
            Extinction tag (e.g. ``'becker-coppens'``).
        """
        supported = ExtinctionFactory.supported_for(
            calculator=self.calculation.calculator_type.value,
        )
        supported_tags = [k.type_info.tag for k in supported]
        if new_type not in supported_tags:
            log.warning(
                f"Unsupported extinction type '{new_type}'. "
                f'Supported: {supported_tags}. '
                f"For more information, use 'show_extinction_types()'",
            )
            return
        self._extinction = ExtinctionFactory.create(new_type)
        self._extinction_type = new_type
        console.paragraph('Extinction type changed to')
        console.print(new_type)

    def show_extinction_types(self) -> None:
        """Print supported extinction types and mark current type."""
        supported = ExtinctionFactory.supported_for(
            calculator=self.calculation.calculator_type.value,
        )
        columns_data = [
            [
                '*' if klass.type_info.tag == self._extinction_type else '',
                klass.type_info.tag,
                klass.type_info.description,
            ]
            for klass in supported
        ]
        console.paragraph('Extinction types')
        render_table(
            columns_headers=['', 'Type', 'Description'],
            columns_alignment=['left', 'left', 'left'],
            columns_data=columns_data,
        )

    # ------------------------------------------------------------------
    #  Linked crystal (read-only, single type)
    # ------------------------------------------------------------------

    @property
    def linked_crystal(self) -> object:
        """Linked crystal model for this experiment."""
        return self._linked_crystal

    # ------------------------------------------------------------------
    #  Instrument (fixed at creation)
    # ------------------------------------------------------------------

    @property
    def instrument(self) -> object:
        """Active instrument model for this experiment."""
        return self._instrument

    @property
    def refln(self) -> object:
        """Reflection collection for this experiment."""
        return self._refln

    @property
    def data(self) -> object:
        """Compatibility alias for the reflection collection."""
        return self._refln

    def _calculator_support_category(self) -> object | None:
        """
        Return the reflection collection that constrains calculators.
        """
        return self._refln

    def _intensity_category(self) -> object:
        """Return the single-crystal reflection collection."""
        return self._refln


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
        self._resolve_calculation()

    def _get_valid_linked_phases(
        self,
        structures: Structures,
    ) -> list[Any]:
        """
        Get valid linked phases for this experiment.

        Parameters
        ----------
        structures : Structures
            Collection of structures.

        Returns
        -------
        list[Any]
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
    def _load_ascii_data_to_experiment(self, data_path: str) -> int:
        """
        Load powder diffraction data from an ASCII file.

        Parameters
        ----------
        data_path : str
            Path to data file with columns compatible with the beam mode
            (e.g. 2theta/I/sigma for CWL, TOF/I/sigma for TOF).

        Returns
        -------
        int
            Number of loaded data points.
        """

    @property
    def linked_phases(self) -> object:
        """Collection of phases linked to this experiment."""
        return self._linked_phases

    @property
    def excluded_regions(self) -> object:
        """Collection of excluded regions for the x-grid."""
        return self._excluded_regions

    # ------------------------------------------------------------------
    #  Data (fixed at creation)
    # ------------------------------------------------------------------

    @property
    def data(self) -> object:
        """Data collection for this experiment."""
        return self._data

    def _calculator_support_category(self) -> object | None:
        """
        Return the powder data collection that constrains calculators.
        """
        return self._data

    def _intensity_category(self) -> object:
        """Return the powder intensity data collection."""
        return self._data

    @property
    def peak(self) -> object:
        """Peak category object with profile parameters and mixins."""
        return self._peak

    @property
    def peak_profile_type(self) -> object:
        """Currently selected peak profile type alias."""
        return PeakFactory._local_alias_for(
            self._peak_profile_type,
            **self._peak_profile_context(),
        )

    @peak_profile_type.setter
    def peak_profile_type(self, new_type: str) -> None:
        """
        Change the active peak profile type, if supported.

        Parameters
        ----------
        new_type : str
            New profile type as context-local alias or canonical tag.
        """
        context = self._peak_profile_context()
        supported = PeakFactory.supported_for(
            calculator=self.calculation.calculator_type.value,
            **context,
        )
        supported_tags = [klass.type_info.tag for klass in supported]
        supported_aliases = [
            PeakFactory._local_alias_for(tag, **context) for tag in supported_tags
        ]
        canonical_type = PeakFactory._canonical_tag_for(new_type, **context)

        if canonical_type not in supported_tags:
            log.warning(
                f"Unsupported peak profile '{new_type}'. "
                f'Supported peak profiles: {supported_aliases}. '
                f"For more information, use 'show_peak_profile_types()'",
            )
            return

        if self._peak is not None:
            log.warning(
                'Switching peak profile type discards existing peak parameters.',
            )

        self._peak = PeakFactory.create(canonical_type)
        self._peak_profile_type = canonical_type
        console.paragraph(f"Peak profile type for experiment '{self.name}' changed to")
        console.print(self.peak_profile_type)

    def show_peak_profile_types(self) -> None:
        """Print supported peak profile types and mark current type."""
        supported = PeakFactory.supported_for(
            calculator=self.calculation.calculator_type.value,
            scattering_type=self.type.scattering_type.value,
            beam_mode=self.type.beam_mode.value,
        )
        context = self._peak_profile_context()
        current = PeakFactory._local_alias_for(self._peak_profile_type, **context)
        columns_data = [
            [
                '*'
                if PeakFactory._local_alias_for(klass.type_info.tag, **context) == current
                else '',
                PeakFactory._local_alias_for(klass.type_info.tag, **context),
                klass.type_info.description,
            ]
            for klass in supported
        ]
        console.paragraph('Peak profile types')
        render_table(
            columns_headers=['', 'Type', 'Description'],
            columns_alignment=['left', 'left', 'left'],
            columns_data=columns_data,
        )

    def _set_peak_profile_type(self, new_type: str) -> None:
        """
        Switch the peak profile type without console output.

        Used internally by the factory when restoring state from CIF so
        that no user-facing warnings or progress messages are emitted.
        Invalid type tags are logged as warnings and ignored.

        Parameters
        ----------
        new_type : str
            Peak profile type alias or canonical tag.
        """
        context = self._peak_profile_context()
        supported = PeakFactory.supported_for(
            **context,
        )
        supported_tags = [klass.type_info.tag for klass in supported]
        canonical_type = PeakFactory._canonical_tag_for(new_type, **context)
        if canonical_type not in supported_tags:
            supported_aliases = [
                PeakFactory._local_alias_for(tag, **context) for tag in supported_tags
            ]
            log.warning(
                f"Unsupported peak profile '{new_type}' in CIF. "
                f'Supported: {supported_aliases}. Keeping default.',
            )
            return
        self._peak = PeakFactory.create(canonical_type)
        self._peak_profile_type = canonical_type

    def _peak_profile_context(self) -> dict[str, object]:
        """
        Return the context that resolves local peak profile aliases.
        """
        return {
            'scattering_type': self.type.scattering_type.value,
            'beam_mode': self.type.beam_mode.value,
        }

    def _normalize_switchable_type_descriptors(self) -> None:
        """
        Normalize switchable category descriptors after CIF loading.
        """
        super()._normalize_switchable_type_descriptors()
        self.peak.profile_type.value = self._peak_profile_type

    def _restore_switchable_types(self, block: object) -> None:
        """
        Restore switchable category types for powder experiments.

        Reads ``_peak.profile_type`` from the CIF block and switches to
        the matching peak implementation before category parameters are
        loaded, ensuring profile-specific descriptors are present.

        Parameters
        ----------
        block : object
            Parsed ``gemmi.cif.Block`` to read type tags from.
        """
        super()._restore_switchable_types(block)
        peak_type = read_cif_str(block, '_peak.profile_type')
        if peak_type is not None:
            self._set_peak_profile_type(peak_type)
