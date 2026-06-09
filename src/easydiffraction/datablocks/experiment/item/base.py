# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Base classes for experiment datablock items."""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING
from typing import Any

import numpy as np

from easydiffraction.core.datablock import DatablockItem
from easydiffraction.datablocks.experiment.categories.background.factory import BackgroundFactory
from easydiffraction.datablocks.experiment.categories.calculator import CalculatorCategoryFactory
from easydiffraction.datablocks.experiment.categories.data.factory import DataFactory
from easydiffraction.datablocks.experiment.categories.data_range.factory import DataRangeFactory
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
from easydiffraction.utils.utils import format_bulleted_warning
from easydiffraction.utils.utils import render_cif

if TYPE_CHECKING:
    from easydiffraction.core.variable import NumericDescriptor
    from easydiffraction.datablocks.experiment.categories.experiment_type import ExperimentType
    from easydiffraction.datablocks.structure.collection import Structures

MeasuredRange = tuple[float, float, float | None]
_MEASURED_RANGE_UNIFORM_TOLERANCE = 0.01


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
        self._identity.datablock_entry_name = lambda: self.name

        self._diffrn_type: str = DiffrnFactory.default_tag()
        self._diffrn = DiffrnFactory.create(self._diffrn_type)
        self._calculator_category = CalculatorCategoryFactory.create(
            'default',
            type=self._default_calculator_tag(),
        )
        self._attach_category_parents()

    def _attach_category_parents(self) -> None:
        """Link owned categories back to this experiment object."""
        for category in [
            self._type,
            getattr(self, '_diffrn', None),
            getattr(self, '_calculator_category', None),
            getattr(self, '_extinction', None),
            getattr(self, '_linked_crystal', None),
            getattr(self, '_instrument', None),
            getattr(self, '_refln', None),
            getattr(self, '_linked_phases', None),
            getattr(self, '_excluded_regions', None),
            getattr(self, '_data', None),
            getattr(self, '_data_range', None),
            getattr(self, '_peak', None),
            getattr(self, '_background', None),
        ]:
            if category is not None:
                category._parent = self

    def _supported_filters_for(self, category: object) -> dict[str, object]:
        """Return owner context filters for a switchable category."""
        calculator = self.calculator.type
        if category is getattr(self, '_background', None):
            return {'calculator': calculator}
        if category is getattr(self, '_extinction', None):
            return {'calculator': calculator}
        if category is getattr(self, '_peak', None):
            return {
                'calculator': calculator,
                'sample_form': self.type.sample_form.value,
                'scattering_type': self.type.scattering_type.value,
                'beam_mode': self.type.beam_mode.value,
            }
        return {}

    def _swap_calculator(
        self,
        new_type: str,
        *,
        announce: bool = True,
        strict: bool = True,
    ) -> None:
        """Switch the active calculator backend."""
        from easydiffraction.analysis.calculators.factory import CalculatorFactory  # noqa: PLC0415

        supported = self._supported_calculator_tags()
        if new_type not in supported:
            msg = (
                f"Unsupported calculator '{new_type}' for experiment "
                f"'{self.name}'. Supported: {supported}. "
                f"For more information, use 'calculator.show_supported()'"
            )
            if strict:
                raise ValueError(msg)
            log.warning(msg)
            return
        if self._calculator_category._type.value == new_type and self._calculator is not None:
            if announce:
                console.paragraph(f"Calculator for experiment '{self.name}' already set to")
                console.print(new_type)
            return
        self._calculator = CalculatorFactory.create(new_type)
        self._calculator_category._type.value = new_type
        if announce:
            console.paragraph(f"Calculator for experiment '{self.name}' changed to")
            console.print(new_type)

    def _swap_peak(self, new_type: str) -> None:
        """Switch the active peak category."""
        self._replace_peak_profile(new_type, announce=True)

    def _swap_background(self, new_type: str) -> None:
        """Switch the active background category."""
        self._replace_background(new_type, announce=True)

    def _replace_background(
        self,
        new_type: str,
        *,
        announce: bool,
        strict: bool = True,
    ) -> None:
        """Replace the active background category."""
        supported = BackgroundFactory.supported_for(
            **self._supported_filters_for(self.background),
        )
        supported_tags = [klass.type_info.tag for klass in supported]
        if new_type not in supported_tags:
            msg = (
                f"Unsupported background type '{new_type}'. "
                f'Supported: {supported_tags}. '
                f"For more information, use 'background.show_supported()'"
            )
            if strict:
                raise ValueError(msg)
            log.warning(msg)
            return

        if self._background._type.value == new_type:
            if announce:
                console.paragraph(f"Background type for experiment '{self.name}' already set to")
                console.print(new_type)
            return

        if len(self._background) > 0 and announce:
            log.warning(
                f'Switching background type discards {len(self._background)} '
                f'existing background point(s).',
            )

        old_background = self._background
        self._background = BackgroundFactory.create(new_type)
        old_background._parent = None
        self._background._parent = self
        self._background._type.value = new_type
        if announce:
            console.paragraph(f"Background type for experiment '{self.name}' changed to")
            console.print(new_type)

    def _swap_extinction(self, new_type: str) -> None:
        """Switch the active extinction category."""
        self._replace_extinction(new_type, announce=True)

    def _replace_extinction(
        self,
        new_type: str,
        *,
        announce: bool,
        strict: bool = True,
    ) -> None:
        """Replace the active extinction category."""
        supported = ExtinctionFactory.supported_for(
            **self._supported_filters_for(self.extinction),
        )
        supported_tags = [klass.type_info.tag for klass in supported]
        if new_type not in supported_tags:
            msg = (
                f"Unsupported extinction type '{new_type}'. "
                f'Supported: {supported_tags}. '
                f"For more information, use 'extinction.show_supported()'"
            )
            if strict:
                raise ValueError(msg)
            log.warning(msg)
            return

        old_extinction = self._extinction
        self._extinction = ExtinctionFactory.create(new_type)
        old_extinction._parent = None
        self._extinction._parent = self
        self._extinction._type.value = new_type
        if announce:
            console.paragraph('Extinction type changed to')
            console.print(new_type)

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

    @property
    def measured_range(self) -> MeasuredRange | None:
        """Measured x-axis range as ``(min, max, inc)``."""
        values = self._measured_x_values()
        if values is None or values.size == 0:
            return None

        values = np.sort(values.astype(float, copy=False))
        range_min = float(values[0])
        range_max = float(values[-1])
        if values.size == 1:
            return (range_min, range_max, None)

        increment = _representative_increment(values)
        return (range_min, range_max, increment)

    def _measured_x_values(self) -> np.ndarray | None:
        """Return the measured x-axis values for this experiment."""
        try:
            category = intensity_category_for(self)
        except AttributeError:
            return None
        values = getattr(category, 'unfiltered_x', None)
        if values is None:
            values = getattr(category, 'x', None)
        if values is None:
            return None
        return np.asarray(values, dtype=float)

    # ------------------------------------------------------------------
    #  Diffrn conditions (read-only, single type)
    # ------------------------------------------------------------------

    @property
    def diffrn(self) -> object:
        """Ambient conditions recorded during measurement."""
        return self._diffrn

    # ------------------------------------------------------------------
    #  Data range (fixed by experiment type)
    # ------------------------------------------------------------------

    @property
    def data_range(self) -> object:
        """Reciprocal-space range used to calculate without measured data."""
        return self._data_range

    def _restore_switchable_types(self, block: object) -> None:
        """
        Restore switchable category types from a parsed CIF block.

        Called by the factory immediately after the experiment object is
        created and before any category parameters are loaded from CIF.
        Subclasses with switchable categories must override this method
        and call their private swap hook for each category whose active
        implementation is identified by a CIF type tag.

        Parameters
        ----------
        block : object
            Parsed ``gemmi.cif.Block`` to read type tags from.
        """
        calculator_tag = read_cif_str(block, '_calculator.type')
        if calculator_tag is not None:
            self._swap_calculator(calculator_tag, announce=False, strict=False)

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
    #  Calculator (switchable-category pattern)
    # ------------------------------------------------------------------

    @property
    def calculator(self) -> object:
        """
        The active calculator category for this experiment.

        Holds the selected calculator type and provides access to the
        live calculator backend instance.
        """
        if self._calculator is None:
            self._resolve_calculator()
        return self._calculator_category

    def _default_calculator_tag(self) -> str:
        """Return the default calculator tag for this experiment."""
        from easydiffraction.analysis.calculators.factory import CalculatorFactory  # noqa: PLC0415

        return CalculatorFactory.default_tag(
            scattering_type=self.type.scattering_type.value,
        )

    def _resolve_calculator(self) -> None:
        """Auto-resolve the default calculator from category support."""
        from easydiffraction.analysis.calculators.factory import CalculatorFactory  # noqa: PLC0415

        tag = self._default_calculator_tag()
        supported = self._supported_calculator_tags()
        if supported and tag not in supported:
            tag = supported[0]
        self._calculator = CalculatorFactory.create(tag)
        self._calculator_category._type.value = tag

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


