# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from abc import abstractmethod

from easydiffraction.core.category import CategoryCollection
from easydiffraction.core.switchable import SwitchableCategoryBase
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import MembershipValidator
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.datablocks.experiment.categories.background.enums import BackgroundTypeEnum
from easydiffraction.datablocks.experiment.categories.background.factory import BackgroundFactory
from easydiffraction.io.cif.handler import CifHandler


class BackgroundBase(CategoryCollection, SwitchableCategoryBase):
    """
    Abstract base for background subcategories in experiments.

    Concrete implementations provide parameterized background models and
    compute background intensities on the experiment grid.
    """

    _category_code = 'background'
    _owner_attr_name = 'background'
    _swap_method_name = '_swap_background'

    def __init__(self, item_type: type) -> None:
        super().__init__(item_type=item_type)

        type_info = getattr(type(self), 'type_info', None)
        default_tag = type_info.tag if type_info is not None else ''
        self._type: StringDescriptor = StringDescriptor(
            name='type',
            description='Active background type tag',
            value_spec=AttributeSpec(
                default=default_tag,
                validator=MembershipValidator(
                    allowed=[member.value for member in BackgroundTypeEnum],
                ),
            ),
            cif_handler=CifHandler(names=['_background.type']),
        )

    def _supported_types(
        self,
        filters: dict[str, object],
    ) -> list[tuple[str, str]]:
        """Return background types supported for owner filters."""
        return [
            (klass.type_info.tag, klass.type_info.description)
            for klass in BackgroundFactory.supported_for(
                calculator=filters.get('calculator'),
                sample_form=filters.get('sample_form'),
                scattering_type=filters.get('scattering_type'),
                beam_mode=filters.get('beam_mode'),
                radiation_probe=filters.get('radiation_probe'),
            )
        ]

    # TODO: Consider moving to CategoryCollection
    @abstractmethod
    def show(self) -> None:
        """Print a human-readable view of background components."""
