# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Experiment calculation category."""

from __future__ import annotations

from easydiffraction.core.category import CategoryItem
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import MembershipValidator
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.datablocks.experiment.categories.calculation.factory import CalculationFactory
from easydiffraction.datablocks.experiment.item.enums import CalculatorEnum
from easydiffraction.io.cif.handler import CifHandler
from easydiffraction.io.cif.parse import read_cif_str
from easydiffraction.utils.logging import console
from easydiffraction.utils.utils import render_table


@CalculationFactory.register
class Calculation(CategoryItem):
    """Calculator selection and access for an experiment."""

    type_info = TypeInfo(
        tag='default',
        description='Experiment calculation category',
    )

    def __init__(
        self,
        *,
        calculator_type: str,
    ) -> None:
        super().__init__()

        self._calculator_type = StringDescriptor(
            name='calculator_type',
            description='Calculation backend type',
            value_spec=AttributeSpec(
                default=calculator_type,
                validator=MembershipValidator(
                    allowed=[member.value for member in CalculatorEnum],
                ),
            ),
            cif_handler=CifHandler(names=['_calculation.calculator_type']),
        )

        self._identity.category_code = 'calculation'

    @property
    def calculator_type(self) -> StringDescriptor:
        """Calculation backend type."""
        return self._calculator_type

    @calculator_type.setter
    def calculator_type(self, value: str) -> None:
        parent = getattr(self, '_parent', None)
        if parent is None:
            self._calculator_type.value = value
            return
        parent._set_calculator_type(value)

    @property
    def calculator(self) -> object | None:
        """Live calculator backend instance."""
        parent = getattr(self, '_parent', None)
        if parent is None:
            return None
        if getattr(parent, '_calculator', None) is None:
            parent._resolve_calculation()
        return parent._calculator

    def show_calculator_types(self) -> None:
        """Print supported calculator backends and mark current type."""
        from easydiffraction.analysis.calculators.factory import CalculatorFactory  # noqa: PLC0415

        parent = getattr(self, '_parent', None)
        current = self.calculator_type.value
        if parent is None:
            supported_tags = CalculatorFactory.supported_tags()
        else:
            supported_tags = parent._supported_calculator_tags()
        all_classes = CalculatorFactory._supported_map()
        columns_data = [
            ['*' if tag == current else '', tag, cls.type_info.description]
            for tag, cls in all_classes.items()
            if tag in supported_tags
        ]
        console.paragraph('Calculator types')
        render_table(
            columns_headers=['', 'Type', 'Description'],
            columns_alignment=['left', 'left', 'left'],
            columns_data=columns_data,
        )

    def from_cif(self, block: object, idx: int = 0) -> None:
        """Populate this calculation category from a CIF block."""
        del idx
        tag = read_cif_str(block, '_calculation.calculator_type')
        if tag is None:
            return
        parent = getattr(self, '_parent', None)
        if parent is None:
            self._calculator_type.value = tag
            return
        parent._set_calculator_type(tag, announce=False)
