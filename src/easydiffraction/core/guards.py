from __future__ import annotations

import difflib
import inspect
from abc import ABC
from abc import abstractmethod
from typing import Any

from easydiffraction import log


class GuardedBase(ABC):
    @abstractmethod
    def __str__(self) -> str:
        """Subclasses must implement human-readable representation."""
        raise NotImplementedError

    def __repr__(self) -> str:
        # Reuse __str__; subclasses only override if needed
        return self.__str__()

    def __setattr__(self, key, value):
        """Subclasses must implement controlled attribute setting."""
        raise NotImplementedError


class DiagnosticsMixin:
    """Centralized error and warning reporting for guarded objects.

    Provides common diagnostics for attribute access, type mismatches,
    range and allowed-values violations, and read-only enforcement. Used
    as a base for all core model objects to ensure consistent
    error/warning reporting.
    """

    def _readonly_error(self) -> None:
        """Error for attempts to modify a read-only attribute."""
        caller = inspect.stack()[1].function
        message = f'Attribute {caller} of {self.uid} is read-only.'
        log.error(message, exc_type=AttributeError)

    def _setattr_error(self, key: str, allowed: set[str] | None = None) -> None:
        """Error for attempts to set a non-existent attribute."""
        suggestion = difflib.get_close_matches(key, allowed or [], n=1)
        hint = f' Did you mean "{suggestion[0]}"?' if suggestion else ''
        allowed_list = f' Allowed: {sorted(allowed)}' if allowed else ''
        message = f'Cannot set "{key}" on {type(self).__name__}.{hint}{allowed_list}'
        log.error(message, exc_type=AttributeError)

    def _getattr_error(self, key: str, allowed: set[str] | None = None) -> None:
        """Error for attempts to get a non-existent attribute."""
        suggestion = difflib.get_close_matches(key, allowed or [], n=1)
        hint = f' Did you mean "{suggestion[0]}"?' if suggestion else ''
        allowed_list = f' Allowed: {sorted(allowed)}' if allowed else ''
        message = f'Cannot get "{key}" on {type(self).__name__}.{hint}{allowed_list}'
        log.error(message, exc_type=AttributeError)

    def _type_warning(self, key: str, expected: type, got: Any) -> None:
        """Warning for wrong type assignment (respects Logger mode)."""
        message = f'Got type {type(got).__name__} for {key}. Allowed: {expected.__name__}.'
        log.warning(message, exc_type=UserWarning)

    def _allowed_values_warning(self, key: str, value: Any, allowed: list[Any]) -> None:
        """Warning for invalid allowed-values assignment (respects
        Logger mode).
        """
        suggestion = difflib.get_close_matches(str(value), [str(a) for a in allowed], n=1)
        hint = f' Did you mean "{suggestion[0]}"?' if suggestion else ''
        allowed_list = f' Allowed: {allowed}' if allowed else ''
        message = f'Got "{value}" for {key}.{hint}{allowed_list}'
        log.warning(message, exc_type=UserWarning)

    def _range_warning(self, key: str, value: Any, min_val: Any, max_val: Any) -> None:
        """Warning for value outside allowed range."""
        message = f'Value {value} for {key} is outside [{min_val}, {max_val}].'
        log.warning(message, exc_type=UserWarning)


class AttributeAccessGuardMixin:
    """Blocks adding unknown attributes and caches the allowed set.

    The union of ``_class_public_attrs`` across the class MRO and the
    instance's current public ``__dict__`` keys defines what can be
    assigned via normal attribute access.
    """

    _class_public_attrs: set[str] = set()
    _merged_public_attrs: set[str] = set()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        allowed = set()
        for base in cls.__mro__:
            allowed |= getattr(base, '_class_public_attrs', set())
        cls._merged_public_attrs = allowed

    def __getattr__(self, key: str) -> Any:
        """Fallback for missing attribute access (emits helpful
        diagnostics).
        """
        allowed = type(self)._merged_public_attrs
        self._getattr_error(key, allowed)


class AttributeSetGuardMixin:
    """Provides a reusable guard for __setattr__ implementations.

    - Private attributes (starting with '_') are always allowed.
    - Public attributes must be in `_merged_public_attrs`.
    - Delegates error reporting to DiagnosticsMixin._setattr_error.
    """

    def _guarded_setattr(self, key: str, value: Any) -> bool:
        """Helper for __setattr__ implementations.

        Returns True if the attribute was handled (set or error), False
        if the caller should continue with custom logic.
        """
        if key.startswith('_'):
            object.__setattr__(self, key, value)
            return True
        allowed = type(self)._merged_public_attrs
        if key not in allowed:
            self._setattr_error(key, allowed)
            return True
        return False
