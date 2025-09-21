# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause


from easydiffraction.core.objects import CategoryCollection
from easydiffraction.core.objects import CategoryItem
from easydiffraction.core.objects import Descriptor


class Alias(CategoryItem):
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

        # Select which of the input parameters is used for the
        # as ID for the whole object
        self._entry_name = label

        # Lock further attribute additions to prevent
        # accidental modifications by users
        self._locked = True


class Aliases(CategoryCollection):
    # @property
    # def _type(self) -> str:
    #    return 'category'  # datablock or category

    # @property
    # def _child_class(self) -> Type[Alias]:
    #    return Alias

    def __init__(self):
        super().__init__(child_class=Alias)
