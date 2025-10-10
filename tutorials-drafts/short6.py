import difflib
import re
from abc import ABC
from abc import abstractmethod
from typing import Callable

import numpy as np

from easydiffraction.utils.logging import log

# ---------------------- Diagnostics ---------------------- #


class Diagnostics:
    """Centralized logger for attribute errors and validation
    guidance.
    """

    # ==== Attribute diagnostics ====

    @staticmethod
    def readonly_error(name: str, key: str | None = None):
        Diagnostics._log_error(
            f"Cannot modify read-only attribute '{key}' of <{name}>.",
            exc_type=AttributeError,
        )

    @staticmethod
    def attr_error(name: str, key: str, allowed: set[str]):
        suggestion = Diagnostics._build_suggestion(key, allowed)
        hint = suggestion or Diagnostics._build_allowed(allowed)
        Diagnostics._log_error(
            f"Unknown attribute '{key}' of <{name}>.{hint}",
            exc_type=AttributeError,
        )

    # ==== Validation diagnostics ====

    @staticmethod
    def type_mismatch(name: str, value, expected_type, current=None, default=None):
        msg = (
            f'Type mismatch for <{name}>. '
            f'Expected `{expected_type}`, got `{type(value).__name__}` ({value!r}).'
        )
        Diagnostics._log_with_fallback(msg, current=current, default=default, exc_type=TypeError)

    @staticmethod
    def range_mismatch(name: str, value, ge, le, current=None, default=None):
        msg = f'Value mismatch for <{name}>. Provided {value!r} outside [{ge}, {le}].'
        Diagnostics._log_with_fallback(msg, current=current, default=default, exc_type=TypeError)

    @staticmethod
    def choice_mismatch(name: str, value, allowed, current=None, default=None):
        msg = f'Value mismatch for <{name}>. Provided {value!r} is unknown.'
        if allowed is not None:
            msg += Diagnostics._build_allowed(allowed)
        Diagnostics._log_with_fallback(msg, current=current, default=default, exc_type=TypeError)

    @staticmethod
    def regex_mismatch(name: str, value, pattern, current=None, default=None):
        msg = (
            f"Value mismatch for <{name}>. Provided {value!r} does not match pattern '{pattern}'."
        )
        Diagnostics._log_with_fallback(msg, current=current, default=default, exc_type=TypeError)

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
    def _log_with_fallback(msg, current=None, default=None, exc_type=Exception):
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
    def _build_allowed(allowed):
        # allowed may be a set, list, or other iterable
        if allowed:
            allowed_list = list(allowed)
            if len(allowed_list) <= 10:
                s = ', '.join(map(repr, sorted(allowed_list)))
                return f' Allowed: {s}.'
            else:
                return f' ({len(allowed_list)} allowed values not listed here).'
        return ''


# ---------------------- Validators ---------------------- #


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
            Diagnostics.type_mismatch(name, value, expected_type, current=current, default=default)
            return self._fallback(current, default)
        Diagnostics.validated(name, value, stage='type')

        return value


