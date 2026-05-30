# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Per-structure bond-generation cutoffs (standard cif_core ``_geom``)."""

from __future__ import annotations

from easydiffraction.core.category import CategoryItem
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import RangeValidator
from easydiffraction.core.variable import NumericDescriptor
from easydiffraction.datablocks.structure.categories.geom.factory import GeomFactory
from easydiffraction.io.cif.handler import CifHandler


@GeomFactory.register
class Geom(CategoryItem):
    """Bond-generation cutoffs for a structure (cif_core ``_geom``)."""

    _category_code = 'geom'

    type_info = TypeInfo(
        tag='default',
        description='Structure bond-geometry cutoffs',
    )

    def __init__(self) -> None:
        super().__init__()

        self._min_bond_distance_cutoff = NumericDescriptor(
            name='min_bond_distance_cutoff',
            description='Minimum permitted bonded distance (angstrom).',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(ge=0.0),
            ),
            cif_handler=CifHandler(names=['_geom.min_bond_distance_cutoff']),
        )
        self._bond_distance_incr = NumericDescriptor(
            name='bond_distance_incr',
            description='Increment added to the summed bonding radii (angstrom).',
            value_spec=AttributeSpec(
                default=0.25,
                validator=RangeValidator(ge=0.0),
            ),
            cif_handler=CifHandler(names=['_geom.bond_distance_incr']),
        )

    @property
    def min_bond_distance_cutoff(self) -> NumericDescriptor:
        """Minimum permitted bonded distance (angstrom)."""
        return self._min_bond_distance_cutoff

    @min_bond_distance_cutoff.setter
    def min_bond_distance_cutoff(self, value: float) -> None:
        self._min_bond_distance_cutoff.value = value

    @property
    def bond_distance_incr(self) -> NumericDescriptor:
        """Increment added to the summed bonding radii (angstrom)."""
        return self._bond_distance_incr

    @bond_distance_incr.setter
    def bond_distance_incr(self, value: float) -> None:
        self._bond_distance_incr.value = value

    @property
    def as_cif(self) -> str:
        """Return CIF representation of this geom category."""
        return super().as_cif
