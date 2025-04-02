from easydiffraction.core.component import StandardComponent
from easydiffraction.core.parameter import Parameter

class Cell(StandardComponent):
    """
    Represents the unit cell parameters of a sample model.
    """
    @property
    def cif_category_name(self):
        return "_cell"

    def __init__(self,
                 length_a=10.0,
                 length_b=10.0,
                 length_c=10.0,
                 angle_alpha=90.0,
                 angle_beta=90.0,
                 angle_gamma=90.0):
        super().__init__()

        self.length_a = Parameter(
            value=length_a,
            cif_name="length_a",
            units="Å"
        )
        self.length_b = Parameter(
            value=length_b,
            cif_name="length_b",
            units="Å"
        )
        self.length_c = Parameter(
            value=length_c,
            cif_name="length_c",
            units="Å"
        )
        self.angle_alpha = Parameter(
            value=angle_alpha,
            cif_name="angle_alpha",
            units="deg"
        )
        self.angle_beta = Parameter(
            value=angle_beta,
            cif_name="angle_beta",
            units="deg"
        )
        self.angle_gamma = Parameter(
            value=angle_gamma,
            cif_name="angle_gamma",
            units="deg"
        )