class RangeValidator(BaseValidator):
    """Ensures a numeric value lies within [ge, le]."""

    def __init__(self, *, ge=-np.inf, le=np.inf):
        self.ge, self.le = ge, le

    def validated(self, value, name, default=None, current=None):
        if current is None and value is None:
            Diagnostics.none_value(name, default)
            return default
        if not isinstance(value, (int, float, np.number)):
            Diagnostics.type_mismatch(name, value, 'numeric', current=current, default=default)
            return self._fallback(current, default)
        if not (self.ge <= value <= self.le):
            Diagnostics.range_mismatch(
                name, value, self.ge, self.le, current=current, default=default
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

    def validated(self, value, name, default=None, current=None):
        if current is None and value is None:
            Diagnostics.none_value(name, default)
            return default
        if value not in self.allowed:
            Diagnostics.choice_mismatch(
                name, value, self.allowed, current=current, default=default
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
            Diagnostics.type_mismatch(name, value, 'str', current=current, default=default)
            return self._fallback(current, default)
        if not self.pattern.fullmatch(value):
            Diagnostics.regex_mismatch(
                name, value, self.pattern.pattern, current=current, default=default
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
            self._diagnoser.attr_error(self.unique_name, key, allowed)

    def __setattr__(self, key: str, value):
        # Always allow private or special attributes without diagnostics
        if key.startswith('_'):
            object.__setattr__(self, key, value)
            return

        # Handle public attributes with diagnostics
        cls = type(self)
        allowed = cls._public_attrs()
        if key in cls._public_readonly_attrs():
            self._diagnoser.readonly_error(self.unique_name, key)
            return
        if key not in allowed:
            self._diagnoser.attr_error(self.unique_name, key, allowed)
            return

        self._assign_attr(key, value)

    def _assign_attr(self, key, value):
        """Low-level assignment with parent linkage."""
        object.__setattr__(self, key, value)
        if key != '_parent' and isinstance(value, GuardedBase):
            object.__setattr__(value, '_parent', self)

    @classmethod
    def _iter_properties(cls):
        for base in cls.mro():
            for key, attr in base.__dict__.items():
                if key.startswith('_') or not isinstance(attr, property):
                    continue
                yield key, attr

    @classmethod
    def _public_attrs(cls):
        return {key for key, _ in cls._iter_properties()}

    @classmethod
    def _public_readonly_attrs(cls):
        return {key for key, prop in cls._iter_properties() if prop.fset is None}

    @property
    def _log_name(self):
        return type(self).__name__

    @property
    def unique_name(self):
        return type(self).__name__


# ---------------------- Attribute specifications -------------------- #


class AttributeSpec:
    """Holds metadata and validators for a single attribute."""

    def __init__(self, *, value=None, type_=None, default=None, content_validator=None):
        self.value = value
        self.default = default
        self._type_validator = TypeValidator(type_) if type_ else None
        self._content_validator = content_validator

    def validated(self, value, name, current=None):
        val = value
        if self._type_validator:
            val = self._type_validator.validated(val, name, default=self.default, current=current)
        if self._content_validator:
            val = self._content_validator.validated(
                val, name, default=self.default, current=current
            )
        return val


# ---------------------- Parameter ---------------------- #


class Parameter(GuardedBase):
    """A parameter with validated value, free flag, and optional
    description.
    """

    _BOOL_SPECS_TEMPLATE = AttributeSpec(type_=bool, default=False)

    def __init__(
        self,
        *,
        value_spec: AttributeSpec,
        name: str,
        description: str = None,
    ):
        super().__init__()

        self._value_spec = value_spec
        self._name = name
        self._description = description

        # Initial validated states
        self._value = self._value_spec.validated(value_spec.value, name=self.unique_name)
        self._free_spec = self._BOOL_SPECS_TEMPLATE
        self._free = self._free_spec.default

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
        self._value = self._value_spec.validated(v, name=self.unique_name, current=self._value)

    @property
    def free(self):
        return self._free

    @free.setter
    def free(self, v):
        self._free = self._free_spec.validated(
            v, name=f'{self.unique_name}.free', current=self._free
        )

    @property
    def description(self):
        return self._description


# ---------------------- Example class ---------------------- #


class Cell(GuardedBase):
    def __init__(self, *, length_a=None):
        super().__init__()

        self._length_a = Parameter(
            value_spec=AttributeSpec(
                value=length_a,
                type_=float,
                default=10.0,
                content_validator=RangeValidator(ge=0, le=1000),
            ),
            name='length_a',
            description='Length of the a-axis of the unit cell.',
        )

    @property
    def unique_name(self):
        parts = [
            self._identity.datablock_entry_name,
            self._identity.category_code,
            self._identity.category_entry_name,
        ]
        return '.'.join(p for p in parts if p is not None)

    @property
    def length_a(self) -> Parameter:
        """Access the Parameter object for the a-axis length."""
        return self._length_a

    @length_a.setter
    def length_a(self, v):
        """Assign a raw value (validated by Parameter.value)."""
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
