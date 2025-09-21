# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause


from easydiffraction.core.objects import CategoryCollection
from easydiffraction.core.objects import CategoryItem
from easydiffraction.core.objects import Descriptor


class Constraint(CategoryItem):
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

        # Select which of the input parameters is used for the
        # as ID for the whole object
        self._entry_name = lhs_alias

        # Lock further attribute additions to prevent
        # accidental modifications by users
        self._locked = True


class Constraints(CategoryCollection):
    # @property
    # def _type(self) -> str:
    #    return 'category'  # datablock or category

    # @property
    # def _child_class(self) -> Type[Constraint]:
    #    return Constraint

    def __init__(self):
        super().__init__(child_class=Constraint)
