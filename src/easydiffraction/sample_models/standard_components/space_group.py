from easydiffraction.core.component import StandardComponent
from easydiffraction.core.parameter import Descriptor


class SpaceGroup(StandardComponent):
    """
    Represents the space group of a sample model.
    """
    @property
    def cif_category_name(self):
        return "_space_group"

    def __init__(self, name="P1"):
        super().__init__()

        self.name = Descriptor(
            value=name,
            cif_name="name_H-M_alt"
        )

