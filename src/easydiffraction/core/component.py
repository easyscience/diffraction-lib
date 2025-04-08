from abc import ABC, abstractmethod

from easydiffraction.utils.formatting import error
from easydiffraction.core.parameter import Descriptor, Parameter


class ComponentBase(ABC):
    """
    Base class for all components in the EasyDiffraction framework.
    Provides common functionality for CIF export and parameter handling.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._locked = False  # If adding new attributes is locked


class StandardComponent(ComponentBase):
    """
    Base class for experiment and sample model components of the standard type.
    Provides common functionality for CIF export and parameter handling.
    """
    @property
    @abstractmethod
    def cif_category_key(self):
        """
        Must be implemented in subclasses to return the CIF category name.
        """
        pass

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._ordered_attrs = []

    def __getattr__(self, name):
        """
        If the attribute is a Parameter or Descriptor, return its value by default
        """
        attr = self.__dict__.get(name, None)
        if isinstance(attr, (Descriptor, Parameter)):
            return attr.value
        raise AttributeError(f"{name} not found")

    def __setattr__(self, name, value):
        """
        If an object is locked for adding new attributes, raise an error.
        If the attribute 'name' does not exist, add it.
        If the attribute 'name' exists and is a Parameter or Descriptor, set its value.
        """
        if hasattr(self, "_locked") and self._locked:
            if not hasattr(self, name):
                print(error(f"Cannot add new parameter '{name}'"))
                return

        # Try to get the attribute from the instance's dictionary
        attr = self.__dict__.get(name, None)

        # If the attribute is not set, set it
        if attr is None:
            # If the attribute is a Parameter or Descriptor, add its
            # name to the list of ordered attributes
            if isinstance(value, (Descriptor, Parameter)):
                self._ordered_attrs.append(name)
            super().__setattr__(name, value)
        # If the attribute is set and is a Parameter or Descriptor,
        # update its value
        else:
            if isinstance(attr, (Descriptor, Parameter)):
                attr.value = value

    def parameters(self):
        attr_objs = []
        for attr_name in dir(self):
            attr_obj = getattr(self, attr_name)
            if isinstance(attr_obj, (Descriptor, Parameter)):
                attr_objs.append(attr_obj)
        return attr_objs

    def as_dict(self):
        d = {}

        for attr_name in dir(self):
            if attr_name.startswith('_'):
                continue

            attr_obj = getattr(self, attr_name)
            if not isinstance(attr_obj, (Descriptor, Parameter)):
                continue

            key = attr_obj.cif_param_name
            value = attr_obj.value
            d[key] = value

        return d

    def as_cif(self):
        if not self.cif_category_key:
            raise ValueError("cif_category_key must be defined in the derived class.")

        lines = []

        for attr_name in dir(self):
            if attr_name.startswith('_'):
                continue

            attr_obj = getattr(self, attr_name)
            if not isinstance(attr_obj, (Descriptor, Parameter)):
                continue

            key = f"{self.cif_category_key}.{attr_obj.cif_param_name}"
            value = attr_obj.value

            if value is None:
                continue

            if isinstance(value, str) and " " in value:
                value = f'"{value}"'

            line = f"{key}  {value}"
            lines.append(line)

        return "\n".join(lines)
