import difflib
import re
import secrets
import string
from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import Callable

import numpy as np
from typeguard import TypeCheckError
from typeguard import typechecked

from easydiffraction.utils.logging import Logger
from easydiffraction.utils.logging import log

Logger.configure(
    level=Logger.Level.DEBUG,
    mode=Logger.Mode.COMPACT,
    reaction=Logger.Reaction.WARN,
)

# ---------------------- Diagnostics ---------------------- #


class Diagnostics:
    """Centralized logger for attribute errors and validation
    guidance.
    """

    # ==== Configuration / definition diagnostics ====

    @staticmethod
    def type_override_error(cls_name: str, expected, got):
        msg = (
            f'Invalid type override in <{cls_name}>. '
            f'Descriptor enforces `{expected.__name__}`, '
            f'but AttributeSpec defines `{got.__name__}`.'
        )
        Diagnostics._log_error(msg, exc_type=TypeError)

    # ==== Attribute diagnostics ====

    @staticmethod
    def readonly_error(
        name: str,
        key: str | None = None,
    ):
        Diagnostics._log_error(
            f"Cannot modify read-only attribute '{key}' of <{name}>.",
            exc_type=AttributeError,
        )

    @staticmethod
    def attr_error(
        name: str,
        key: str,
        allowed: set[str],
        label='Allowed',
    ):
        suggestion = Diagnostics._build_suggestion(key, allowed)
        hint = suggestion or Diagnostics._build_allowed(allowed, label=label)
        Diagnostics._log_error(
            f"Unknown attribute '{key}' of <{name}>.{hint}",
            exc_type=AttributeError,
        )

    # ==== Validation diagnostics ====

    @staticmethod
    def type_mismatch(
        name: str,
        value,
        expected_type,
        current=None,
        default=None,
    ):
        got_type = type(value).__name__
        msg = (
            f'Type mismatch for <{name}>. '
            f'Expected `{expected_type}`, got `{got_type}` ({value!r}).'
        )
        Diagnostics._log_error_with_fallback(
            msg, current=current, default=default, exc_type=TypeError
        )

    @staticmethod
    def range_mismatch(
        name: str,
        value,
        ge,
        le,
        current=None,
        default=None,
    ):
        msg = f'Value mismatch for <{name}>. Provided {value!r} outside [{ge}, {le}].'
        Diagnostics._log_error_with_fallback(
            msg, current=current, default=default, exc_type=TypeError
        )

    @staticmethod
    def choice_mismatch(
        name: str,
        value,
        allowed,
        current=None,
        default=None,
    ):
        msg = f'Value mismatch for <{name}>. Provided {value!r} is unknown.'
        if allowed is not None:
            msg += Diagnostics._build_allowed(allowed)
        Diagnostics._log_error_with_fallback(
            msg, current=current, default=default, exc_type=TypeError
        )

    @staticmethod
    def regex_mismatch(
        name: str,
        value,
        pattern,
        current=None,
        default=None,
    ):
        msg = (
            f"Value mismatch for <{name}>. Provided {value!r} does not match pattern '{pattern}'."
        )
        Diagnostics._log_error_with_fallback(
            msg, current=current, default=default, exc_type=TypeError
        )

    @staticmethod
    def none_value(name, default):
        Diagnostics._log_debug(f'No value provided for <{name}>. Using default {default!r}.')

    @staticmethod
    def validated(name, value, stage: str | None = None):
        stage_info = f' ({stage})' if stage else ''
        Diagnostics._log_debug(f'Value {value!r} for <{name}> passed validation{stage_info}.')

    # ==== Helper log methods ====

    @staticmethod
    def _log_error(msg, exc_type=Exception):
        log.error(message=msg, exc_type=exc_type)

    @staticmethod
    def _log_error_with_fallback(
        msg,
        current=None,
        default=None,
        exc_type=Exception,
    ):
        if current is not None:
            msg += f' Keeping current {current!r}.'
        else:
            msg += f' Using default {default!r}.'
        log.error(message=msg, exc_type=exc_type)

    @staticmethod
    def _log_debug(msg):
        log.debug(message=msg)

    # ==== Suggestion and allowed value helpers ====

    @staticmethod
    def _suggest(key: str, allowed: set[str]):
        if not allowed:
            return None
        # Return the allowed key with smallest Levenshtein distance
        matches = difflib.get_close_matches(key, allowed, n=1)
        return matches[0] if matches else None

    @staticmethod
    def _build_suggestion(key: str, allowed: set[str]):
        s = Diagnostics._suggest(key, allowed)
        return f" Did you mean '{s}'?" if s else ''

    @staticmethod
    def _build_allowed(allowed, label='Allowed attributes'):
        # allowed may be a set, list, or other iterable
        if allowed:
            allowed_list = list(allowed)
            if len(allowed_list) <= 10:
                s = ', '.join(map(repr, sorted(allowed_list)))
                return f' {label}: {s}.'
            else:
                return f' ({len(allowed_list)} {label.lower()} not listed here).'
        return ''


