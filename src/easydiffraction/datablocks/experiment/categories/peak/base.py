# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Base class for peak profile categories."""

from __future__ import annotations

from easydiffraction.core.category import CategoryItem
from easydiffraction.core.display_handler import DisplayHandler
from easydiffraction.core.switchable import SwitchableCategoryBase
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import MembershipValidator
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.datablocks.experiment.categories.peak.factory import PeakFactory
from easydiffraction.datablocks.experiment.item.enums import PeakProfileTypeEnum
from easydiffraction.io.cif.handler import CifHandler
from easydiffraction.utils.logging import console
from easydiffraction.utils.utils import render_table


class PeakBase(CategoryItem, SwitchableCategoryBase):
    """Base class for peak profile categories."""

    _category_code = 'peak'
    _owner_attr_name = 'peak'
    _swap_method_name = '_swap_peak'

    def __init__(self) -> None:
        super().__init__()

        type_info = getattr(type(self), 'type_info', None)
        default_tag = type_info.tag if type_info is not None else ''
        self._type: StringDescriptor = StringDescriptor(
            name='type',
            description='Active peak profile type tag',
            display_handler=DisplayHandler(
                display_name='Type',
                latex_name='Type',
            ),
            value_spec=AttributeSpec(
                default=default_tag,
                validator=MembershipValidator(
                    allowed=[member.value for member in PeakProfileTypeEnum],
                ),
            ),
            cif_handler=CifHandler(
                names=['_peak.type'],
                iucr_name='_easydiffraction_peak.type',
            ),
        )

    def _canonicalize(self, value: str) -> str:
        """Resolve a context-local peak alias to a canonical tag."""
        context = self._parent._peak_profile_context() if self._parent is not None else {}
        return PeakFactory._canonical_tag_for(value, **context)

    @staticmethod
    def _supported_types(
        filters: dict[str, object],
    ) -> list[tuple[str, str]]:
        """Return peak profile types supported for owner filters."""
        return [
            (klass.type_info.tag, klass.type_info.description)
            for klass in PeakFactory.supported_for(
                calculator=filters.get('calculator'),
                sample_form=filters.get('sample_form'),
                scattering_type=filters.get('scattering_type'),
                beam_mode=filters.get('beam_mode'),
                radiation_probe=filters.get('radiation_probe'),
            )
        ]

    def show_supported(self) -> None:
        """Print supported peak profiles with context-local aliases."""
        filters = self._parent._supported_filters_for(self) if self._parent is not None else {}
        context = self._parent._peak_profile_context() if self._parent is not None else {}
        rows = self._supported_types(filters)
        aliases = [PeakFactory._local_alias_for(tag, **context) for tag, _ in rows]
        columns_headers = ['', 'Type', 'Description']
        columns_alignment = ['left', 'left', 'left']
        columns_data = [
            ['*' if tag == self.type else '', alias, description]
            for alias, (tag, description) in zip(aliases, rows, strict=True)
        ]

        console.paragraph('Peak types')
        render_table(
            columns_headers=columns_headers,
            columns_alignment=columns_alignment,
            columns_data=columns_data,
        )
