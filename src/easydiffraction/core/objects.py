import random
import string
from abc import (
    ABC,
    abstractmethod
)

from easydiffraction.utils.formatting import (
    warning,
    error
)


class Descriptor:
    """
    Base class for descriptors (non-refinable attributes).
    """

    def __init__(self,
                 value,  # Value of the parameter
                 name,  # ED parameter name (to access it in the code)
                 cif_name,  # CIF parameter name (to show it in the CIF)
                 pretty_name=None,  # Pretty name (to show it in the table)
                 datablock_id=None, # Parent datablock name
                 category_key=None,  # ED parent category name
                 cif_category_key=None,  # CIF parent category name
                 collection_entry_id=None, # Parent collection entry id
                 units=None,  # Units of the parameter
                 description=None,  # Description of the parameter
                 editable=True  # If false, the parameter can never be edited. It is calculated automatically
                 ):

        self._value = value
        self.name = name
        self.cif_name = cif_name
        self.pretty_name = pretty_name,
        self.datablock_id = datablock_id
        self.category_key = category_key,
        self.cif_category_key = cif_category_key
        self.collection_entry_id = collection_entry_id
        self.units = units
        self._description = description
        self._editable = editable

        self.uid = self._generate_unique_id()

    def _generate_unique_id(self):
        # Derived class Parameter will use this unique id for the
        # minimization process to identify the parameter.
        # TODO: Instead of generating a random string, we can use the
        #  name of the parameter and the block name to create a unique id.
        #  E.g.:
        #  - "block-id__category-name__parameter-name": "lbco__cell__length_a"
        #  - "block-id__category-name__row-id__parameter-name": "lbco__atom_site__ba__fract_x"
        length = 12
        letters = random.choices(string.ascii_lowercase, k=length)
        uid = ''.join(letters)
        return uid

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        if self._editable:
            self._value = new_value
        else:
            print(warning(f"The parameter '{self.cif_name}' it is calculated automatically and cannot be changed manually."))

    @property
    def description(self):
        return self._description

    @property
    def editable(self):
        return self._editable

class Parameter(Descriptor):
    """
    A parameter with a value, uncertainty, units, and CIF representation.
    """

    def __init__(self,
                 value,
                 name,
                 cif_name,
                 pretty_name=None,
                 datablock_id=None,
                 category_key=None,
                 cif_category_key=None,
                 collection_entry_id=None,
                 units=None,
                 description=None,
                 editable=True,
                 uncertainty=0.0,
                 free=False,
                 constrained=False,
                 min_value=None,
                 max_value=None,
                 ):
        super().__init__(value,
                         name,
                         cif_name,
                         pretty_name,
                         datablock_id,
                         category_key,
                         cif_category_key,
                         collection_entry_id,
                         units,
                         description,
                         editable)
        self.uncertainty = uncertainty  # Standard uncertainty or estimated standard deviation
        self.free = free  # If the parameter is free to be fitted during the optimization
        self.constrained = constrained  # If symmetry constrains the parameter during the optimization
        self.min = min_value  # Minimum physical value of the parameter
        self.max = max_value  # Maximum physical value of the parameter


class Component(ABC):
    """
    Base class for single components, like Cell, Peak, etc.
    """

    @property
    @abstractmethod
    def _entry_id(self):
        pass

    @property
    @abstractmethod
    def cif_category_key(self):
        """
        Must be implemented in subclasses to return the CIF category name.
        """
        pass

    @property
    @abstractmethod
    def category_key(self):
        """
        Must be implemented in subclasses to return the ED category name.
        Can differ from cif_category_key.
        """
        pass

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._locked = False  # If adding new attributes is locked
        # TODO: Currently, it is not used. Planned to be used for displaying
        #  the parameters in the specific order.
        self._ordered_attrs = []

    def __getattr__(self, name):
        """
        If the attribute is a Parameter or Descriptor, return its value by default
        """
        attr = self.__dict__.get(name, None)
        if isinstance(attr, (Descriptor, Parameter)):
            return attr.value
        raise AttributeError(f"{name} not found in {self}")

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

    def add_attribute(self, name, value):
        """
        Add a new attribute to the object, avoiding the _locked check.
        This method is used to add attributes dynamically.
        """
        if isinstance(value, (Descriptor, Parameter)):
            self._ordered_attrs.append(name)

        super().__setattr__(name, value)
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

            key = attr_obj.cif_name
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

            key = f"_{self.cif_category_key}.{attr_obj.cif_name}"
            value = attr_obj.value

            if value is None:
                continue

            if isinstance(value, str) and " " in value:
                value = f'"{value}"'

            line = f"{key}  {value}"
            lines.append(line)

        return "\n".join(lines)

class Collection:
    """
    Base class for collections like AtomSites, LinkedPhases, SampleModels,
    Experiments, etc.
    """

    def __init__(self):
        self._items = {}

    def __getitem__(self, key):
        return self._items[key]

    def __iter__(self):
        return iter(self._items.values())

    def get_all_params(self):
        params = []
        for datablock in self._items.values():
            for component in datablock.components():
                if isinstance(component, Component):
                    standard_component = component
                    for param in standard_component.parameters():
                        param.datablock_id = datablock.name
                        param.category_key = standard_component.category_key
                        param.collection_entry_id = ""
                        params.append(param)
                elif isinstance(component, Collection):
                    iterable_component = component
                    for standard_component in iterable_component:
                        for param in standard_component.parameters():
                            param.datablock_id = datablock.name
                            param.category_key = standard_component.category_key
                            param.collection_entry_id = standard_component._entry_id
                            params.append(param)

        return params

    def get_fittable_params(self):
        all_params = self.get_all_params()
        params = []
        for param in all_params:
            if hasattr(param, 'free') and not param.constrained:
                params.append(param)
        return params

    def get_free_params(self):
        fittable_params = self.get_fittable_params()
        params = []
        for param in fittable_params:
            if param.free:
                params.append(param)
        return params

    def as_cif(self):
        lines = []
        if self._type == "category":
            for idx, item in enumerate(self._items.values()):
                params = item.as_dict()
                category_key = item.cif_category_key
                keys = [f'_{category_key}.{param_key}' for param_key in params.keys()]
                values = [f"{value}" for value in params.values()]
                if idx == 0:
                    header = "\n".join(keys)
                    lines.append(f"loop_")
                    lines.append(header)
                line = ' '.join(values)
                lines.append(line)
        return "\n".join(lines)


class Datablock(ABC):
    """
    Base class for Sample Model and Experiment data blocks.
    """
    # TODO: Consider unifying with class Component?

    def components(self):
        """
        Returns a list of both standard and iterable components in the
        data block.
        """
        attr_objs = []
        for attr_name in dir(self):
            attr_obj = getattr(self, attr_name)
            if isinstance(attr_obj, (Component,
                                     Collection)):
                attr_objs.append(attr_obj)
        return attr_objs
