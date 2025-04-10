from easydiffraction.core.objects import (
    Descriptor,
    Component,
    Collection
)


class ConstraintExpression(Component):
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

    @property
    def cif_category_key(self):
        return "constraint_expression"

    @property
    def category_key(self):
        return "constraint_expression"

    @property
    def _entry_id(self):
        return self.id.value


class ConstraintExpressions(Collection):
    @property
    def _type(self):
        return "category"  # datablock or category

    def add(self,
            id: str,
            lhs_alias: str,
            rhs_expr: str):
        expression_obj = ConstraintExpression(id, lhs_alias, rhs_expr)
        self._items[expression_obj.id.value] = expression_obj
