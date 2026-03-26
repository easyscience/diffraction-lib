# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Default linked-crystal reference (id + scale)."""

from __future__ import annotations

from easydiffraction.core.category import CategoryItem
from easydiffraction.core.metadata import Compatibility
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import RangeValidator
from easydiffraction.core.validation import RegexValidator
from easydiffraction.core.variable import Parameter
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.datablocks.experiment.categories.linked_crystal.factory import (
    LinkedCrystalFactory,
)
from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
from easydiffraction.io.cif.handler import CifHandler


@LinkedCrystalFactory.register
class LinkedCrystal(CategoryItem):
    """Linked crystal category for referencing from the experiment for
    single crystal diffraction.
    """

    type_info = TypeInfo(
        tag='default',
        description='Crystal reference with id and scale factor',
    )
    compatibility = Compatibility(
        sample_form=frozenset({SampleFormEnum.SINGLE_CRYSTAL}),
    )

    def __init__(self) -> None:
        super().__init__()

        self._id = StringDescriptor(
            name='id',
            description='Identifier of the linked crystal.',
            value_spec=AttributeSpec(
                default='Si',
                validator=RegexValidator(pattern=r'^[A-Za-z_][A-Za-z0-9_]*$'),
            ),
            cif_handler=CifHandler(names=['_sc_crystal_block.id']),
        )
        self._scale = Parameter(
            name='scale',
            description='Scale factor of the linked crystal.',
            value_spec=AttributeSpec(
                default=1.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_sc_crystal_block.scale']),
        )

        self._identity.category_code = 'linked_crystal'

    # ------------------------------------------------------------------
    #  Public properties
    # ------------------------------------------------------------------

    @property
    def id(self) -> StringDescriptor:
        """Identifier of the linked crystal.

        Reading this property returns the underlying
        ``StringDescriptor`` object. Assigning to it updates the
        parameter value.
        """
        return self._id

    @id.setter
    def id(self, value: str) -> None:
        self._id.value = value

    @property
    def scale(self) -> Parameter:
        """Scale factor of the linked crystal.

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._scale

    @scale.setter
    def scale(self, value: float) -> None:
        self._scale.value = value
