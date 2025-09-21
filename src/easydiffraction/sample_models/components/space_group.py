# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from typing import Any

from cryspy.A_functions_base.function_2_space_group import ACCESIBLE_NAME_HM_SHORT
from cryspy.A_functions_base.function_2_space_group import (
    get_it_coordinate_system_codes_by_it_number,
)
from cryspy.A_functions_base.function_2_space_group import get_it_number_by_name_hm_short

from easydiffraction.core.objects import CategoryItem
from easydiffraction.core.objects import Descriptor


class SpaceGroup(CategoryItem):
    """Represents the space group of a sample model."""

    _allowed_attributes = {
        'name_h_m',
        'it_coordinate_system_code',
    }

    @property
    def category_key(self) -> str:
        return 'space_group'

    def __init__(
        self,
        name_h_m: Any = None,
        it_coordinate_system_code: Any = None,
    ) -> None:
        super().__init__()

        self.name_h_m = Descriptor(
            value=name_h_m,
            name='name_h_m',
            value_type=str,
            default_value='P 1',
            allowed_values=lambda: self._name_h_m_allowed_values,
            full_cif_names=[
                '_space_group.name_H-M_alt',
                '_space_group_name_H-M_alt',
                '_symmetry.space_group_name_H-M',
                '_symmetry_space_group_name_H-M',
            ],
            description='Hermann-Mauguin symbol of the space group.',
        )
        self.it_coordinate_system_code = Descriptor(
            value=it_coordinate_system_code,
            name='it_coordinate_system_code',
            value_type=str,
            full_cif_names=[
                '_space_group.IT_coordinate_system_code',
                '_space_group_IT_coordinate_system_code',
                '_symmetry.IT_coordinate_system_code',
                '_symmetry_IT_coordinate_system_code',
            ],
            default_value=lambda: self._it_coordinate_system_code_default_value,
            allowed_values=lambda: self._it_coordinate_system_code_allowed_values,
            description='A qualifier identifying which setting in IT is used.',
        )

    @property
    def _name_h_m_allowed_values(self):
        return ACCESIBLE_NAME_HM_SHORT

    @property
    def _it_coordinate_system_code_allowed_values(self):
        name = self.name_h_m.value
        it_number = get_it_number_by_name_hm_short(name)
        codes = get_it_coordinate_system_codes_by_it_number(it_number)
        codes = [str(code) for code in codes]
        if not codes:
            codes = ['']
        return codes

    @property
    def _it_coordinate_system_code_default_value(self):
        return self._it_coordinate_system_code_allowed_values[0]

    def _update_it_coordinate_system_code(self):
        try:
            code = object.__getattribute__(self, 'it_coordinate_system_code')
        except AttributeError:
            return
        if code is not None:
            code._default_value = self._it_coordinate_system_code_default_value
            code._allowed_values = self._it_coordinate_system_code_allowed_values
