from easydiffraction.core.parameter import Parameter, Descriptor


class StandardComponentBase:
    """
    Base class for experiment and sample model components.
    Provides common functionality for CIF export and parameter handling.
    """

    cif_category_name = None  # Should be set in the derived class (e.g., "_instr_setup")

    def __setattr__(self, name, value):
        attr = self.__dict__.get(name)
        # If the attribute exists and is a Parameter instance, set its value
        if isinstance(attr, Parameter):
            attr.value = value
        else:
            # Otherwise, set the attribute normally
            super().__setattr__(name, value)

    def __getattr__(self, name):
        # If the attribute is a Parameter, return its value by default
        attr = self.__dict__.get(name)
        if isinstance(attr, (Parameter, Descriptor)):
            return attr.value
        raise AttributeError(f"{name} not found")

    def as_cif(self):
        """
        Export parameters to CIF format with uncertainties and units.
        """
        if not self.cif_category_name:
            raise ValueError("cif_category_name must be defined in the derived class.")

        lines = []

        # Iterate over all attributes of the instance
        for attr_name in dir(self):
            
            # Skip internal attributes and methods
            if attr_name.startswith('_'):
                continue

            attr_obj = getattr(self, attr_name)

            # Skip methods and non-Descriptor/non-Parameter attributes
            if not isinstance(attr_obj, (Descriptor, Parameter)):
                continue

            full_cif_name = f"{self.cif_category_name}.{attr_obj.cif_name}"
            line = f"{full_cif_name} {attr_obj.value}"

            # Append units as comment (if any)
            if hasattr(attr_obj, "units") and attr_obj.units:
                line += f"  # units: {attr_obj.units}"

            lines.append(line)

        return "\n".join(lines)
