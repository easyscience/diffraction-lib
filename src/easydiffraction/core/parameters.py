"""Parameter, descriptor & constant abstraction layer.

This module defines a lightweight three-layer hierarchy for
*constants*, *descriptors* and *parameters* used across the library.
It intentionally separates **metadata** concerns (name, units, CIF tags)
from **value semantics** (validation, range checking, fitting flags)
to keep mutation and validation logic centralised and observable by
the guard / diagnostics system.

Key concepts
------------
Constant (``ConstantBase`` / ``GenericConstant`` / ``Constant``)
    Immutable values (string or float). Always read-only for the user.

Descriptor (``GenericDescriptor`` / ``Descriptor``)
    Mutable values (string or float), but not refinable.

Parameter (``GenericParameter`` / ``Parameter``)
    Float-only. Mutable and refinable with physical/fit bounds.

Design notes
------------
* All three categories share a common root ``ConstantBase``.
* ``Domain`` enum allows robust type checks instead of relying on
  ``isinstance(obj, Descriptor)`` style checks.
* CIF integration is added via ``CifMixin`` at the final concrete
  classes (Descriptor, Parameter).
"""

from __future__ import annotations

import secrets
import string
from abc import ABC
from enum import Enum
from enum import auto
from typing import Any
from typing import List
from typing import Optional
from typing import TypeVar

import numpy as np

from easydiffraction.core.guards import AttributeAccessGuardMixin
from easydiffraction.core.guards import AttributeSetGuardMixin
from easydiffraction.core.guards import DiagnosticsMixin
from easydiffraction.core.guards import GuardedBase
from easydiffraction.core.singletons import UidMapHandler
from easydiffraction.utils.utils import str_to_ufloat

T = TypeVar('T')


# ----------------------------------------------------------------------
# Domain enum
# ----------------------------------------------------------------------
class Domain(Enum):
    CONSTANT = auto()
    DESCRIPTOR = auto()
    PARAMETER = auto()


# ----------------------------------------------------------------------
# Constant hierarchy (base + generic + CIF-aware concrete)
# ----------------------------------------------------------------------
class ConstantBase(
    DiagnosticsMixin,
    AttributeAccessGuardMixin,
    AttributeSetGuardMixin,
    GuardedBase,
    ABC,
):
    """Abstract root for constant-like objects."""

    _readonly_attributes = {
        'name',
        'pretty_name',
        'value_type',
        'units',
        'description',
        'editable',
        'parameters',
        'default_value',
        'allowed_values',
    }
    _class_public_attrs = _readonly_attributes

    @staticmethod
    def _make_callable(x):
        return x if callable(x) else (lambda: x)

    def __init__(
        self,
        name: str,
        value_type: type,
        pretty_name: Optional[str] = None,
        units: Optional[str] = None,
        description: Optional[str] = None,
        editable: bool = False,
        default_value: Any = None,
        allowed_values: Optional[List[T]] = None,
    ) -> None:
        if type(self) is ConstantBase:
            raise TypeError('ConstantBase is abstract and cannot be instantiated directly.')
        self._parent: Optional[Any] = None
        self._name = name
        self._pretty_name = pretty_name
        self._value_type = value_type
        self._units = units
        self._description = description
        self._editable = editable
        self._default_value_provider = self._make_callable(default_value)
        self._allowed_values_provider = self._make_callable(allowed_values)

    def __setattr__(self, key: str, value: Any) -> None:
        if self._guarded_setattr(key, value):
            return
        object.__setattr__(self, key, value)

    @property
    def parameters(self) -> list:
        return [self]

    @property
    def name(self):
        return self._name

    @property
    def pretty_name(self):
        return self._pretty_name

    @property
    def value_type(self):
        return self._value_type

    @property
    def units(self):
        return self._units

    @property
    def description(self):
        return self._description

    @property
    def editable(self):
        return self._editable

    @property
    def allowed_values(self):
        return self._allowed_values_provider()

    @property
    def default_value(self):
        return self._default_value_provider()

    @property
    def domain(self) -> Domain:
        return Domain.CONSTANT


