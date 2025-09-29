# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import difflib
import inspect
from abc import ABC
from abc import abstractmethod
from typing import Any

from easydiffraction import log


class DiagnosticsMixin:
    """Centralized error and warning reporting for guarded objects.

    Provides common diagnostics for attribute access, type mismatches,
    range and allowed-values violations, and read-only enforcement. Used
    as a base for all core model objects to ensure consistent
    error/warning reporting.
    """

    def _readonly_error(self, key=None) -> None:
        """Error for attempts to modify a read-only attribute."""
        caller = key if key is not None else inspect.stack()[1].function
        obj_type = type(self).__name__
        obj_name = self.full_name
        message = f"Attribute '{caller}' of '{obj_type}' ({obj_name}) is read-only"
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
        message = f'Got type {type(got).__name__} for {key}. Allowed: {expected.__name__}'
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
        message = f'Value {value} for {key} is outside [{min_val}, {max_val}]'
        log.warning(message, exc_type=UserWarning)


class AttributeGuardMixin:
    """Reusable mixin enforcing controlled __setattr__ rules.

    - Private attributes (names starting with '_') are always allowed.
    - Public attributes must be whitelisted in `_merged_public_attrs`,
       which is the union of `_class_public_attrs` across the MRO.
    - Error reporting is delegated to DiagnosticsMixin (e.g.,
       _setattr_error).
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

    def _validate_setattr(self, key: str) -> bool:
        """Return True if assignment is allowed (private or
        whitelisted).

        Emits a helpful error and returns False otherwise.
        """
        # Private attributes are always allowed
        if key.startswith('_'):
            return True
        # Check against allowed public attributes
        allowed = type(self)._merged_public_attrs
        if key not in allowed:
            self._setattr_error(key, allowed)
            return False
        # Check if it's a property without a setter (read-only)
        attr = getattr(type(self), key, None)
        if isinstance(attr, property) and attr.fset is None:
            self._readonly_error(key)
            return False
        return True


class GuardedBase(ABC, AttributeGuardMixin, DiagnosticsMixin):
    _class_public_attrs = {
        'full_name',
    }

    @property
    @abstractmethod
    def full_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def __str__(self) -> str:
        """Subclasses must implement human-readable representation."""
        raise NotImplementedError

    def __repr__(self) -> str:
        # Reuse __str__; subclasses only override if needed
        return self.__str__()

    def __setattr__(self, key: str, value: Any) -> None:
        """Default controlled attribute setting.

        Subclasses should call `super().__setattr__` to preserve guard
        checks before adding custom logic.
        """
        if not self._validate_setattr(key):
            return
        object.__setattr__(self, key, value)
