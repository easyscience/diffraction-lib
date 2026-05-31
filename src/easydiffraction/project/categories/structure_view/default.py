# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
Project structure_view category (durable content + region view state).
"""

from __future__ import annotations

from easydiffraction.core.category import CategoryItem
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.variable import BoolDescriptor
from easydiffraction.core.variable import NumericDescriptor
from easydiffraction.io.cif.handler import CifHandler
from easydiffraction.project.categories.structure_view.factory import StructureViewFactory
from easydiffraction.utils.logging import log


def _range_descriptor(name: str, default: float) -> NumericDescriptor:
    return NumericDescriptor(
        name=name,
        description='Per-axis fractional view-range bound.',
        value_spec=AttributeSpec(default=default),
        cif_handler=CifHandler(names=[f'_structure_view.{name}']),
    )


@StructureViewFactory.register
class StructureView(CategoryItem):
    """What and where to draw in the structure view (engine-neutral)."""

    _category_code = 'structure_view'

    type_info = TypeInfo(
        tag='default',
        description='Project structure_view category',
    )

    def __init__(self) -> None:
        super().__init__()

        self._show_labels = BoolDescriptor(
            name='show_labels',
            description='Show atom labels when the view opens.',
            value_spec=AttributeSpec(default=False),
            cif_handler=CifHandler(names=['_structure_view.show_labels']),
        )
        self._show_moments = BoolDescriptor(
            name='show_moments',
            description='Show magnetic-moment arrows where the data exists.',
            value_spec=AttributeSpec(default=True),
            cif_handler=CifHandler(names=['_structure_view.show_moments']),
        )
        self._range_a_min = _range_descriptor('range_a_min', 0.0)
        self._range_a_max = _range_descriptor('range_a_max', 1.0)
        self._range_b_min = _range_descriptor('range_b_min', 0.0)
        self._range_b_max = _range_descriptor('range_b_max', 1.0)
        self._range_c_min = _range_descriptor('range_c_min', 0.0)
        self._range_c_max = _range_descriptor('range_c_max', 1.0)

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
        """
        Assemble the per-axis ``((min, max), ...)`` fractional window.
        """
        return (
            (self._range_a_min.value, self._range_a_max.value),
            (self._range_b_min.value, self._range_b_max.value),
            (self._range_c_min.value, self._range_c_max.value),
        )

    @property
    def as_cif(self) -> str:
        """Return CIF representation of this structure_view category."""
        return super().as_cif
