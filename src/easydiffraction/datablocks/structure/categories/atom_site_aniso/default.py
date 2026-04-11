# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
Anisotropic ADP category.

Defines :class:`AtomSiteAniso` items and :class:`AtomSiteAnisoCollection`
used alongside :class:`AtomSites` to hold anisotropic displacement
parameters.
"""

from __future__ import annotations

from easydiffraction.core.category import CategoryCollection
from easydiffraction.core.category import CategoryItem
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import RangeValidator
from easydiffraction.core.variable import Parameter
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.datablocks.structure.categories.atom_site_aniso.factory import (
    AtomSiteAnisoFactory,
)
from easydiffraction.io.cif.handler import CifHandler


class AtomSiteAniso(CategoryItem):
    """Single atom site anisotropic ADP entry.

    Each entry mirrors an :class:`AtomSite` by label and holds six
    tensor components whose physical meaning (B or U) is determined
    by ``atom_site.adp_type``.
    """

    def __init__(self) -> None:
        """Initialise with default zero-valued tensor components."""
        super().__init__()

        self._label = StringDescriptor(
            name='label',
            description='Atom-site label matching the parent atom_site entry.',
            value_spec=AttributeSpec(default=''),
            cif_handler=CifHandler(names=['_atom_site_aniso.label']),
        )

        self._adp_11 = Parameter(
            name='adp_11',
            description='Anisotropic ADP tensor component (1,1).',
            units='Å²',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(
                names=[
                    '_atom_site_aniso.B_11',
                    '_atom_site_aniso.U_11',
                ]
            ),
        )
        self._adp_22 = Parameter(
            name='adp_22',
            description='Anisotropic ADP tensor component (2,2).',
            units='Å²',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(
                names=[
                    '_atom_site_aniso.B_22',
                    '_atom_site_aniso.U_22',
                ]
            ),
        )
        self._adp_33 = Parameter(
            name='adp_33',
            description='Anisotropic ADP tensor component (3,3).',
            units='Å²',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(
                names=[
                    '_atom_site_aniso.B_33',
                    '_atom_site_aniso.U_33',
                ]
            ),
        )
        self._adp_12 = Parameter(
            name='adp_12',
            description='Anisotropic ADP tensor component (1,2).',
            units='Å²',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(
                names=[
                    '_atom_site_aniso.B_12',
                    '_atom_site_aniso.U_12',
                ]
            ),
        )
        self._adp_13 = Parameter(
            name='adp_13',
            description='Anisotropic ADP tensor component (1,3).',
            units='Å²',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(
                names=[
                    '_atom_site_aniso.B_13',
                    '_atom_site_aniso.U_13',
                ]
            ),
        )
        self._adp_23 = Parameter(
            name='adp_23',
            description='Anisotropic ADP tensor component (2,3).',
            units='Å²',
            value_spec=AttributeSpec(
                default=0.0,
                validator=RangeValidator(),
            ),
            cif_handler=CifHandler(
                names=[
                    '_atom_site_aniso.B_23',
                    '_atom_site_aniso.U_23',
                ]
            ),
        )

        self._identity.category_code = 'atom_site_aniso'
        self._identity.category_entry_name = lambda: str(self.label.value)

    # ------------------------------------------------------------------
    #  Public properties
    # ------------------------------------------------------------------

    @property
    def label(self) -> StringDescriptor:
        """Label matching the parent atom_site entry."""
        return self._label

    @label.setter
    def label(self, value: str) -> None:
        self._label.value = value

    @property
    def adp_11(self) -> Parameter:
        """Anisotropic ADP tensor component (1,1) in Å²."""
        return self._adp_11

    @adp_11.setter
    def adp_11(self, value: float) -> None:
        self._adp_11.value = value

    @property
    def adp_22(self) -> Parameter:
        """Anisotropic ADP tensor component (2,2) in Å²."""
        return self._adp_22

    @adp_22.setter
    def adp_22(self, value: float) -> None:
        self._adp_22.value = value

    @property
    def adp_33(self) -> Parameter:
        """Anisotropic ADP tensor component (3,3) in Å²."""
        return self._adp_33

    @adp_33.setter
    def adp_33(self, value: float) -> None:
        self._adp_33.value = value

    @property
    def adp_12(self) -> Parameter:
        """Anisotropic ADP tensor component (1,2) in Å²."""
        return self._adp_12

    @adp_12.setter
    def adp_12(self, value: float) -> None:
        self._adp_12.value = value

    @property
    def adp_13(self) -> Parameter:
        """Anisotropic ADP tensor component (1,3) in Å²."""
        return self._adp_13

    @adp_13.setter
    def adp_13(self, value: float) -> None:
        self._adp_13.value = value

    @property
    def adp_23(self) -> Parameter:
        """Anisotropic ADP tensor component (2,3) in Å²."""
        return self._adp_23

    @adp_23.setter
    def adp_23(self, value: float) -> None:
        self._adp_23.value = value


@AtomSiteAnisoFactory.register
class AtomSiteAnisoCollection(CategoryCollection):
    """Collection of :class:`AtomSiteAniso` instances."""

    type_info = TypeInfo(
        tag='default',
        description='Anisotropic ADP collection',
    )

    def __init__(self) -> None:
        """Initialise an empty aniso-ADP collection."""
        super().__init__(item_type=AtomSiteAniso)
