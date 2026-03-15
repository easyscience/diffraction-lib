# SPDX-FileCopyrightText: 2021-2026 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Linked phases allow combining phases with scale factors."""

from easydiffraction.core.category import CategoryCollection
from easydiffraction.core.category import CategoryItem
from easydiffraction.core.parameters import Parameter
from easydiffraction.core.parameters import StringDescriptor
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import RangeValidator
from easydiffraction.core.validation import RegexValidator
from easydiffraction.io.cif.handler import CifHandler


class LinkedPhase(CategoryItem):
    """Link to a phase by id with a scale factor."""

    def __init__(self):
        super().__init__()

        self._id = StringDescriptor(
            name='id',
            description='Identifier of the linked phase.',
            value_spec=AttributeSpec(
                default='Si',
                validator=RegexValidator(pattern=r'^[A-Za-z_][A-Za-z0-9_]*$'),
            ),
            cif_handler=CifHandler(names=['_pd_phase_block.id']),
        )
        self._scale = Parameter(
            name='scale',
            description='Scale factor of the linked phase.',
            value_spec=AttributeSpec(
                default=1.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(names=['_pd_phase_block.scale']),
        )

        self._identity.category_code = 'linked_phases'
        self._identity.category_entry_name = lambda: str(self.id.value)

    # ------------------------------------------------------------------
    #  Public properties
    # ------------------------------------------------------------------

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
        """Create an empty collection of linked phases."""
        super().__init__(item_type=LinkedPhase)
