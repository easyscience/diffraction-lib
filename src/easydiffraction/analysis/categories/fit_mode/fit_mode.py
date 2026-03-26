# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Fit-mode category item.

Stores the active fitting strategy as a CIF-serializable descriptor
validated by ``FitModeEnum``.
"""

from __future__ import annotations

from easydiffraction.analysis.categories.fit_mode.enums import FitModeEnum
from easydiffraction.analysis.categories.fit_mode.factory import FitModeFactory
from easydiffraction.core.category import CategoryItem
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import MembershipValidator
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.io.cif.handler import CifHandler


@FitModeFactory.register
class FitMode(CategoryItem):
    """Fitting strategy selector.

    Holds a single ``mode`` descriptor whose value is one of
    ``FitModeEnum`` members (``'single'`` or ``'joint'``).
    """

    type_info = TypeInfo(
        tag='default',
        description='Fit-mode category',
    )

    def __init__(self) -> None:
        super().__init__()

        self._mode: StringDescriptor = StringDescriptor(
            name='mode',
            description='Fitting strategy',
            value_spec=AttributeSpec(
                default=FitModeEnum.default().value,
                validator=MembershipValidator(allowed=[member.value for member in FitModeEnum]),
            ),
            cif_handler=CifHandler(names=['_analysis.fit_mode']),
        )

        self._identity.category_code = 'fit_mode'

    @property
    def mode(self) -> StringDescriptor:
        """Fitting strategy.

        Reading this property returns the underlying
        ``StringDescriptor`` object. Assigning to it updates the
        parameter value.
        """
        return self._mode

    @mode.setter
    def mode(self, value: str) -> None:
        self._mode.value = value
