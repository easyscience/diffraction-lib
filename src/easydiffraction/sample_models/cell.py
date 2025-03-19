from easydiffraction.parameter import Parameter

class Cell:
    """
    Represents the unit cell parameters of a sample model.
    """
    cif_category_name = "_cell"

    def __init__(self):
        self.length_a = Parameter(1.0, cif_name="length_a", units="Å")
        self.length_b = Parameter(1.0, cif_name="length_b", units="Å")
        self.length_c = Parameter(1.0, cif_name="length_c", units="Å")
        self.angle_alpha = Parameter(90.0, cif_name="angle_alpha", units="degree")
        self.angle_beta = Parameter(90.0, cif_name="angle_beta", units="degree")
        self.angle_gamma = Parameter(90.0, cif_name="angle_gamma", units="degree")

    def from_cif(self, cif_data):
        print("Parsing unit cell parameters from CIF...")

    def as_dict(self):
        return {
            "length_a": self.length_a.value,
            "length_b": self.length_b.value,
            "length_c": self.length_c.value,
            "angle_alpha": self.angle_alpha.value,
            "angle_beta": self.angle_beta.value,
            "angle_gamma": self.angle_gamma.value
        }

    def as_cif(self):
        lines = []
        for attr in [self.length_a, self.length_b, self.length_c, 
                     self.angle_alpha, self.angle_beta, self.angle_gamma]:
            lines.append(attr.as_cif())
        return "\n".join(lines)