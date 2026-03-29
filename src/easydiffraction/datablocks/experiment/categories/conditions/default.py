# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Experimental conditions category with parameters like temperature, etc."""

from __future__ import annotations

from easydiffraction.core.category import CategoryItem
from easydiffraction.core.metadata import Compatibility
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import RangeValidator
from easydiffraction.core.validation import RegexValidator
from easydiffraction.core.variable import Parameter
from easydiffraction.core.variable import NumericDescriptor
from easydiffraction.datablocks.experiment.categories.conditions.factory import ConditionsFactory
from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
from easydiffraction.io.cif.handler import CifHandler


@ConditionsFactory.register
class Conditions(CategoryItem):
    """Experimental conditions category with parameters like temperature, etc."""

    type_info = TypeInfo(
        tag='default',
        description='Experimental conditions category with parameters like temperature, etc.',
    )

    def __init__(self) -> None:
        super().__init__()

        self._temperature = NumericDescriptor(
            name='temperature',
            description='Temperature of the sample during measurement',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_conditions.temperature']),
        )

        self._identity.category_code = 'conditions'

    # ------------------------------------------------------------------
    #  Public properties
    # ------------------------------------------------------------------

    @property
    def temperature(self) -> NumericDescriptor:
        """
        Temperature of the sample during measurement.

        Reading this property returns the underlying
        ``StringDescriptor`` object. Assigning to it updates the
        parameter value.
        """
        return self._temperature

    @temperature.setter
    def temperature(self, value: float) -> None:
        self._temperature.value = value