#

# ---------------------- Validators ---------------------- #

# Runtime type checking decorator for validating those methods
# annotated with type hints, which are writable for the user, and
# which are not covered by custom validators for Parameter attribute
# types and content, implemented below.


def checktype(func):
    """Minimal wrapper to perform runtime type checking and log
    errors.
    """
    checked_func = typechecked(func)

    def wrapper(*args, **kwargs):
        try:
            return checked_func(*args, **kwargs)
        except TypeCheckError as err:
            log.error(message=str(err), exc_type=TypeError)
            return None

    return wrapper


# Advanced runtime custom validators for both Parameter attribute types
# and content, which are writable for the user.


class BaseValidator(ABC):
    """Abstract base class for all validators."""

    @abstractmethod
    def validated(self, value, name, default=None, current=None):
        """Return a validated value or fallback.
        Subclasses must implement this method.
        """
        raise NotImplementedError

    def _fallback(self, current=None, default=None):
        return current if current is not None else default


class TypeValidator(BaseValidator):
    """Ensures a value is of the expected Python type."""

    def __init__(self, expected_type):
        self.expected_type = expected_type

    def validated(self, value, name, default=None, current=None):
        if current is None and value is None:
            Diagnostics.none_value(name, default)
            return default
        if not isinstance(value, self.expected_type):
            expected_type = f'{self.expected_type.__name__}'
            Diagnostics.type_mismatch(
                name,
                value,
                expected_type,
                current=current,
                default=default,
            )
            return self._fallback(current, default)
        Diagnostics.validated(name, value, stage='type')

        return value


class RangeValidator(BaseValidator):
    """Ensures a numeric value lies within [ge, le]."""

    def __init__(self, *, ge=-np.inf, le=np.inf):
        self.ge, self.le = ge, le

    def validated(
        self,
        value,
        name,
        default=None,
        current=None,
    ):
        if current is None and value is None:
            Diagnostics.none_value(name, default)
            return default
        if not isinstance(value, (int, float, np.number)):
            Diagnostics.type_mismatch(
                name,
                value,
                expected_type='numeric',
                current=current,
                default=default,
            )
            return self._fallback(current, default)
        if not (self.ge <= value <= self.le):
            Diagnostics.range_mismatch(
                name,
                value,
                self.ge,
                self.le,
                current=current,
                default=default,
            )
            return self._fallback(current, default)
        Diagnostics.validated(name, value, stage='range')
        return value


class ChoiceValidator(BaseValidator):
    """Ensures that a value belongs to a predefined list of allowed
    choices.
    """

    def __init__(self, allowed):
        self.allowed = list(allowed)

    def validated(
        self,
        value,
        name,
        default=None,
        current=None,
    ):
        if current is None and value is None:
            Diagnostics.none_value(name, default)
            return default
        if value not in self.allowed:
            Diagnostics.choice_mismatch(
                name,
                value,
                self.allowed,
                current=current,
                default=default,
            )
            return self._fallback(current, default)
        Diagnostics.validated(name, value, stage='choice')
        return value


class RegexValidator(BaseValidator):
    """Ensures that a string value matches a given regular
    expression.
    """

    def __init__(self, pattern):
        self.pattern = re.compile(pattern)

    def validated(self, value, name, default=None, current=None):
        if current is None and value is None:
            Diagnostics.none_value(name, default)
            return default
        if not isinstance(value, str):
            Diagnostics.type_mismatch(
                name,
                value,
                expected_type='str',
                current=current,
                default=default,
            )
            return self._fallback(current, default)
        if not self.pattern.fullmatch(value):
            Diagnostics.regex_mismatch(
                name,
                value,
                self.pattern.pattern,
                current=current,
                default=default,
            )
            return self._fallback(current, default)
        Diagnostics.validated(name, value, stage='regex')
        return value


