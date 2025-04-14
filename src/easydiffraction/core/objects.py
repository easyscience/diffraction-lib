import random
import string
from abc import (
    ABC,
    abstractmethod
)

from easydiffraction.core.singletons import UidMapHandler
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
        self.pretty_name = pretty_name
        self._datablock_id = datablock_id
        self.category_key = category_key
        self.cif_category_key = cif_category_key
        self._collection_entry_id = collection_entry_id
        self.units = units
        self._description = description
        self._editable = editable

        self._human_uid = self._generate_human_readable_unique_id()

        UidMapHandler.get().add_to_uid_map(self)

    def __str__(self):
        return f"{self.__class__.__name__}: {self.uid} = {self.value} {self.units or ''}".strip()

    def _generate_random_unique_id(self):
        # Derived class Parameter will use this unique id for the
        # minimization process to identify the parameter. It will also be
        # used to create the alias for the parameter in the constraint
        # expression.
        length = 16
        letters = random.choices(string.ascii_lowercase, k=length)
        uid = ''.join(letters)
        return uid

    def _generate_human_readable_unique_id(self):
        # Instead of generating a random string, we can use the
        # name of the parameter and the block name to create a unique id.
        #  E.g.:
        #  - "block-id.category-name.parameter-name": "lbco.cell.length_a"
        #  - "block-id.category-name.entry-id.parameter-name": "lbco.atom_site.Ba.fract_x"
        # For the analysis, we can use the same format, but without the
        # datablock id. E.g.:
        #  - "category-name.entry-id.parameter-name": "alias.occ_Ba.label"
        # This need to be called after the parameter is created and all its
        # attributes are set.
        if self.datablock_id:
            uid = f"{self.datablock_id}.{self.cif_category_key}"
        else:
            uid = f"{self.cif_category_key}"
        if self.collection_entry_id:
            uid += f".{self.collection_entry_id}"
        uid += f".{self.cif_name}"
        return uid

    @property
    def datablock_id(self):
        return self._datablock_id

    @datablock_id.setter
    def datablock_id(self, new_id):
        self._datablock_id = new_id
        # Update the unique id, when datablock_id attribute is of
        # the parameter is changed
        self.uid = self._generate_human_readable_unique_id()

    @property
    def collection_entry_id(self):
        return self._collection_entry_id

    @collection_entry_id.setter
    def collection_entry_id(self, new_id):
        self._collection_entry_id = new_id
        # Update the unique id, when datablock_id attribute is of
        # the parameter is changed
        self.uid = self._generate_human_readable_unique_id()

    @property
    def uid(self):
        return self._human_uid

    @uid.setter
    def uid(self, new_uid):
        # Update the unique id in the global uid map
        old_uid = self._human_uid
        self._human_uid = new_uid
        UidMapHandler.get().replace_uid(old_uid, new_uid)

    @property
    def minimizer_uid(self):
        return self.uid.replace(".", "__")

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        if self._editable:
            self._value = new_value
        else:
            print(warning(f"The parameter '{self.cif_name}' it is calculated "
                          f"automatically and cannot be changed manually."))

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
                 datablock_id=None, # Parent datablock name
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
                 max_value=None):
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
    Base class for standard components, like Cell, Peak, etc.
    """

    @property
    @abstractmethod
    def category_key(self):
        """
        Must be implemented in subclasses to return the ED category name.
        Can differ from cif_category_key.
        """
        pass

    @property
    @abstractmethod
    def cif_category_key(self):
        """
        Must be implemented in subclasses to return the CIF category name.
        """
        pass

    def __init__(self):
        self._locked = False  # If adding new attributes is locked

        self._datablock_id = None  # Parent datablock name to be set by the parent
        self._entry_id = None  # Parent collection entry id to be set by the parent

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

        # If the attribute is not set, and it is a Parameter or Descriptor,
        # set its category_key and cif_category_key to the current category_key
        # and cif_category_key and add it to the component.
        # Also add its name to the list of ordered attributes
        if attr is None:
            if isinstance(value, (Descriptor, Parameter)):
                value.category_key = self.category_key
                value.cif_category_key = self.cif_category_key
                self._ordered_attrs.append(name)
            super().__setattr__(name, value)
        # If the attribute is already set and is a Parameter or Descriptor,
        # update its value. Else, allow normal reassignment
        else:
            if isinstance(attr, (Descriptor, Parameter)):
                attr.value = value
            else:
                super().__setattr__(name, value)

    @property
    def datablock_id(self):
        return self._datablock_id

    @datablock_id.setter
    def datablock_id(self, new_id):
        self._datablock_id = new_id
        # For each parameter in this component, also update its datablock_id
        for param in self.get_all_params():
            param.datablock_id = new_id

    @property
    def entry_id(self):
        return self._entry_id

    @entry_id.setter
    def entry_id(self, new_id):
        self._entry_id = new_id
        # For each parameter in the component, set the entry_id
        for param in self.get_all_params():
            param.collection_entry_id = new_id

    def get_all_params(self):
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


class Collection(ABC):
    """
    Base class for collections like AtomSites, LinkedPhases, SampleModels,
    Experiments, etc.
    """
    @property
    @abstractmethod
    def _child_class(self):
        return None

    def __init__(self):
        self._datablock_id = None  # Parent datablock name to be set by the parent
        self._items = {}

    def __getitem__(self, key):
        return self._items[key]

    def __iter__(self):
        return iter(self._items.values())

    @property
    def datablock_id(self):
        return self._datablock_id

    @datablock_id.setter
    def datablock_id(self, new_id):
        self._datablock_id = new_id
        for param in self.get_all_params():
            param.datablock_id = new_id

    def add(self, *args, **kwargs):
        """
        Add a new item to the collection. The item must be a subclass of
        Component.
        """
        if self._child_class is None:
            raise ValueError("Child class is not defined.")
        child_obj = self._child_class(*args, **kwargs)
        child_obj.datablock_id = self.datablock_id  # Setting the datablock_id to update its child parameters
        child_obj.entry_id = child_obj.entry_id  # Forcing the entry_id to be reset to update its child parameters
        self._items[child_obj._entry_id] = child_obj

    def get_all_params(self):
        params = []
        for item in self._items.values():
            if isinstance(item, Datablock):
                datablock = item
                for datablock_item in datablock.items():
                    if isinstance(datablock_item, Component):
                        component = datablock_item
                        for param in component.get_all_params():
                            params.append(param)
                    elif isinstance(datablock_item, Collection):
                        collection = datablock_item
                        for component in collection:
                            for param in component.get_all_params():
                                params.append(param)
            elif isinstance(item, Component):
                component = item
                for param in component.get_all_params():
                    params.append(param)
            else:
                raise TypeError(f"Expected a Component or Datablock, got {type(item)}")
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
                # Keys
                keys = [f'_{category_key}.{param_key}' for param_key in params.keys()]
                # Values. If the value is a string and contains spaces, add quotes
                values = []
                for value in params.values():
                    value = f'{value}'
                    if " " in value:
                        value = f'"{value}"'
                    values.append(value)
                # Header is added only for the first item
                if idx == 0:
                    lines.append(f"loop_")
                    header = "\n".join(keys)
                    lines.append(header)
                line = ' '.join(values)
                lines.append(line)
        return "\n".join(lines)


class Datablock(ABC):
    """
    Base class for Sample Model and Experiment data blocks.
    """
    # TODO: Consider unifying with class Component?

    def __init__(self):
        self._name = None

    def __setattr__(self, name, value):
        # TODO: compare with class Component
        # If the value is a Component or Collection:
        # - set its datablock_id to the current datablock name
        # - add it to the datablock
        if isinstance(value, (Component, Collection)):
            value.datablock_id = self._name
        super().__setattr__(name, value)

    def items(self):
        """
        Returns a list of both components and collections in the
        data block.
        """
        attr_objs = []
        for attr_name in dir(self):
            if attr_name.startswith('_'):
                continue
            attr_obj = getattr(self, attr_name)
            if isinstance(attr_obj, (Component,
                                     Collection)):
                attr_objs.append(attr_obj)
        return attr_objs

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, new_name):
        self._name = new_name
        # For each component/collection in this datablock,
        # also update its datablock_id
        for item in self.items():
            item.datablock_id = new_name
