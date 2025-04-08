from easydiffraction.core.component import StandardComponent
from easydiffraction.core.parameter import Descriptor


class SpaceGroup(StandardComponent):
    """
    Represents the space group of a sample model.
    """
    @property
    def cif_category_key(self):
        return "_space_group"

    def __init__(self, name_h_m="P 1", it_coordinate_system_code=None):
        super().__init__()

        self.name_h_m = Descriptor(
            value=name_h_m,
            cif_param_name="name_H-M_alt"
        )
        self.it_coordinate_system_code = Descriptor(
            value=it_coordinate_system_code,
            cif_param_name="IT_coordinate_system_code"
        )