# ---------------------- Identity ---------------------- #


class Identity:
    """Hierarchical identity resolver for datablock/category/entry
    relationships.
    """

    def __init__(
        self,
        *,
        owner: object,
        datablock_entry: Callable | None = None,
        category_code: str | None = None,
        category_entry: Callable | None = None,
    ):
        self._owner = owner
        self._datablock_entry = datablock_entry
        self._category_code = category_code
        self._category_entry = category_entry

    def _resolve_up(self, attr: str, visited=None):
        """Resolve attribute by walking up parent chain safely."""
        if visited is None:
            visited = set()
        if id(self) in visited:
            return None
        visited.add(id(self))

        # Direct callable or value on self
        value = getattr(self, f'_{attr}', None)
        if callable(value):
            return value()
        if isinstance(value, str):
            return value

        # Climb to parent if available
        parent = getattr(self._owner, '__dict__', {}).get('_parent')
        if parent and hasattr(parent, '_identity'):
            return parent._identity._resolve_up(attr, visited)
        return None

    @property
    def datablock_entry_name(self):
        return self._resolve_up('datablock_entry')

    @datablock_entry_name.setter
    def datablock_entry_name(self, func: callable):
        self._datablock_entry = func

    @property
    def category_code(self):
        return self._resolve_up('category_code')

    @category_code.setter
    def category_code(self, value: str):
        self._category_code = value

    @property
    def category_entry_name(self):
        return self._resolve_up('category_entry')

    @category_entry_name.setter
    def category_entry_name(self, func: callable):
        self._category_entry = func


# ---------------------- GuardedBase ---------------------- #


