# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause


from easydiffraction.core.categories import CategoryCollection
from easydiffraction.core.categories import CategoryItem
from easydiffraction.core.parameters import Descriptor


class Constraint(CategoryItem):
    _class_public_attrs = {
        'name',
        'lhs_alias',
        'rhs_expr',
    }

    @property
    def category_key(self) -> str:
        return 'constraint'

    def __init__(self, lhs_alias: str, rhs_expr: str) -> None:
        super().__init__()

        self.lhs_alias: Descriptor = Descriptor(
            value=lhs_alias,
            name='lhs_alias',
            value_type=str,
            full_cif_names=['_constraint.lhs_alias'],
            default_value=lhs_alias,
        )
        self.rhs_expr: Descriptor = Descriptor(
            value=rhs_expr,
            name='rhs_expr',
            value_type=str,
            full_cif_names=['_constraint.rhs_expr'],
            default_value=rhs_expr,
        )
        self._category_entry_attr_name = self.lhs_alias.name
        self.name = self.lhs_alias.value


class Constraints(CategoryCollection[Constraint]):
    def __init__(self):
        super().__init__(item_type=Constraint)
