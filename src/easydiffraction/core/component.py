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
    def cif_category_name(self):
        """
        Must be implemented in subclasses to return the CIF category name.
        """
        pass

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
                #raise AttributeError(f"Cannot add new attribute '{name}' to locked class '{self.__class__.__name__}'")
                print(error(f"Cannot add new parameter '{name}'"))
                return

        attr = self.__dict__.get(name, None)
        if isinstance(attr, (Descriptor, Parameter)):
            attr.value = value
        else:
            super().__setattr__(name, value)

    def as_dict(self):
        d = {}

        for attr_name in dir(self):
            if attr_name.startswith('_'):
                continue

            attr_obj = getattr(self, attr_name)
            if not isinstance(attr_obj, (Descriptor, Parameter)):
                continue

            key = attr_obj.cif_name
            value = attr_obj.value
            d[key] = value

        return d

    def as_cif(self):
        if not self.cif_category_name:
            raise ValueError("cif_category_name must be defined in the derived class.")

        lines = []

        for attr_name in dir(self):
            if attr_name.startswith('_'):
                continue

            attr_obj = getattr(self, attr_name)
            if not isinstance(attr_obj, (Descriptor, Parameter)):
                continue

            key = f"{self.cif_category_name}.{attr_obj.cif_name}"
            value = attr_obj.value

            if value is None:
                continue

            if isinstance(value, str) and " " in value:
                value = f'"{value}"'

            line = f"{key}  {value}"
            lines.append(line)

        return "\n".join(lines)


class IterableComponentRow(ABC):
    # TODO: Implement this in all derived classes
    #@property
    #@abstractmethod
    #def id(self):
    #    """
    #    Must be implemented in subclasses to return the ID of the row.
    #    ID is used to access the row in the iterable component.
    #    """
    #    pass
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._ordered_attrs = []

    def __setattr__(self, key, value):
        if isinstance(value, (Descriptor, Parameter)):
            if not hasattr(self, "_ordered_attrs"):
                super().__setattr__("_ordered_attrs", [])
            self._ordered_attrs.append(key)
        super().__setattr__(key, value)


class IterableComponent(ComponentBase):
    """
    Base class for experiment and sample model components of the iterable type.
    Provides common functionality for CIF export and parameter handling.
    """
    @staticmethod
    def _get_params(row: IterableComponentRow):
        attrs = [getattr(row, name) for name in row._ordered_attrs]
        return attrs

    @property
    @abstractmethod
    def cif_category_name(self):
        """
        Must be implemented in subclasses to return the CIF category name.
        """
        pass

    def __init__(self):
        super().__init__()
        self._rows = []

    def __iter__(self):
        """
        Iterate through the rows of the iterable component.
        """
        return iter(self._rows)

    def __len__(self) -> int:
        """
        Return the number of rows in the iterable component.
        """
        return len(self._rows)

    def __getitem__(self, key: str):
        """
        Get a specific row by its ID.
        """
        for row in self._rows:
            if row.id.value == key:
                return row
        raise KeyError(f"No row item with id '{key}' found.")

    def as_cif(self) -> str:
        if not self.cif_category_name:
            raise ValueError("cif_category_name must be defined in the derived class.")

        # Start with the loop line
        lines = ["loop_"]

        # Create the header lines
        first_row = self._rows[0]
        params = IterableComponent._get_params(first_row)
        for param in params:
            lines.append(f"{self.cif_category_name}.{param.cif_name}")

        # Add the data lines
        for item in self._rows:
            line = ""
            params = IterableComponent._get_params(item)
            for param in params:
                line += f"  {param.value}"
            lines.append(line)

        return "\n".join(lines)
