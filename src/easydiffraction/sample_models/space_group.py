class SpaceGroup:
    """
    Represents the space group of a sample model.
    """
    cif_category_name = "_space_group"

    def __init__(self, name="P1", number=1):
        self.name = name
        self.number = number

    def from_cif(self, cif_data):
        """Parse space group from CIF data (stub)."""
        print("Parsing space group from CIF...")

    def as_dict(self):
        return {
            "name": self.name,
            "number": self.number
        }