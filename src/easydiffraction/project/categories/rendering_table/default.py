# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Project rendering_table category."""

from __future__ import annotations

from easydiffraction.core.category import CategoryItem
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.switchable import SwitchableCategoryBase
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import MembershipValidator
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.display.tables import TableEngineEnum
from easydiffraction.display.tables import TableRenderer
from easydiffraction.display.tables import TableRendererFactory
from easydiffraction.io.cif.handler import CifHandler
from easydiffraction.io.cif.parse import read_cif_str
from easydiffraction.project.categories.rendering_table.factory import RenderingTableFactory
from easydiffraction.utils.logging import log

AUTO_ENGINE = 'auto'
AUTO_DESCRIPTION = 'Environment default table engine'
TABLE_ENGINE_OPTIONS = [AUTO_ENGINE, *[member.value for member in TableEngineEnum]]


@RenderingTableFactory.register
class RenderingTable(CategoryItem, SwitchableCategoryBase):
    """Table engine selection for a project."""

    _category_code = 'rendering_table'
    _owner_attr_name = 'rendering_table'
    _swap_method_name = '_swap_rendering_table'

    type_info = TypeInfo(
        tag='default',
        description='Project rendering_table category',
    )

    def __init__(self) -> None:
        super().__init__()

        self._tabler = TableRenderer.get()
        self._type = StringDescriptor(
            name='type',
            description='Table renderer backend type',
            value_spec=AttributeSpec(
                default=AUTO_ENGINE,
                validator=MembershipValidator(
                    allowed=TABLE_ENGINE_OPTIONS,
                ),
            ),
            cif_handler=CifHandler(names=['_rendering_table.type']),
        )

    @staticmethod
    def _resolved_engine(value: str) -> str:
        if value == AUTO_ENGINE:
            return TableEngineEnum.default().value
        return value

    def _set_type(self, value: str, *, strict: bool = True) -> None:
        if value not in TABLE_ENGINE_OPTIONS:
            msg = (
                f"Unsupported rendering_table type '{value}'. "
                f'Supported: {TABLE_ENGINE_OPTIONS}. '
                f"For more information, use 'rendering_table.show_supported()'"
            )
            if strict:
                raise ValueError(msg)
            log.warning(msg)
            return

        resolved_engine = self._resolved_engine(value)
        if self._tabler.engine != resolved_engine:
            self._tabler.engine = resolved_engine
        self._type.value = value

    @property
    def tabler(self) -> TableRenderer:
        """Live table-rendering facade."""
        return self._tabler

    @staticmethod
    def _supported_types(
        filters: dict[str, object],
    ) -> list[tuple[str, str]]:
        """Return supported table renderer backends."""
        del filters
        return [(AUTO_ENGINE, AUTO_DESCRIPTION), *TableRendererFactory.descriptions()]

    def from_cif(self, block: object, idx: int = 0) -> None:
        """Populate this rendering_table category from a CIF block."""
        del idx
        table_type = read_cif_str(block, '_rendering_table.type')
        if table_type is None:
            return
        self._parent._swap_rendering_table(table_type, strict=False)
