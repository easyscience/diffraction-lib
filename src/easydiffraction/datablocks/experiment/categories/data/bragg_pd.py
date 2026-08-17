# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Measured and calculated powder pattern data categories."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from easydiffraction.core.category import CategoryCollection
from easydiffraction.core.category import CategoryItem
from easydiffraction.core.display_handler import DisplayHandler
from easydiffraction.core.metadata import CalculatorSupport
from easydiffraction.core.metadata import Compatibility
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import MembershipValidator
from easydiffraction.core.validation import RangeValidator
from easydiffraction.core.validation import RegexValidator
from easydiffraction.core.variable import NumericDescriptor
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.datablocks.experiment.categories.data.factory import DataFactory
from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
from easydiffraction.datablocks.experiment.item.enums import CalculatorEnum
from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum
from easydiffraction.io.cif.handler import TagSpec
from easydiffraction.utils.logging import log
from easydiffraction.utils.utils import tof_to_d
from easydiffraction.utils.utils import twotheta_to_d

if TYPE_CHECKING:
    from easydiffraction.analysis.calculators.base import PowderReflnRecord

# Uncertainty values below this threshold are replaced with 1.0
_MIN_UNCERTAINTY = 0.0001

# Float tolerance so an x-grid whose span is an exact multiple of the
# step keeps its final point instead of dropping it to rounding noise.
_GRID_STEP_TOLERANCE = 1e-9


