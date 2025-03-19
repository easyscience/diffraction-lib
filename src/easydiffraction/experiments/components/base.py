from easydiffraction.parameter import Parameter


class ComponentBase:
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
        if isinstance(attr, Parameter):
            return attr.value
        raise AttributeError(f"{name} not found")

    def as_cif(self):
        """
        Export parameters to CIF format with uncertainties and units.
        """
        if not self.cif_category_name:
            raise ValueError("cif_category_name must be defined in the derived class.")

        lines = []

        for attr_name in dir(self):
            # Skip internal attributes and methods
            if attr_name.startswith('_'):
                continue

            attr_value = getattr(self, attr_name)

            # Skip methods and non-Parameter attributes
            if not isinstance(attr_value, Parameter):
                continue

            # Format value with uncertainty (if non-zero)
            value = attr_value.value
            uncertainty = attr_value.uncertainty

            if uncertainty:
                value_str = f"{value}({uncertainty})"
            else:
                value_str = str(value)

            # Compose CIF field name
            cif_field_name = f"{self.cif_category_name}.{attr_value.cif_name or attr_name}"

            # Append units as comment (if any)
            line = f"{cif_field_name} {value_str}"
            if attr_value.units:
                line += f"  # units: {attr_value.units}"

            lines.append(line)

        return "\n".join(lines)