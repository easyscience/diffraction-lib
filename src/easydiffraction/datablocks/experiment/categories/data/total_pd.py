# SPDX-FileCopyrightText: 2021-2026 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Data categories for total scattering (PDF) experiments."""

from __future__ import annotations

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


class TotalDataPoint(CategoryItem):
    """Total scattering (PDF) data point in r-space (real space).

    Note: PDF data is always in r-space regardless of whether the
    original measurement was CWL or TOF.
    """

    def __init__(self) -> None:
        super().__init__()

        self._point_id = StringDescriptor(
            name='point_id',
            description='Identifier for this data point in the dataset.',
            value_spec=AttributeSpec(
                default='0',
                validator=RegexValidator(pattern=r'^[A-Za-z0-9_]*$'),
            ),
            cif_handler=CifHandler(
                names=[
                    '_pd_data.point_id',  # TODO: Use total scattering CIF names
                ]
            ),
        )
        self._r = NumericDescriptor(
            name='r',
            description='Interatomic distance in real space.',
            units='Å',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(ge=0),
            ),
            cif_handler=CifHandler(
                names=[
                    '_pd_proc.r',  # TODO: Use PDF-specific CIF names
                ]
            ),
        )
        self._g_r_meas = NumericDescriptor(
            name='g_r_meas',
            description='Measured pair distribution function G(r).',
            value_spec=AttributeSpec(
                default=0.0,
            ),
            cif_handler=CifHandler(
                names=[
                    '_pd_meas.intensity_total',  # TODO: Use PDF-specific CIF names
                ]
            ),
        )
        self._g_r_meas_su = NumericDescriptor(
            name='g_r_meas_su',
            description='Standard uncertainty of measured G(r).',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(ge=0),
            ),
            cif_handler=CifHandler(
                names=[
                    '_pd_meas.intensity_total_su',  # TODO: Use PDF-specific CIF names
                ]
            ),
        )
        self._g_r_calc = NumericDescriptor(
            name='g_r_calc',
            description='Calculated pair distribution function G(r).',
            value_spec=AttributeSpec(
                default=0.0,
            ),
            cif_handler=CifHandler(
                names=[
                    '_pd_calc.intensity_total',  # TODO: Use PDF-specific CIF names
                ]
            ),
        )
        self._calc_status = StringDescriptor(
            name='calc_status',
            description='Status code of the data point in calculation.',
            value_spec=AttributeSpec(
                default='incl',
                validator=MembershipValidator(allowed=['incl', 'excl']),
            ),
            cif_handler=CifHandler(
                names=[
                    '_pd_data.refinement_status',  # TODO: Use PDF-specific CIF names
                ]
            ),
        )

        self._identity.category_code = 'total_data'
        self._identity.category_entry_name = lambda: str(self.point_id.value)

    # ------------------------------------------------------------------
    #  Public properties
    # ------------------------------------------------------------------

    @property
    def point_id(self) -> StringDescriptor:
        return self._point_id

    @property
    def r(self) -> NumericDescriptor:
        return self._r

    @property
    def g_r_meas(self) -> NumericDescriptor:
        return self._g_r_meas

    @property
    def g_r_meas_su(self) -> NumericDescriptor:
        return self._g_r_meas_su

    @property
    def g_r_calc(self) -> NumericDescriptor:
        return self._g_r_calc

    @property
    def calc_status(self) -> StringDescriptor:
        return self._calc_status


