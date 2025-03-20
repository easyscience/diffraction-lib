class Descriptor:
    """
    Base class for descriptors (non-refinable attributes).
    """

    def __init__(self, value, cif_name, block_name=None, units=None):
        self.value = value
        self.cif_name = cif_name
        self.units = units
        self.is_parameter = False  # Differentiates from Parameter class
        self.block_name = block_name
        self.id = self._generate_unique_id()

    def _generate_unique_id(self):
        raw_name = self.cif_name
        sanitized = (
            raw_name.replace("[", "_")
                    .replace("]", "")
                    .replace(".", "_")
                    .replace("'", "")
        )
        if self.block_name:
            return f"{self.block_name}_{sanitized}"
        return sanitized

    def __repr__(self):
        return f"{self.value}"

    def __str__(self):
        return str(self.value)



class Parameter(Descriptor):
    """
    A parameter with a value, uncertainty, units, and CIF representation.
    """

    def __init__(self, value, cif_name, block_name=None, uncertainty=0.0, free=False, units=None, min_value=None, max_value=None):
        super().__init__(value, cif_name, block_name, units)
        self.uncertainty = uncertainty
        self.free = free
        self.is_parameter = True  # Flag to detect parameters
        self.min = min_value
        self.max = max_value

    def __get__(self, instance, owner):
        return self._value

    def __set__(self, instance, value):
        self._value = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        self._value = new_value

    def __repr__(self):
        return f"{self._value}"

    def __str__(self):
        return str(self._value)