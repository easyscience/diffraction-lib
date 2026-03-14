# SPDX-FileCopyrightText: 2021-2026 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from easydiffraction.core.category import CategoryItem
from easydiffraction.core.parameters import Parameter
from easydiffraction.core.parameters import StringDescriptor
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import DataTypes
from easydiffraction.core.validation import RangeValidator
from easydiffraction.core.validation import RegexValidator
from easydiffraction.io.cif.handler import CifHandler


class LinkedCrystal(CategoryItem):
    """Linked crystal category for referencing from the experiment for
    single crystal diffraction.
    """

    def __init__(self) -> None:
        super().__init__()

        self._id = StringDescriptor(
            name='id',
            description='Identifier of the linked crystal.',
            value_spec=AttributeSpec(
                type_=DataTypes.STRING,
                default='Si',
                content_validator=RegexValidator(pattern=r'^[A-Za-z_][A-Za-z0-9_]*$'),
            ),
            cif_handler=CifHandler(
                names=[
                    '_sc_crystal_block.id',
                ]
            ),
        )
        self._scale = Parameter(
            name='scale',
            description='Scale factor of the linked crystal.',
            value_spec=AttributeSpec(
                type_=DataTypes.NUMERIC,
                default=1.0,
                content_validator=RangeValidator(),
            ),
            cif_handler=CifHandler(
                names=[
                    '_sc_crystal_block.scale',
                ]
            ),
        )

        self._identity.category_code = 'linked_crystal'

    @property
    def id(self) -> StringDescriptor:
        """Identifier of the linked crystal."""
        return self._id

    @id.setter
    def id(self, value: str):
        """Set the linked crystal identifier."""
        self._id.value = value

    @property
    def scale(self) -> Parameter:
        """Scale factor parameter."""
        return self._scale

    @scale.setter
    def scale(self, value: float):
        """Set scale factor value."""
        self._scale.value = value
