# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from easydiffraction.core.category import CategoryCollection
from easydiffraction.core.metadata import CalculatorSupport
from easydiffraction.core.metadata import Compatibility
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import RangeValidator
from easydiffraction.core.variable import NumericDescriptor
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.datablocks.experiment.categories.refln.bragg_sc import (
    Refln as SingleCrystalRefln,
)
from easydiffraction.datablocks.experiment.categories.refln.factory import ReflnFactory
from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
from easydiffraction.datablocks.experiment.item.enums import CalculatorEnum
from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum
from easydiffraction.io.cif.handler import CifHandler

if TYPE_CHECKING:
    from collections.abc import Sequence

    from easydiffraction.analysis.calculators.base import PowderReflnRecord


class PowderReflnBase(SingleCrystalRefln):
    """Single calculated powder reflection row."""

    def __init__(self) -> None:
        super().__init__()

        self._phase_id = StringDescriptor(
            name='phase_id',
            description='Identifier of the linked phase for this reflection',
            value_spec=AttributeSpec(default=''),
            cif_handler=CifHandler(names=['_refln.phase_id']),
        )
        self._f_calc = NumericDescriptor(
            name='f_calc',
            description='Calculated structure-factor amplitude for this reflection',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(ge=0),
            ),
            cif_handler=CifHandler(names=['_refln.f_calc']),
        )
        self._f_squared_calc = NumericDescriptor(
            name='f_squared_calc',
            description='Calculated structure-factor amplitude squared for this reflection',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(ge=0),
            ),
            cif_handler=CifHandler(names=['_refln.f_squared_calc']),
        )

    @property
    def phase_id(self) -> StringDescriptor:
        """Linked-phase identifier for this reflection."""
        return self._phase_id

    @property
    def f_calc(self) -> NumericDescriptor:
        """Calculated structure-factor amplitude for this reflection."""
        return self._f_calc

    @property
    def f_squared_calc(self) -> NumericDescriptor:
        """Calculated structure-factor amplitude squared."""
        return self._f_squared_calc

    @property
    def parameters(self) -> list:
        """Powder reflection descriptors serialized in CIF loops."""
        return [
            self._id,
            self._phase_id,
            self._d_spacing,
            self._sin_theta_over_lambda,
            self._index_h,
            self._index_k,
            self._index_l,
            self._f_calc,
            self._f_squared_calc,
        ]


class PowderCwlRefln(PowderReflnBase):
    """Single calculated powder reflection row for CWL experiments."""

    def __init__(self) -> None:
        super().__init__()

        self._two_theta = NumericDescriptor(
            name='two_theta',
            description='Calculated 2theta position for this reflection',
            units='deg',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(ge=0, le=180),
            ),
            cif_handler=CifHandler(names=['_refln.two_theta']),
        )

    @property
    def two_theta(self) -> NumericDescriptor:
        """Calculated 2theta position for this reflection."""
        return self._two_theta

    @property
    def parameters(self) -> list:
        """Powder CWL reflection descriptors serialized in CIF loops."""
        return [*super().parameters, self._two_theta]


class PowderTofRefln(PowderReflnBase):
    """Single calculated powder reflection row for TOF experiments."""

    def __init__(self) -> None:
        super().__init__()

        self._time_of_flight = NumericDescriptor(
            name='time_of_flight',
            description='Calculated time-of-flight position for this reflection',
            units='μs',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(ge=0),
            ),
            cif_handler=CifHandler(names=['_refln.time_of_flight']),
        )

    @property
    def time_of_flight(self) -> NumericDescriptor:
        """Calculated time-of-flight position for this reflection."""
        return self._time_of_flight

    @property
    def parameters(self) -> list:
        """Powder TOF reflection descriptors serialized in CIF loops."""
        return [*super().parameters, self._time_of_flight]


