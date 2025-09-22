# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause


from easydiffraction.core.objects import CategoryCollection
from easydiffraction.core.objects import CategoryItem
from easydiffraction.core.objects import Descriptor
from easydiffraction.core.objects import Parameter


class LinkedPhase(CategoryItem):
    _class_public_attrs = {
        'id',
        'scale',
    }

    @property
    def category_key(self) -> str:
        return 'linked_phases'

    def __init__(
        self,
        id: str,  # TODO: need new name instead of id
        scale: float,
    ):
        super().__init__()

        self.id = Descriptor(
            value=id,
            name='id',
            value_type=str,
            full_cif_names=['_pd_phase_block.id'],
            default_value=id,
            description='Identifier of the linked phase.',
        )
        self.scale = Parameter(
            value=scale,
            name='scale',
            full_cif_names=['_pd_phase_block.scale'],
            default_value=scale,
            description='Scale factor of the linked phase.',
        )
        self._category_entry_attr_name = self.id.name


class LinkedPhases(CategoryCollection):
    """Collection of LinkedPhase instances."""

    def __init__(self):
        super().__init__(child_class=LinkedPhase)
