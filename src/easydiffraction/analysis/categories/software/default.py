# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Analysis software-provenance category."""

from __future__ import annotations

from easydiffraction.analysis.categories.software.base import SoftwareRole
from easydiffraction.analysis.categories.software.factory import SoftwareFactory
from easydiffraction.core.category import CategoryItem
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.io.cif.handler import CifHandler


@SoftwareFactory.register
class Software(CategoryItem):
    """Software-provenance snapshot for the latest successful fit."""

    _category_code = 'software'

    type_info = TypeInfo(
        tag='default',
        description='Analysis software provenance category',
    )

    def __init__(self) -> None:
        super().__init__()
        self._framework = SoftwareRole(
            role_name='framework',
            description='EasyDiffraction framework',
        )
        self._calculator = SoftwareRole(
            role_name='calculator',
            description='Calculation engine',
        )
        self._minimizer = SoftwareRole(
            role_name='minimizer',
            description='Minimization engine',
        )
        self._timestamp = StringDescriptor(
            name='timestamp',
            description='UTC timestamp of the fit provenance snapshot.',
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(names=['_software.timestamp']),
        )

    @property
    def framework(self) -> SoftwareRole:
        """EasyDiffraction framework provenance."""
        return self._framework

    @property
    def calculator(self) -> SoftwareRole:
        """Calculation-engine provenance."""
        return self._calculator

    @property
    def minimizer(self) -> SoftwareRole:
        """Minimization-engine provenance."""
        return self._minimizer

    @property
    def timestamp(self) -> StringDescriptor:
        """UTC timestamp of the fit provenance snapshot."""
        return self._timestamp

    @timestamp.setter
    def timestamp(self, value: str | None) -> None:
        self._timestamp.value = value

    @property
    def parameters(self) -> list[StringDescriptor]:
        """Descriptors owned by this software category."""
        return [
            *self._framework.parameters,
            *self._calculator.parameters,
            *self._minimizer.parameters,
            self._timestamp,
        ]

    @property
    def as_cif(self) -> str:
        """Return CIF representation of this software category."""
        return super().as_cif