class PdDataPointBaseMixin:
    """Single base data point mixin for powder diffraction data."""

    def __init__(self) -> None:
        super().__init__()

        self._id = StringDescriptor(
            name='id',
            description='Identifier for this data point in the dataset',
            display_handler=DisplayHandler(
                display_name='ID',
                latex_name='ID',
            ),
            value_spec=AttributeSpec(
                default='0',
                # TODO: the following pattern is valid for dict key
                #  (keywords are not checked). CIF label is less strict.
                #  Do we need conversion between CIF and internal label?
                validator=RegexValidator(pattern=r'^[A-Za-z0-9_]*$'),
            ),
            tags=TagSpec(edi_names=['_data.id'], cif_names=['_pd_data.point_id']),
        )
        self._d_spacing = NumericDescriptor(
            name='d_spacing',
            description='d-spacing value corresponding to this data point',
            units='angstroms',
            display_handler=DisplayHandler(
                display_name='d',
                display_units='Å',
                latex_name=r'$d$',
                latex_units=r'\AA',
            ),
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(ge=0),
            ),
            tags=TagSpec(edi_names=['_data.d_spacing'], cif_names=['_pd_proc.d_spacing']),
        )
        self._intensity_meas = NumericDescriptor(
            name='intensity_meas',
            description='Intensity recorded at each measurement point (angle/time)',
            display_handler=DisplayHandler(
                display_name='Imeas',
                latex_name=r'$I_{\mathrm{meas}}$',
            ),
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(ge=0),
            ),
            tags=TagSpec(
                edi_names=['_data.intensity_meas'],
                cif_names=['_pd_meas.intensity_total', '_pd_proc.intensity_norm'],
            ),
        )
        self._intensity_meas_su = NumericDescriptor(
            name='intensity_meas_su',
            description='Standard uncertainty of the measured intensity at this point',
            display_handler=DisplayHandler(
                display_name='s.u.(Imeas)',
                latex_name=r'$\sigma(I_{\mathrm{meas}})$',
            ),
            value_spec=AttributeSpec(
                default=1.0,
                validator=RangeValidator(ge=0),
            ),
            tags=TagSpec(
                edi_names=['_data.intensity_meas_su'],
                cif_names=['_pd_meas.intensity_total_su', '_pd_proc.intensity_norm_su'],
            ),
        )
        self._intensity_calc = NumericDescriptor(
            name='intensity_calc',
            description='Intensity of a computed diffractogram at this point',
            display_handler=DisplayHandler(
                display_name='Icalc',
                latex_name=r'$I_{\mathrm{calc}}$',
            ),
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(ge=0),
            ),
            tags=TagSpec(
                edi_names=['_data.intensity_calc'], cif_names=['_pd_calc.intensity_total']
            ),
        )
        self._intensity_bkg = NumericDescriptor(
            name='intensity_bkg',
            description='Intensity of a computed background at this point',
            display_handler=DisplayHandler(
                display_name='Ibkg',
                latex_name=r'$I_{\mathrm{bkg}}$',
            ),
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(ge=0),
            ),
            tags=TagSpec(edi_names=['_data.intensity_bkg'], cif_names=['_pd_calc.intensity_bkg']),
        )
        self._calc_status = StringDescriptor(
            name='calc_status',
            description='Status code of the data point in the calculation process',
            display_handler=DisplayHandler(
                display_name='Status',
                latex_name='Status',
            ),
            value_spec=AttributeSpec(
                default='incl',  # TODO: Make Enum
                validator=MembershipValidator(allowed=['incl', 'excl']),
            ),
            tags=TagSpec(
                edi_names=['_data.calc_status'], cif_names=['_pd_data.refinement_status']
            ),
        )

    # ------------------------------------------------------------------
    #  Public properties
    # ------------------------------------------------------------------

    @property
    def id(self) -> StringDescriptor:
        """
        Identifier for this data point in the dataset.

        Reading this property returns the underlying
        ``StringDescriptor`` object.
        """
        return self._id

    @property
    def d_spacing(self) -> NumericDescriptor:
        """
        d-spacing value corresponding to this data point.

        Reading this property returns the underlying
        ``NumericDescriptor`` object.
        """
        return self._d_spacing

    @property
    def intensity_meas(self) -> NumericDescriptor:
        """
        Intensity recorded at each measurement point (angle/time).

        Reading this property returns the underlying
        ``NumericDescriptor`` object.
        """
        return self._intensity_meas

    @property
    def intensity_meas_su(self) -> NumericDescriptor:
        """
        Standard uncertainty of the measured intensity at this point.

        Reading this property returns the underlying
        ``NumericDescriptor`` object.
        """
        return self._intensity_meas_su

    @property
    def intensity_calc(self) -> NumericDescriptor:
        """
        Intensity of a computed diffractogram at this point.

        Reading this property returns the underlying
        ``NumericDescriptor`` object.
        """
        return self._intensity_calc

    @property
    def intensity_bkg(self) -> NumericDescriptor:
        """
        Intensity of a computed background at this point.

        Reading this property returns the underlying
        ``NumericDescriptor`` object.
        """
        return self._intensity_bkg

    @property
    def calc_status(self) -> StringDescriptor:
        """
        Status code of the data point in the calculation process.

        Reading this property returns the underlying
        ``StringDescriptor`` object.
        """
        return self._calc_status


class PdCwlDataPointMixin:
    """Mixin for CWL powder diffraction data points."""

    def __init__(self) -> None:
        super().__init__()

        self._two_theta = NumericDescriptor(
            name='two_theta',
            description='Measured 2θ diffraction angle.',
            units='degrees',
            display_handler=DisplayHandler(
                display_name='2θ',
                display_units='deg',
                latex_name=r'$2\theta$',
                latex_units=r'\mathrm{deg}',
            ),
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(ge=0, le=180),
            ),
            tags=TagSpec(
                edi_names=['_data.two_theta'],
                cif_names=['_pd_proc.2theta_scan', '_pd_meas.2theta_scan'],
            ),
        )

    # ------------------------------------------------------------------
    #  Public properties
    # ------------------------------------------------------------------

    @property
    def two_theta(self) -> NumericDescriptor:
        """
        Measured 2θ diffraction angle (deg).

        Reading this property returns the underlying
        ``NumericDescriptor`` object.
        """
        return self._two_theta


