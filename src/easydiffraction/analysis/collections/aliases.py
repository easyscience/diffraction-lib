from easydiffraction.core.objects import (
    Descriptor,
    Component,
    Collection
)


class Alias(Component):
    def __init__(self, label: str, param_uid: str):
        super().__init__()

        self.label = Descriptor(
            value=label,
            name="label",
            cif_name="label"
        )
        self.param_uid = Descriptor(
            value=param_uid,
            name="param_uid",
            cif_name="param_uid"
        )

    @property
    def cif_category_key(self):
        return "alias"

    @property
    def category_key(self):
        return "alias"

    @property
    def _entry_id(self):
        return self.alias.value


class Aliases(Collection):
    @property
    def _type(self):
        return "category"  # datablock or category

    def add(self, label: str, param_uid: str):
        alias_obj = Alias(label, param_uid)
        self._items[alias_obj.label.value] = alias_obj