class TotalDataBase(CategoryCollection):
    """Base class for total scattering data collections."""

    _update_priority = 100

    #################
    # Private methods
    #################

    # Should be set only once

    def _set_point_id(self, values) -> None:
        """Helper method to set point IDs."""
        for p, v in zip(self._items, values, strict=True):
            p.point_id._value = v

    def _set_g_r_meas(self, values) -> None:
        """Helper method to set measured G(r)."""
        for p, v in zip(self._items, values, strict=True):
            p.g_r_meas._value = v

    def _set_g_r_meas_su(self, values) -> None:
        """Helper method to set standard uncertainty of measured
        G(r).
        """
        for p, v in zip(self._items, values, strict=True):
            p.g_r_meas_su._value = v

    # Can be set multiple times

    def _set_g_r_calc(self, values) -> None:
        """Helper method to set calculated G(r)."""
        for p, v in zip(self._calc_items, values, strict=True):
            p.g_r_calc._value = v

    def _set_calc_status(self, values) -> None:
        """Helper method to set calculation status."""
        for p, v in zip(self._items, values, strict=True):
            if v:
                p.calc_status._value = 'incl'
            elif not v:
                p.calc_status._value = 'excl'
            else:
                raise ValueError(
                    f'Invalid calculation status value: {v}. Expected boolean True/False.'
                )

    @property
    def _calc_mask(self) -> np.ndarray:
        return self.calc_status == 'incl'

    @property
    def _calc_items(self):
        """Get only the items included in calculations."""
        return [item for item, mask in zip(self._items, self._calc_mask, strict=False) if mask]

    # Misc

    def _update(self, called_by_minimizer=False):
        experiment = self._parent
        experiments = experiment._parent
        project = experiments._parent
        structures = project.structures
        calculator = experiment.calculator

        initial_calc = np.zeros_like(self.x)
        calc = initial_calc

        # TODO: refactor _get_valid_linked_phases to only be responsible
        #  for returning list. Warning message should be defined here,
        #  at least some of them.
        # TODO: Adapt following the _update method in bragg_sc.py
        for linked_phase in experiment._get_valid_linked_phases(structures):
            structure_id = linked_phase._identity.category_entry_name
            structure_scale = linked_phase.scale.value
            structure = structures[structure_id]

            structure_calc = calculator.calculate_pattern(
                structure,
                experiment,
                called_by_minimizer=called_by_minimizer,
            )

            structure_scaled_calc = structure_scale * structure_calc
            calc += structure_scaled_calc

        self._set_g_r_calc(calc)

    # ------------------------------------------------------------------
    #  Public properties
    # ------------------------------------------------------------------

    @property
    def calc_status(self) -> np.ndarray:
        return np.fromiter(
            (p.calc_status.value for p in self._items),
            dtype=object,  # TODO: needed? DataTypes.NUMERIC?
        )

    @property
    def intensity_meas(self) -> np.ndarray:
        return np.fromiter(
            (p.g_r_meas.value for p in self._calc_items),
            dtype=float,  # TODO: needed? DataTypes.NUMERIC?
        )

    @property
    def intensity_meas_su(self) -> np.ndarray:
        return np.fromiter(
            (p.g_r_meas_su.value for p in self._calc_items),
            dtype=float,  # TODO: needed? DataTypes.NUMERIC?
        )

    @property
    def intensity_calc(self) -> np.ndarray:
        return np.fromiter(
            (p.g_r_calc.value for p in self._calc_items),
            dtype=float,  # TODO: needed? DataTypes.NUMERIC?
        )

    @property
    def intensity_bkg(self) -> np.ndarray:
        """Background is always zero for PDF data."""
        return np.zeros_like(self.intensity_calc)


@DataFactory.register
class TotalData(TotalDataBase):
    """Total scattering (PDF) data collection in r-space.

    Note: Works for both CWL and TOF measurements as PDF data
    is always transformed to r-space.
    """

    type_info = TypeInfo(tag='total-pd', description='Total scattering (PDF) data')
    compatibility = Compatibility(
        sample_form=frozenset({SampleFormEnum.POWDER}),
        scattering_type=frozenset({ScatteringTypeEnum.TOTAL}),
        beam_mode=frozenset({BeamModeEnum.CONSTANT_WAVELENGTH, BeamModeEnum.TIME_OF_FLIGHT}),
    )
    calculator_support = CalculatorSupport(
        calculators=frozenset({CalculatorEnum.PDFFIT}),
    )

    def __init__(self):
        super().__init__(item_type=TotalDataPoint)

    #################
    # Private methods
    #################

    # Should be set only once

    def _create_items_set_xcoord_and_id(self, values) -> None:
        """Helper method to set r values."""
        # TODO: split into multiple methods

        # Create items
        self._items = [self._item_type() for _ in range(values.size)]

        # Set r values
        for p, v in zip(self._items, values, strict=True):
            p.r._value = v

        # Set point IDs
        self._set_point_id([str(i + 1) for i in range(values.size)])

    # ------------------------------------------------------------------
    #  Public properties
    # ------------------------------------------------------------------

    @property
    def x(self) -> np.ndarray:
        """Get the r values for data points included in calculations."""
        return np.fromiter(
            (p.r.value for p in self._calc_items),
            dtype=float,  # TODO: needed? DataTypes.NUMERIC?
        )

    @property
    def unfiltered_x(self) -> np.ndarray:
        """Get the r values for all data points."""
        return np.fromiter(
            (p.r.value for p in self._items),
            dtype=float,  # TODO: needed? DataTypes.NUMERIC?
        )
