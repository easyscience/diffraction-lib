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

    def as_cif(self):
        tags_and_values = [
            (f"{self.cif_category_name}.{self.length_a.cif_name}", self.length_a.value),
            (f"{self.cif_category_name}.{self.length_b.cif_name}", self.length_b.value),
            (f"{self.cif_category_name}.{self.length_c.cif_name}", self.length_c.value),
            (f"{self.cif_category_name}.{self.angle_alpha.cif_name}", self.angle_alpha.value),
            (f"{self.cif_category_name}.{self.angle_beta.cif_name}", self.angle_beta.value),
            (f"{self.cif_category_name}.{self.angle_gamma.cif_name}", self.angle_gamma.value)
        ]

        # Format numbers with consistent precision and alignment
        max_tag_length = max(len(tag) for tag, _ in tags_and_values)
        formatted_lines = []

        for tag, val in tags_and_values:
            # Format number with fixed width, right-aligned to decimal point
            formatted_val = f"{val:>10.4f}".rstrip('0').rstrip('.')
            formatted_lines.append(f"{tag.ljust(max_tag_length)} {formatted_val}")

        return "\n".join(formatted_lines)
