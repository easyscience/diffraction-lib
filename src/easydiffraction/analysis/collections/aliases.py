from easydiffraction.core.objects import (
    Descriptor,
    Component,
    Collection
)


class Alias(Component):
    @property
    def category_key(self):
        return "alias"

    @property
    def cif_category_key(self):
        return "alias"

    def __init__(self,
                 label: str,
                 param_uid: str):
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

        # Select which of the input parameters is used for the
        # as ID for the whole object
        self._entry_id = label

        # Lock further attribute additions to prevent
        # accidental modifications by users
        self._locked = True


class Aliases(Collection):
    @property
    def _type(self):
        return "category"  # datablock or category

    @property
    def _child_class(self):
        return Alias