def _representative_increment(values: np.ndarray) -> float | None:
    """Return a representative increment for sorted x-axis values."""
    steps = np.diff(values)
    median_step = float(np.median(steps))
    if median_step == 0:
        return None
    tolerance = abs(median_step) * _MEASURED_RANGE_UNIFORM_TOLERANCE
    if np.max(np.abs(steps - median_step)) > tolerance:
        return None
    return median_step


class ScExperimentBase(ExperimentBase):
    """Base class for all single crystal experiments."""

    def __init__(
        self,
        *,
        name: str,
        type: ExperimentType,
    ) -> None:
        super().__init__(name=name, type=type)

        self._extinction = ExtinctionFactory.create(ExtinctionFactory.default_tag())
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
        self._data_range_type: str = DataRangeFactory.default_tag(
            beam_mode=self.type.beam_mode.value,
            sample_form=self.type.sample_form.value,
        )
        self._data_range = DataRangeFactory.create(self._data_range_type)
        self._resolve_calculator()
        self._attach_category_parents()

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

    def _restore_switchable_types(self, block: object) -> None:
        """
        Restore single-crystal switchable category types from CIF.
        """
        super()._restore_switchable_types(block)
        extinction_tag = read_cif_str(block, '_extinction.type')
        if extinction_tag is not None:
            self._replace_extinction(extinction_tag, announce=False, strict=False)

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
    def x_descriptor(self) -> NumericDescriptor | None:
        """Return None because single-crystal data has no 1-D x axis."""
        return None

    @staticmethod
    def fit_data_arrays() -> dict[str, np.ndarray | None]:
        """Return no 1-D fit arrays for single-crystal experiments."""
        return {}

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
        self._data_type: str = DataFactory.default_tag(
            sample_form=self.type.sample_form.value,
            beam_mode=self.type.beam_mode.value,
            scattering_type=self.type.scattering_type.value,
        )
        self._data = DataFactory.create(self._data_type)
        self._data_range_type: str = DataRangeFactory.default_tag(
            beam_mode=self.type.beam_mode.value,
            sample_form=self.type.sample_form.value,
        )
        self._data_range = DataRangeFactory.create(self._data_range_type)
        self._peak = PeakFactory.create(
            PeakFactory.default_tag(
                scattering_type=self.type.scattering_type.value,
                beam_mode=self.type.beam_mode.value,
            )
        )
        self._resolve_calculator()
        self._attach_category_parents()

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
            log.warning('No linked phases defined. Returning empty pattern.')
            return []

        valid_linked_phases = []
        for linked_phase in self.linked_phases:
            if linked_phase._identity.category_entry_name not in structures.names:
                log.warning(
                    f"Linked phase '{linked_phase.id.value}' not "
                    f'found in Structures {structures.names}. Skipping it.'
                )
                continue
            valid_linked_phases.append(linked_phase)

        if not valid_linked_phases:
            log.warning('None of the linked phases found in Structures. Returning empty pattern.')

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

    @property
    def x_descriptor(self) -> NumericDescriptor:
        """
        Descriptor that owns the powder experiment's x-axis metadata.
        """
        return self.data.x_descriptor

    def fit_data_arrays(self) -> dict[str, np.ndarray | None]:
        """Return arrays needed to draw the powder fit-data chart."""
        return self.data.fit_data_arrays()

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

    def _replace_peak_profile(
        self,
        new_type: str,
        *,
        announce: bool,
        strict: bool = True,
    ) -> None:
        """Replace the active peak profile category."""
        context = self._peak_profile_context()
        supported = PeakFactory.supported_for(
            **self._supported_filters_for(self.peak),
        )
        supported_tags = [klass.type_info.tag for klass in supported]
        supported_aliases = [
            PeakFactory._local_alias_for(tag, **context) for tag in supported_tags
        ]
        canonical_type = PeakFactory._canonical_tag_for(new_type, **context)

        if canonical_type not in supported_tags:
            msg = (
                f"Unsupported peak profile '{new_type}'. "
                f'Supported peak profiles: {supported_aliases}. '
                f"For more information, use 'peak.show_supported()'"
            )
            if strict:
                raise ValueError(msg)
            log.warning(msg)
            return

        old_peak = self._peak
        new_peak = PeakFactory.create(canonical_type)
        if old_peak is not None and announce:
            self._warn_about_peak_profile_swap(old_peak, new_peak)

        self._peak = new_peak
        if old_peak is not None:
            old_peak._parent = None
        self._peak._parent = self
        self._peak._type.value = canonical_type
        if announce:
            console.paragraph(f"Peak profile type for experiment '{self.name}' changed to")
            console.print(PeakFactory._local_alias_for(canonical_type, **context))

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
        self._replace_peak_profile(new_type, announce=False, strict=False)

    def _peak_profile_context(self) -> dict[str, object]:
        """
        Return the context that resolves local peak profile aliases.
        """
        return {
            'scattering_type': self.type.scattering_type.value,
            'beam_mode': self.type.beam_mode.value,
        }

    def _restore_switchable_types(self, block: object) -> None:
        """
        Restore switchable category types for powder experiments.

        Reads ``_peak.type`` from the CIF block and switches to the
        matching peak implementation before category parameters are
        loaded, ensuring profile-specific descriptors are present.

        Parameters
        ----------
        block : object
            Parsed ``gemmi.cif.Block`` to read type tags from.
        """
        super()._restore_switchable_types(block)
        peak_type = read_cif_str(block, '_peak.type')
        if peak_type is not None:
            self._set_peak_profile_type(peak_type)

    @staticmethod
    def _peak_parameter_values(peak: object) -> dict[str, object]:
        """Return peak parameter values excluding the selector type."""
        return {
            parameter.name: parameter.value
            for parameter in getattr(peak, 'parameters', [])
            if parameter.name != 'type'
        }

    @classmethod
    def _peak_profile_swap_diff(
        cls,
        old_peak: object,
        new_peak: object,
    ) -> tuple[list[str], list[str], list[str]]:
        """Return removed, added, and reset peak-setting rows."""
        old_values = cls._peak_parameter_values(old_peak)
        new_values = cls._peak_parameter_values(new_peak)
        old_keys = set(old_values)
        new_keys = set(new_values)
        removed = sorted(old_keys - new_keys)
        added = sorted(f'{name}={new_values[name]!r}' for name in (new_keys - old_keys))
        reset = sorted(
            f'{name}: {old_values[name]!r} -> {new_values[name]!r}'
            for name in (old_keys & new_keys)
            if old_values[name] != new_values[name]
        )
        return removed, added, reset

    @classmethod
    def _warn_about_peak_profile_swap(
        cls,
        old_peak: object,
        new_peak: object,
    ) -> None:
        """Warn about peak settings changed by a profile swap."""
        removed, added, reset = cls._peak_profile_swap_diff(old_peak, new_peak)
        if removed:
            log.warning(
                format_bulleted_warning(
                    'Switching peak profile type removes these settings:',
                    removed,
                )
            )
        if added:
            log.warning(
                format_bulleted_warning(
                    'Switching peak profile type adds these settings with defaults:',
                    added,
                )
            )
        if reset:
            log.warning(
                format_bulleted_warning(
                    'Switching peak profile type resets these settings to defaults:',
                    reset,
                )
            )
