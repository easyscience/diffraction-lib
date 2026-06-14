# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Analysis software-provenance category."""

from __future__ import annotations

from easydiffraction.analysis.categories.software.base import SoftwareRole
from easydiffraction.analysis.categories.software.factory import SoftwareFactory
from easydiffraction.analysis.enums import SoftwareRoleEnum
from easydiffraction.core.category import CategoryCollection
from easydiffraction.core.metadata import TypeInfo


@SoftwareFactory.register
class Software(CategoryCollection):
    """Software-provenance snapshot for the latest successful fit."""

    type_info = TypeInfo(
        tag='default',
        description='Analysis software provenance category',
    )

    def __init__(self) -> None:
        """Initialize the role-keyed software provenance collection."""
        super().__init__(item_type=SoftwareRole)
        self._ensure_role_rows()

    @staticmethod
    def _role_order() -> tuple[SoftwareRoleEnum, ...]:
        """Return the canonical software role order."""
        return (
            SoftwareRoleEnum.FRAMEWORK,
            SoftwareRoleEnum.CALCULATOR,
            SoftwareRoleEnum.MINIMIZER,
        )

    def _ensure_role_rows(self) -> None:
        """Ensure every supported role has exactly one row."""
        rows_by_role: dict[str, SoftwareRole] = {}
        for item in self:
            role = SoftwareRoleEnum(item.id.value)
            rows_by_role[role.value] = item

        ordered_rows: list[SoftwareRole] = []
        for role in self._role_order():
            item = rows_by_role.get(role.value)
            if item is None:
                item = SoftwareRole(role)
            elif item.id.value != role.value:
                item._set_id(role.value)
            ordered_rows.append(item)
        self._adopt_items(ordered_rows)

    @staticmethod
    def _legacy_value(block: object, tag: str) -> str | None:
        """Return a legacy scalar software value from a CIF block."""
        values = list(block.find_values(tag))
        return values[0] if values else None

    def _restore_legacy_role_fields(self, block: object) -> None:
        """Read beta-window wide software fields into role rows."""
        for role in self._role_order():
            item = self[role.value]
            for attr_name in ('name', 'version', 'url'):
                value = self._legacy_value(block, f'_software.{role.value}_{attr_name}')
                descriptor = getattr(item, attr_name)
                if value not in {None, '?', '.'} and descriptor.value is None:
                    setattr(item, attr_name, value)

    def _restore_legacy_timestamp(self, block: object) -> None:
        """
        Move a legacy analysis software timestamp to project metadata.
        """
        value = self._legacy_value(block, '_software.timestamp')
        if value in {None, '?', '.'}:
            return

        analysis = getattr(self, '_parent', None)
        if analysis is None:
            return
        analysis.project.metadata.timestamp = value

    def _after_from_cif(self) -> None:
        """Normalize restored rows after loop parsing."""
        self._ensure_role_rows()

    def from_cif(self, block: object) -> None:
        """Populate software provenance from Edifa or legacy CIF."""
        super().from_cif(block)
        self._ensure_role_rows()
        self._restore_legacy_role_fields(block)
        self._restore_legacy_timestamp(block)

    def has_provenance(self) -> bool:
        """Return True when any role contains provenance data."""
        return any(
            item.name.value is not None
            or item.version.value is not None
            or item.url.value is not None
            for item in self
        )
