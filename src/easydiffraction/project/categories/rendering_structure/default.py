# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Project structure-rendering_structure category (switchable renderer + view state)."""

from __future__ import annotations

from easydiffraction.core.category import CategoryItem
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.switchable import SwitchableCategoryBase
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import MembershipValidator
from easydiffraction.core.variable import BoolDescriptor
from easydiffraction.core.variable import NumericDescriptor
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.display.structure.enums import ViewerEngineEnum
from easydiffraction.display.structure.viewing import Viewer
from easydiffraction.display.structure.viewing import ViewerFactory
from easydiffraction.io.cif.handler import CifHandler
from easydiffraction.io.cif.parse import read_cif_str
from easydiffraction.project.categories.rendering_structure.factory import RenderingStructureFactory
from easydiffraction.utils.logging import log

AUTO_ENGINE = 'auto'
AUTO_DESCRIPTION = 'Environment default structure-view engine'
VIEW_ENGINE_OPTIONS = [AUTO_ENGINE, *[member.value for member in ViewerEngineEnum]]


def _range_descriptor(name: str, default: float) -> NumericDescriptor:
    return NumericDescriptor(
        name=name,
        description='Per-axis fractional view-range bound.',
        value_spec=AttributeSpec(default=default),
        cif_handler=CifHandler(names=[f'_rendering_structure.{name}']),
    )


@RenderingStructureFactory.register
class RenderingStructure(CategoryItem, SwitchableCategoryBase):
    """Renderer engine selection and view state for a project."""

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
            cif_handler=CifHandler(names=['_rendering_structure.type']),
        )
        self._show_labels = BoolDescriptor(
            name='show_labels',
            description='Show atom labels when the view opens.',
            value_spec=AttributeSpec(default=False),
            cif_handler=CifHandler(names=['_rendering_structure.show_labels']),
        )
        self._show_moments = BoolDescriptor(
            name='show_moments',
            description='Show magnetic-moment arrows where the data exists.',
            value_spec=AttributeSpec(default=True),
            cif_handler=CifHandler(names=['_rendering_structure.show_moments']),
        )
        self._range_a_min = _range_descriptor('range_a_min', 0.0)
        self._range_a_max = _range_descriptor('range_a_max', 1.0)
        self._range_b_min = _range_descriptor('range_b_min', 0.0)
        self._range_b_max = _range_descriptor('range_b_max', 1.0)
        self._range_c_min = _range_descriptor('range_c_min', 0.0)
        self._range_c_max = _range_descriptor('range_c_max', 1.0)

    @staticmethod
    def _resolved_engine(value: str) -> str:
        if value == AUTO_ENGINE:
            return ViewerEngineEnum.default().value
        return value

    def _set_type(self, value: str, *, strict: bool = True) -> None:
        if value not in VIEW_ENGINE_OPTIONS:
            msg = (
                f"Unsupported rendering_structure type '{value}'. Supported: {VIEW_ENGINE_OPTIONS}. "
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

    @property
    def show_labels(self) -> BoolDescriptor:
        """Whether atom labels are shown when the view opens."""
        return self._show_labels

    @show_labels.setter
    def show_labels(self, value: bool) -> None:
        self._show_labels.value = value

    @property
    def show_moments(self) -> BoolDescriptor:
        """Whether moment arrows are shown where the data exists."""
        return self._show_moments

    @show_moments.setter
    def show_moments(self, value: bool) -> None:
        self._show_moments.value = value

    def _set_bound(self, descriptor: NumericDescriptor, value: float, *, lower: float, upper: float) -> None:
        if not lower < value < upper:
            log.warning(
                f"'{descriptor.name}' = {value} violates min < max on its axis; ignored.",
            )
            return
        descriptor.value = value

    @property
    def range_a_min(self) -> NumericDescriptor:
        """Lower fractional bound along a."""
        return self._range_a_min

    @range_a_min.setter
    def range_a_min(self, value: float) -> None:
        self._set_bound(self._range_a_min, value, lower=float('-inf'), upper=self._range_a_max.value)

    @property
    def range_a_max(self) -> NumericDescriptor:
        """Upper fractional bound along a."""
        return self._range_a_max

    @range_a_max.setter
    def range_a_max(self, value: float) -> None:
        self._set_bound(self._range_a_max, value, lower=self._range_a_min.value, upper=float('inf'))

    @property
    def range_b_min(self) -> NumericDescriptor:
        """Lower fractional bound along b."""
        return self._range_b_min

    @range_b_min.setter
    def range_b_min(self, value: float) -> None:
        self._set_bound(self._range_b_min, value, lower=float('-inf'), upper=self._range_b_max.value)

    @property
    def range_b_max(self) -> NumericDescriptor:
        """Upper fractional bound along b."""
        return self._range_b_max

    @range_b_max.setter
    def range_b_max(self, value: float) -> None:
        self._set_bound(self._range_b_max, value, lower=self._range_b_min.value, upper=float('inf'))

    @property
    def range_c_min(self) -> NumericDescriptor:
        """Lower fractional bound along c."""
        return self._range_c_min

    @range_c_min.setter
    def range_c_min(self, value: float) -> None:
        self._set_bound(self._range_c_min, value, lower=float('-inf'), upper=self._range_c_max.value)

    @property
    def range_c_max(self) -> NumericDescriptor:
        """Upper fractional bound along c."""
        return self._range_c_max

    @range_c_max.setter
    def range_c_max(self, value: float) -> None:
        self._set_bound(self._range_c_max, value, lower=self._range_c_min.value, upper=float('inf'))

    def view_range(self) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float]]:
        """Assemble the per-axis ``((min, max), ...)`` fractional window."""
        return (
            (self._range_a_min.value, self._range_a_max.value),
            (self._range_b_min.value, self._range_b_max.value),
            (self._range_c_min.value, self._range_c_max.value),
        )

    def from_cif(self, block: object, idx: int = 0) -> None:
        """Populate this rendering_structure category from a CIF block, rebinding engine."""
        super().from_cif(block, idx)
        view_type = read_cif_str(block, '_rendering_structure.type')
        if view_type is not None:
            self._parent._swap_rendering_structure(view_type, strict=False)

    @property
    def as_cif(self) -> str:
        """Return CIF representation of this rendering_structure category."""
        return super().as_cif