class PdTofDataPointMixin:
    """Mixin for powder diffraction data points with time-of-flight."""

    def __init__(self) -> None:
        super().__init__()

        self._time_of_flight = NumericDescriptor(
            name='time_of_flight',
            description='Measured time for time-of-flight neutron measurement.',
            units='microseconds',
            display_handler=DisplayHandler(
                display_name='TOF',
                latex_name='TOF',
                display_units='μs',
                latex_units=r'$\mu\mathrm{s}$',
            ),
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(ge=0),
            ),
            tags=TagSpec(
                edi_names=['_data.time_of_flight'], cif_names=['_pd_meas.time_of_flight']
            ),
        )

    # ------------------------------------------------------------------
    #  Public properties
    # ------------------------------------------------------------------

    @property
    def time_of_flight(self) -> NumericDescriptor:
        """
        Measured time for time-of-flight neutron measurement (μs).

        Reading this property returns the underlying
        ``NumericDescriptor`` object.
        """
        return self._time_of_flight


class PdCwlDataPoint(
    PdDataPointBaseMixin,  # TODO: rename to BasePdDataPointMixin???
    PdCwlDataPointMixin,  # TODO: rename to CwlPdDataPointMixin???
    CategoryItem,  # Must be last to ensure mixins initialized first
    # TODO: Check this. AI suggest class
    #  CwlThompsonCoxHastings(
    #     PeakBase, # From CategoryItem
    #     CwlBroadeningMixin,
    #     FcjAsymmetryMixin,
    #  ):
    #  But also says, that in fact, it is just for consistency. And both
    #  orders work.
):
    """Powder diffraction data point for CWL experiments."""

    _category_code = 'data'
    _category_entry_name = 'id'

    def __init__(self) -> None:
        super().__init__()


class PdTofDataPoint(
    PdDataPointBaseMixin,
    PdTofDataPointMixin,
    CategoryItem,  # Must be last to ensure mixins initialized first
):
    """Powder diffraction data point for time-of-flight experiments."""

    _category_code = 'data'
    _category_entry_name = 'id'

    def __init__(self) -> None:
        super().__init__()


