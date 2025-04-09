from easydiffraction.core.objects import (
    Descriptor,
    Component,
    Collection
)


class ConstraintExpression(Component):
    def __init__(self, id: str, expression: str):
        super().__init__()

        self.id = Descriptor(
            value=id,
            name="id",
            cif_name="id"
        )
        self.expression = Descriptor(
            value=expression,
            name="expression",
            cif_name="expression"
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

    def add(self, id: str, expression: str):
        expression_obj = ConstraintExpression(id, expression)
        self._items[expression_obj.id.value] = expression_obj
