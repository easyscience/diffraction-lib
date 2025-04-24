from easydiffraction.core.objects import (
    Descriptor,
    Parameter,
    Component,
    Collection
)


class ConstraintAlias(Component):
    def __init__(self, alias: str, param: Parameter) -> None:
        super().__init__()

        self.alias: Descriptor = Descriptor(
            value=alias,
            name="alias",
            cif_name="alias"
        )
        self.param: Parameter = param

    @property
    def cif_category_key(self) -> str:
        return "constraint_alias"

    @property
    def category_key(self) -> str:
        return "constraint_alias"

    @property
    def _entry_id(self) -> str:
        return self.alias.value


class ConstraintAliases(Collection):
    @property
    def _type(self) -> str:
        return "category"  # datablock or category

    def add(self, alias: str, param: Parameter) -> None:
        alias_obj = ConstraintAlias(alias, param)
        self._items[alias_obj.alias.value] = alias_obj
