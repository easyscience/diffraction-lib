# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from easydiffraction.core.categories import CategoryCollection
from easydiffraction.core.categories import CategoryItem
from easydiffraction.core.parameters import DescriptorStr
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import DataTypes
from easydiffraction.core.validation import RegexValidator
from easydiffraction.io.cif.handler import CifHandler


class Constraint(CategoryItem):
    def __init__(
        self,
        *,
        lhs_alias: str,
        rhs_expr: str,
    ) -> None:
        super().__init__()

        self._lhs_alias: DescriptorStr = DescriptorStr(
            name='lhs_alias',
            description='...',
            value_spec=AttributeSpec(
                value=lhs_alias,
                type_=DataTypes.STRING,
                default='...',
                content_validator=RegexValidator(pattern=r'.*'),
            ),
            cif_handler=CifHandler(
                names=[
                    '_constraint.lhs_alias',
                ]
            ),
        )
        self._rhs_expr: DescriptorStr = DescriptorStr(
            name='rhs_expr',
            description='...',
            value_spec=AttributeSpec(
                value=rhs_expr,
                type_=DataTypes.STRING,
                default='...',
                content_validator=RegexValidator(pattern=r'.*'),
            ),
            cif_handler=CifHandler(
                names=[
                    '_constraint.rhs_expr',
                ]
            ),
        )
        # self._category_entry_attr_name = self.lhs_alias.name
        # self.name = self.lhs_alias.value
        self._identity.category_code = 'constraint'
        self._identity.category_entry_name = lambda: self.lhs_alias.value

    @property
    def lhs_alias(self):
        return self._lhs_alias

    @lhs_alias.setter
    def lhs_alias(self, value):
        self._lhs_alias.value = value

    @property
    def rhs_expr(self):
        return self._rhs_expr

    @rhs_expr.setter
    def rhs_expr(self, value):
        self._rhs_expr.value = value


class Constraints(CategoryCollection):
    def __init__(self):
        super().__init__(item_type=Constraint)
