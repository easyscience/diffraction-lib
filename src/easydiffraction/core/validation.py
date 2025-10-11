# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

import functools
import re
from abc import ABC
from abc import abstractmethod
from enum import Enum

import numpy as np
from typeguard import TypeCheckError
from typeguard import typechecked

from easydiffraction.core.diagnostics import Diagnostics
from easydiffraction.utils.logging import log

# ==============================================================
# Shared constants
# ==============================================================


class DataTypes(Enum):
    NUMERIC = (int, float, np.integer, np.floating, np.number)
    STRING = (str,)
    BOOL = (bool,)
    ANY = (object,)  # fallback for unconstrained

    def __str__(self):
        return self.name.lower()

    @property
    def expected_type(self):
        """Convenience alias for tuple of allowed Python types."""
        return self.value


# Runtime type checking decorator for validating those methods
# annotated with type hints, which are writable for the user, and
# which are not covered by custom validators for Parameter attribute
# types and content, implemented below.


def checktype(func=None, *, context=None):
    """Minimal wrapper to perform runtime type checking and log errors.

    Optionally prepends context to log message.
    """

    def decorator(f):
        checked_func = typechecked(f)

        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            try:
                return checked_func(*args, **kwargs)
            except TypeCheckError as err:
                msg = str(err)
                if context:
                    msg = f'{context}: {msg}'
                log.error(message=msg, exc_type=TypeError)
                return None

        return wrapper

    if func is None:
        return decorator
    return decorator(func)


# ==============================================================
# Validation stages (enum/constant)
# ==============================================================
class ValidationStage:
    TYPE = 'type'
    RANGE = 'range'
    MEMBERSHIP = 'membership'
    REGEX = 'regex'
    CUSTOM = 'custom'


# ==============================================================
# Advanced runtime custom validators for Parameter types/content
# ==============================================================


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

    def __init__(self, expected_type: DataTypes):
        if isinstance(expected_type, DataTypes):
            self.expected_type = expected_type
            self.expected_label = str(expected_type)
        else:
            raise TypeError(f'TypeValidator expected a DataTypes member, got {expected_type!r}')

    def validated(self, value, name, default=None, current=None):
        if current is None and value is None:
            Diagnostics.none_value(name, default)
            return default

        if not isinstance(value, self.expected_type.value):
            Diagnostics.type_mismatch(
                name,
                value,
                expected_type=self.expected_label,
                current=current,
                default=default,
            )
            return self._fallback(current, default)

        Diagnostics.validated(name, value, stage=ValidationStage.TYPE)
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

        Diagnostics.validated(name, value, stage=ValidationStage.RANGE)
        return value


class MembershipValidatorOld(BaseValidator):
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

        Diagnostics.validated(name, value, stage=ValidationStage.MEMBERSHIP)
        return value


class MembershipValidator(BaseValidator):
    """Ensures that a value belongs to a predefined list of allowed
    choices.

    `allowed` can be a static iterable or a callable returning allowed
    values.
    """

    def __init__(self, allowed):
        # Do not convert immediately to list — may be callable
        self.allowed = allowed

    def validated(
        self,
        value,
        name,
        default=None,
        current=None,
    ):
        # Dynamically evaluate allowed if callable (e.g. lambda)
        allowed_values = self.allowed() if callable(self.allowed) else self.allowed

        if current is None and value is None:
            Diagnostics.none_value(name, default)
            return default

        if value not in allowed_values:
            Diagnostics.choice_mismatch(
                name,
                value,
                allowed_values,
                current=current,
                default=default,
            )
            return self._fallback(current, default)

        Diagnostics.validated(name, value, stage=ValidationStage.MEMBERSHIP)
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

        if not self.pattern.fullmatch(value):
            Diagnostics.regex_mismatch(
                name,
                value,
                self.pattern.pattern,
                current=current,
                default=default,
            )
            return self._fallback(current, default)

        Diagnostics.validated(name, value, stage=ValidationStage.REGEX)
        return value


# 3d: CombinedValidator
class CombinedValidator(BaseValidator):
    """Chains multiple validators sequentially."""

    def __init__(self, *validators):
        self._validators = validators

    def validated(self, value, name, default=None, current=None):
        val = value
        for validator in self._validators:
            val = validator.validated(val, name, default=default, current=current)
        return val


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

    def validated_old(self, value, name, current=None):
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
        # 6b: Call Diagnostics.validated after full validation
        Diagnostics.validated(name, val, stage='full')
        return val

    def validated(self, value, name, current=None):
        # Evaluate callable defaults dynamically
        default = self.default() if callable(self.default) else self.default

        val = value
        if self._type_validator:
            val = self._type_validator.validated(
                val,
                name,
                default=default,
                current=current,
            )
        if self._content_validator:
            val = self._content_validator.validated(
                val,
                name,
                default=default,
                current=current,
            )

        Diagnostics.validated(name, val, stage='full')
        return val