class PdDataBase(CategoryCollection):
    """Base class for powder diffraction data collections."""

    # TODO: ???

    # Redefine update priority to ensure data updated after other
    # categories. Higher number = runs later. Default for other
    # categories, e.g., background and excluded regions are 10 by
    # default
    _update_priority = 100

    #################
    # Private methods
    #################

    # Should be set only once

    def _set_id(self, values: object) -> None:
        """Set data-point IDs."""
        for p, v in zip(self._items, values, strict=True):
            p.id._value = v

    def _set_intensity_meas(self, values: object) -> None:
        """Set measured intensity."""
        for p, v in zip(self._items, values, strict=True):
            p.intensity_meas._value = v

    def _set_intensity_meas_su(self, values: object) -> None:
        """Set standard uncertainty of measured intensity values."""
        for p, v in zip(self._items, values, strict=True):
            p.intensity_meas_su._value = v

    # Can be set multiple times

    def _set_d_spacing(self, values: object) -> None:
        """Set d-spacing values."""
        for p, v in zip(self._calc_items, values, strict=True):
            p.d_spacing._value = v

    def _set_intensity_calc(self, values: object) -> None:
        """Set calculated intensity."""
        for p, v in zip(self._calc_items, values, strict=True):
            p.intensity_calc._value = v

    def _set_intensity_bkg(self, values: object) -> None:
        """Set background intensity."""
        for p, v in zip(self._calc_items, values, strict=True):
            p.intensity_bkg._value = v

    def _invalidate_calc_cache(self) -> None:
        """
        Drop the cached included-point mask/list.

        Called whenever the calc-status flags or the point set change,
        so the cached ``_calc_mask`` / ``_calc_items`` are rebuilt on
        next access.
        """
        self._calc_mask_cache = None
        self._calc_items_cache = None

    def _on_items_changed(self) -> None:
        """
        Invalidate the calc cache and wire per-point status callbacks.

        Runs after every point add, replace, remove, and bulk-adopt (via
        the base collection hook). It drops the cached included-point
        view and (re)wires each point's ``calc_status`` descriptor so a
        later public ``point.calc_status.value = ...`` write also
        invalidates the cache, keeping ``_calc_mask`` / ``_calc_items``
        correct after any public mutation.
        """
        self._invalidate_calc_cache()
        for point in self._items:
            point.calc_status._on_change = self._invalidate_calc_cache

    def _set_calc_status(self, values: object) -> None:
        """Set refinement status."""
        for p, v in zip(self._items, values, strict=True):
            if v:
                p.calc_status._value = 'incl'
            elif not v:
                p.calc_status._value = 'excl'
            else:
                msg = f'Invalid refinement status value: {v}. Expected boolean True/False.'
                raise ValueError(msg)
        self._invalidate_calc_cache()

    @property
    def _calc_mask(self) -> np.ndarray:
        # Cached: depends only on calc_status (changed only via
        # _set_calc_status) and the point set (rebuilt on creation) —
        # both invalidate the cache. Stable during a fit, so this avoids
        # rebuilding the full calc_status array on every iteration.
        cache = getattr(self, '_calc_mask_cache', None)
        if cache is None:
            cache = self.calc_status == 'incl'
            self._calc_mask_cache = cache
        return cache

    @property
    def _calc_items(self) -> list:
        """Only the items included in calculations."""
        cache = getattr(self, '_calc_items_cache', None)
        if cache is None:
            cache = [
                item for item, mask in zip(self._items, self._calc_mask, strict=False) if mask
            ]
            self._calc_items_cache = cache
        return cache

    # Grid generation when no measured scan exists

    @staticmethod
    def _grid_from_data_range(data_range: object, experiment_name: str) -> np.ndarray | None:
        """
        Return an evenly spaced x-grid from the data range.

        Returns ``None`` when the range cannot be resolved at all (for
        example no instrument to project defaults), leaving the calc
        path to report its own "without measured data" error. Raises a
        clear, named error for an inverted or degenerate range, which is
        user input rather than a missing source.
        """
        x_min = data_range.x_min
        x_max = data_range.x_max
        x_step = data_range.x_step
        if x_step is None or not (
            np.isfinite(x_min) and np.isfinite(x_max) and np.isfinite(x_step)
        ):
            return None
        if x_max <= x_min or x_step <= 0:
            msg = (
                f"Cannot build a calculation grid for experiment '{experiment_name}': "
                f'the data range is empty or inverted (min={x_min}, max={x_max}, '
                f'step={x_step}). Set data_range bounds with min < max and step > 0.'
            )
            raise ValueError(msg)
        # Floor (with a small tolerance) so the last point never
        # exceeds x_max — an overshoot could push 2θ past the 180°
        # validator limit.
        num = int(np.floor((x_max - x_min) / x_step + _GRID_STEP_TOLERANCE)) + 1
        return x_min + np.arange(num) * x_step

    def _has_measured_intensities(self) -> bool:
        """
        Return whether any point carries a finite measured intensity.

        Iterates **all** points (unfiltered): whether a measured scan
        exists is independent of which points are excluded from the
        calculation. Using the exclusion-filtered ``intensity_meas``
        here would misread a fully-excluded scan as "no measured data".
        """
        measured = np.fromiter(
            (point.intensity_meas.value for point in self._items),
            dtype=float,
            count=len(self._items),
        )
        return bool(measured.size) and bool(np.any(np.isfinite(measured)))

    def _clear_generated_grid(self) -> None:
        """
        Drop an auto-generated grid so a changed range can rebuild it.

        Only removes points that were generated from ``data_range``
        (measured intensities absent / all ``NaN``); a measured scan is
        never cleared.
        """
        if not self._items:
            return
        if self._has_measured_intensities():
            return
        self.clear()

    def _skip_cif_serialization(self) -> bool:
        """
        Suppress the data loop for a generated (unmeasured) grid.

        A calculated-only experiment holds generated points whose
        measured intensities are absent (all ``NaN``); serialising them
        would emit ``nan`` tokens and duplicate the ``data_range`` model
        state. The grid is recomputable, so only ``data_range`` is
        persisted. A measured scan serialises unchanged.
        """
        return bool(self._items) and not self._has_measured_intensities()

    def _ensure_grid_from_data_range(self) -> None:
        """
        Build the calculation grid from ``data_range`` when unmeasured.

        Runs only when no data points exist yet. Generated points carry
        an absent (``NaN``) measured intensity so they are never drawn
        or treated as a measured scan; the calculator still fills
        ``intensity_calc`` over the populated x-grid.
        """
        if self._items:
            return
        data_range = getattr(self._parent, 'data_range', None)
        if data_range is None:
            return
        experiment_name = getattr(self._parent, 'name', '?')
        grid = self._grid_from_data_range(data_range, experiment_name)
        if grid is None or grid.size == 0:
            return
        self._create_items_set_xcoord_and_id(grid)
        self._set_intensity_meas(np.full(grid.size, np.nan))

    # Misc

    def _update(
        self,
        *,
        called_by_minimizer: bool = False,
    ) -> None:
        self._ensure_grid_from_data_range()
        experiment = self._parent
        experiments = experiment._parent
        project = experiments._parent
        structures = project.structures
        calculator = experiment.calculator.calculator
        refln = experiment.refln

        calc, refln_records, missing_refln_records = self._phase_calculation_results(
            experiment=experiment,
            structures=structures,
            calculator=calculator,
            called_by_minimizer=called_by_minimizer,
            collect_refln_records=refln is not None,
        )
        self._set_intensity_calc(calc + self.intensity_bkg)
        if refln is None:
            return

        if missing_refln_records:
            refln._replace_from_records([])
            log.warning(
                'Calculated powder reflection metadata is unavailable for '
                f"experiment '{experiment.name}' with calculator "
                f"'{calculator.name}'. Clearing experiment.refln.",
            )
            return

        refln._replace_from_records(refln_records)

    def _phase_calculation_results(
        self,
        *,
        experiment: object,
        structures: object,
        calculator: object,
        called_by_minimizer: bool,
        collect_refln_records: bool,
    ) -> tuple[np.ndarray, list[PowderReflnRecord], bool]:
        calc = np.zeros_like(self.x)
        refln_records: list[PowderReflnRecord] = []
        missing_refln_records = False

        for linked_structure in experiment._get_valid_linked_structures(structures):
            structure_id = linked_structure._identity.category_entry_name
            structure = structures[structure_id]
            structure_scaled_calc, structure_refln_records = self._phase_result(
                structure=structure,
                experiment=experiment,
                calculator=calculator,
                linked_structure=linked_structure,
                called_by_minimizer=called_by_minimizer,
                collect_refln_records=collect_refln_records,
            )
            calc += structure_scaled_calc
            if not collect_refln_records:
                continue
            if structure_refln_records is None:
                missing_refln_records = True
                continue
            refln_records.extend(structure_refln_records)

        return calc, refln_records, missing_refln_records

    @staticmethod
    def _phase_result(
        *,
        structure: object,
        experiment: object,
        calculator: object,
        linked_structure: object,
        called_by_minimizer: bool,
        collect_refln_records: bool,
    ) -> tuple[np.ndarray, list[PowderReflnRecord] | None]:
        structure_calc = calculator.calculate_pattern(
            structure,
            experiment,
            called_by_minimizer=called_by_minimizer,
        )
        structure_scaled_calc = linked_structure.scale.value * structure_calc
        if not collect_refln_records:
            return structure_scaled_calc, []

        structure_refln_records = calculator.last_powder_refln_records(
            structure,
            experiment,
            structure_id=linked_structure.structure_id.value,
        )
        return structure_scaled_calc, structure_refln_records

    ###################
    # Public properties
    ###################

    @property
    def calc_status(self) -> np.ndarray:
        """Refinement-status flags for each data point as an array."""
        return np.fromiter(
            (p.calc_status.value for p in self._items),
            dtype=object,  # TODO: needed? DataTypes.NUMERIC?
        )

    @property
    def d_spacing(self) -> np.ndarray:
        """D-spacing values for active (non-excluded) data points."""
        return np.fromiter(
            (p.d_spacing.value for p in self._calc_items),
            dtype=float,  # TODO: needed? DataTypes.NUMERIC?
        )

    @property
    def intensity_meas(self) -> np.ndarray:
        """Measured intensities for active data points."""
        return np.fromiter(
            (p.intensity_meas.value for p in self._calc_items),
            dtype=float,  # TODO: needed? DataTypes.NUMERIC?
        )

    @property
    def intensity_meas_su(self) -> np.ndarray:
        """
        Standard uncertainties of the measured intensities.

        Values smaller than 0.0001 are replaced with 1.0 to prevent
        fitting failures.
        """
        # TODO: The following is a temporary workaround to handle zero
        #  or near-zero uncertainties in the data, when dats is loaded
        #  from CIF files. This is necessary because zero uncertainties
        #  cause fitting algorithms to fail.
        #  The current implementation is inefficient.
        #  In the future, we should extend the functionality of
        #  the NumericDescriptor to automatically replace the value
        #  outside of the valid range (`validator`) with a
        #  default value (`default`), when the value is set.
        #  BraggPdExperiment._load_ascii_data_to_experiment() handles
        #  this for ASCII data, but we also need to handle CIF data and
        #  come up with a consistent approach for both data sources.
        original = np.fromiter(
            (p.intensity_meas_su.value for p in self._calc_items),
            dtype=float,  # TODO: needed? DataTypes.NUMERIC?
        )
        # Replace values smaller than _MIN_UNCERTAINTY with 1.0
        return np.where(original < _MIN_UNCERTAINTY, 1.0, original)

    @property
    def intensity_calc(self) -> np.ndarray:
        """Calculated intensities for active data points."""
        return np.fromiter(
            (p.intensity_calc.value for p in self._calc_items),
            dtype=float,  # TODO: needed? DataTypes.NUMERIC?
        )

    @property
    def intensity_bkg(self) -> np.ndarray:
        """Background intensities for active data points."""
        return np.fromiter(
            (p.intensity_bkg.value for p in self._calc_items),
            dtype=float,  # TODO: needed? DataTypes.NUMERIC?
        )

    def fit_data_arrays(self) -> dict[str, np.ndarray | None]:
        """Return arrays needed to draw the fit-data chart."""
        meas = self.intensity_meas
        calc = self.intensity_calc
        return {
            'x': self.x,
            'meas': meas,
            'meas_su': self.intensity_meas_su,
            'calc': calc,
            'diff': meas - calc,
            'bkg': self.intensity_bkg,
        }


