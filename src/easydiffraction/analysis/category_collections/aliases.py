# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from easydiffraction.core.categories import CategoryCollection
from easydiffraction.core.categories import CategoryItem
from easydiffraction.core.parameters import DescriptorStr
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import DataTypes
from easydiffraction.core.validation import RegexValidator
from easydiffraction.io.cif.handler import CifHandler


class Alias(CategoryItem):
    def __init__(
        self,
        *,
        label: str,
        param_uid: str,
    ) -> None:
        super().__init__()

        self._label: DescriptorStr = DescriptorStr(
            name='label',
            description='...',
            value_spec=AttributeSpec(
                value=label,
                type_=DataTypes.STRING,
                default='...',
                content_validator=RegexValidator(pattern=r'^[A-Za-z_][A-Za-z0-9_]*$'),
            ),
            cif_handler=CifHandler(
                names=[
                    '_alias.label',
                ]
            ),
        )
        self._param_uid: DescriptorStr = DescriptorStr(
            name='param_uid',
            description='...',
            value_spec=AttributeSpec(
                value=param_uid,
                type_=DataTypes.STRING,
                default='...',
                content_validator=RegexValidator(pattern=r'^[A-Za-z_][A-Za-z0-9_]*$'),
            ),
            cif_handler=CifHandler(
                names=[
                    '_alias.param_uid',
                ]
            ),
        )

        # self._category_entry_attr_name = self.label.name
        # self.name = self.label.value
        self._identity.category_code = 'alias'
        self._identity.category_entry_name = lambda: self.label.value

    @property
    def label(self):
        return self._label

    @label.setter
    def label(self, value):
        self._label.value = value

    @property
    def param_uid(self):
        return self._param_uid

    @param_uid.setter
    def param_uid(self, value):
        self._param_uid.value = value


class Aliases(CategoryCollection):
    def __init__(self):
        super().__init__(item_type=Alias)
