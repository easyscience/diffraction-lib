# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from easydiffraction.core.category import CategoryCollection
from easydiffraction.core.category import CategoryItem
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
from easydiffraction.io.cif.handler import CifHandler
from easydiffraction.utils.logging import log
from easydiffraction.utils.utils import tof_to_d
from easydiffraction.utils.utils import twotheta_to_d

if TYPE_CHECKING:
    from easydiffraction.analysis.calculators.base import PowderReflnRecord

# Uncertainty values below this threshold are replaced with 1.0
_MIN_UNCERTAINTY = 0.0001


class PdDataPointBaseMixin:
    """Single base data point mixin for powder diffraction data."""

    def __init__(self) -> None:
        super().__init__()

        self._point_id = StringDescriptor(
            name='point_id',
            description='Identifier for this data point in the dataset',
            value_spec=AttributeSpec(
                default='0',
                # TODO: the following pattern is valid for dict key
                #  (keywords are not checked). CIF label is less strict.
                #  Do we need conversion between CIF and internal label?
                validator=RegexValidator(pattern=r'^[A-Za-z0-9_]*$'),
            ),
            cif_handler=CifHandler(
                names=[
                    '_pd_data.point_id',
                ]
            ),
        )
        self._d_spacing = NumericDescriptor(
            name='d_spacing',
            description='d-spacing value corresponding to this data point',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(ge=0),
            ),
            cif_handler=CifHandler(names=['_pd_proc.d_spacing']),
        )
        self._intensity_meas = NumericDescriptor(
            name='intensity_meas',
            description='Intensity recorded at each measurement point (angle/time)',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(ge=0),
            ),
            cif_handler=CifHandler(
                names=[
                    '_pd_meas.intensity_total',
                    '_pd_proc.intensity_norm',
                ]
            ),
        )
        self._intensity_meas_su = NumericDescriptor(
            name='intensity_meas_su',
            description='Standard uncertainty of the measured intensity at this point',
            value_spec=AttributeSpec(
                default=1.0,
                validator=RangeValidator(ge=0),
            ),
            cif_handler=CifHandler(
                names=[
                    '_pd_meas.intensity_total_su',
                    '_pd_proc.intensity_norm_su',
                ]
            ),
        )
        self._intensity_calc = NumericDescriptor(
            name='intensity_calc',
            description='Intensity of a computed diffractogram at this point',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(ge=0),
            ),
            cif_handler=CifHandler(names=['_pd_calc.intensity_total']),
        )
        self._intensity_bkg = NumericDescriptor(
            name='intensity_bkg',
            description='Intensity of a computed background at this point',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(ge=0),
            ),
            cif_handler=CifHandler(names=['_pd_calc.intensity_bkg']),
        )
        self._calc_status = StringDescriptor(
            name='calc_status',
            description='Status code of the data point in the calculation process',
            value_spec=AttributeSpec(
                default='incl',  # TODO: Make Enum
                validator=MembershipValidator(allowed=['incl', 'excl']),
            ),
            cif_handler=CifHandler(
                names=[
                    '_pd_data.refinement_status',  # TODO: rename to calc_status
                ]
            ),
        )

    # ------------------------------------------------------------------
    #  Public properties
    # ------------------------------------------------------------------

    @property
    def point_id(self) -> StringDescriptor:
        """
        Identifier for this data point in the dataset.

        Reading this property returns the underlying
        ``StringDescriptor`` object.
        """
        return self._point_id

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
            units='deg',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(ge=0, le=180),
            ),
            cif_handler=CifHandler(
                names=[
                    '_pd_proc.2theta_scan',
                    '_pd_meas.2theta_scan',
                ]
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
            units='μs',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(ge=0),
            ),
            cif_handler=CifHandler(names=['_pd_meas.time_of_flight']),
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

    def __init__(self) -> None:
        super().__init__()
        self._identity.category_code = 'pd_data'
        self._identity.category_entry_name = lambda: str(self.point_id.value)