class GuardedBase(ABC):
    """Base class enforcing controlled attribute access and parent
    linkage.
    """

    def __init__(self):
        self._diagnoser = Diagnostics()
        self._identity = Identity(owner=self)

    def __str__(self) -> str:
        return f'<{self.unique_name}>'

    def __repr__(self) -> str:
        return self.__str__()

    def __getattr__(self, key: str):
        cls = type(self)
        allowed = cls._public_attrs()
        if key not in allowed:
            self._diagnoser.attr_error(
                self.unique_name,
                key,
                allowed,
                label='Allowed readable/writable',
            )

    def __setattr__(self, key: str, value):
        # Always allow private or special attributes without diagnostics
        if key.startswith('_'):
            object.__setattr__(self, key, value)
            return

        # Handle public attributes with diagnostics
        cls = type(self)
        # Prevent modification of read-only attributes
        if key in cls._public_readonly_attrs():
            self._diagnoser.readonly_error(
                self.unique_name,
                key,
            )
            return
        # Prevent assignment to unknown attributes
        # Show writable attributes only as allowed
        if key not in cls._public_attrs():
            allowed = cls._public_writable_attrs()
            self._diagnoser.attr_error(
                self.unique_name,
                key,
                allowed,
                label='Allowed writable',
            )
            return

        self._assign_attr(key, value)

    def _assign_attr(self, key, value):
        """Low-level assignment with parent linkage."""
        object.__setattr__(self, key, value)
        if key != '_parent' and isinstance(value, GuardedBase):
            object.__setattr__(value, '_parent', self)

    @classmethod
    def _iter_properties(cls):
        """Iterate over all public properties defined in the class
        hierarchy.

        Yields:
            tuple[str, property]: Each (key, property) pair for public
                attributes.
        """
        for base in cls.mro():
            for key, attr in base.__dict__.items():
                if key.startswith('_') or not isinstance(attr, property):
                    continue
                yield key, attr

    @classmethod
    def _public_attrs(cls):
        """All public properties (read-only + writable)."""
        return {key for key, _ in cls._iter_properties()}

    @classmethod
    def _public_readonly_attrs(cls):
        """Public properties without a setter."""
        return {key for key, prop in cls._iter_properties() if prop.fset is None}

    @classmethod
    def _public_writable_attrs(cls) -> set[str]:
        """Public properties with a setter."""
        return {key for key, prop in cls._iter_properties() if prop.fset is not None}

    # TODO: Check if needed
    @property
    def _log_name(self):
        return type(self).__name__

    @property
    def unique_name(self):
        return type(self).__name__

    @property
    @abstractmethod
    def parameters(self):
        """Return a list of parameter objects (to be implemented by
        subclasses).
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def as_cif(self) -> str:
        """Return CIF representation of this object (to be implemented
        by subclasses).
        """
        raise NotImplementedError


# ---------------------- Attribute specifications -------------------- #


class AttributeSpec:
    """Holds metadata and validators for a single attribute."""

    def __init__(
        self,
        *,
        value=None,
        type_=None,
        default=None,
        content_validator=None,
    ):
        self.value = value
        self.default = default
        self._type_validator = TypeValidator(type_) if type_ else None
        self._content_validator = content_validator

    def validated(self, value, name, current=None):
        val = value
        if self._type_validator:
            val = self._type_validator.validated(
                val,
                name,
                default=self.default,
                current=current,
            )
        if self._content_validator:
            val = self._content_validator.validated(
                val,
                name,
                default=self.default,
                current=current,
            )
        return val


# ---------------------- Parameter ---------------------- #


class GenericDescriptorBase(GuardedBase):
    """..."""

    _BOOL_SPEC_TEMPLATE = AttributeSpec(
        type_=bool,
        default=False,
    )

    def __init__(
        self,
        *,
        value_spec: AttributeSpec,
        name: str,
        description: str = None,
    ):
        super().__init__()

        expected_type = getattr(self, '_value_type', None)

        if expected_type:
            user_type = (
                value_spec._type_validator.expected_type
                if value_spec._type_validator is not None
                else None
            )
            if user_type and user_type is not expected_type:
                Diagnostics.type_override_error(
                    type(self).__name__,
                    expected_type,
                    user_type,
                )
            else:
                # Enforce descriptor's own type if not already defined
                value_spec._type_validator = TypeValidator(expected_type)

        self._value_spec = value_spec
        self._name = name
        self._description = description
        self._uid: str = self._generate_uid()
        # UidMapHandler.get().add_to_uid_map(self)

        # Initial validated states
        self._value = self._value_spec.validated(
            value_spec.value,
            name=self.unique_name,
        )

    def __str__(self) -> str:
        return f'<{self.unique_name} = {self.value!r}>'

    @staticmethod
    def _generate_uid() -> str:
        length: int = 16
        return ''.join(secrets.choice(string.ascii_lowercase) for _ in range(length))

    @property
    def name(self) -> str:
        return self._name

    @property
    def unique_name(self):
        parts = [
            self._identity.datablock_entry_name,
            self._identity.category_code,
            self._identity.category_entry_name,
            self.name,
        ]
        return '.'.join(p for p in parts if p is not None)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, v):
        self._value = self._value_spec.validated(
            v,
            name=self.unique_name,
            current=self._value,
        )

    @property
    def description(self):
        return self._description

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
    _value_type = str

    def __init__(
        self,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)


class GenericDescriptorFloat(GenericDescriptorBase):
    _value_type = float

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


class GenericParameter(GenericDescriptorFloat):
    """..."""

    def __init__(
        self,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)

        # Initial validated states
        self._free_spec = self._BOOL_SPEC_TEMPLATE
        self._free = self._free_spec.default
        self._uncertainty_spec = AttributeSpec(
            type_=float,
            content_validator=RangeValidator(ge=0),
        )
        self._uncertainty = self._uncertainty_spec.default
        self._fit_min_spec = AttributeSpec(type_=float, default=-np.inf)
        self._fit_min = self._fit_min_spec.default
        self._fit_max_spec = AttributeSpec(type_=float, default=np.inf)
        self._fit_max = self._fit_max_spec.default
        self._start_value_spec = AttributeSpec(type_=float, default=0.0)
        self._start_value = self._start_value_spec.default
        self._constrained_spec = self._BOOL_SPEC_TEMPLATE
        self._constrained = self._constrained_spec.default

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
    def _minimizer_uid(self):
        """Return variant of uid safe for minimizer engines."""
        # return self.unique_name.replace('.', '__')
        return self.uid

    @property
    def name(self) -> str:
        return self._name

    @property
    def unique_name(self):
        parts = [
            self._identity.datablock_entry_name,
            self._identity.category_code,
            self._identity.category_entry_name,
            self.name,
        ]
        return '.'.join(p for p in parts if p is not None)

    @property
    def constrained(self):
        return self._constrained

    @property
    def free(self):
        return self._free

    @free.setter
    def free(self, v):
        self._free = self._free_spec.validated(
            v, name=f'{self.unique_name}.free', current=self._free
        )

    @property
    def uncertainty(self):
        return self._free

    @uncertainty.setter
    def uncertainty(self, v):
        self._uncertainty = self._uncertainty_spec.validated(
            v, name=f'{self.unique_name}.uncertainty', current=self._uncertainty
        )

    @property
    def fit_min(self):
        return self._fit_min

    @fit_min.setter
    def fit_min(self, v):
        self._fit_min = self._fit_min_spec.validated(
            v, name=f'{self.unique_name}.fit_min', current=self._fit_min
        )

    @property
    def fit_max(self):
        return self._fit_max

    @fit_max.setter
    def fit_max(self, v):
        self._fit_max = self._fit_max_spec.validated(
            v, name=f'{self.unique_name}.fit_max', current=self._fit_max
        )


class CifHandler:
    def __init__(self, *, names: list[str]) -> None:
        self._names = names
        self._owner = None  # will be linked later

    def attach(self, owner):
        """Attach handler to its owning descriptor or parameter."""
        self._owner = owner

    @property
    def names(self):
        return self._names

    @property
    def uid(self) -> str | None:
        """Return CIF UID derived from the owner's unique name."""
        if self._owner is None:
            return None
        return self._owner.unique_name


