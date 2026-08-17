# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Space group category for crystallographic structures."""

from __future__ import annotations

from cryspy.A_functions_base.function_2_space_group import ACCESIBLE_NAME_HM_SHORT
from cryspy.A_functions_base.function_2_space_group import (
    get_it_coordinate_system_codes_by_it_number,
)
from cryspy.A_functions_base.function_2_space_group import get_it_number_by_name_hm_short

from easydiffraction.core.category import CategoryItem
from easydiffraction.core.display_handler import DisplayHandler
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import MembershipValidator
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.datablocks.structure.categories.space_group.factory import SpaceGroupFactory
from easydiffraction.io.cif.handler import TagSpec

_CRYSTAL_SYSTEM_RANGES = (
    (1, 2, 'triclinic'),
    (3, 15, 'monoclinic'),
    (16, 74, 'orthorhombic'),
    (75, 142, 'tetragonal'),
    (143, 167, 'trigonal'),
    (168, 194, 'hexagonal'),
    (195, 230, 'cubic'),
)


@SpaceGroupFactory.register
class SpaceGroup(CategoryItem):
    """
    Space group with H-M symbol and coordinate-system code.

    Holds the space-group symbol (``name_h_m``) and the International
    Tables coordinate-system qualifier (``coord_system_code``). Changing
    the symbol automatically resets the coordinate-system code to the
    first allowed value for the new group.
    """

    _category_code = 'space_group'

    type_info = TypeInfo(
        tag='default',
        description='Space group symmetry',
    )

    def __init__(self) -> None:
        """Initialise the space group with default values."""
        super().__init__()

        self._name_h_m = StringDescriptor(
            name='name_h_m',
            description='Hermann-Mauguin symbol of the space group.',
            display_handler=DisplayHandler(
                display_name='H-M symbol',
                latex_name='H-M symbol',
            ),
            value_spec=AttributeSpec(
                default='P 1',
                validator=MembershipValidator(
                    allowed=lambda: self._name_h_m_allowed_values,
                ),
            ),
            tags=TagSpec(
                edi_names=['_space_group.name_h_m'],
                cif_names=[
                    '_space_group.name_H-M_alt',
                    '_space_group_name_H-M_alt',
                    '_symmetry.space_group_name_H-M',
                    '_symmetry_space_group_name_H-M',
                ],
            ),
        )
        self._coord_system_code = StringDescriptor(
            name='coord_system_code',
            description='A qualifier identifying which setting in IT is used.',
            display_handler=DisplayHandler(
                display_name='IT code',
                latex_name='IT code',
            ),
            value_spec=AttributeSpec(
                default=lambda: self._coord_system_code_default_value,
                validator=MembershipValidator(
                    allowed=lambda: self._coord_system_code_allowed_values
                ),
            ),
            tags=TagSpec(
                edi_names=['_space_group.coord_system_code'],
                cif_names=[
                    '_space_group.IT_coordinate_system_code',
                    '_space_group_IT_coordinate_system_code',
                    '_symmetry.IT_coordinate_system_code',
                    '_symmetry_IT_coordinate_system_code',
                ],
            ),
        )

    # ------------------------------------------------------------------
    #  Private helper methods
    # ------------------------------------------------------------------

    def _reset_coord_system_code(self) -> None:
        """Reset IT coordinate system code to default for this group."""
        self._coord_system_code.value = self._coord_system_code_default_value

    @property
    def _name_h_m_allowed_values(self) -> list[str]:
        """
        The list of recognised Hermann-Mauguin short symbols.

        Returns
        -------
        list[str]
            All short H-M symbols known to *cryspy*.
        """
        return ACCESIBLE_NAME_HM_SHORT

    @property
    def _coord_system_code_allowed_values(self) -> list[str]:
        """
        Allowed IT coordinate system codes for the current group.

        Returns
        -------
        list[str]
            Coordinate-system codes, or ``['']`` when none are defined.
        """
        name = self.name_h_m.value
        it_number = get_it_number_by_name_hm_short(name)
        codes = get_it_coordinate_system_codes_by_it_number(it_number)
        codes = [str(code) for code in codes]
        return codes or ['']

    @property
    def _coord_system_code_default_value(self) -> str:
        """
        The default IT coordinate system code.

        Returns
        -------
        str
            First element of the allowed codes list.
        """
        return self._coord_system_code_allowed_values[0]

    # ------------------------------------------------------------------
    #  Public properties
    # ------------------------------------------------------------------

    @property
    def name_h_m(self) -> StringDescriptor:
        """
        Hermann-Mauguin symbol of the space group.

        Reading this property returns the underlying
        ``StringDescriptor`` object. Assigning to it updates the
        parameter value.
        """
        return self._name_h_m

    @name_h_m.setter
    def name_h_m(self, value: str) -> None:
        self._name_h_m.value = value
        self._reset_coord_system_code()

    @property
    def coord_system_code(self) -> StringDescriptor:
        """
        A qualifier identifying which setting in IT is used.

        Reading this property returns the underlying
        ``StringDescriptor`` object. Assigning to it updates the
        parameter value.
        """
        return self._coord_system_code

    @coord_system_code.setter
    def coord_system_code(self, value: str) -> None:
        self._coord_system_code.value = value

    @property
    def crystal_system(self) -> str:
        """Crystal system derived from the H-M symbol."""
        it_number = get_it_number_by_name_hm_short(self.name_h_m.value)
        return _crystal_system_from_it_number(it_number)


def _crystal_system_from_it_number(it_number: int) -> str:
    """Return the crystal system for an International Tables number."""
    for start, stop, crystal_system in _CRYSTAL_SYSTEM_RANGES:
        if start <= it_number <= stop:
            return crystal_system
    msg = f'Unknown International Tables number: {it_number}'
    raise ValueError(msg)
