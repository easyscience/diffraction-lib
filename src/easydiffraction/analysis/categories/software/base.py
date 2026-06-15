# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Software-provenance row items."""

from __future__ import annotations

from easydiffraction.analysis.enums import SoftwareRoleEnum
from easydiffraction.core.category import CategoryItem
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.variable import EnumDescriptor
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.io.cif.handler import TagSpec


class SoftwareRole(CategoryItem):
    """Name, version, and URL for one software role."""

    _category_code = 'software'
    _category_entry_name = 'id'

    def __init__(self, role: SoftwareRoleEnum | str = 'framework') -> None:
        """
        Create descriptors for one software role.

        Parameters
        ----------
        role : SoftwareRoleEnum | str, default='framework'
            Software role represented by this row.
        """
        super().__init__()
        role_value = SoftwareRoleEnum(role).value
        self._id = EnumDescriptor(
            name='id',
            enum=SoftwareRoleEnum,
            description='Software role.',
            default=role_value,
            tags=TagSpec(edi_names=['_software.id']),
        )
        self._name = StringDescriptor(
            name='name',
            description='Software package name.',
            value_spec=AttributeSpec(default=None, allow_none=True),
            tags=TagSpec(edi_names=['_software.name']),
        )
        self._version = StringDescriptor(
            name='version',
            description='Software package version.',
            value_spec=AttributeSpec(default=None, allow_none=True),
            tags=TagSpec(edi_names=['_software.version']),
        )
        self._url = StringDescriptor(
            name='url',
            description='Software project URL.',
            value_spec=AttributeSpec(default=None, allow_none=True),
            tags=TagSpec(edi_names=['_software.url']),
        )

    @property
    def id(self) -> EnumDescriptor:
        """Software role."""
        return self._id

    def _set_id(self, value: str) -> None:
        """Set the software role for restore helpers."""
        self._id.value = value

    @property
    def name(self) -> StringDescriptor:
        """Software name."""
        return self._name

    @name.setter
    def name(self, value: str | None) -> None:
        """Set the software name."""
        self._name.value = value

    @property
    def version(self) -> StringDescriptor:
        """Software version."""
        return self._version

    @version.setter
    def version(self, value: str | None) -> None:
        """Set the software version."""
        self._version.value = value

    @property
    def url(self) -> StringDescriptor:
        """Software project URL."""
        return self._url

    @url.setter
    def url(self, value: str | None) -> None:
        """Set the software project URL."""
        self._url.value = value

    @property
    def parameters(self) -> list[StringDescriptor]:
        """Descriptors owned by this software role."""
        return [self._id, self._name, self._version, self._url]
