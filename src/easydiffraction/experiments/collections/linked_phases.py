# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause


from easydiffraction.core.categories import CategoryCollection
from easydiffraction.core.categories import CategoryItem
from easydiffraction.core.guards import RangeValidator
from easydiffraction.core.guards import RegexValidator
from easydiffraction.core.parameters import DescriptorStr
from easydiffraction.core.parameters import Parameter
from easydiffraction.crystallography.cif import CifHandler


class LinkedPhase(CategoryItem):
    def __init__(
        self,
        *,
        id: str,  # TODO: need new name instead of id
        scale: float,
    ):
        super().__init__()

        self._id = DescriptorStr(
            name='id',
            description='Identifier of the linked phase.',
            validator=RegexValidator(
                pattern=r'^[A-Za-z_][A-Za-z0-9_]*$',
                default='Si',
            ),
            value=id,
            cif_handler=CifHandler(
                names=[
                    '_pd_phase_block.id',
                ]
            ),
        )
        self._scale = Parameter(
            name='scale',
            description='Scale factor of the linked phase.',
            validator=RangeValidator(default=1.0),
            value=scale,
            cif_handler=CifHandler(
                names=[
                    '_pd_phase_block.scale',
                ]
            ),
        )
        # self._category_entry_attr_name = self.id.name
        # self.name = self.id.value
        self._identity.category_code = 'linked_phases'
        self._identity.category_entry_name = lambda: self.id.value

    @property
    def id(self) -> DescriptorStr:
        return self._id

    @id.setter
    def id(self, value: str):
        self._id.value = value

    @property
    def scale(self) -> Parameter:
        return self._scale

    @scale.setter
    def scale(self, value: float):
        self._scale.value = value


class LinkedPhases(CategoryCollection):
    """Collection of LinkedPhase instances."""

    def __init__(self):
        super().__init__(item_type=LinkedPhase)
