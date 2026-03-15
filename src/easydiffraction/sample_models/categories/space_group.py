# SPDX-FileCopyrightText: 2021-2026 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Space group category for crystallographic sample models."""

from cryspy.A_functions_base.function_2_space_group import ACCESIBLE_NAME_HM_SHORT
from cryspy.A_functions_base.function_2_space_group import (
    get_it_coordinate_system_codes_by_it_number,
)
from cryspy.A_functions_base.function_2_space_group import get_it_number_by_name_hm_short

from easydiffraction.core.category import CategoryItem
from easydiffraction.core.parameters import StringDescriptor
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import MembershipValidator
from easydiffraction.io.cif.handler import CifHandler


class SpaceGroup(CategoryItem):
    """Space group with Hermann–Mauguin symbol and IT code."""

    def __init__(self) -> None:
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

    def _reset_it_coordinate_system_code(self):
        """Reset the IT coordinate system code."""
        self._it_coordinate_system_code.value = self._it_coordinate_system_code_default_value

    @property
    def _name_h_m_allowed_values(self):
        """Allowed values for Hermann-Mauguin symbol."""
        return ACCESIBLE_NAME_HM_SHORT

    @property
    def _it_coordinate_system_code_allowed_values(self):
        """Allowed values for IT coordinate system code."""
        name = self.name_h_m.value
        it_number = get_it_number_by_name_hm_short(name)
        codes = get_it_coordinate_system_codes_by_it_number(it_number)
        codes = [str(code) for code in codes]
        return codes if codes else ['']

    @property
    def _it_coordinate_system_code_default_value(self):
        """Default value for IT coordinate system code."""
        return self._it_coordinate_system_code_allowed_values[0]

    # ------------------------------------------------------------------
    #  Public properties
    # ------------------------------------------------------------------

    @property
    def name_h_m(self):
        return self._name_h_m

    @name_h_m.setter
    def name_h_m(self, value):
        self._name_h_m.value = value
        self._reset_it_coordinate_system_code()

    @property
    def it_coordinate_system_code(self):
        return self._it_coordinate_system_code

    @it_coordinate_system_code.setter
    def it_coordinate_system_code(self, value):
        self._it_coordinate_system_code.value = value
