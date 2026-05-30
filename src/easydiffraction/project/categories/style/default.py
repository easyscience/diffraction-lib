# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Project structure-view styling category."""

from __future__ import annotations

from easydiffraction.core.category import CategoryItem
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import MembershipValidator
from easydiffraction.core.validation import RangeValidator
from easydiffraction.core.variable import NumericDescriptor
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.display.structure.enums import AtomShapeEnum
from easydiffraction.display.structure.enums import ColorSchemeEnum
from easydiffraction.display.structure.enums import RadiusModelEnum
from easydiffraction.io.cif.handler import CifHandler
from easydiffraction.project.categories.style.factory import StyleFactory
from easydiffraction.utils.logging import console


@StyleFactory.register
class Style(CategoryItem):
    """Visual styling for the structure view (not per-element)."""

    _category_code = 'style'

    type_info = TypeInfo(
        tag='default',
        description='Project structure-view style category',
    )

    def __init__(self) -> None:
        super().__init__()

        self._atom_shape = StringDescriptor(
            name='atom_shape',
            description='Atom depiction mode for the structure view.',
            value_spec=AttributeSpec(
                default=AtomShapeEnum.default().value,
                validator=MembershipValidator(
                    allowed=[member.value for member in AtomShapeEnum],
                ),
            ),
            cif_handler=CifHandler(names=['_style.atom_shape']),
        )
        self._radius_model = StringDescriptor(
            name='radius_model',
            description='Standard per-element radius model.',
            value_spec=AttributeSpec(
                default=RadiusModelEnum.default().value,
                validator=MembershipValidator(
                    allowed=[member.value for member in RadiusModelEnum],
                ),
            ),
            cif_handler=CifHandler(names=['_style.radius_model']),
        )
        self._color_scheme = StringDescriptor(
            name='color_scheme',
            description='Standard element colour scheme.',
            value_spec=AttributeSpec(
                default=ColorSchemeEnum.default().value,
                validator=MembershipValidator(
                    allowed=[member.value for member in ColorSchemeEnum],
                ),
            ),
            cif_handler=CifHandler(names=['_style.color_scheme']),
        )
        self._adp_probability = NumericDescriptor(
            name='adp_probability',
            description='ORTEP probability level, a fraction in (0, 1).',
            value_spec=AttributeSpec(
                default=0.5,
                validator=RangeValidator(gt=0.0, lt=1.0),
            ),
            cif_handler=CifHandler(names=['_style.adp_probability']),
        )
        self._atom_scale = NumericDescriptor(
            name='atom_scale',
            description='Ball-atom radius as a fraction of the model radius.',
            value_spec=AttributeSpec(
                default=0.5,
                validator=RangeValidator(gt=0.0, le=1.0),
            ),
            cif_handler=CifHandler(names=['_style.atom_scale']),
        )

    @property
    def atom_shape(self) -> StringDescriptor:
        """Atom depiction mode (``ball`` or ``ortep``)."""
        return self._atom_shape

    @atom_shape.setter
    def atom_shape(self, value: str) -> None:
        self._atom_shape.value = AtomShapeEnum(value).value

    @property
    def radius_model(self) -> StringDescriptor:
        """Standard per-element radius model."""
        return self._radius_model

    @radius_model.setter
    def radius_model(self, value: str) -> None:
        self._radius_model.value = RadiusModelEnum(value).value

    @property
    def color_scheme(self) -> StringDescriptor:
        """Standard element colour scheme."""
        return self._color_scheme

    @color_scheme.setter
    def color_scheme(self, value: str) -> None:
        self._color_scheme.value = ColorSchemeEnum(value).value

    @property
    def adp_probability(self) -> NumericDescriptor:
        """ORTEP probability level (fraction in the open interval (0, 1))."""
        return self._adp_probability

    @adp_probability.setter
    def adp_probability(self, value: float) -> None:
        self._adp_probability.value = value

    @property
    def atom_scale(self) -> NumericDescriptor:
        """Ball-atom radius as a fraction of the model radius (0, 1]."""
        return self._atom_scale

    @atom_scale.setter
    def atom_scale(self, value: float) -> None:
        self._atom_scale.value = value

    def show_supported(self) -> None:
        """List the accepted values for every styling setting."""
        console.paragraph('Supported style settings')
        for setting, enum in (
            ('atom_shape', AtomShapeEnum),
            ('radius_model', RadiusModelEnum),
            ('color_scheme', ColorSchemeEnum),
        ):
            console.print(f"{setting}: {', '.join(member.value for member in enum)}")
        console.print('adp_probability: float in the open interval (0, 1)')
        console.print('atom_scale: float in (0, 1] (1 = space-filling model radius)')

    @property
    def as_cif(self) -> str:
        """Return CIF representation of this style category."""
        return super().as_cif
