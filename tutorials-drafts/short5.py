from __future__ import annotations

import difflib
import re
import secrets
import string
from abc import ABC
from abc import abstractmethod
from enum import Enum
from enum import auto
from functools import wraps
from typing import Any
from typing import Callable
from typing import Optional
from typing import ParamSpec
from typing import TypeVar
from typing import Union

from typeguard import TypeCheckError
from typeguard import typechecked

from easydiffraction.utils.logging import log  # type: ignore
#from easydiffraction.sample_models.components.cell import Cell # type: ignore

import numpy as np
P = ParamSpec('P')
R = TypeVar('R')


# ---------------------------------------------------------------------
# decorators.py
# ---------------------------------------------------------------------
def checktype(func: Callable[P, R]) -> Callable[P, Optional[R]]:
    """Wrapper around @typechecked that catches and logs type errors during runtime."""
    checked_func = typechecked(func)

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> Optional[R]:
        try:
            return checked_func(*args, **kwargs)
        except TypeCheckError as err:
            message = f'Type error in {func.__qualname__}: {err}'
            log.error(message, exc_type=TypeError)
            return None

    return wrapper


# ---------------------------------------------------------------------
# diagnostic.py
# ---------------------------------------------------------------------
class Diagnostics:
    @staticmethod
    def readonly_error(name, key=None):
        message = f"Cannot modify read-only attribute '{key}' of <{name}>."
        log.error(message, exc_type=AttributeError)

    @staticmethod
    def attr_error(name, key, allowed):
        suggestion = Diagnostics._build_suggestion(key, allowed)
        hint = suggestion or Diagnostics._build_allowed(allowed)
        message = f"Unknown attribute '{key}' of <{name}>.{hint}"
        log.error(message, exc_type=AttributeError)

    @staticmethod
    def _suggest(key, allowed):
        if not allowed:
            return None
        # Return the allowed key with smallest Levenshtein distance
        matches = difflib.get_close_matches(key, allowed, n=1)
        match = matches[0] if matches else None
        return match

    @staticmethod
    def _build_suggestion(key, allowed):
        suggestion = Diagnostics._suggest(key, allowed)
        if suggestion:
            return f" Did you mean '{suggestion}'?"
        return ''

    @staticmethod
    def _build_allowed(allowed):
        if allowed:
            s = f'{sorted(allowed)}'[1:-1] # strip brackets
            return f' Allowed: {s}.'
        return ''


# ---------------------------------------------------------------------
# validation.py
# ---------------------------------------------------------------------
class Validator(ABC):
    """Abstract validator base class with global strictness control."""

    def __init__(
            self, 
            *,
            default: Any = None,
    ) -> None:
        self.default: Any = default

    @abstractmethod
    def validate(
            self, 
            *,
            name: str, 
            new: Any, 
            current: Any,
    ) -> Any:
        """Validate value and return possibly corrected one."""
        raise NotImplementedError


