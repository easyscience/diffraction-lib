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
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import MembershipValidator
from easydiffraction.core.variable import StringDescriptor
from easydiffraction.datablocks.structure.categories.space_group.factory import SpaceGroupFactory
from easydiffraction.io.cif.handler import CifHandler


@SpaceGroupFactory.register
class SpaceGroup(CategoryItem):
    """
    Space group with H-M symbol and IT coordinate system code.

    Holds the space-group symbol (``name_h_m``) and the International
    Tables coordinate-system qualifier (``it_coordinate_system_code``).
    Changing the symbol automatically resets the coordinate-system code
    to the first allowed value for the new group.
    """

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
            value_spec=AttributeSpec(
                default='P 1',
                validator=MembershipValidator(
                    allowed=lambda: self._name_h_m_allowed_values,
                ),
            ),
            cif_handler=CifHandler(
                # TODO: Keep only version with "." and automate ...
                names=[
                    '_space_group.name_H-M_alt',
                    '_space_group_name_H-M_alt',
                    '_symmetry.space_group_name_H-M',
                    '_symmetry_space_group_name_H-M',
                ]
            ),
        )
        self._it_coordinate_system_code = StringDescriptor(
            name='it_coordinate_system_code',
            description='A qualifier identifying which setting in IT is used.',
            value_spec=AttributeSpec(
                default=lambda: self._it_coordinate_system_code_default_value,
                validator=MembershipValidator(
                    allowed=lambda: self._it_coordinate_system_code_allowed_values
                ),
            ),
            cif_handler=CifHandler(
                names=[
                    '_space_group.IT_coordinate_system_code',
                    '_space_group_IT_coordinate_system_code',
                    '_symmetry.IT_coordinate_system_code',
                    '_symmetry_IT_coordinate_system_code',
                ]
            ),
        )

        self._identity.category_code = 'space_group'

    # ------------------------------------------------------------------
    #  Private helper methods
    # ------------------------------------------------------------------

    def _reset_it_coordinate_system_code(self) -> None:
        """Reset IT coordinate system code to default for this group."""
        self._it_coordinate_system_code.value = self._it_coordinate_system_code_default_value

    @property
    def _name_h_m_allowed_values(self) -> list[str]:
        """
        Return the list of recognised Hermann–Mauguin short symbols.

        Returns
        -------
        list[str]
            All short H-M symbols known to *cryspy*.
        """
        return ACCESIBLE_NAME_HM_SHORT

    @property
    def _it_coordinate_system_code_allowed_values(self) -> list[str]:
        """
        Return allowed IT coordinate system codes for the current group.

        Returns
        -------
        list[str]
            Coordinate-system codes, or ``['']`` when none are defined.
        """
        name = self.name_h_m.value
        it_number = get_it_number_by_name_hm_short(name)
        codes = get_it_coordinate_system_codes_by_it_number(it_number)
        codes = [str(code) for code in codes]
        return codes if codes else ['']

    @property
    def _it_coordinate_system_code_default_value(self) -> str:
        """
        Return the default IT coordinate system code.

        Returns
        -------
        str
            First element of the allowed codes list.
        """
        return self._it_coordinate_system_code_allowed_values[0]

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
        self._reset_it_coordinate_system_code()

    @property
    def it_coordinate_system_code(self) -> StringDescriptor:
        """
        A qualifier identifying which setting in IT is used.

        Reading this property returns the underlying
        ``StringDescriptor`` object. Assigning to it updates the
        parameter value.
        """
        return self._it_coordinate_system_code

    @it_coordinate_system_code.setter
    def it_coordinate_system_code(self, value: str) -> None:
        self._it_coordinate_system_code.value = value
