# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from easydiffraction.core.category import CategoryCollection
from easydiffraction.core.category import CategoryItem
from easydiffraction.core.parameters import Parameter
from easydiffraction.core.parameters import StringDescriptor
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import DataTypes
from easydiffraction.core.validation import RangeValidator
from easydiffraction.core.validation import RegexValidator
from easydiffraction.io.cif.handler import CifHandler


class LinkedPhase(CategoryItem):
    def __init__(
        self,
        *,
        id: str,  # TODO: need new name instead of id
        scale: float,
    ):
        super().__init__()

        self._id = StringDescriptor(
            name='id',
            description='Identifier of the linked phase.',
            value_spec=AttributeSpec(
                value=id,
                type_=DataTypes.STRING,
                default='Si',
                content_validator=RegexValidator(pattern=r'^[A-Za-z_][A-Za-z0-9_]*$'),
            ),
            cif_handler=CifHandler(
                names=[
                    '_pd_phase_block.id',
                ]
            ),
        )
        self._scale = Parameter(
            name='scale',
            description='Scale factor of the linked phase.',
            value_spec=AttributeSpec(
                value=scale,
                type_=DataTypes.NUMERIC,
                default=1.0,
                content_validator=RangeValidator(),
            ),
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
    def id(self) -> StringDescriptor:
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