class PdTofDataPoint(
    PdDataPointBaseMixin,
    PdTofDataPointMixin,
    CategoryItem,  # Must be last to ensure mixins initialized first
):
    """Powder diffraction data point for time-of-flight experiments."""

    def __init__(self) -> None:
        super().__init__()
        self._identity.category_code = 'pd_data'
        self._identity.category_entry_name = lambda: str(self.point_id.value)


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

    def _set_point_id(self, values: object) -> None:
        """Set point IDs."""
        for p, v in zip(self._items, values, strict=True):
            p.point_id._value = v

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

    @property
    def _calc_mask(self) -> np.ndarray:
        return self.calc_status == 'incl'

    @property
    def _calc_items(self) -> list:
        """Get only the items included in calculations."""
        return [item for item, mask in zip(self._items, self._calc_mask, strict=False) if mask]

    # Misc

    def _update(
        self,
        *,
        called_by_minimizer: bool = False,
    ) -> None:
        experiment = self._parent
        experiments = experiment._parent
        project = experiments._parent
        structures = project.structures
        calculator = experiment.calculation.calculator

        initial_calc = np.zeros_like(self.x)
        calc = initial_calc
        refln_records: list[PowderReflnRecord] = []
        missing_refln_records = False

        # TODO: refactor _get_valid_linked_phases to only be responsible
        #  for returning list. Warning message should be defined here,
        #  at least some of them.
        # TODO: Adapt following the _update method in bragg_sc.py
        for linked_phase in experiment._get_valid_linked_phases(structures):
            structure_id = linked_phase._identity.category_entry_name
            phase_id = linked_phase.id.value
            structure_scale = linked_phase.scale.value
            structure = structures[structure_id]

            structure_calc = calculator.calculate_pattern(
                structure,
                experiment,
                called_by_minimizer=called_by_minimizer,
            )

            structure_scaled_calc = structure_scale * structure_calc
            calc += structure_scaled_calc

            structure_refln_records = calculator.last_powder_refln_records(
                structure,
                experiment,
                phase_id=phase_id,
            )
            if structure_refln_records is None:
                missing_refln_records = True
            else:
                refln_records.extend(structure_refln_records)

        self._set_intensity_calc(calc + self.intensity_bkg)
        if missing_refln_records:
            experiment.refln._replace_from_records([])
            log.warning(
                'Calculated powder reflection metadata is unavailable for '
                f"experiment '{experiment.name}' with calculator "
                f"'{calculator.name}'. Clearing experiment.refln.",
            )
            return

        experiment.refln._replace_from_records(refln_records)

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
        self._items = [self._item_type() for _ in range(values.size)]

        # Set two-theta values
        for p, v in zip(self._items, values, strict=True):
            p.two_theta._value = v

        # Set point IDs
        self._set_point_id([str(i + 1) for i in range(values.size)])

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
        """Get 2θ values for data points included in calculations."""
        return np.fromiter(
            (p.two_theta.value for p in self._calc_items),
            dtype=float,  # TODO: needed? DataTypes.NUMERIC?
        )

    @property
    def x(self) -> np.ndarray:
        """Alias for two_theta."""
        return self.two_theta

    @property
    def unfiltered_x(self) -> np.ndarray:
        """Get the 2θ values for all data points in this collection."""
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
        self._items = [self._item_type() for _ in range(values.size)]

        # Set time-of-flight values
        for p, v in zip(self._items, values, strict=True):
            p.time_of_flight._value = v

        # Set point IDs
        self._set_point_id([str(i + 1) for i in range(values.size)])

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
            experiment.instrument.calib_d_to_tof_quad.value,
        )
        self._set_d_spacing(d_spacing)

    ###################
    # Public properties
    ###################

    @property
    def time_of_flight(self) -> np.ndarray:
        """Get TOF values for data points included in calculations."""
        return np.fromiter(
            (p.time_of_flight.value for p in self._calc_items),
            dtype=float,  # TODO: needed? DataTypes.NUMERIC?
        )

    @property
    def x(self) -> np.ndarray:
        """Alias for time_of_flight."""
        return self.time_of_flight

    @property
    def unfiltered_x(self) -> np.ndarray:
        """Get the TOF values for all data points in this collection."""
        return np.fromiter(
            (p.time_of_flight.value for p in self._items),
            dtype=float,  # TODO: needed? DataTypes.NUMERIC?
        )
