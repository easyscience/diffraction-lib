# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Base class for sample-absorption correction categories."""

from __future__ import annotations

from easydiffraction.core.category import CategoryItem
from easydiffraction.core.switchable import SwitchableCategoryBase
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import MembershipValidator
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.datablocks.experiment.categories.absorption.factory import AbsorptionFactory
from easydiffraction.datablocks.experiment.item.enums import AbsorptionTypeEnum
from easydiffraction.io.cif.handler import CifHandler


class AbsorptionBase(CategoryItem, SwitchableCategoryBase):
    """Base class for sample-absorption correction categories."""

    _category_code = 'absorption'
    _owner_attr_name = 'absorption'
    _swap_method_name = '_swap_absorption'

    def __init__(self) -> None:
        super().__init__()

        type_info = getattr(type(self), 'type_info', None)
        default_tag = type_info.tag if type_info is not None else ''
        self._type: StringDescriptor = StringDescriptor(
            name='type',
            description='Active absorption type tag',
            value_spec=AttributeSpec(
                default=default_tag,
                validator=MembershipValidator(
                    allowed=[member.value for member in AbsorptionTypeEnum],
                ),
            ),
            cif_handler=CifHandler(
                names=['_absorption.type'],
                iucr_name='_easydiffraction_absorption.type',
            ),
        )

    @staticmethod
    def _supported_types(
        filters: dict[str, object],
    ) -> list[tuple[str, str]]:
        """Return absorption types supported for owner filters."""
        return [
            (klass.type_info.tag, klass.type_info.description)
            for klass in AbsorptionFactory.supported_for(
                calculator=filters.get('calculator'),
                sample_form=filters.get('sample_form'),
                scattering_type=filters.get('scattering_type'),
                beam_mode=filters.get('beam_mode'),
                radiation_probe=filters.get('radiation_probe'),
            )
        ]
