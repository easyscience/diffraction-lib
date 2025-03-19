class Descriptor:
    """
    Base class for descriptors (non-refinable attributes).
    """

    def __init__(self, value, cif_name, units=None):
        self.value = value
        self.cif_name = cif_name
        self.units = units
        self.is_parameter = False  # Differentiates from Parameter class

    def __repr__(self):
        return f"{self.value}"

    def __str__(self):
        return str(self.value)



class Parameter(Descriptor):
    """
    A parameter with a value, uncertainty, units, and CIF representation.
    """

    def __init__(self, value, cif_name, uncertainty=0.0, vary=False, units=None):
        super().__init__(value, cif_name, units)
        self.uncertainty = uncertainty
        self.vary = vary
        self.is_parameter = True  # Flag to detect parameters

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