@DataFactory.register
class PdCwlData(PdDataBase):
    """Bragg powder CWL data collection."""

    # TODO: ???
    # _description: str = 'Powder diffraction data points for
    # constant-wavelength experiments.'
    type_info = TypeInfo(tag='bragg-pd', description='Bragg powder CWL data')
    compatibility = Compatibility(
        sample_form=frozenset({SampleFormEnum.POWDER}),
        scattering_type=frozenset({ScatteringTypeEnum.BRAGG}),
        beam_mode=frozenset({BeamModeEnum.CONSTANT_WAVELENGTH, BeamModeEnum.TIME_OF_FLIGHT}),
    )
    calculator_support = CalculatorSupport(
        calculators=frozenset({CalculatorEnum.CRYSPY, CalculatorEnum.CRYSFML}),
    )

    def __init__(self) -> None:
        super().__init__(item_type=PdCwlDataPoint)

    #################
    # Private methods
    #################

    # Should be set only once

    def _create_items_set_xcoord_and_id(self, values: object) -> None:
        """Set 2θ values."""
        # TODO: split into multiple methods

        # Create items
        self._adopt_items([self._item_type() for _ in range(values.size)])
        self._invalidate_calc_cache()  # point set changed

        # Set two-theta values
        for p, v in zip(self._items, values, strict=True):
            p.two_theta._value = v

        # Set point IDs
        self._set_id([str(i + 1) for i in range(values.size)])

    # Misc

    def _update(
        self,
        *,
        called_by_minimizer: bool = False,
    ) -> None:
        super()._update(called_by_minimizer=called_by_minimizer)

        experiment = self._parent
        d_spacing = twotheta_to_d(
            self.x,
            experiment.instrument.setup_wavelength.value,
        )
        self._set_d_spacing(d_spacing)

    ###################
    # Public properties
    ###################

    @property
    def two_theta(self) -> np.ndarray:
        """2θ values for data points included in calculations."""
        return np.fromiter(
            (p.two_theta.value for p in self._calc_items),
            dtype=float,  # TODO: needed? DataTypes.NUMERIC?
        )

    @property
    def x_descriptor(self) -> NumericDescriptor:
        """Descriptor that owns the 2θ x-axis metadata."""
        if self._items:
            return self._items[0].two_theta
        return self._item_type().two_theta

    @property
    def x(self) -> np.ndarray:
        """Alias for two_theta."""
        return self.two_theta

    @property
    def unfiltered_x(self) -> np.ndarray:
        """The 2θ values for all data points in this collection."""
        return np.fromiter(
            (p.two_theta.value for p in self._items),
            dtype=float,  # TODO: needed? DataTypes.NUMERIC?
        )