class DescriptorStr(GenericDescriptorStr):
    def __init__(
        self,
        *,
        cif_handler: CifHandler,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._cif_handler = cif_handler
        self._cif_handler.attach(self)


class DescriptorFloat(GenericDescriptorFloat):
    def __init__(
        self,
        *,
        cif_handler: CifHandler,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._cif_handler = cif_handler
        self._cif_handler.attach(self)


class Parameter(GenericParameter):
    def __init__(
        self,
        *,
        cif_handler: CifHandler,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._cif_handler = cif_handler
        self._cif_handler.attach(self)


# ---------------------- ... ---------------------- #


class CollectionBase(GuardedBase):
    def __init__(self, item_type) -> None:
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
        item._parent = self  # Explicitly set the parent for the item
        self._items.append(item)
        self._rebuild_index()

    def __delitem__(self, name: str) -> None:
        # Remove from _items by identity entry name
        for i, item in enumerate(self._items):
            if item._identity.category_entry_name == name:
                object.__setattr__(item, '_parent', None)  # Unlink the parent before removal
                del self._items[i]
                self._rebuild_index()
                return
        raise KeyError(name)

    def __iter__(self):
        return iter(self._items)

    def __len__(self) -> int:
        return len(self._items)

    def _key_for(self, item):
        """Private helper to get the key for an item."""
        return item._identity.category_entry_name or item._identity.datablock_entry_name

    def _rebuild_index(self) -> None:
        self._index.clear()
        for item in self._items:
            key = self._key_for(item)
            if key:
                self._index[key] = item

    def keys(self):
        return (self._key_for(item) for item in self._items)

    def values(self):
        return (item for item in self._items)

    def items(self):
        return ((self._key_for(item), item) for item in self._items)

    @property
    def names(self):
        """Return a list of all item keys in the collection."""
        return list(self.keys())


class CategoryItem(GuardedBase):
    """Base class for items in a category collection."""

    def __str__(self) -> str:
        """Human-readable representation of this component."""
        name = self._log_name
        params = ', '.join(f'{p.name}={p.value!r}' for p in self.parameters)
        return f'<{name} ({params})>'

    @property
    def unique_name(self):
        parts = [
            self._identity.datablock_entry_name,
            self._identity.category_code,
            self._identity.category_entry_name,
        ]
        return '.'.join(p for p in parts if p is not None)

    @property
    def parameters(self):
        return [v for v in self.__dict__.values() if isinstance(v, GenericDescriptorBase)]

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
    def unique_name(self):
        return None

    @property
    def parameters(self):
        """All parameters from all items in this collection."""
        params = []
        for item in self._items:
            params.extend(item.parameters)
        return params

    @property
    def as_cif(self) -> str:
        """Return CIF representation of this object."""
        if not self:
            return ''  # Empty collection
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

    @typechecked
    def add(self, item) -> None:
        """Add an item to the collection."""
        self[item._identity.category_entry_name] = item

    @typechecked
    def add_from_args(self, *args, **kwargs) -> None:
        """Create and add a new child instance from the provided
        arguments.
        """
        child_obj = self._item_type(*args, **kwargs)
        self.add(child_obj)


class DatablockItem(GuardedBase):
    """Base class for items in a datablock collection."""

    def __str__(self) -> str:
        """Human-readable representation of this component."""
        name = self._log_name
        items = self._items
        return f'<{name} ({items})>'

    @property
    def unique_name(self):
        return self._identity.datablock_entry_name

    @property
    def parameters(self):
        """All parameters from all categories contained in this
        datablock.
        """
        params = []
        for v in self.__dict__.values():
            if isinstance(v, (CategoryItem, CategoryCollection)):
                params.extend(v.parameters)
        return params

    @property
    def as_cif(self) -> str:
        """Return CIF representation of this object."""
        lines = [f'data_{self._identity.datablock_entry_name}']
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
    def unique_name(self):
        return None

    @property
    def parameters(self):
        """All parameters from all datablocks in this collection."""
        params = []
        for db in self._items:
            params.extend(db.parameters)
        return params

    # was in class AbstractDatablock(ABC):
    @property
    def fittable_parameters(self) -> list:
        return [p for p in self.parameters if isinstance(p, Parameter) and not p.constrained]

    # was in class AbstractDatablock(ABC):
    @property
    def free_parameters(self) -> list:
        return [p for p in self.fittable_parameters if p.free]

    @property
    def as_cif(self) -> str:
        """Return CIF representation of this object."""
        parts = [
            datablock.as_cif for datablock in self.values() if isinstance(datablock, DatablockItem)
        ]
        return '\n'.join(parts)

    @typechecked
    def add(self, item) -> None:
        """Add an item to the collection."""
        self[item._identity.datablock_entry_name] = item


class Cell(CategoryItem):
    def __init__(self, *, length_a=None):
        super().__init__()

        self._length_a = Parameter(
            value_spec=AttributeSpec(
                value=length_a,
                type_=str,
                default=10.0,
                content_validator=RangeValidator(ge=0, le=1000),
            ),
            name='length_a',
            description='Length of the a-axis of the unit cell.',
            units='Å',
            cif_handler=CifHandler(names=['_cell.length_a']),
        )

    @property
    def length_a(self) -> Parameter:
        """Parameter representing the a-axis length of the unit cell."""
        return self._length_a

    @length_a.setter
    def length_a(self, v):
        """Assign a raw value to length_a (validated internally)."""
        self._length_a.value = v


# ---------------------- Example usage ---------------------- #

if __name__ == '__main__':
    c = Cell()

    c.length_a.value = 1.234
    log.info(f'c.length_a.value: {c.length_a.value}')

    c.length_a.value = -5.5
    log.info(f'c.length_a.value: {c.length_a.value}')

    c.length_a.value = 'xyz'
    log.info(f'c.length_a.value: {c.length_a.value}')

    c.length_a.free = True
    log.info(f'c.length_a.free: {c.length_a.free}')

    c.length_a.free = 'oops'
    log.info(f'c.length_a.free: {c.length_a.free}')

    c.length_a = 'xyz'
    log.info(f'c.length_a.value (after direct assign attempt): {c.length_a.value}')

    c_bad = Cell(length_a='xyz')
    log.info(f'c_bad.length_a.value: {c_bad.length_a.value}')

    c_ok = Cell(length_a=2.5)
    log.info(f'c_ok.length_a.value: {c_ok.length_a.value}')

    c_ok.length_a.description = 'read-only'
    log.info(f'c_ok.length_a.description: {c_ok.length_a.description}')

    c_ok.length_a.aaa = 'aaa'
    log.info(f'c_ok.length_a.aaa: {c_ok.length_a.aaa}')

    log.info(f'c_ok.length_a.bbb: {c_ok.length_a.bbb}')

    log.info(f'c_ok.length_a.fre: {c_ok.length_a.fre}')

    log.info(c.as_cif)
    log.info(c.length_a.as_cif)

    log.info(c.length_a._cif_handler.uid)