class PowderReflnDataBase(CategoryCollection):
    """Base collection for calculated powder reflection rows."""

    _update_priority = 110

    def _replace_from_records(self, records: Sequence[PowderReflnRecord]) -> None:
        """Replace all rows from calculator reflection records."""
        for item in self._items:
            item._parent = None

        new_items = []
        for index, record in enumerate(records, start=1):
            item = self._item_type()
            item._parent = self
            item.id._value = str(index)
            item.phase_id._value = str(record.phase_id)
            item.d_spacing._value = float(record.d_spacing)
            item.sin_theta_over_lambda._value = float(record.sin_theta_over_lambda)
            item.index_h._value = record.index_h
            item.index_k._value = record.index_k
            item.index_l._value = record.index_l
            item.f_calc._value = float(record.f_calc)
            item.f_squared_calc._value = float(record.f_squared_calc)
            self._set_x_value(item=item, record=record)
            new_items.append(item)

        self._items = new_items
        self._rebuild_index()

    def _set_x_value(
        self,
        *,
        item: PowderReflnBase,
        record: PowderReflnRecord,
    ) -> None:
        """Set the beam-mode-specific x coordinate."""
        del self, item, record

    @property
    def id(self) -> np.ndarray:
        """Reflection identifiers for all rows."""
        return np.fromiter((item.id.value for item in self._items), dtype=object)

    @property
    def phase_id(self) -> np.ndarray:
        """Linked-phase identifiers for all rows."""
        return np.fromiter((item.phase_id.value for item in self._items), dtype=object)

    @property
    def d_spacing(self) -> np.ndarray:
        """D-spacing values for all rows."""
        return np.fromiter((item.d_spacing.value for item in self._items), dtype=float)

    @property
    def sin_theta_over_lambda(self) -> np.ndarray:
        """sin(theta)/lambda values for all rows."""
        return np.fromiter(
            (item.sin_theta_over_lambda.value for item in self._items),
            dtype=float,
        )

    @property
    def index_h(self) -> np.ndarray:
        """Miller h indices for all rows."""
        return np.fromiter((item.index_h.value for item in self._items), dtype=float)

    @property
    def index_k(self) -> np.ndarray:
        """Miller k indices for all rows."""
        return np.fromiter((item.index_k.value for item in self._items), dtype=float)

    @property
    def index_l(self) -> np.ndarray:
        """Miller l indices for all rows."""
        return np.fromiter((item.index_l.value for item in self._items), dtype=float)

    @property
    def f_calc(self) -> np.ndarray:
        """Calculated structure-factor amplitudes for all rows."""
        return np.fromiter((item.f_calc.value for item in self._items), dtype=float)

    @property
    def f_squared_calc(self) -> np.ndarray:
        """
        Calculated structure-factor amplitudes squared for all rows.
        """
        return np.fromiter((item.f_squared_calc.value for item in self._items), dtype=float)


@ReflnFactory.register
class PowderCwlReflnData(PowderReflnDataBase):
    """Calculated powder reflection collection for CWL experiments."""

    type_info = TypeInfo(tag='bragg-pd-refln', description='Bragg powder CWL reflection data')
    compatibility = Compatibility(
        sample_form=frozenset({SampleFormEnum.POWDER}),
        scattering_type=frozenset({ScatteringTypeEnum.BRAGG}),
        beam_mode=frozenset({BeamModeEnum.CONSTANT_WAVELENGTH}),
    )
    calculator_support = CalculatorSupport(
        calculators=frozenset({CalculatorEnum.CRYSPY}),
    )

    def __init__(self) -> None:
        super().__init__(item_type=PowderCwlRefln)

    def _set_x_value(
        self,
        *,
        item: PowderReflnBase,
        record: PowderReflnRecord,
    ) -> None:
        del self
        item.two_theta._value = float(record.two_theta)

    @property
    def two_theta(self) -> np.ndarray:
        """Calculated 2theta positions for all rows."""
        return np.fromiter((item.two_theta.value for item in self._items), dtype=float)


@ReflnFactory.register
class PowderTofReflnData(PowderReflnDataBase):
    """Calculated powder reflection collection for TOF experiments."""

    type_info = TypeInfo(tag='bragg-pd-tof-refln', description='Bragg powder TOF reflection data')
    compatibility = Compatibility(
        sample_form=frozenset({SampleFormEnum.POWDER}),
        scattering_type=frozenset({ScatteringTypeEnum.BRAGG}),
        beam_mode=frozenset({BeamModeEnum.TIME_OF_FLIGHT}),
    )
    calculator_support = CalculatorSupport(
        calculators=frozenset({CalculatorEnum.CRYSPY}),
    )

    def __init__(self) -> None:
        super().__init__(item_type=PowderTofRefln)

    def _set_x_value(
        self,
        *,
        item: PowderReflnBase,
        record: PowderReflnRecord,
    ) -> None:
        del self
        item.time_of_flight._value = float(record.time_of_flight)

    @property
    def time_of_flight(self) -> np.ndarray:
        """Calculated time-of-flight positions for all rows."""
        return np.fromiter((item.time_of_flight.value for item in self._items), dtype=float)
