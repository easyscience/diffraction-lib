from easydiffraction.core.objects import (
    Descriptor,
    Component,
    Collection
)


class Constraint(Component):
    @property
    def category_key(self):
        return "constraint"

    @property
    def cif_category_key(self):
        return "constraint"

    def __init__(self,
                 id: str,
                 lhs_alias: str,
                 rhs_expr: str):
        super().__init__()

        self.id = Descriptor(
            value=id,
            name="id",
            cif_name="id"
        )
        self.lhs_alias = Descriptor(
            value=lhs_alias,
            name="lhs_alias",
            cif_name="lhs_alias"
        )
        self.rhs_expr = Descriptor(
            value=rhs_expr,
            name="rhs_expr",
            cif_name="rhs_expr"
        )

        # Select which of the input parameters is used for the
        # as ID for the whole object
        self._entry_id = id

        # Lock further attribute additions to prevent
        # accidental modifications by users
        self._locked = True


class Constraints(Collection):
    @property
    def _type(self):
        return "category"  # datablock or category

    @property
    def _child_class(self):
        return Constraint
