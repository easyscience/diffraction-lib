# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Experiment calculator category."""

from __future__ import annotations

from easydiffraction.core.category import CategoryItem
from easydiffraction.core.display_handler import DisplayHandler
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.switchable import SwitchableCategoryBase
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import MembershipValidator
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.datablocks.experiment.categories.calculator.factory import (
    CalculatorCategoryFactory,
)
from easydiffraction.datablocks.experiment.item.enums import CalculatorEnum
from easydiffraction.io.cif.handler import TagSpec
from easydiffraction.io.cif.parse import read_cif_str


@CalculatorCategoryFactory.register
class Calculator(CategoryItem, SwitchableCategoryBase):
    """Calculator selection and access for an experiment."""

    _category_code = 'calculator'
    _owner_attr_name = 'calculator'
    _swap_method_name = '_swap_calculator'

    type_info = TypeInfo(
        tag='default',
        description='Experiment calculator category',
    )

    def __init__(
        self,
        *,
        type: str,
    ) -> None:
        super().__init__()

        self._type = StringDescriptor(
            name='type',
            description='Calculator backend type',
            value_spec=AttributeSpec(
                default=type,
                validator=MembershipValidator(
                    allowed=[member.value for member in CalculatorEnum],
                ),
            ),
            tags=TagSpec(
                edi_names=['_calculator.type'], cif_names=['_easydiffraction_calculator.type']
            ),
            display_handler=DisplayHandler(
                display_name='Type',
                latex_name='Type',
            ),
        )

    @property
    def calculator(self) -> object | None:
        """Live calculator backend instance."""
        parent = getattr(self, '_parent', None)
        if parent is None:
            return None
        if getattr(parent, '_calculator', None) is None:
            parent._resolve_calculator()
        return parent._calculator

    def _supported_types(
        self,
        filters: dict[str, object],
    ) -> list[tuple[str, str]]:
        """Return calculator backends supported by this experiment."""
        del filters
        from easydiffraction.analysis.calculators.factory import CalculatorFactory  # noqa: PLC0415

        parent = getattr(self, '_parent', None)
        if parent is None:
            supported_tags = CalculatorFactory.supported_tags()
        else:
            supported_tags = parent._supported_calculator_tags()
        all_classes = CalculatorFactory._supported_map()
        return [
            (tag, cls.type_info.description)
            for tag, cls in all_classes.items()
            if tag in supported_tags
        ]

    def from_cif(self, block: object, idx: int = 0) -> None:
        """Populate this calculator category from a CIF block."""
        del idx
        tag = read_cif_str(block, '_calculator.type')
        if tag is None:
            return
        parent = getattr(self, '_parent', None)
        if parent is None:
            self._type.value = tag
            return
        parent._swap_calculator(tag, announce=False, strict=False)