class GenericConstant(ConstantBase):
    """Adds runtime storage and UID to constants."""

    _writable_attributes = {'value'}
    _readonly_attributes = ConstantBase._readonly_attributes | {
        'uid',
        'full_name',
        'datablock_name',
        'category_key',
        'category_entry_name',
    }
    _class_public_attrs = _readonly_attributes | _writable_attributes

    @staticmethod
    def _generate_uid() -> str:
        length = 16
        return ''.join(secrets.choice(string.ascii_lowercase) for _ in range(length))

    def __init__(
        self,
        value: Any,
        name: str,
        value_type: type,
        default_value: Any = None,
        pretty_name: Optional[str] = None,
        units: Optional[str] = None,
        description: Optional[str] = None,
        editable: bool = False,
        allowed_values: Optional[List[T]] = None,
    ) -> None:
        super().__init__(
            name=name,
            value_type=value_type,
            pretty_name=pretty_name,
            units=units,
            description=description,
            editable=editable,
            default_value=default_value,
            allowed_values=allowed_values,
        )
        self._value = value if value is not None else self.default_value
        self._uid = self._generate_uid()
        UidMapHandler.get().add_to_uid_map(self)

    def __str__(self) -> str:
        value_str = f'{self.__class__.__name__}: {self.full_name} = "{self.value}"'
        if self.units:
            value_str += f' {self.units}'
        return value_str

    @property
    def value(self) -> Any:
        return self._value

    @value.setter
    def value(self, _):
        self._readonly_error()

    @property
    def uid(self) -> str:
        return self._uid

    @property
    def datablock_name(self) -> Optional[str]:
        return getattr(self._parent, 'datablock_name', None) if self._parent else None

    @property
    def category_entry_name(self) -> Optional[str]:
        return getattr(self._parent, 'category_entry_name', None) if self._parent else None

    @property
    def category_key(self) -> Optional[str]:
        return getattr(self._parent, 'category_key', None) if self._parent else None

    @property
    def full_name(self) -> str:
        parts = []
        if self.datablock_name:
            parts.append(self.datablock_name)
        if self.category_key:
            parts.append(self.category_key)
        if self.category_entry_name:
            parts.append(str(self.category_entry_name))
        parts.append(self.name)
        return '.'.join(parts)


class Constant(GenericConstant):
    """Concrete read-only constant (no CIF integration)."""

    pass


# ----------------------------------------------------------------------
# Descriptor hierarchy (mutable, not refinable)
# ----------------------------------------------------------------------
class GenericDescriptor(GenericConstant):
    """Descriptor: mutable but not refinable."""

    @property
    def domain(self) -> Domain:
        return Domain.DESCRIPTOR

    @GenericConstant.value.setter
    def value(self, new_value: Any) -> None:
        if self._value == new_value:
            return
        if self.value_type and not isinstance(new_value, self.value_type):
            self._type_warning(self.name, self.value_type, new_value)
            return
        if self.allowed_values is not None and new_value not in self.allowed_values:
            self._allowed_values_warning(self.name, new_value, self.allowed_values)
            return
        self._value = new_value


# ----------------------------------------------------------------------
# Parameter hierarchy (mutable, refinable floats)
# ----------------------------------------------------------------------
class GenericParameter(GenericDescriptor):
    """Parameter: refinable floats with bounds, uncertainty, flags."""

    _writable_attributes = GenericDescriptor._writable_attributes | {
        'uncertainty',
        'free',
        'start_value',
    }
    _readonly_attributes = GenericDescriptor._readonly_attributes | {
        'physical_min',
        'physical_max',
        'fit_min',
        'fit_max',
        'constrained',
    }
    _class_public_attrs = _readonly_attributes | _writable_attributes

    def __init__(
        self,
        value: Any,
        name: str,
        value_type: type = float,
        default_value: Any = None,
        pretty_name: Optional[str] = None,
        units: Optional[str] = None,
        description: Optional[str] = None,
        editable: bool = True,
        allowed_values: Optional[List[T]] = None,
        uncertainty: float = np.nan,
        free: bool = False,
        constrained: bool = False,
        physical_min: float = -np.inf,
        physical_max: float = np.inf,
        fit_min: float = -np.inf,
        fit_max: float = np.inf,
    ) -> None:
        super().__init__(
            value=value,
            name=name,
            value_type=value_type,
            default_value=default_value,
            pretty_name=pretty_name,
            units=units,
            description=description,
            editable=editable,
            allowed_values=allowed_values,
        )
        self._uncertainty = uncertainty
        self._free = free
        self._constrained = constrained
        self._physical_min = physical_min
        self._physical_max = physical_max
        self._fit_min = fit_min
        self._fit_max = fit_max
        self.start_value = None

    @property
    def domain(self) -> Domain:
        return Domain.PARAMETER

    @property
    def uncertainty(self):
        return self._uncertainty

    @uncertainty.setter
    def uncertainty(self, v):
        self._uncertainty = v

    @property
    def free(self):
        return self._free

    @free.setter
    def free(self, v):
        self._free = v

    @property
    def constrained(self):
        return self._constrained

    @property
    def physical_min(self):
        return self._physical_min

    @property
    def physical_max(self):
        return self._physical_max

    @property
    def fit_min(self):
        return self._fit_min

    @property
    def fit_max(self):
        return self._fit_max

    @GenericDescriptor.value.setter
    def value(self, new_value: Any) -> None:
        if self._value == new_value:
            return
        if isinstance(new_value, int):
            new_value = float(new_value)
        if self.value_type and not isinstance(new_value, self.value_type):
            self._type_warning(self.name, self.value_type, new_value)
            return
        if not (self.physical_min <= new_value <= self.physical_max):
            self._range_warning(self.name, new_value, self.physical_min, self.physical_max)
            return
        self._value = new_value


