# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Shared software-provenance role helpers."""

from __future__ import annotations

from easydiffraction.core.guard import GuardedBase
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.io.cif.handler import CifHandler


class SoftwareRole(GuardedBase):
    """Name, version, and URL for one software role."""

    def __init__(self, *, role_name: str, description: str) -> None:
        """
        Create descriptors for one software role.

        Parameters
        ----------
        role_name : str
            Role prefix used in persisted CIF item names.
        description : str
            Human-readable role description.
        """
        super().__init__()
        self._name = StringDescriptor(
            name=f'{role_name}_name',
            description=f'{description} name.',
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(names=[f'_software.{role_name}_name']),
        )
        self._version = StringDescriptor(
            name=f'{role_name}_version',
            description=f'{description} version.',
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(names=[f'_software.{role_name}_version']),
        )
        self._url = StringDescriptor(
            name=f'{role_name}_url',
            description=f'{description} URL.',
            value_spec=AttributeSpec(default=None, allow_none=True),
            cif_handler=CifHandler(names=[f'_software.{role_name}_url']),
        )

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
        return [self._name, self._version, self._url]

    @property
    def as_cif(self) -> str:
        """Return CIF representation of this software role."""
        return '\n'.join(param.as_cif for param in self.parameters)
