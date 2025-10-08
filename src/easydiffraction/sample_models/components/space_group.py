# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause


from easydiffraction.core.categories import CategoryItem
from easydiffraction.core.guards import ListValidator
from easydiffraction.core.parameters import DescriptorStr
from easydiffraction.crystallography.cif import CifHandler


class SpaceGroup(CategoryItem):
    def __init__(
        self,
        *,
        name_h_m: str = None,
        it_coordinate_system_code: str = None,
    ) -> None:
        super().__init__()
        self._name_h_m: DescriptorStr = DescriptorStr(
            name='name_h_m',
            description='Hermann-Mauguin symbol of the space group.',
            validator=ListValidator(
                allowed_values=['P 1', 'P n m a', 'P m -3 m'],
                default='P 1',
            ),
            value=name_h_m,
            cif_handler=CifHandler(
                names=[
                    '_space_group.name_H-M_alt',
                    '_space_group_name_H-M_alt',
                    '_symmetry.space_group_name_H-M',
                    '_symmetry_space_group_name_H-M',
                ]
            ),
        )
        self._it_coordinate_system_code: DescriptorStr = DescriptorStr(
            name='it_coordinate_system_code',
            description='A qualifier identifying which setting in IT is used.',
            validator=ListValidator(
                allowed_values=['1', '2', 'abc', 'cab'],
                default='',
            ),
            value=it_coordinate_system_code,
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

    @property
    def name_h_m(self):
        return self._name_h_m

    @name_h_m.setter
    def name_h_m(self, value):
        self._name_h_m.value = value

    @property
    def it_coordinate_system_code(self):
        return self._it_coordinate_system_code

    @it_coordinate_system_code.setter
    def it_coordinate_system_code(self, value):
        self._it_coordinate_system_code.value = value
