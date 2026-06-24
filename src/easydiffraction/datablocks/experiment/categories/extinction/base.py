# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Base class for extinction correction categories."""

from __future__ import annotations

from easydiffraction.core.category import CategoryItem
from easydiffraction.core.switchable import SwitchableCategoryBase
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import MembershipValidator
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.datablocks.experiment.categories.extinction.factory import ExtinctionFactory
from easydiffraction.io.cif.handler import TagSpec


class ExtinctionBase(CategoryItem, SwitchableCategoryBase):
    """Base class for extinction correction categories."""

    _category_code = 'extinction'
    _owner_attr_name = 'extinction'
    _swap_method_name = '_swap_extinction'

    def __init__(self) -> None:
        super().__init__()

        type_info = getattr(type(self), 'type_info', None)
        default_tag = type_info.tag if type_info is not None else ''
        self._type: StringDescriptor = StringDescriptor(
            name='type',
            description='Active extinction type tag',
            value_spec=AttributeSpec(
                default=default_tag,
                validator=MembershipValidator(
                    allowed=ExtinctionFactory.supported_tags(),
                ),
            ),
            tags=TagSpec(
                edi_names=['_extinction.type'], cif_names=['_easydiffraction_extinction.type']
            ),
        )

    @staticmethod
    def _supported_types(
        filters: dict[str, object],
    ) -> list[tuple[str, str]]:
        """Return extinction types supported for owner filters."""
        return [
            (klass.type_info.tag, klass.type_info.description)
            for klass in ExtinctionFactory.supported_for(
                calculator=filters.get('calculator'),
                sample_form=filters.get('sample_form'),
                scattering_type=filters.get('scattering_type'),
                beam_mode=filters.get('beam_mode'),
                radiation_probe=filters.get('radiation_probe'),
            )
        ]