class RangeValidator(Validator):
    def __init__(
        self,
        *,
        ge: Optional[int | float] = None,
        le: Optional[int | float] = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.ge: Optional[int | float] = ge
        self.le: Optional[int | float] = le

    def validate(
            self, 
            *,
            name: str, 
            new: Any, 
            current: Any,
    ) -> Any:
        if current is None and new is None:
            message = f'No value provided for <{name}>. Using default {self.default!r}.'
            log.warning(message, exc_type=UserWarning)
            return self.default
        
        if not isinstance(new, (float, int, np.floating, np.integer)):
            message = f'Value {new!r} ({type(new).__name__}) is not float expected for <{name}>.'
            log.error(message, exc_type=TypeError)
            return current if current is not None else self.default
        
        if (self.ge is not None and new < self.ge) or (self.le is not None and new > self.le):
            message = f'Value {new} is outside of expected range [{self.ge}, {self.le}] for <{name}>.'
            log.error(message, exc_type=ValueError)
            return current if current is not None else self.default
        
        log.debug(f'<{name}> set to validated {new}.')
        return new


class ListValidator(Validator):
    def __init__(
        self,
        *,
        allowed_values,
        default=None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._allowed_values = allowed_values
        self._default = default

    @property
    def allowed_values(self):
        return self._allowed_values() if callable(self._allowed_values) else self._allowed_values

    @allowed_values.setter
    def allowed_values(self, value):
        self._allowed_values = value

    @property
    def default(self):
        return self._default() if callable(self._default) else self._default

    @default.setter
    def default(self, value):
        self._default = value

    def validate(
            self, 
            *,
            name: str, 
            new: Any, 
            current: Any,
    ) -> Any:
        if current is None and new is None:
            message = f'No value provided for <{name}>. Using default {self.default!r}.'
            log.warning(message, exc_type=UserWarning)
            return self.default
        
        if new not in self.allowed_values:
            message = f"Value {new!r} is not allowed for <{name}>."
            log.error(message, exc_type=ValueError)
            return current if current is not None else self.default

        log.debug(f'<{name}> set to validated {new!r}.')
        return new
    


class RegexValidator(Validator):
    def __init__(
        self,
        *,
        pattern: str,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.pattern = pattern
        self._regex = re.compile(pattern)

    def validate(
            self, 
            *,
            name: str, 
            new: Any, 
            current: Any,
    ) -> Any:
        if current is None and new is None:
            message = f'No value provided for <{name}>. Using default {self.default!r}.'
            log.warning(message, exc_type=UserWarning)
            return self.default
        
        if not isinstance(new, str):
            message = f'Value {new} ({type(new).__name__}) is not string expected for <{name}>.'
            log.error(message, exc_type=TypeError)
            return current if current is not None else self.default
        
        if not self._regex.match(new):
            message = f"Value {new!r} does not match pattern '{self.pattern}' for <{name}>."
            log.error(message, exc_type=ValueError)
            return current if current is not None else self.default

        log.debug(f'<{name}> set to validated {new!r}.')
        return new
    


# ---------------------------------------------------------------------
# guards.py
# ---------------------------------------------------------------------
class GuardedBase(ABC):
    """Base class providing attribute guarding and automatic parent linkage."""

    def __init__(self) -> None:
        self._diagnoser: Diagnostics = Diagnostics()
        self._identity: Identity = Identity(owner=self)

    def __getattr__(self, key: str):
        cls = type(self)
        if key not in cls._public_attrs():
            name = self._log_name
            allowed = cls._public_attrs()
            self._diagnoser.attr_error(name, key, allowed)

    def __setattr__(self, key: str, value: Any):
        # Allow private attributes
        if key.startswith('_'):
            self._assign_attr(key, value)
            return
        
        # Handle public attributes with diagnostics
        cls = type(self)
        name = self._log_name

        if key in cls._public_readonly_attrs():
            self._diagnoser.readonly_error(name, key)
            return

        if key not in cls._public_attrs():
            allowed = cls._public_writable_attrs()
            self._diagnoser.attr_error(name, key, allowed)
            return

        self._assign_attr(key, value)

    def __str__(self) -> str:
        return f'<{self._log_name}>'

    def __repr__(self) -> str:
        return self.__str__()

    def _assign_attr(self, key: str, value: Any) -> None:
        """Low-level assignment with automatic parent linkage."""
        object.__setattr__(self, key, value)
        if key != "_parent" and isinstance(value, GuardedBase):
            object.__setattr__(value, "_parent", self)

    @classmethod
    def _iter_properties(cls):
        """Iterate over all public properties defined in the class hierarchy."""
        for base in cls.mro():
            for key, attr in base.__dict__.items():
                if key.startswith('_') or not isinstance(attr, property):
                    continue
                yield key, attr

    @classmethod
    def _public_attrs(cls) -> set[str]:
        """All public properties (read-only + writable)."""
        return {key for key, _ in cls._iter_properties()}

    @classmethod
    def _public_readonly_attrs(cls) -> set[str]:
        """Public properties without a setter."""
        return {key for key, prop in cls._iter_properties() if prop.fset is None}

    @classmethod
    def _public_writable_attrs(cls) -> set[str]:
        """Public properties with a setter."""
        return {key for key, prop in cls._iter_properties() if prop.fset is not None}

    @property
    def _log_name(self) -> str:
        return type(self).__name__
    
    def _get_parent(self):
        return object.__getattribute__(self, "__dict__").get("_parent")

    @property
    @abstractmethod
    def parameters(self):
        """Return a list of parameter objects (to be implemented by subclasses)."""
        raise NotImplementedError

    @property
    @abstractmethod
    def as_cif(self) -> str:
        """Return CIF representation of this object (to be implemented by subclasses)."""
        raise NotImplementedError

# ---------------------------------------------------------------------
# identity.py
# ---------------------------------------------------------------------

class Identity:
    """Dynamic hierarchical identity resolving through parent chain safely."""

    def __init__(
        self,
        *,
        owner: object,
        datablock: Callable[[], str] | None = None,
        category: Callable[[], str] | None = None,
        entry: Callable[[], str] | None = None,
    ) -> None:
        self._owner = owner
        self._datablock = datablock # TODO: Rename to datablock_entry
        self._category = category
        self._entry = entry  # TODO: Rename to category_entry

    def _resolve_up(self, attr: str, visited=None):
        """Resolve an attribute by walking up the parent chain safely."""
        if visited is None:
            visited = set()
        if id(self) in visited:
            return None
        visited.add(id(self))

        # Direct callable or value on self
        value = getattr(self, f"_{attr}", None)
        if callable(value):
            return value()
        if isinstance(value, str):
            return value

        # Climb to parent if available
        parent = getattr(self._owner, "__dict__", {}).get("_parent")
        if parent and hasattr(parent, "_identity"):
            return parent._identity._resolve_up(attr, visited)
        return None

    @property
    def datablock_entry_name(self):
        return self._resolve_up("datablock")

    @datablock_entry_name.setter
    def datablock_entry_name(self, func: Callable[[], str]) -> None:
        self._datablock = func

    @property
    def category_code(self):
        return self._resolve_up("category")

    @category_code.setter
    def category_code(self, func_or_value: str | Callable[[], str]) -> None:
        self._category = func_or_value

    @property
    def category_entry_name(self):
        return self._resolve_up("entry")

    @category_entry_name.setter
    def category_entry_name(self, func: Callable[[], str]) -> None:
        self._entry = func

    @property
    def full_name(self):
        """Return hierarchical identity including parameter name if available."""
        parts = [
            str(p)
            for p in [
                self.datablock_entry_name,
                self.category_code,
                self.category_entry_name,
            ]
            if p is not None
        ]

        # If the owner is a Parameter/Descriptor, append its name
        owner = getattr(self, "_owner", None)
        if owner and hasattr(owner, "name") and owner.name is not None:
            parts.append(str(owner.name))

        return ".".join(parts) if parts else "UNSET"


# ---------------------------------------------------------------------
# parameters.py
# ---------------------------------------------------------------------
class ValidatedBase(GuardedBase):
    def __init__(
        self,
        *,
        name: str,
        validator: Validator,
        value: Any,
    ) -> None:
        super().__init__()
        self._name: str = name
        self._validator: Validator = validator
        self._value: Any = self._validator.validate(
            name=self._log_name,
            new=value,
            current=None,
        )

    @property
    def _log_name(self) -> str:
        return f'{type(self).__name__} {self.name}'

    @property
    def name(self) -> str:
        return self._name

    @property
    def value(self) -> Any:
        return self._value

    @value.setter
    @checktype
    def value(self, new: Any) -> None:
        self._value = self._validator.validate(
            name=self._log_name,
            new=new,
            current=self._value,
        )
                


class GenericDescriptorBase(ValidatedBase):
    def __init__(
        self,
        *,
        description: str = '',
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._description: str = description
        self._uid: str = self._generate_uid()

    def __str__(self) -> str:
        return f'<{self._log_name} = {self.value!r}>'

    @property
    def description(self) -> str:
        return self._description

    @staticmethod
    def _generate_uid() -> str:
        length: int = 16
        return ''.join(secrets.choice(string.ascii_lowercase) for _ in range(length))

    # TODO: Check following properties. Make private, etc.

    @property
    def uid(self):
        return self._uid

    @property
    def parameters(self):
        # For a single descriptor, itself is the only parameter.
        return [self]

    @property
    def as_cif(self) -> str:
        tags = self._cif_handler.names
        main_key = tags[0]
        value = self.value
        value = f'"{value}"' if isinstance(value, str) and ' ' in value else value
        return f'{main_key} {value}'
    

class GenericDescriptorStr(GenericDescriptorBase):
    def __init__(
        self,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)


class GenericDescriptorFloat(GenericDescriptorBase):
    def __init__(
        self,
        *,
        units: str = '',
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._units: str = units

    def __str__(self) -> str:
        s: str = super().__str__()
        s = s[1:-1]  # strip <>
        if self.units:
            s += f' {self.units}'
        return f'<{s}>'

    @property
    def units(self) -> str:
        return self._units

# ---------------------------------------------------------------------
# Parameter
# ---------------------------------------------------------------------
class GenericParameter(GenericDescriptorFloat):
    """Numeric parameter with runtime validation and safe assignment."""

    def __init__(
        self,
        *,
        free: bool = False,
        uncertainty: Optional[float] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._free: bool = free
        self._uncertainty: Optional[float] = uncertainty
        self._fit_min: float = -np.inf  # TODO: consider renaming
        self._fit_max: float = np.inf  # TODO: consider renaming
        self._start_value: float = 0.0  # TODO: consider removing
        self._constrained: bool = False  # TODO: freeze

    def __str__(self) -> str:
        s = GenericDescriptorBase.__str__(self)
        s = s[1:-1]  # strip <>
        if self.uncertainty is not None:
            s += f' ± {self.uncertainty}'
        if self.units is not None:
            s += f' {self.units}'
        s += f' (free={self.free})'
        return f'<{s}>'


    @property
    def free(self) -> bool:
        return self._free

    @free.setter
    @checktype
    def free(self, new: bool) -> None:
        self._free = new

    @property
    def uncertainty(self) -> Optional[float]:
        return self._uncertainty

    @uncertainty.setter
    @checktype
    def uncertainty(self, new: float) -> None:
        self._uncertainty = new

    # TODO: Check following properties. Make private, etc.

    @property
    def fit_min(self) -> float:
        return -np.inf
    @fit_min.setter
    @checktype
    def fit_min(self, new: float) -> None:
        self._fit_min = new

    @property
    def fit_max(self) -> float:
        return np.inf
    @fit_max.setter
    @checktype
    def fit_max(self, new: float) -> None:
        self._fit_max = new

    @property
    def start_value(self) -> float:
        return self._start_value

    @property
    def constrained(self) -> bool:
        return self._constrained

    @property
    def _minimizer_uid(self):
        """Return variant of uid safe for minimizer engines."""
        return self.uid
        # return self.full_name.replace('.', '__')



# ----------------------------------------------------------------------
# CifHandler
# ----------------------------------------------------------------------
class CifHandler:
    def __init__(
            self,
            *,
            names: list[str]
    ) -> None:
        self._names = names

    @property
    def names(self):
        return self._names

class DescriptorStr(GenericDescriptorStr):
    def __init__(
        self,
        *,
        cif_handler: CifHandler,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._cif_handler = cif_handler

class DescriptorFloat(GenericDescriptorFloat):
    def __init__(
        self,
        *,
        cif_handler: CifHandler,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._cif_handler = cif_handler

class Parameter(GenericParameter):
    def __init__(
        self,
        *,
        cif_handler: CifHandler,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._cif_handler = cif_handler

# ---------------------------------------------------------------------
# collections.py
# ---------------------------------------------------------------------
class CollectionBase(GuardedBase):

    def __init__(
            self, 
            item_type
        ) -> None:
        super().__init__()
        self._items: list = []
        self._index: dict = {}
        self._item_type = item_type

    def __getitem__(self, name: str):
        try:
            return self._index[name]
        except KeyError:
            self._rebuild_index()
            return self._index[name]

    def __setitem__(self, name: str, item) -> None:
        # Check if item with same identity exists; if so, replace it
        for i, existing_item in enumerate(self._items):
            if existing_item._identity.category_entry_name == name:
                self._items[i] = item
                self._rebuild_index()
                return
        # Otherwise append new item
        item._parent = self # Explicitly set the parent for the item
        self._items.append(item)
        self._rebuild_index()

    def __delitem__(self, name: str) -> None:
        # Remove from _items by identity entry name
        for i, item in enumerate(self._items):
            if item._identity.category_entry_name == name:
                object.__setattr__(item, "_parent", None) # Unlink the parent before removal                
                del self._items[i]
                self._rebuild_index()
                return
        raise KeyError(name)

    def __iter__(self):
        return iter(self._items)

    def __len__(self) -> int:
        return len(self._items)

    def _rebuild_index(self) -> None:
        self._index.clear()
        for item in self._items:
            key = item._identity.category_entry_name or item._identity.datablock_entry_name
            if key:
                self._index[key] = item

    def keys(self):
        return (item._identity.category_entry_name for item in self._items)

    def values(self):
        return (item for item in self._items)

    def items(self):
        return ((item._identity.category_entry_name, item) for item in self._items)

    # TODO: Check if needed.
    @property
    def names(self):
        """Return a list of all item keys in the collection."""
        return list(self.keys())

# ---------------------------------------------------------------------
# categories.py
# ---------------------------------------------------------------------
class CategoryItem(GuardedBase):
    """Base class for items in a category collection."""

    def __str__(self) -> str:
        """Human-readable representation of this component."""
        name = self._log_name
        params = ', '.join(f'{p.name}={p.value!r}' for p in self.parameters)
        return f'<{name} ({params})>'

    @property
    def parameters(self):
        # Only direct descriptor/parameter attributes (not recursive)
        params = []
        for v in self.__dict__.values():
            if isinstance(v, GenericDescriptorBase):
                params.append(v)
        return params

    @property
    def as_cif(self) -> str:
        """Return CIF representation of this object."""
        lines: list[str] = ['']
        for param in self.parameters:
            tags = param._cif_handler.names
            main_key = tags[0]
            value = param.value
            value = f'"{value}"' if isinstance(value, str) and ' ' in value else value
            lines.append(f'{main_key} {value}')
        return '\n'.join(lines)


class CategoryCollection(CollectionBase):
    """Handles loop-style category containers (e.g. AtomSites).

    Each item is a CategoryItem (component).
    """

    def __str__(self) -> str:
        """Human-readable representation of this component."""
        name = self._log_name
        size = len(self)
        return f'<{name} collection ({size} items)>'

    @property
    def parameters(self):
        # Only direct items (not recursive)
        return list(self._items)

    @property
    def as_cif(self) -> str:
        """Return CIF representation of this object."""
        lines: list[str] = ['']
        # Add header using the first item
        first_item = list(self.values())[0]
        lines.append('loop_')
        for param in first_item.parameters:
            tags = param._cif_handler.names
            main_key = tags[0]
            lines.append(main_key)
        # Add data from all items one by one
        for item in self.values():
            line = []
            for param in item.parameters:
                value = param.value
                line.append(str(value))
            line = ' '.join(line)
            lines.append(line)
        return '\n'.join(lines)

    # TODO: Check following properties. Make private, etc.

    @typechecked
    def add(self, item) -> None:
        """Add an item to the collection."""
        self[item._identity.category_entry_name] = item

    def add_from_args(self, *args, **kwargs) -> None:
        """Create and add a new child instance from the provided
        arguments.
        """
        child_obj = self._item_type(*args, **kwargs)
        self.add(child_obj)



# ---------------------------------------------------------------------
# datablocks.py
# ---------------------------------------------------------------------
class DatablockItem(GuardedBase):
    """Base class for items in a datablock collection."""

    def __str__(self) -> str:
        """Human-readable representation of this component."""
        name = self._log_name
        items = self._items
        return f'<{name} ({items})>'

    @property
    def parameters(self):
        # Only direct attributes that are CategoryItem or CategoryCollection
        params = []
        for v in self.__dict__.values():
            if isinstance(v, (CategoryItem, CategoryCollection)):
                params.append(v)
        return params

    @property
    def as_cif(self) -> str:
        """Return CIF representation of this object."""
        lines = [f'data_{self._identity.datablock_entry_name }']
        for category in self.__dict__.values():
            if isinstance(category, (CategoryItem, CategoryCollection)):
                lines.append(category.as_cif)
        return '\n'.join(lines)


class DatablockCollection(CollectionBase):
    """Handles top-level collections (e.g. SampleModels, Experiments).

    Each item is a DatablockItem.
    """

    def __str__(self) -> str:
        """Human-readable representation of this component."""
        name = self._log_name
        size = len(self)
        return f'<{name} collection ({size} items)>'

    @property
    def parameters(self):
        # Only direct items (not recursive)
        return list(self._items)

    @property
    def as_cif(self) -> str:
        """Return CIF representation of this object."""
        l = [datablock.as_cif for datablock in self.values() 
             if isinstance(datablock, DatablockItem)]
        s = '\n'.join(l)
        return s

    # TODO: Check following properties. Make private, etc.

    @typechecked
    def add(self, item) -> None:
        """Add an item to the collection."""
        self[item._identity.datablock_entry_name] = item

    def add_from_args(self, *args, **kwargs) -> None:
        """Create and add a new child instance from the provided
        arguments.
        """
        child_obj = self._item_type(*args, **kwargs)
        self.add(child_obj)

    

# ---------------------------------------------------------------------
# cell.py
# ---------------------------------------------------------------------
class Cell(CategoryItem):
    def __init__(
        self,
        *,
        length_b: Optional[int | float] = None,
    ) -> None:
        super().__init__()
        self._length_b: Parameter = Parameter(
            name='length_b',
            description='Length of the b axis of the unit cell.',
            validator=RangeValidator(ge=0, le=1000, default=10.0),
            value=length_b,
            units='Å',
            cif_handler=CifHandler(names=['_cell.length_b'])
        )
        self._identity.category_code = 'cell'

    @property
    def length_b(self) -> Parameter:
        return self._length_b

    # TODO: Consider using @checktype here and remove typecheck in 
    #  Parameter.value setter.
    @length_b.setter
    def length_b(self, new: int | float) -> None:
        self._length_b.value = new


# ---------------------------------------------------------------------
# space_group.py
# ---------------------------------------------------------------------
class SpaceGroup(CategoryItem):
    def __init__(
        self,
        *,
        name_h_m: str = None,
        it_coordinate_system_code: str = None,
    ) -> None:
        super().__init__()
        self._name_h_m: Parameter = Parameter(
            name='name_h_m',
            description='Hermann-Mauguin symbol of the space group.',
            validator=ListValidator(
                allowed_values=['P 1', 'P n m a'],
                default='P 1',
            ),
            value=name_h_m,
            cif_handler=CifHandler(names=[
                '_space_group.name_H-M_alt',
                '_space_group_name_H-M_alt',
                '_symmetry.space_group_name_H-M',
                '_symmetry_space_group_name_H-M',
                ])
        )
        self._it_coordinate_system_code: Parameter = Parameter(
            name='it_coordinate_system_code',
            description='A qualifier identifying which setting in IT is used.',
            validator=ListValidator(
                allowed_values=['1', '2', 'abc', 'cab'],
                default='',
            ),
            value=it_coordinate_system_code,
            cif_handler=CifHandler(names=[
                '_space_group.IT_coordinate_system_code',
                '_space_group_IT_coordinate_system_code',
                '_symmetry.IT_coordinate_system_code',
                '_symmetry_IT_coordinate_system_code',
                ])
        )
        self._identity.category_code = 'space_group'    

    @property
    def name_h_m(self):
        return self._name_h_m

    @name_h_m.setter
    def name_h_m(self, value):
        self._name_h_m.value = value

    @property
    def it_coordinate_system_code(self):
        return self._it_coordinate_system_code

    @it_coordinate_system_code.setter
    def it_coordinate_system_code(self, value):
        self._it_coordinate_system_code.value = value






# ---------------------------------------------------------------------
# atom_sites.py
# ---------------------------------------------------------------------
class AtomSite(CategoryItem):
    def __init__(
        self,
        *,
        label=None,
        type_symbol=None,
        fract_x=None,
        fract_y=None,
        fract_z=None,
        wyckoff_letter=None,
        occupancy=None,
        b_iso=None,
        adp_type=None,
    ) -> None:
        super().__init__()
        self._label: DescriptorStr = DescriptorStr(
            name='label',
            description='Unique identifier for the atom site.',
            validator=RegexValidator(
                pattern=r'^[A-Za-z_][A-Za-z0-9_]*$',
                default='Si',
            ),
            value=label,
            cif_handler=CifHandler(names=[
                '_atom_site.label',
                ])
        )
        self._type_symbol: DescriptorStr = DescriptorStr(
            name='type_symbol',
            description='Chemical symbol of the atom type.',
            validator=ListValidator(
                allowed_values=['Si', 'O', 'Tb'],
                default='Tb',
            ),
            value=type_symbol,
            cif_handler=CifHandler(names=[
                '_atom_site.type_symbol',
                ])
        )
        self._fract_x: Parameter = Parameter(
            name='fract_x',
            description='Fractional x-coordinate of the atom site within the unit cell.',
            validator=RangeValidator(
                default=0.0,
            ),
            value=fract_x,
            cif_handler=CifHandler(names=[
                '_atom_site.fract_x',
                ])
        )
        self._fract_y: Parameter = Parameter(
            name='fract_y',
            description='Fractional y-coordinate of the atom site within the unit cell.',
            validator=RangeValidator(
                default=0.0,
            ),
            value=fract_y,
            cif_handler=CifHandler(names=[
                '_atom_site.fract_y',
                ])
        )
        self._fract_z: Parameter = Parameter(
            name='fract_z',
            description='Fractional z-coordinate of the atom site within the unit cell.',
            validator=RangeValidator(
                default=0.0,
            ),
            value=fract_z,
            cif_handler=CifHandler(names=[
                '_atom_site.fract_z',
                ])
        )   
        self._wyckoff_letter: DescriptorStr = DescriptorStr(
            name='wyckoff_letter',
            description='Wyckoff letter indicating the symmetry of the '
            'atom site within the space group.',
            validator=ListValidator(
                allowed_values=['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't'],
                default='a',
            ),
            value=wyckoff_letter,
            cif_handler=CifHandler(names=[
                '_atom_site.Wyckoff_letter',
                '_atom_site.Wyckoff_symbol',
                ])
        )
        self._occupancy: Parameter = Parameter(
            name='occupancy',
            description='Occupancy of the atom site, representing the '
            'fraction of the site occupied by the atom type.',
            validator=RangeValidator(
                default=1.0,
            ),
            value=occupancy,
            cif_handler=CifHandler(names=[
                '_atom_site.occupancy',
                ])
        )
        self._b_iso: Parameter = Parameter(
            name='b_iso',
            description='Isotropic atomic displacement parameter (ADP) '
            'for the atom site.',
            validator=RangeValidator(
                default=0.0,
            ),
            value=b_iso,
            units='Å²',
            cif_handler=CifHandler(names=[
                '_atom_site.B_iso_or_equiv',
                ])
        )
        self._adp_type: DescriptorStr = DescriptorStr(
            name='adp_type',
            description='Type of atomic displacement parameter (ADP) '
            'used (e.g., Biso, Uiso, Uani, Bani).',
            validator=ListValidator(
                allowed_values=['Biso'],
                default='Biso',
            ),
            value=adp_type,
            cif_handler=CifHandler(names=[
                '_atom_site.adp_type',
                ])
        )
        self._identity.category_code = 'atom_site'    
        self._identity.category_entry_name = lambda: self.label.value

    @property
    def label(self):
        return self._label

    @label.setter
    def label(self, value):
        self._label.value = value

    @property
    def type_symbol(self):
        return self._type_symbol

    @type_symbol.setter
    def type_symbol(self, value):
        self._type_symbol.value = value

    @property
    def adp_type(self):
        return self._adp_type

    @adp_type.setter
    def adp_type(self, value):
        self._adp_type.value = value

    @property
    def wyckoff_letter(self):
        return self._wyckoff_letter

    @wyckoff_letter.setter
    def wyckoff_letter(self, value):
        self._wyckoff_letter.value = value

    @property
    def fract_x(self):
        return self._fract_x

    @fract_x.setter
    def fract_x(self, value):
        self._fract_x.value = value

    @property
    def fract_y(self):
        return self._fract_y

    @fract_y.setter
    def fract_y(self, value):
        self._fract_y.value = value

    @property
    def fract_z(self):
        return self._fract_z

    @fract_z.setter
    def fract_z(self, value):
        self._fract_z.value = value

    @property
    def occupancy(self):
        return self._occupancy

    @occupancy.setter
    def occupancy(self, value):
        self._occupancy.value = value

    @property
    def b_iso(self):
        return self._b_iso

    @b_iso.setter
    def b_iso(self, value):
        self._b_iso.value = value

class AtomSites(CategoryCollection):
    """Collection of AtomSite instances."""

    def __init__(self):
        super().__init__(item_type=AtomSite)

# ---------------------------------------------------------------------
# sample_model.py
# ---------------------------------------------------------------------
class SampleModel(DatablockItem):
    def __init__(self, *, name) -> None:
        super().__init__()
        self._name = name
        self._cell: Cell = Cell()
        self._space_group: SpaceGroup = SpaceGroup()
        self._atom_sites: AtomSites = AtomSites()
        self._identity.datablock_entry_name = lambda: self.name


    def __str__(self) -> str:
        """Human-readable representation of this component."""
        name = self._log_name
        items = ', '.join(f'{k}={v}' for k, v in {
            'cell': self.cell,
            'space_group': self.space_group,
            'atom_sites': self.atom_sites,
        }.items())
        return f'<{name} ({items})>'

    @property
    def name(self) -> str:
        return self._name
    @name.setter
    def name(self, new: str) -> None:
        self._name = new

    @property
    def cell(self) -> Cell:
        return self._cell
    @cell.setter
    def cell(self, new: Cell) -> None:
        self._cell = new

    @property
    def space_group(self) -> SpaceGroup:
        return self._space_group
    @space_group.setter
    def space_group(self, new: SpaceGroup) -> None:
        self._space_group = new

    @property
    def atom_sites(self) -> AtomSites:
        return self._atom_sites
    @atom_sites.setter
    def atom_sites(self, new: AtomSites) -> None:
        self._atom_sites = new

class SampleModels(DatablockCollection):
    """Collection of SampleModel instances."""

    def __init__(self):
        super().__init__(item_type=SampleModel)


# ---------------------------------------------------------------------
# Example usage
# ---------------------------------------------------------------------
if __name__ == '__main__':
    log.info('-------- Cell --------')

    c = Cell()
    assert c.length_b.value == 10.0
    c = Cell(length_b=-8.8)
    assert c.length_b.value == 10.0
    c = Cell(length_b='7.7')  # type: ignore
    assert c.length_b.value == 10.0
    c = Cell(length_b=6.6)
    assert c.length_b.value == 6.6
    c.length_b.value = -5.5
    assert c.length_b.value == 6.6
    c.length_b = -4.4
    assert c.length_b.value == 6.6
    c.length_b = 3.3
    assert c.length_b.value == 3.3
    c.length_b = 2222.2
    assert c.length_b.value == 3.3
    c.length_b.free = 'qwe'  # type: ignore
    assert c.length_b.free is False
    c.length_b.fre = 'fre'  # type: ignore
    assert getattr(c.length_b, 'fre', None) is None
    c.length_b.qwe = 'qwe'  # type: ignore
    assert getattr(c.length_b, 'qwe', None) is None
    c.length_b.description = 'desc'  # type: ignore
    assert c.length_b.description == 'Length of the b axis of the unit cell.'  # type: ignore
    assert c.length_b._public_readonly_attrs() == {
        'constrained', 'units', 'uid', 'name', 'start_value', 'parameters', 'as_cif', 'description'
        }
    assert c.length_b._public_writable_attrs() == {
        'value', 'fit_max', 'free', 'uncertainty', 'fit_min'
    }
    c.qwe = 'qwe'
    assert getattr(c.length_b, 'qwe', None) is None
    assert c.length_b._cif_handler.names == ['_cell.length_b']
    assert len(c.length_b._minimizer_uid) == 16
    assert(c.parameters[0].value == 3.3)  # type: ignore

    log.info(f'-------- SpaceGroup --------')

    sg = SpaceGroup()
    assert sg.name_h_m.value == 'P 1'
    sg = SpaceGroup(name_h_m='qwe')
    assert sg.name_h_m.value == 'P 1'
    sg = SpaceGroup(name_h_m='P b n m', it_coordinate_system_code='cab')
    assert sg.name_h_m.value == 'P 1'
    assert sg.it_coordinate_system_code.value == 'cab' # TODO: Should be ''
    sg = SpaceGroup(name_h_m='P n m a', it_coordinate_system_code='cab')
    assert sg.name_h_m.value == 'P n m a'
    assert sg.it_coordinate_system_code.value == 'cab'
    sg.name_h_m = 34.9
    assert sg.name_h_m.value == 'P n m a'
    sg.name_h_m = 'P 1'
    assert sg.name_h_m.value == 'P 1'

    log.info(f'-------- AtomSites --------')

    s1 = AtomSite(label='La', type_symbol='La')
    assert s1.label.value == 'La'
    assert s1.type_symbol.value == 'Tb'
    s2 = AtomSite(label='Si', type_symbol='Si')
    assert s2.label.value == 'Si'
    assert s2.type_symbol.value == 'Si'
    sites = AtomSites()
    assert len(sites) == 0
    sites.add(s1)
    sites.add(s2)
    assert len(sites) == 2
    s1.label = 'Tb'
    assert s1.label.value == 'Tb'
    assert list(sites.keys()) == ['Tb', 'Si']
    assert sites['Tb'] is s1
    assert sites['Tb'].fract_x.value == 0.0
    s2.fract_x.value = 0.123
    assert s2.fract_x.value == 0.123
    s2.fract_x = 0.456
    assert s2.fract_x.value == 0.456
    sites['Tb'].fract_x = 0.789
    assert sites['Tb'].fract_x.value == 0.789
    sites['Tb'].qwe = 'qwe'  # type: ignore
    assert getattr(sites['Tb'], 'qwe', None) is None
    sites.abc = 'abc'  # type: ignore
    assert getattr(sites, 'abc', None) is None
    sites['Tb'].label = 'a b c'
    assert sites['Tb'].label.value == 'Tb'

    assert c._identity.full_name == 'cell'
    assert c.length_b._identity.full_name == 'cell.length_b'
    assert sites._identity.full_name == 'UNSET' # ???
    assert sites['Tb']._identity.full_name == 'atom_site.Tb'
    assert sites['Tb'].fract_x._identity.full_name == 'atom_site.Tb.fract_x'
    assert sites['Tb']._label.value == 'Tb'
    assert sites['Tb'].label.value == 'Tb'
    assert sites['Tb'].name is None

    log.info(f'-------- SampleModel --------')

    model = SampleModel(name='lbco')
    assert model.name == 'lbco'
    assert model.cell.length_b.value == 10.0
    assert len(model.atom_sites) == 0
    model.atom_sites.add(s1)
    model.atom_sites.add(s2)
    assert len(model.atom_sites) == 2
    assert model.atom_sites.names == ['Tb', 'Si']
    assert model.atom_sites._items[0].label.value == 'Tb'
    assert model.atom_sites._items[1].label.value == 'Si'
    assert model.atom_sites['Tb'].fract_x._identity.full_name == 'lbco.atom_site.Tb.fract_x'

    log.info(f'-------- SampleModels --------')

    models = SampleModels()
    assert len(models) == 0
    models.add(model)
    assert len(models) == 1
    assert models._items[0].name == 'lbco'
    assert models['lbco'].atom_sites['Tb'].fract_x._identity.full_name == 'lbco.atom_site.Tb.fract_x'

    log.info(f'-------- PARENTS --------')

    assert models._parent is None
    assert type(models['lbco']._parent) is SampleModels
    assert type(models['lbco'].cell._parent) is SampleModel
    assert type(models['lbco'].cell.length_b._parent) is Cell
    assert type(models['lbco'].atom_sites._parent) is SampleModel
    assert type(models['lbco'].atom_sites['Tb']._parent) is AtomSites
    assert type(models['lbco'].atom_sites['Tb'].fract_x._parent) is AtomSite

    assert type(s1._parent) is AtomSites
    assert type(models['lbco'].atom_sites) is AtomSites
    assert len(models['lbco'].atom_sites) == 2
    del models['lbco'].atom_sites['Tb']
    assert len(models['lbco'].atom_sites) == 1
    assert s1._parent is None
    assert type(models['lbco'].atom_sites) is AtomSites

    log.info(f'-------- PARAMETERS --------')

    assert len(models['lbco'].atom_sites['Si'].parameters) == 9
    assert models['lbco'].atom_sites['Si'].parameters[0].value == 'Si'
    assert len(models['lbco'].atom_sites.parameters) == 1 # TODO: Wrong, it shows items, not parameters
    assert len(models['lbco'].cell.parameters) == 1
    assert len(models['lbco'].parameters) == 3 # TODO: Wrong, it shows categories, not parameters
    assert len(models.parameters) == 1 # TODO: Wrong, it shows datablocks, not parameters

    log.info(f'-------- CIF HANDLERS --------')

    s3 = AtomSite(label='La', type_symbol='La')
    assert s3.label.value == 'La'
    assert s3.type_symbol.value == 'Tb'

    assert len(models['lbco'].atom_sites) == 1
    models['lbco'].atom_sites.add(s3)
    assert len(models['lbco'].atom_sites) == 2
    assert models['lbco'].cell.length_b.as_cif == '_cell.length_b 10.0'
    assert models['lbco'].cell.as_cif == '\n_cell.length_b 10.0'

    assert models['lbco'].atom_sites.as_cif == """
loop_
_atom_site.label
_atom_site.type_symbol
_atom_site.fract_x
_atom_site.fract_y
_atom_site.fract_z
_atom_site.Wyckoff_letter
_atom_site.occupancy
_atom_site.B_iso_or_equiv
_atom_site.adp_type
Si Si 0.456 0.0 0.0 a 1.0 0.0 Biso
La Tb 0.0 0.0 0.0 a 1.0 0.0 Biso"""

    assert models['lbco'].as_cif =="""data_lbco

_cell.length_b 10.0

_space_group.name_H-M_alt "P 1"
_space_group.IT_coordinate_system_code 

loop_
_atom_site.label
_atom_site.type_symbol
_atom_site.fract_x
_atom_site.fract_y
_atom_site.fract_z
_atom_site.Wyckoff_letter
_atom_site.occupancy
_atom_site.B_iso_or_equiv
_atom_site.adp_type
Si Si 0.456 0.0 0.0 a 1.0 0.0 Biso
La Tb 0.0 0.0 0.0 a 1.0 0.0 Biso"""

    assert models.as_cif =="""data_lbco

_cell.length_b 10.0

_space_group.name_H-M_alt "P 1"
_space_group.IT_coordinate_system_code 

loop_
_atom_site.label
_atom_site.type_symbol
_atom_site.fract_x
_atom_site.fract_y
_atom_site.fract_z
_atom_site.Wyckoff_letter
_atom_site.occupancy
_atom_site.B_iso_or_equiv
_atom_site.adp_type
Si Si 0.456 0.0 0.0 a 1.0 0.0 Biso
La Tb 0.0 0.0 0.0 a 1.0 0.0 Biso"""

