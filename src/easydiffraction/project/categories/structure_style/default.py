# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
Project structure_style category (durable structure-view appearance).
"""

from __future__ import annotations

from easydiffraction.core.category import CategoryItem
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import RangeValidator
from easydiffraction.core.variable import EnumDescriptor
from easydiffraction.core.variable import NumericDescriptor
from easydiffraction.display.structure.enums import AtomViewEnum
from easydiffraction.display.structure.enums import ColorSchemeEnum
from easydiffraction.io.cif.handler import CifHandler
from easydiffraction.project.categories.structure_style.factory import StructureStyleFactory


@StructureStyleFactory.register
class StructureStyle(CategoryItem):
    """How the structure view looks (appearance, not per-element)."""

    _category_code = 'structure_style'

    type_info = TypeInfo(
        tag='default',
        description='Project structure_style category',
    )

    def __init__(self) -> None:
        super().__init__()

        self._atom_view = EnumDescriptor(
            name='atom_view',
            enum=AtomViewEnum,
            description='How atoms are sized and shaped in the structure view.',
            cif_handler=CifHandler(names=['_structure_style.atom_view']),
        )
        self._color_scheme = EnumDescriptor(
            name='color_scheme',
            enum=ColorSchemeEnum,
            description='Standard element colour scheme.',
            cif_handler=CifHandler(names=['_structure_style.color_scheme']),
        )
        self._adp_probability = NumericDescriptor(
            name='adp_probability',
            description='ORTEP probability level, a fraction in (0, 1).',
            value_spec=AttributeSpec(
                default=0.99,
                validator=RangeValidator(gt=0.0, lt=1.0),
            ),
            cif_handler=CifHandler(names=['_structure_style.adp_probability']),
        )
        self._atom_scale = NumericDescriptor(
            name='atom_scale',
            description='Overall ball-atom size factor (square-root compressed).',
            value_spec=AttributeSpec(
                default=0.3,
                validator=RangeValidator(gt=0.0, le=1.0),
            ),
            cif_handler=CifHandler(names=['_structure_style.atom_scale']),
        )

    @property
    def atom_view(self) -> EnumDescriptor:
        """How atoms are sized/shaped (vdw/covalent/ionic/adp)."""
        return self._atom_view

    @atom_view.setter
    def atom_view(self, value: str) -> None:
        self._atom_view.value = AtomViewEnum(value).value

    @property
    def color_scheme(self) -> EnumDescriptor:
        """Standard element colour scheme."""
        return self._color_scheme

    @color_scheme.setter
    def color_scheme(self, value: str) -> None:
        self._color_scheme.value = ColorSchemeEnum(value).value

    @property
    def adp_probability(self) -> NumericDescriptor:
        """ORTEP probability level (fraction in interval (0, 1))."""
        return self._adp_probability

    @adp_probability.setter
    def adp_probability(self, value: float) -> None:
        self._adp_probability.value = value

    @property
    def atom_scale(self) -> NumericDescriptor:
        """Overall ball-atom size factor in (0, 1] (sqrt compressed)."""
        return self._atom_scale

    @atom_scale.setter
    def atom_scale(self, value: float) -> None:
        self._atom_scale.value = value

    @property
    def as_cif(self) -> str:
        """Return CIF text for this structure_style category."""
        return super().as_cif
