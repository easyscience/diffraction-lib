from __future__ import annotations

import difflib
import re
from abc import ABC
from abc import abstractmethod
from functools import wraps
from typing import Any
from typing import Callable
from typing import Optional
from typing import ParamSpec
from typing import TypeVar

import numpy as np
from typeguard import TypeCheckError
from typeguard import typechecked

from easydiffraction import log

P = ParamSpec('P')
R = TypeVar('R')


def checktype(func: Callable[P, R]) -> Callable[P, Optional[R]]:
    """Wrapper around @typechecked that catches and logs type errors
    during runtime.
    """
    # TODO: It is not supposed to be used for attribute .value of the
    #  GenericDescriptorBase. In there, the typecheck is done via
    #  Validator. Consider split for typechecking and validation. But
    #  need to cover typechecking during init, setter of parameter
    #  and setter of parameter.value...

    # TODO: Consider messaging via Diagnostics
    checked_func = typechecked(func)

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> Optional[R]:
        try:
            return checked_func(*args, **kwargs)
        except TypeCheckError as err:
            first_arg = args[0]
            from easydiffraction.core.parameters import GenericDescriptorBase

            if isinstance(first_arg, GenericDescriptorBase):
                new = args[1]
                new_type = type(new).__name__
                expected_type = err.args[0].split(' ')[-1]
                unique_name = first_arg.unique_name
                attr_name = func.__name__
                name = f'{unique_name}.{attr_name}'
                message = (
                    f'Type mismatch for <{name}>. '
                    f'Provided {new!r} ({new_type}) is not {expected_type}'
                )
            else:
                message = f'Type mismatch in {func.__qualname__}: {err}'
            log.error(message, exc_type=TypeError)

    return wrapper


class Validator(ABC):
    """Abstract validator base class with global strictness control."""

    # TODO: Consider messaging via Diagnostics

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
            log.debug(message)
            return self.default

        if not isinstance(new, (float, int, np.floating, np.integer)):
            message = (
                f'Type mismatch for <{name}>. '
                f'Provided {new!r} ({type(new).__name__}) is not float.'
            )
            log.error(message, exc_type=TypeError)
            return current if current is not None else self.default

        if (self.ge is not None and new < self.ge) or (self.le is not None and new > self.le):
            message = (
                f'Value mismatch for <{name}>. '
                f'Provided {new} is outside of [{self.ge}, {self.le}].'
            )
            log.error(message, exc_type=ValueError)
            return current if current is not None else self.default

        log.debug(f'Setting <{name}> to validated {new!r}.')
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
            log.debug(message)
            return self.default

        if new not in self.allowed_values:
            message = f'Value mismatch for <{name}>. Provided {new!r} is unknown.'
            log.error(message, exc_type=ValueError)
            return current if current is not None else self.default

        log.debug(f'Setting <{name}> to validated {new!r}.')
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
            log.debug(message)
            return self.default

        if not isinstance(new, str):
            message = (
                f'Type mismatch for <{name}>. '
                f'Provided {new!r} ({type(new).__name__}) is not string.'
            )
            log.error(message, exc_type=TypeError)
            return current if current is not None else self.default

        if not self._regex.match(new):
            message = (
                f'Value mismatch for <{name}>. '
                f"Provided {new!r} does not match pattern '{self.pattern}'."
            )
            log.error(message, exc_type=ValueError)
            return current if current is not None else self.default

        log.debug(f'Setting <{name}> to validated {new!r}.')
        return new


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
            s = f'{sorted(allowed)}'[1:-1]  # strip brackets
            return f' Allowed: {s}.'
        return ''


class Identity:
    """Dynamic hierarchical identity resolving through parent chain
    safely.
    """

    def __init__(
        self,
        *,
        owner: object,
        datablock: Callable[[], str] | None = None,
        category: str | None = None,
        entry: Callable[[], str] | None = None,
    ) -> None:
        self._owner = owner
        self._datablock = datablock  # TODO: Rename to datablock_entry
        self._category = category
        self._entry = entry  # TODO: Rename to category_entry

    def _resolve_up(self, attr: str, visited=None):
        """Resolve an attribute by walking up the parent chain
        safely.
        """
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
        return self._resolve_up('datablock')

    @datablock_entry_name.setter
    def datablock_entry_name(self, func: Callable[[], str]) -> None:
        self._datablock = func

    @property
    def category_code(self):
        return self._resolve_up('category')

    @category_code.setter
    def category_code(self, value: str) -> None:
        self._category = value

    @property
    def category_entry_name(self):
        return self._resolve_up('entry')

    @category_entry_name.setter
    def category_entry_name(self, func: Callable[[], str]) -> None:
        self._entry = func


class GuardedBase(ABC):
    """Base class providing attribute guarding and automatic parent
    linkage.
    """

    def __init__(self) -> None:
        self._diagnoser: Diagnostics = Diagnostics()
        self._identity: Identity = Identity(owner=self)

    def __getattr__(self, key: str):
        cls = type(self)
        if key not in cls._public_attrs():
            name = self.unique_name
            allowed = cls._public_attrs()
            self._diagnoser.attr_error(name, key, allowed)

    def __setattr__(self, key: str, value: Any):
        # Allow private attributes
        if key.startswith('_'):
            self._assign_attr(key, value)
            return

        # Handle public attributes with diagnostics
        cls = type(self)
        name = self.unique_name

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
        return object.__getattribute__(self, '__dict__').get('_parent')

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
