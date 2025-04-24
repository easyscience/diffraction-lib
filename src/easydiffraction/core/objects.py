import random
import string
from abc import (
    ABC,
    abstractmethod
)
from typing import Any, Dict, List, Optional, Union, Iterator, TypeVar

from easydiffraction.utils.formatting import (
    warning,
    error
)

T = TypeVar('T')

class Descriptor:
    """
    Base class for descriptors (non-refinable attributes).
    """

    def __init__(self,
                 value: Any,  # Value of the parameter
                 name: str,  # ED parameter name (to access it in the code)
                 cif_name: str,  # CIF parameter name (to show it in the CIF)
                 pretty_name: Optional[str] = None,  # Pretty name (to show it in the table)
                 datablock_id: Optional[str] = None, # Parent datablock name
                 category_key: Optional[str] = None,  # ED parent category name
                 cif_category_key: Optional[str] = None,  # CIF parent category name
                 collection_entry_id: Optional[str] = None, # Parent collection entry id
                 units: Optional[str] = None,  # Units of the parameter
                 description: Optional[str] = None,  # Description of the parameter
                 editable: bool = True  # If false, the parameter can never be edited. It is calculated automatically
                 ) -> None:

        self._value = value
        self.name: str = name
        self.cif_name: str = cif_name
        self.pretty_name: Optional[str] = pretty_name
        self.datablock_id: Optional[str] = datablock_id
        self.category_key: Optional[str] = category_key
        self.cif_category_key: Optional[str] = cif_category_key
        self.collection_entry_id: Optional[str] = collection_entry_id
        self.units: Optional[str] = units
        self._description: Optional[str] = description
        self._editable: bool = editable

        self.uid: str = self._generate_unique_id()

    def _generate_unique_id(self) -> str:
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
    def value(self) -> Any:
        return self._value

    @value.setter
    def value(self, new_value: Any) -> None:
        if self._editable:
            self._value = new_value
        else:
            print(warning(f"The parameter '{self.cif_name}' it is calculated automatically and cannot be changed manually."))

    @property
    def description(self) -> Optional[str]:
        return self._description

    @property
    def editable(self) -> bool:
        return self._editable


class Parameter(Descriptor):
    """
    A parameter with a value, uncertainty, units, and CIF representation.
    """

    def __init__(self,
                 value: Any,
                 name: str,
                 cif_name: str,
                 pretty_name: Optional[str] = None,
                 datablock_id: Optional[str] = None,
                 category_key: Optional[str] = None,
                 cif_category_key: Optional[str] = None,
                 collection_entry_id: Optional[str] = None,
                 units: Optional[str] = None,
                 description: Optional[str] = None,
                 editable: bool = True,
                 uncertainty: float = 0.0,
                 free: bool = False,
                 constrained: bool = False,
                 min_value: Optional[float] = None,
                 max_value: Optional[float] = None,
                 ) -> None:
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
        self.uncertainty: float = uncertainty  # Standard uncertainty or estimated standard deviation
        self.free: bool = free  # If the parameter is free to be fitted during the optimization
        self.constrained: bool = constrained  # If symmetry constrains the parameter during the optimization
        self.min: Optional[float] = min_value  # Minimum physical value of the parameter
        self.max: Optional[float] = max_value  # Maximum physical value of the parameter
        self.start_value: Optional[Any] = None  # Starting value for optimization


class Component(ABC):
    """
    Base class for single components, like Cell, Peak, etc.
    """

    @property
    @abstractmethod
    def _entry_id(self) -> str:
        pass

    @property
    @abstractmethod
    def cif_category_key(self) -> str:
        """
        Must be implemented in subclasses to return the CIF category name.
        """
        pass

    @property
    @abstractmethod
    def category_key(self) -> str:
        """
        Must be implemented in subclasses to return the ED category name.
        Can differ from cif_category_key.
        """
        pass

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._locked: bool = False  # If adding new attributes is locked
        # TODO: Currently, it is not used. Planned to be used for displaying
        #  the parameters in the specific order.
        self._ordered_attrs: List[str] = []

    def __getattr__(self, name: str) -> Any:
        """
        If the attribute is a Parameter or Descriptor, return its value by default
        """
        attr = self.__dict__.get(name, None)
        if isinstance(attr, (Descriptor, Parameter)):
            return attr.value
        raise AttributeError(f"{name} not found in {self}")

    def __setattr__(self, name: str, value: Any) -> None:
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

    def parameters(self) -> List[Union[Descriptor, Parameter]]:
        attr_objs = []
        for attr_name in dir(self):
            attr_obj = getattr(self, attr_name)
            if isinstance(attr_obj, (Descriptor, Parameter)):
                attr_objs.append(attr_obj)
        return attr_objs

    def as_dict(self) -> Dict[str, Any]:
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

    def as_cif(self) -> str:
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
        self._items: Dict[str, Union[Component, 'Collection']] = {}

    def __getitem__(self, key: str) -> Union[Component, 'Collection']:
        return self._items[key]

    def __iter__(self) -> Iterator[Union[Component, 'Collection']]:
        return iter(self._items.values())

    def get_all_params(self) -> List[Parameter]:
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

    def get_fittable_params(self) -> List[Parameter]:
        all_params = self.get_all_params()
        params = []
        for param in all_params:
            if hasattr(param, 'free') and not param.constrained:
                params.append(param)
        return params

    def get_free_params(self) -> List[Parameter]:
        fittable_params = self.get_fittable_params()
        params = []
        for param in fittable_params:
            if param.free:
                params.append(param)
        return params

    def as_cif(self) -> str:
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

    def components(self) -> List[Union[Component, Collection]]:
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
