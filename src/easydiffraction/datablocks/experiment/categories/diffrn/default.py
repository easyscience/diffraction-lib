# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Default diffraction ambient-conditions category."""

from __future__ import annotations

from easydiffraction.core.category import CategoryItem
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import RangeValidator
from easydiffraction.core.variable import NumericDescriptor
from easydiffraction.datablocks.experiment.categories.diffrn.factory import DiffrnFactory
from easydiffraction.io.cif.handler import CifHandler


@DiffrnFactory.register
class DefaultDiffrn(CategoryItem):
    """Ambient conditions recorded during diffraction measurement."""

    type_info = TypeInfo(
        tag='default',
        description='Diffraction ambient conditions',
    )

    def __init__(self) -> None:
        super().__init__()

        self._ambient_temperature = NumericDescriptor(
            name='ambient_temperature',
            description='Mean temperature during measurement',
            units='K',
            value_spec=AttributeSpec(
                default=None,
                allow_none=True,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_diffrn.ambient_temperature']),
        )

        self._ambient_pressure = NumericDescriptor(
            name='ambient_pressure',
            description='Mean hydrostatic pressure during measurement',
            units='kPa',
            value_spec=AttributeSpec(
                default=None,
                allow_none=True,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_diffrn.ambient_pressure']),
        )

        self._ambient_magnetic_field = NumericDescriptor(
            name='ambient_magnetic_field',
            description='Mean magnetic field during measurement',
            units='T',
            value_spec=AttributeSpec(
                default=None,
                allow_none=True,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_diffrn.ambient_magnetic_field']),
        )

        self._ambient_electric_field = NumericDescriptor(
            name='ambient_electric_field',
            description='Mean electric field during measurement',
            units='V/m',
            value_spec=AttributeSpec(
                default=None,
                allow_none=True,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_diffrn.ambient_electric_field']),
        )

        self._identity.category_code = 'diffrn'

    # ------------------------------------------------------------------
    #  Public properties
    # ------------------------------------------------------------------

    @property
    def ambient_temperature(self) -> NumericDescriptor:
        """
        Mean temperature during measurement (K).

        Reading this property returns the underlying
        ``NumericDescriptor`` object. Assigning to it updates the value.
        """
        return self._ambient_temperature

    @ambient_temperature.setter
    def ambient_temperature(self, value: float) -> None:
        self._ambient_temperature.value = value

    @property
    def ambient_pressure(self) -> NumericDescriptor:
        """
        Mean hydrostatic pressure during measurement (kPa).

        Reading this property returns the underlying
        ``NumericDescriptor`` object. Assigning to it updates the value.
        """
        return self._ambient_pressure

    @ambient_pressure.setter
    def ambient_pressure(self, value: float) -> None:
        self._ambient_pressure.value = value

    @property
    def ambient_magnetic_field(self) -> NumericDescriptor:
        """
        Mean magnetic field during measurement (T).

        Reading this property returns the underlying
        ``NumericDescriptor`` object. Assigning to it updates the value.
        """
        return self._ambient_magnetic_field

    @ambient_magnetic_field.setter
    def ambient_magnetic_field(self, value: float) -> None:
        self._ambient_magnetic_field.value = value

    @property
    def ambient_electric_field(self) -> NumericDescriptor:
        """
        Mean electric field during measurement (V/m).

        Reading this property returns the underlying
        ``NumericDescriptor`` object. Assigning to it updates the value.
        """
        return self._ambient_electric_field

    @ambient_electric_field.setter
    def ambient_electric_field(self, value: float) -> None:
        self._ambient_electric_field.value = value
