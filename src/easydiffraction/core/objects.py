import random
import string
from abc import (ABC,
                 abstractmethod)

from easydiffraction.utils.formatting import (warning,
                                              error)


class Descriptor:
    """
    Base class for descriptors (non-refinable attributes).
    """

    def __init__(self,
                 value,
                 cif_param_name,
                 pretty_name=None,
                 cif_datablock_id=None,
                 cif_category_key=None,
                 cif_entry_id=None,
                 units=None,
                 description=None,
                 editable=True):
        self._value = value
        self._description = description
        self._editable = editable
        self._pretty_name = pretty_name,
        self.cif_param_name = cif_param_name
        self.cif_category_key = cif_category_key
        self.cif_datablock_id = cif_datablock_id
        self.cif_entry_id = cif_entry_id
        self.units = units
        self.uid = self._generate_unique_id()

    def _generate_unique_id(self):
        # TODO: Instead of generating a random string, we can use the
        #  name of the parameter and the block name to create a unique id.
        #  E.g.:
        #  - "block-id__category-name__parameter-name": "lbco__cell__length_a"
        #  - "block-id__category-name__row-id__parameter-name": "lbco__atom_site__ba__fract_x"
        length = 12
        letters = random.choices(string.ascii_lowercase, k=length)
        uid = ''.join(letters)
        return uid
        # self.uid is needed to make a list of free parameters for the
        # minimization engine, and then to be able to update the sample
        # models and experiments with the new values.
        # TODO: It is used in collection.py to generate a unique id for
        #  the parameter. Check if it is needed here. When called from
        #  __init__, cif_datablock_id is not set yet?
        # TODO: Check if it works for the iterable components, such as
        #  atoms_sites, background, etc.
        # TODO: Check if we need to replace "-" with "_"
        # TODO: Check if we need make it lowercase
        raw_name = self.cif_param_name
        sanitized = (
            raw_name.replace("[", "_")
                    .replace("]", "")
                    .replace(".", "_")
                    .replace("'", "")
        )
        if self.cif_datablock_id:
            sanitized = f"{self.cif_datablock_id}_{sanitized}"
        return sanitized

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        if self._editable:
            self._value = new_value
        else:
            print(warning(f"The parameter '{self.cif_param_name}' it is calculated automatically and cannot be changed manually."))

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
                 cif_param_name,
                 pretty_name=None,
                 cif_datablock_id=None,
                 cif_category_key=None,
                 cif_entry_id=None,
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
                         cif_param_name,
                         pretty_name,
                         cif_datablock_id,
                         cif_category_key,
                         cif_entry_id,
                         units,
                         description,
                         editable)
        self.uncertainty = uncertainty
        self.free = free
        self.constrained = constrained
        self.min = min_value
        self.max = max_value


class Component(ABC):
    """
    Base class for single components, like Cell, Peak, etc.
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
        self._locked = False  # If adding new attributes is locked
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
                        param.cif_datablock_id = datablock.name
                        param.cif_category_key = standard_component.cif_category_key
                        param.cif_entry_id = ""
                        params.append(param)
                elif isinstance(component, Collection):
                    iterable_component = component
                    for standard_component in iterable_component:
                        for param in standard_component.parameters():
                            param.cif_datablock_id = datablock.name
                            param.cif_category_key = standard_component.cif_category_key
                            param.cif_entry_id = standard_component.id.value
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
                keys = [f'{category_key}.{param_key}' for param_key in params.keys()]
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
