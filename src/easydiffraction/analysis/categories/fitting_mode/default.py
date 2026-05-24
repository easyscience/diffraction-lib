# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Analysis fitting-mode category."""

from __future__ import annotations

from easydiffraction.analysis.categories.fitting_mode.factory import FittingModeFactory
from easydiffraction.analysis.enums import FitModeEnum
from easydiffraction.core.category import CategoryItem
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.switchable import SwitchableCategoryBase
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import MembershipValidator
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.io.cif.handler import CifHandler


@FittingModeFactory.register
class FittingMode(CategoryItem, SwitchableCategoryBase):
    """Fitting-mode selector for an analysis."""

    _category_code = 'fitting_mode'
    _owner_attr_name = 'fitting_mode'
    _swap_method_name = '_swap_fitting_mode'

    type_info = TypeInfo(
        tag='default',
        description='Analysis fitting-mode category',
    )

    def __init__(self) -> None:
        super().__init__()

        self._type = StringDescriptor(
            name='type',
            description='Active fitting mode',
            value_spec=AttributeSpec(
                default=FitModeEnum.default().value,
                validator=MembershipValidator(
                    allowed=[mode.value for mode in FitModeEnum],
                ),
            ),
            cif_handler=CifHandler(names=['_fitting_mode.type']),
        )

    @staticmethod
    def _supported_types(
        filters: dict[str, object],
    ) -> list[tuple[str, str]]:
        """Return supported fitting modes."""
        del filters
        return [(mode.value, mode.description()) for mode in FitModeEnum]
