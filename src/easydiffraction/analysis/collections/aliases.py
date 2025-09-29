# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause


from easydiffraction.core.categories import CategoryCollection
from easydiffraction.core.categories import CategoryItem
from easydiffraction.core.parameters import Descriptor


class Alias(CategoryItem):
    _class_public_attrs = {
        'name',
        'label',
        'param_uid',
    }

    @property
    def category_key(self) -> str:
        return 'alias'

    def __init__(self, label: str, param_uid: str) -> None:
        super().__init__()

        self.label: Descriptor = Descriptor(
            value=label,
            name='label',
            value_type=str,
            full_cif_names=['_alias.label'],
            default_value=label,
        )
        self.param_uid: Descriptor = Descriptor(
            value=param_uid,
            name='param_uid',
            value_type=str,
            full_cif_names=['_alias.param_uid'],
            default_value=param_uid,
        )
        self._category_entry_attr_name = self.label.name
        self.name = self.label.value


class Aliases(CategoryCollection[Alias]):
    def __init__(self):
        super().__init__(item_type=Alias)