# ----------------------------------------------------------------------
# CIF mixin and concrete classes
# ----------------------------------------------------------------------
class CifMixin:
    _readonly_attributes = {'full_cif_names', 'cif_uid'}

    def __init__(self, full_cif_names: list[str]) -> None:
        self._full_cif_names = full_cif_names

    @property
    def full_cif_names(self):
        return self._full_cif_names

    @property
    def cif_uid(self):
        return self.full_name

    def from_cif(self, block: Any, idx: int = 0) -> None:
        found_values: list[Any] = []
        for tag in self.full_cif_names:
            candidate = list(block.find_values(tag))
            if candidate:
                found_values = candidate
                break
        if not found_values:
            self.value = self.default_value
            return
        raw = found_values[idx]
        if self.value_type is float:
            u = str_to_ufloat(raw)
            self.value = u.n
            if hasattr(self, 'uncertainty'):
                self.uncertainty = u.s  # type: ignore[attr-defined]
        elif self.value_type is str:
            if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in {"'", '"'}:
                self.value = raw[1:-1]
            else:
                self.value = raw
        else:
            self.value = raw


class Descriptor(CifMixin, GenericDescriptor):
    """Concrete descriptor with CIF integration."""

    _readonly_attributes = GenericDescriptor._readonly_attributes | CifMixin._readonly_attributes
    _class_public_attrs = _readonly_attributes | GenericDescriptor._writable_attributes

    def __init__(
        self,
        value: Any,
        name: str,
        value_type: type,
        full_cif_names: list[str],
        default_value: Any,
        pretty_name: Optional[str] = None,
        units: Optional[str] = None,
        description: Optional[str] = None,
        editable: bool = True,
        allowed_values: Optional[List[T]] = None,
    ) -> None:
        CifMixin.__init__(self, full_cif_names=full_cif_names)
        GenericDescriptor.__init__(
            self,
            value=value,
            name=name,
            value_type=value_type,
            default_value=default_value,
            pretty_name=pretty_name,
            units=units,
            description=description,
            editable=editable,
            allowed_values=allowed_values,
        )


class Parameter(CifMixin, GenericParameter):
    """Concrete floating point parameter with CIF integration."""

    _readonly_attributes = GenericParameter._readonly_attributes | CifMixin._readonly_attributes
    _class_public_attrs = _readonly_attributes | GenericParameter._writable_attributes

    def __init__(
        self,
        value: Any,
        name: str,
        full_cif_names: list[str],
        default_value: Any,
        pretty_name: Optional[str] = None,
        units: Optional[str] = None,
        description: Optional[str] = None,
        editable: bool = True,
        uncertainty: float = np.nan,
        free: bool = False,
        constrained: bool = False,
        physical_min: float = -np.inf,
        physical_max: float = np.inf,
        fit_min: float = -np.inf,
        fit_max: float = np.inf,
    ) -> None:
        CifMixin.__init__(self, full_cif_names=full_cif_names)
        GenericParameter.__init__(
            self,
            value=value,
            name=name,
            value_type=float,
            default_value=default_value,
            pretty_name=pretty_name,
            units=units,
            description=description,
            editable=editable,
            allowed_values=None,
            uncertainty=uncertainty,
            free=free,
            constrained=constrained,
            physical_min=physical_min,
            physical_max=physical_max,
            fit_min=fit_min,
            fit_max=fit_max,
        )

    @property
    def _minimizer_uid(self):
        """Return variant of uid safe for minimizer engines."""
        return self.full_name.replace('.', '__')
