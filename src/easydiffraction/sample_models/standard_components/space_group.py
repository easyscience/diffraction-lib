from easydiffraction.core.parameter import Descriptor


class SpaceGroup:
    """
    Represents the space group of a sample model.
    """
    cif_category_name = "_space_group"

    def __init__(self, name="P1", number=1):
        self.name = Descriptor(name, cif_name="name_H-M_alt")
        self.number = Descriptor(number, cif_name="IT_number")

    def as_cif(self):
        key = f'{self.cif_category_name}.{self.name.cif_name}'
        value = self.name.value
        return f'{key} "{value}"'