# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Project fit-output verbosity category."""

from __future__ import annotations

from easydiffraction.core.category import CategoryItem
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.variable import EnumDescriptor
from easydiffraction.io.cif.handler import TagSpec
from easydiffraction.project.categories.verbosity.factory import VerbosityFactory
from easydiffraction.utils.enums import VerbosityEnum


@VerbosityFactory.register
class Verbosity(CategoryItem):
    """Fit-output verbosity selection for a project."""

    _category_code = 'verbosity'

    type_info = TypeInfo(
        tag='default',
        description='Project verbosity category',
    )

    def __init__(self) -> None:
        super().__init__()

        self._fit = EnumDescriptor(
            name='fit',
            enum=VerbosityEnum,
            description='Fitting process output verbosity',
            tags=TagSpec(edi_names=['_verbosity.fit']),
        )

    @property
    def fit(self) -> EnumDescriptor:
        """Fitting process output verbosity."""
        return self._fit

    @fit.setter
    def fit(self, value: str) -> None:
        self._fit.value = VerbosityEnum(value).value

    @property
    def as_cif(self) -> str:
        """Return CIF representation of this verbosity category."""
        return super().as_cif
