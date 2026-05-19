# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
Lightweight runtime validation utilities.

Provides DataTypes, type/content validators, and AttributeSpec used by
descriptors and parameters. Only documentation was added here.
"""

import re
from abc import ABC
from abc import abstractmethod
from enum import Enum
from enum import auto

import numpy as np

from easydiffraction.core.diagnostic import Diagnostics

# ======================================================================
# Shared constants
# ======================================================================


# TODO: MkDocs doesn't unpack types
class DataTypeHints:
    """Type hint aliases for numeric, string, and boolean types."""

    Numeric = int | float | np.integer | np.floating
    Integer = int | np.integer
    String = str
    Bool = bool


# ======================================================================


class DataTypes(Enum):
    """Enumeration of supported data types for descriptors."""

    NUMERIC = (int, float, np.integer, np.floating)
    INTEGER = (int, np.integer)
    STRING = (str,)
    BOOL = (bool,)
    ANY = (object,)  # fallback for unconstrained

    def __str__(self) -> str:
        """Return the lowercase name of the data type."""
        return self.name.lower()

    @property
    def expected_type(self) -> tuple:
        """Convenience alias for tuple of allowed Python types."""
        return self.value


# ======================================================================
# Validation stages (enum/constant)
# ======================================================================


class ValidationStage(Enum):
    """Phases of validation for diagnostic logging."""

    TYPE = auto()
    RANGE = auto()
    MEMBERSHIP = auto()
    REGEX = auto()

    def __str__(self) -> str:
        """Return the lowercase name of the validation stage."""
        return self.name.lower()


# ======================================================================
# Advanced runtime custom validators for Parameter types/content
# ======================================================================


class ValidatorBase(ABC):
    """Abstract base class for all validators."""

    @abstractmethod
    def validated(
        self,
        value: object,
        name: str,
        default: object = None,
        current: object = None,
    ) -> object:
        """
        Return a validated value or fallback.

        Subclasses must implement this method.
        """
        raise NotImplementedError

    @staticmethod
    def _fallback(
        current: object = None,
        default: object = None,
    ) -> object:
        """Return current if set, else default."""
        return current if current is not None else default


# ======================================================================


class TypeValidator(ValidatorBase):
    """Ensure a value is of the expected data type."""

    def __init__(self, expected_type: DataTypes) -> None:
        if isinstance(expected_type, DataTypes):
            self.expected_type = expected_type
            self.expected_label = str(expected_type)
        else:
            msg = f'TypeValidator expected a DataTypes member, got {expected_type!r}'
            raise TypeError(msg)

    def validated(
        self,
        value: object,
        name: str,
        default: object = None,
        current: object = None,
        *,
        allow_none: bool = False,
    ) -> object:
        """
        Validate type and return value or fallback.

        If allow_none is True, None bypasses content checks.
        """
        # Fresh initialization, use default
        if current is None and value is None:
            Diagnostics.no_value(name, default)
            return default

        # Explicit None (allowed)
        if value is None and allow_none:
            Diagnostics.none_value(name)
            return None

        # Normal type validation
        if not isinstance(value, self.expected_type.value):
            Diagnostics.type_mismatch(
                name,
                value,
                expected_type=self.expected_label,
                current=current,
                default=default,
            )
            return self._fallback(current, default)

        Diagnostics.validated(
            name,
            value,
            stage=ValidationStage.TYPE,
        )
        return value


# ======================================================================


class RangeValidator(ValidatorBase):
    """Ensure a numeric value lies within [ge, le]."""

    def __init__(
        self,
        *,
        ge: float = -np.inf,
        le: float = np.inf,
    ) -> None:
        self.ge, self.le = ge, le

    def validated(
        self,
        value: object,
        name: str,
        default: object = None,
        current: object = None,
    ) -> object:
        """Validate range and return value or fallback."""
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

        Diagnostics.validated(
            name,
            value,
            stage=ValidationStage.RANGE,
        )
        return value


# ======================================================================


class MembershipValidator(ValidatorBase):
    """
    Ensure that a value is among allowed choices.

    ``allowed`` may be an iterable or a callable returning a collection.
    """

    def __init__(self, allowed: object) -> None:
        # Do not convert immediately to list — may be callable
        self.allowed = allowed

    def validated(
        self,
        value: object,
        name: str,
        default: object = None,
        current: object = None,
    ) -> object:
        """Validate membership and return value or fallback."""
        # Dynamically evaluate allowed if callable (e.g. lambda)
        allowed_values = self.allowed() if callable(self.allowed) else self.allowed

        if value not in allowed_values:
            Diagnostics.choice_mismatch(
                name,
                value,
                allowed_values,
                current=current,
                default=default,
            )
            return self._fallback(current, default)

        Diagnostics.validated(
            name,
            value,
            stage=ValidationStage.MEMBERSHIP,
        )
        return value


# ======================================================================


class RegexValidator(ValidatorBase):
    """Ensure that a string matches a given regular expression."""

    def __init__(self, pattern: str) -> None:
        self.pattern = re.compile(pattern)

    def validated(
        self,
        value: object,
        name: str,
        default: object = None,
        current: object = None,
    ) -> object:
        """Validate regex and return value or fallback."""
        if not self.pattern.fullmatch(value):
            Diagnostics.regex_mismatch(
                name,
                value,
                self.pattern.pattern,
                current=current,
                default=default,
            )
            return self._fallback(current, default)

        Diagnostics.validated(
            name,
            value,
            stage=ValidationStage.REGEX,
        )
        return value


# ======================================================================
# Attribute specification holding metadata and validators
# ======================================================================


class AttributeSpec:
    """Hold metadata and validators for a single attribute."""

    def __init__(
        self,
        *,
        default: object = None,
        data_type: DataTypes | None = None,
        validator: ValidatorBase | None = None,
        allow_none: bool = False,
    ) -> None:
        self.default = default
        self.allow_none = allow_none
        self._data_type_validator = TypeValidator(data_type) if data_type else None
        self._validator = validator

    def validated(
        self,
        value: object,
        name: str,
        current: object = None,
    ) -> object:
        """
        Validate through type and content validators.

        Returns validated value, possibly default or current if errors
        occur. None may short-circuit further checks when allowed.
        """
        val = value
        # Evaluate callable defaults dynamically
        default = self.default() if callable(self.default) else self.default

        # Type validation
        if self._data_type_validator:
            val = self._data_type_validator.validated(
                val,
                name,
                default=default,
                current=current,
                allow_none=self.allow_none,
            )

        # Skip further validation: Special case for None
        if val is None and self.allow_none:
            Diagnostics.none_value_skip_range(name)
            return None

        # Content validation
        if self._validator and val is not None:
            val = self._validator.validated(
                val,
                name,
                default=default,
                current=current,
            )

        return val
