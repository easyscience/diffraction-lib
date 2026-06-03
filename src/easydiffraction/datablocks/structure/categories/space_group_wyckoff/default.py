# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
Derived space-group Wyckoff category.

Defines :class:`SpaceGroupWyckoff` items and the read-only
:class:`SpaceGroupWyckoffCollection`. Rows are derived from the bundled
space-group table for the structure's current space group; they are not
user-edited. ``Structure`` rebuilds the collection when the space group
changes via :meth:`SpaceGroupWyckoffCollection._replace_from_space_group`.
"""

from __future__ import annotations

from easydiffraction.core.category import CategoryCollection
from easydiffraction.core.category import CategoryItem
from easydiffraction.core.display_handler import DisplayHandler
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.variable import IntegerDescriptor
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.crystallography import crystallography as ecr
from easydiffraction.datablocks.structure.categories.space_group_wyckoff.factory import (
    SpaceGroupWyckoffFactory,
)
from easydiffraction.io.cif.handler import CifHandler

_READ_ONLY_MESSAGE = (
    'space_group_wyckoff is derived from the space group and is read-only; '
    'it is rebuilt automatically when the space group changes.'
)


class SpaceGroupWyckoff(CategoryItem):
    """A single Wyckoff position of the space group (all fields read-only)."""

    _category_code = 'space_group_Wyckoff'
    _category_entry_name = 'id'

    def __init__(self) -> None:
        """Initialise an empty Wyckoff-position row."""
        super().__init__()

        self._id = StringDescriptor(
            name='id',
            description='Identifier of the Wyckoff position.',
            display_handler=DisplayHandler(display_name='ID', latex_name='ID'),
            value_spec=AttributeSpec(default=''),
            cif_handler=CifHandler(names=['_space_group_Wyckoff.id']),
        )
        self._letter = StringDescriptor(
            name='letter',
            description='Wyckoff letter of the position.',
            display_handler=DisplayHandler(display_name='Letter', latex_name='Letter'),
            value_spec=AttributeSpec(default=''),
            cif_handler=CifHandler(names=['_space_group_Wyckoff.letter']),
        )
        self._multiplicity = IntegerDescriptor(
            name='multiplicity',
            description='Multiplicity of the Wyckoff position.',
            display_handler=DisplayHandler(display_name='Multiplicity', latex_name='Multiplicity'),
            value_spec=AttributeSpec(default=0),
            cif_handler=CifHandler(names=['_space_group_Wyckoff.multiplicity']),
        )
        self._site_symmetry = StringDescriptor(
            name='site_symmetry',
            description='Site-symmetry symbol of the Wyckoff position.',
            display_handler=DisplayHandler(display_name='Site symmetry', latex_name='Site symmetry'),
            value_spec=AttributeSpec(default=''),
            cif_handler=CifHandler(names=['_space_group_Wyckoff.site_symmetry']),
        )
        self._coords_xyz = StringDescriptor(
            name='coords_xyz',
            description='Coordinates of the Wyckoff orbit.',
            display_handler=DisplayHandler(display_name='Coordinates', latex_name='Coordinates'),
            value_spec=AttributeSpec(default=''),
            cif_handler=CifHandler(names=['_space_group_Wyckoff.coords_xyz']),
        )

    @property
    def id(self) -> StringDescriptor:
        """Read-only Wyckoff-position identifier."""
        return self._id

    @property
    def letter(self) -> StringDescriptor:
        """Read-only Wyckoff letter."""
        return self._letter

    @property
    def multiplicity(self) -> IntegerDescriptor:
        """Read-only multiplicity."""
        return self._multiplicity

    @property
    def site_symmetry(self) -> StringDescriptor:
        """Read-only site-symmetry symbol."""
        return self._site_symmetry

    @property
    def coords_xyz(self) -> StringDescriptor:
        """Read-only orbit coordinates."""
        return self._coords_xyz


@SpaceGroupWyckoffFactory.register
class SpaceGroupWyckoffCollection(CategoryCollection):
    """Read-only collection of Wyckoff positions, derived from the space group."""

    type_info = TypeInfo(
        tag='default',
        description='Derived space-group Wyckoff table',
    )

    def __init__(self) -> None:
        """Initialise an empty derived Wyckoff collection."""
        super().__init__(item_type=SpaceGroupWyckoff)

    def add(self, item: object) -> None:
        """Reject public mutation; the collection is derived (read-only)."""
        raise TypeError(_READ_ONLY_MESSAGE)

    def create(self, **kwargs: object) -> None:
        """Reject public mutation; the collection is derived (read-only)."""
        raise TypeError(_READ_ONLY_MESSAGE)

    def remove(self, name: str) -> None:
        """Reject public mutation; the collection is derived (read-only)."""
        raise TypeError(_READ_ONLY_MESSAGE)

    def from_cif(self, block: object) -> None:
        """
        Ignore incoming CIF values for this derived category.

        The Wyckoff table is derived from the structure's space group and
        is never read back from a CIF file: any ``_space_group_Wyckoff.*``
        loop in incoming CIF (for example a hand-edited project file) is
        discarded and the table is rebuilt from the space group on the
        next update.
        """
        return

    def _replace_from_space_group(self) -> None:
        """
        Rebuild the rows from the parent structure's current space group.

        Repopulates from the bundled Wyckoff table and adopts the new
        rows via ``_adopt_items``, which rebuilds the name index and
        parent links so a stale key lookup cannot survive a space-group
        change. Leaves the collection empty for an absent/untabulated
        space group.
        """
        structure = getattr(self, '_parent', None)
        if structure is None:
            self._adopt_items([])
            return
        name_hm = structure.space_group.name_h_m.value
        coord_code = structure.space_group.it_coordinate_system_code.value
        positions = ecr.space_group_wyckoff_table(name_hm, coord_code)
        if not positions:
            self._adopt_items([])
            return
        rows = []
        for letter, position in positions.items():
            multiplicity = int(position['multiplicity'])
            row = self._item_type()
            row._id.value = f'{multiplicity}{letter}'
            row._letter.value = letter
            row._multiplicity.value = multiplicity
            row._site_symmetry.value = str(position['site_symmetry'])
            row._coords_xyz.value = ' '.join(position['coords_xyz'])
            rows.append(row)
        self._adopt_items(rows)
