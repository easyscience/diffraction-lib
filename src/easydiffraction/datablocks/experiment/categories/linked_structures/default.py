# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Linked structures allow combining models with scale factors."""

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
from easydiffraction.datablocks.experiment.categories.linked_structures.factory import (
    LinkedStructuresFactory,
)
from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
from easydiffraction.io.cif.handler import TagSpec


class LinkedStructure(CategoryItem):
    """Link to a structure by id with a scale factor."""

    _category_code = 'linked_structure'
    _category_entry_name = 'structure_id'

    def __init__(self) -> None:
        super().__init__()

        self._structure_id = StringDescriptor(
            name='structure_id',
            description='Identifier of the linked structure',
            value_spec=AttributeSpec(
                default='Si',
                validator=RegexValidator(pattern=r'^[A-Za-z_][A-Za-z0-9_]*$'),
            ),
            tags=TagSpec(
                edi_names=['_linked_structure.structure_id'], cif_names=['_pd_phase_block.id']
            ),
            display_handler=DisplayHandler(
                display_name='Structure',
                latex_name='Structure',
            ),
        )
        self._scale = Parameter(
            name='scale',
            description='Scale factor of the linked structure.',
            value_spec=AttributeSpec(
                default=1.0,
                validator=RangeValidator(ge=0.0),
            ),
            tags=TagSpec(
                edi_names=['_linked_structure.scale'], cif_names=['_pd_phase_block.scale']
            ),
            display_handler=DisplayHandler(
                display_name='Scale',
                latex_name='Scale',
            ),
        )

    # ------------------------------------------------------------------
    #  Public properties
    # ------------------------------------------------------------------

    @property
    def structure_id(self) -> StringDescriptor:
        """
        Identifier of the linked structure.

        Reading this property returns the underlying
        ``StringDescriptor`` object. Assigning to it updates the
        parameter value.
        """
        return self._structure_id

    @structure_id.setter
    def structure_id(self, value: str) -> None:
        self._structure_id.value = value

    @property
    def scale(self) -> Parameter:
        """
        Scale factor of the linked structure.

        Reading this property returns the underlying ``Parameter``
        object. Assigning to it updates the parameter value.
        """
        return self._scale

    @scale.setter
    def scale(self, value: float) -> None:
        self._scale.value = value


@LinkedStructuresFactory.register
class LinkedStructures(CategoryCollection):
    """Collection of LinkedStructure instances."""

    type_info = TypeInfo(
        tag='default',
        description='Structure references with scale factors',
    )
    compatibility = Compatibility(
        sample_form=frozenset({SampleFormEnum.POWDER}),
    )

    def __init__(self) -> None:
        """Create an empty collection of linked structures."""
        super().__init__(item_type=LinkedStructure)