@DataFactory.register
class PdTofData(PdDataBase):
    """Bragg powder TOF data collection."""

    type_info = TypeInfo(tag='bragg-pd-tof', description='Bragg powder TOF data')
    compatibility = Compatibility(
        sample_form=frozenset({SampleFormEnum.POWDER}),
        scattering_type=frozenset({ScatteringTypeEnum.BRAGG}),
        beam_mode=frozenset({BeamModeEnum.TIME_OF_FLIGHT}),
    )
    calculator_support = CalculatorSupport(
        calculators=frozenset({CalculatorEnum.CRYSPY, CalculatorEnum.CRYSFML}),
    )

    def __init__(self) -> None:
        super().__init__(item_type=PdTofDataPoint)

    #################
    # Private methods
    #################

    # Should be set only once

    def _create_items_set_xcoord_and_id(self, values: object) -> None:
        """Set time-of-flight values."""
        # TODO: split into multiple methods

        # Create items
        self._adopt_items([self._item_type() for _ in range(values.size)])
        self._invalidate_calc_cache()  # point set changed

        # Set time-of-flight values
        for p, v in zip(self._items, values, strict=True):
            p.time_of_flight._value = v

        # Set point IDs
        self._set_id([str(i + 1) for i in range(values.size)])

    # Misc

    def _update(
        self,
        *,
        called_by_minimizer: bool = False,
    ) -> None:
        super()._update(called_by_minimizer=called_by_minimizer)

        experiment = self._parent
        d_spacing = tof_to_d(
            self.x,
            experiment.instrument.calib_d_to_tof_offset.value,
            experiment.instrument.calib_d_to_tof_linear.value,
            experiment.instrument.calib_d_to_tof_quadratic.value,
        )
        self._set_d_spacing(d_spacing)

    ###################
    # Public properties
    ###################

    @property
    def time_of_flight(self) -> np.ndarray:
        """TOF values for data points included in calculations."""
        return np.fromiter(
            (p.time_of_flight.value for p in self._calc_items),
            dtype=float,  # TODO: needed? DataTypes.NUMERIC?
        )

    @property
    def x_descriptor(self) -> NumericDescriptor:
        """Descriptor that owns the TOF x-axis metadata."""
        if self._items:
            return self._items[0].time_of_flight
        return self._item_type().time_of_flight

    @property
    def x(self) -> np.ndarray:
        """Alias for time_of_flight."""
        return self.time_of_flight

    @property
    def unfiltered_x(self) -> np.ndarray:
        """The TOF values for all data points in this collection."""
        return np.fromiter(
            (p.time_of_flight.value for p in self._items),
            dtype=float,  # TODO: needed? DataTypes.NUMERIC?
        )
