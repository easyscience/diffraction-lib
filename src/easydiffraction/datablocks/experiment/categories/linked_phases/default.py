# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Linked phases allow combining phases with scale factors."""

from __future__ import annotations

from easydiffraction.core.category import CategoryCollection
from easydiffraction.core.category import CategoryItem
from easydiffraction.core.display_handler import DisplayHandler
from easydiffraction.core.metadata import Compatibility
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import RangeValidator
from easydiffraction.core.validation import RegexValidator
from easydiffraction.core.variable import Parameter
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.datablocks.experiment.categories.linked_phases.factory import (
    LinkedPhasesFactory,
)
from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
from easydiffraction.io.cif.handler import CifHandler


class LinkedPhase(CategoryItem):
    """Link to a phase by id with a scale factor."""

    _category_code = 'linked_phases'
    _category_entry_name = 'id'

    def __init__(self) -> None:
        super().__init__()

        self._id = StringDescriptor(
            name='id',
            description='Identifier of the linked phase',
            value_spec=AttributeSpec(
                default='Si',
                validator=RegexValidator(pattern=r'^[A-Za-z_][A-Za-z0-9_]*$'),
            ),
            cif_handler=CifHandler(names=['_pd_phase_block.id']),
            display_handler=DisplayHandler(
                display_name='Phase',
                latex_name='Phase',
            ),
        )
        self._scale = Parameter(
            name='scale',
            description='Scale factor of the linked phase.',
            value_spec=AttributeSpec(
                default=1.0,
                validator=RangeValidator(ge=0.0),
            ),
            cif_handler=CifHandler(names=['_pd_phase_block.scale']),
            display_handler=DisplayHandler(
                display_name='Scale',
                latex_name='Scale',
            ),
        )

    # ------------------------------------------------------------------
    #  Public properties
    # ------------------------------------------------------------------

    @property
    def id(self) -> StringDescriptor:
        """
        Identifier of the linked phase.

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
        """
        Scale factor of the linked phase.

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._scale

    @scale.setter
    def scale(self, value: float) -> None:
        self._scale.value = value


@LinkedPhasesFactory.register
class LinkedPhases(CategoryCollection):
    """Collection of LinkedPhase instances."""

    type_info = TypeInfo(
        tag='default',
        description='Phase references with scale factors',
    )
    compatibility = Compatibility(
        sample_form=frozenset({SampleFormEnum.POWDER}),
    )

    def __init__(self) -> None:
        """Create an empty collection of linked phases."""
        super().__init__(item_type=LinkedPhase)
