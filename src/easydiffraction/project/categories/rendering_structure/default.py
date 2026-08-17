# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Project rendering_structure category (switchable renderer engine)."""

from __future__ import annotations

from easydiffraction.core.category import CategoryItem
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.switchable import SwitchableCategoryBase
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import MembershipValidator
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.display.structure.enums import ViewerEngineEnum
from easydiffraction.display.structure.viewing import Viewer
from easydiffraction.display.structure.viewing import ViewerFactory
from easydiffraction.io.cif.handler import TagSpec
from easydiffraction.io.cif.parse import read_cif_str
from easydiffraction.project.categories.rendering_structure.factory import (
    RenderingStructureFactory,
)
from easydiffraction.utils.logging import log

AUTO_ENGINE = 'auto'
AUTO_DESCRIPTION = 'Environment default structure-view engine'
VIEW_ENGINE_OPTIONS = [AUTO_ENGINE, *[member.value for member in ViewerEngineEnum]]


@RenderingStructureFactory.register
class RenderingStructure(CategoryItem, SwitchableCategoryBase):
    """Renderer engine selection for the project structure view."""

    _category_code = 'rendering_structure'
    _owner_attr_name = 'rendering_structure'
    _swap_method_name = '_swap_rendering_structure'

    type_info = TypeInfo(
        tag='default',
        description='Project rendering_structure category',
    )

    def __init__(self) -> None:
        super().__init__()

        self._viewer = Viewer()
        self._type = StringDescriptor(
            name='type',
            description='Structure-view renderer backend type',
            value_spec=AttributeSpec(
                default=AUTO_ENGINE,
                validator=MembershipValidator(allowed=VIEW_ENGINE_OPTIONS),
            ),
            tags=TagSpec(edi_names=['_rendering_structure.type']),
        )

    @staticmethod
    def _resolved_engine(value: str) -> str:
        if value == AUTO_ENGINE:
            return ViewerEngineEnum.default().value
        return value

    def _set_type(self, value: str, *, strict: bool = True) -> None:
        if value not in VIEW_ENGINE_OPTIONS:
            msg = (
                f"Unsupported rendering_structure type '{value}'. "
                f'Supported: {VIEW_ENGINE_OPTIONS}. '
                f"For more information, use 'rendering_structure.show_supported()'"
            )
            if strict:
                raise ValueError(msg)
            log.warning(msg)
            return
        resolved_engine = self._resolved_engine(value)
        if self._viewer.engine != resolved_engine:
            self._viewer.engine = resolved_engine
        self._type.value = value

    @staticmethod
    def _supported_types(filters: dict[str, object]) -> list[tuple[str, str]]:
        """Return supported structure-view renderer backends."""
        del filters
        return [(AUTO_ENGINE, AUTO_DESCRIPTION), *ViewerFactory.descriptions()]

    @property
    def viewer(self) -> Viewer:
        """Live structure-view facade bound to the active engine."""
        return self._viewer

    def from_cif(self, block: object, idx: int = 0) -> None:
        """Populate this category from a CIF block, rebinding engine."""
        super().from_cif(block, idx)
        view_type = read_cif_str(block, '_rendering_structure.type')
        if view_type is not None:
            self._parent._swap_rendering_structure(view_type, strict=False)

    @property
    def as_cif(self) -> str:
        """The CIF text for this rendering_structure category."""
        return super().as_cif
