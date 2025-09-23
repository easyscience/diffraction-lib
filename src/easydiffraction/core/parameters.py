"""Parameter & descriptor abstraction layer.

This module defines a lightweight three-layer hierarchy for
*descriptors* and *parameters* used across the library. It
intentionally separates **metadata** concerns (name, units, CIF tags)
from **value semantics** (validation, range checking, fitting flags)
to keep mutation and validation logic centralised and observable by
the guard / diagnostics system.

Key concepts
------------
Descriptor (``BaseDescriptor`` / ``GenericDescriptor`` / ``Descriptor``)
    Generic piece of data with metadata (name, units, default
    value, allowed values) but without numeric fitting semantics.

Parameter (``BaseParameter`` / ``GenericParameter`` / ``Parameter``)
    Extension of a descriptor adding physical & fit bounds,
    uncertainty, and fitting control flags (``free`` /
    ``constrained``).

Design notes
------------
* A small *3-layer pattern* is used for both descriptors and
    parameters:
    - ``Base*``: abstract metadata & attribute guards (read‑only
        surfaces).
    - ``Generic*``: adds runtime value storage & generic logic.
    - Concrete (``Descriptor`` / ``Parameter``): adds CIF integration.
* Attribute setting is intercepted by ``AttributeSetGuardMixin``; test
    code or user code may assign raw Python values to attributes that
    are descriptor objects higher up the containment graph. Those
    guards forward the assignment to the internal ``value`` field while
    producing diagnostic warnings (e.g., for type coercion or range
    violations).
* No heavy external dependencies: only ``numpy`` (for ``np.inf`` /
    ``np.nan``) and minimal utility parsing via ``str_to_ufloat``.
* The UID generation is deliberately simple & random (sufficient
    session level uniqueness). Stable / persisted UID guarantees are
    handled elsewhere if required.

The intention of the documentation additions in this patch is strictly
clarificatory; no runtime behaviour is modified.
"""

from __future__ import annotations

import secrets
import string
from abc import ABC
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


# Technique-independent base classes for descriptors & parameters


class BaseDescriptor(
    DiagnosticsMixin,
    AttributeAccessGuardMixin,
    AttributeSetGuardMixin,
    GuardedBase,
    ABC,
):
    """Abstract root for descriptor-like objects.

    Provides:
        * Guarded attribute surface (read-only enforcement for declared
            fields).
        * Common metadata fields (``name``, ``units``, ``description``,
            etc.).
        * Lazy providers for ``default_value`` / ``allowed_values`` that
            permit static literals and callables (late binding / dynamic
            defaults).
    """

    # _writable_attributes = set()
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
    _class_public_attrs = _readonly_attributes  # | _writable_attributes

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
        editable: bool = True,
        default_value: Any = None,
        allowed_values: Optional[List[T]] = None,
    ) -> None:
        """Initialise the base descriptor.

        Parameters
        ----------
        name:
            Canonical identifier (last token in fully-qualified name).
        value_type:
            Expected Python type for stored values (used for
            validation).
        pretty_name:
            Optional human readable display label.
        units:
            Physical / semantic units string or ``None``.
        description:
            Free-form explanatory text.
        editable:
            Whether UI / higher layers may edit the value.
        default_value:
            Either a literal or a callable returning the default.
        allowed_values:
            Optional finite list restricting admissible values.
        """
        if type(self) is BaseDescriptor:
            raise TypeError(
                'BaseDescriptor is an abstract class and cannot be instantiated directly.'
            )
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

    @name.setter
    def name(self, _):
        self._readonly_error()

    @property
    def pretty_name(self):
        return self._pretty_name

    @pretty_name.setter
    def pretty_name(self, _):
        self._readonly_error()

    @property
    def value_type(self):
        return self._value_type

    @value_type.setter
    def value_type(self, _):
        self._readonly_error()

    @property
    def units(self):
        return self._units

    @units.setter
    def units(self, _):
        self._readonly_error()

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, _):
        self._readonly_error()

    @property
    def editable(self):
        return self._editable

    @editable.setter
    def editable(self, _):
        self._readonly_error()

    @property
    def allowed_values(self):
        return self._allowed_values_provider()

    @allowed_values.setter
    def allowed_values(self, _):
        self._readonly_error()

    @property
    def default_value(self):
        return self._default_value_provider()

    @default_value.setter
    def default_value(self, _):
        self._readonly_error()


class GenericDescriptor(BaseDescriptor):
    _writable_attributes = {'value'}
    _readonly_attributes = BaseDescriptor._readonly_attributes | {
        'uid',
        'full_name',
        'datablock_name',
        'category_key',
        'category_entry_name',
    }
    _class_public_attrs = _readonly_attributes | _writable_attributes

    @staticmethod
    def _generate_uid() -> str:
        """Generate simple pseudo-random UID.

        Collisions are statistically negligible for typical interactive
        sessions (16 lower-case letters => 26**16 space). Not intended
        for persistent cross-session identity guarantees.
        """
        length = 16
        uid = ''.join(secrets.choice(string.ascii_lowercase) for _ in range(length))
        return uid

    def __init__(
        self,
        value: Any,
        name: str,
        value_type: type,
        default_value: Any = None,
        pretty_name: Optional[str] = None,
        units: Optional[str] = None,
        description: Optional[str] = None,
        editable: bool = True,
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
        """Return concise human-readable representation for logging /
        debug.
        """
        value_str = f'{self.__class__.__name__}: {self.full_name} = "{self.value}"'
        if self.units:
            value_str += f' {self.units}'
        return value_str

    @property
    def value(self) -> Any:
        return self._value

    # TODO
    @value.setter
    def value(self, new_value: Any) -> None:
        if self._value == new_value:
            return
        # Type check
        if self.value_type and not isinstance(new_value, self.value_type):
            self._type_warning(self.name, self.value_type, new_value)
            return
        # Allowed values check
        if self.allowed_values is not None and new_value not in self.allowed_values:
            self._allowed_values_warning(self.name, new_value, self.allowed_values)
            return
        self._value = new_value

    @property
    def uid(self) -> str:
        return self._uid

    @uid.setter
    def uid(self, _):
        self._readonly_error()

    @property
    def datablock_name(self) -> Optional[str]:
        if self._parent is not None:
            return getattr(self._parent, 'datablock_name', None)
        return None

    @datablock_name.setter
    def datablock_name(self, _):
        self._readonly_error()

    @property
    def category_entry_name(self) -> Optional[str]:
        if self._parent is not None:
            return getattr(self._parent, 'category_entry_name', None)
        return None

    @category_entry_name.setter
    def category_entry_name(self, _):
        self._readonly_error()

    @property
    def category_key(self) -> Optional[str]:
        if self._parent is not None:
            return getattr(self._parent, 'category_key', None)
        return None

    @category_key.setter
    def category_key(self, _):
        self._readonly_error()

    @property
    def full_name(self) -> str:
        parts = []
        if self.datablock_name is not None:
            parts.append(self.datablock_name)
        if self.category_key is not None:
            parts.append(self.category_key)
        if self.category_entry_name is not None:
            parts.append(str(self.category_entry_name))
        parts.append(self.name)
        return '.'.join(parts)

    @full_name.setter
    def full_name(self, _):
        self._readonly_error()


class BaseParameter(BaseDescriptor, ABC):
    # _writable_attributes = set()
    _readonly_attributes = BaseDescriptor._readonly_attributes | {
        'physical_min',
        'physical_max',
        'fit_min',
        'fit_max',
        'constrained',
    }
    _class_public_attrs = _readonly_attributes  # | _writable_attributes

    def __init__(
        self,
        name: str,
        value_type: type,
        pretty_name: Optional[str] = None,
        units: Optional[str] = None,
        description: Optional[str] = None,
        editable: bool = True,
        default_value: Any = None,
        allowed_values: Optional[List[T]] = None,
        physical_min: Optional[float] = -np.inf,
        physical_max: Optional[float] = np.inf,
        fit_min: Optional[float] = -np.inf,
        fit_max: Optional[float] = np.inf,
        constrained: bool = False,
    ) -> None:
        """Initialise common parameter metadata & bounds.

        Physical vs fit bounds
        ----------------------
        ``physical_*`` constraints model the admissible region
        defined by physics / domain knowledge. ``fit_*`` may be
        narrower (e.g., to stabilise optimisers) but still lie inside
        the physical bounds. ``constrained`` toggles whether an
        external symbolic expression controls this parameter (handled
        at higher layers; here it is only stored).
        """
        if type(self) is BaseParameter:
            raise TypeError(
                'BaseParameter is an abstract class and cannot be instantiated directly.'
            )
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
        self._physical_min = physical_min
        self._physical_max = physical_max
        self._fit_min = fit_min
        self._fit_max = fit_max
        self._constrained = constrained

    @property
    def physical_min(self):
        return self._physical_min

    @physical_min.setter
    def physical_min(self, _):
        self._readonly_error()

    @property
    def physical_max(self):
        return self._physical_max

    @physical_max.setter
    def physical_max(self, _):
        self._readonly_error()

    @property
    def fit_min(self):
        return self._fit_min

    @fit_min.setter
    def fit_min(self, _):
        self._readonly_error()

    @property
    def fit_max(self):
        return self._fit_max

    @fit_max.setter
    def fit_max(self, _):
        self._readonly_error()

    @property
    def constrained(self):
        return self._constrained

    @constrained.setter
    def constrained(self, _):
        self._readonly_error()


class GenericParameter(GenericDescriptor, BaseParameter):
    """Concrete numeric parameter with validation and uncertainty.

    Adds runtime state used by minimisation:
    * ``uncertainty``: one-sigma estimate (``np.nan`` if unknown).
    * ``free``: candidate for refinement when True.
        * ``start_value``: snapshot of the initial value before a fit
            begins.
    """

    _writable_attributes = GenericDescriptor._writable_attributes | {
        'uncertainty',
        'free',
        'start_value',
    }
    _readonly_attributes = (
        BaseParameter._readonly_attributes | GenericDescriptor._readonly_attributes
    )
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
        physical_min: Optional[float] = -np.inf,
        physical_max: Optional[float] = np.inf,
        fit_min: Optional[float] = -np.inf,
        fit_max: Optional[float] = np.inf,
    ) -> None:
        BaseParameter.__init__(
            self,
            name=name,
            value_type=value_type,
            pretty_name=pretty_name,
            units=units,
            description=description,
            editable=editable,
            default_value=default_value,
            allowed_values=allowed_values,
            physical_min=physical_min,
            physical_max=physical_max,
            fit_min=fit_min,
            fit_max=fit_max,
            constrained=constrained,
        )
        self._value = value if value is not None else self.default_value
        self._uncertainty = uncertainty
        self._free = free
        self.start_value = None

    def __str__(self) -> str:
        """Return concise human-readable representation for logging /
        debug.
        """
        value_str = f'{self.__class__.__name__}: {self.full_name} = "{self.value}"'
        if not np.isnan(self.uncertainty) and self.uncertainty != 0.0:
            value_str += f' ± {self.uncertainty}'
        if self.units:
            value_str += f' {self.units}'
        return value_str

    @property
    def _minimizer_uid(self):
        """Return variant of uid safe for minimizer engines."""
        return self.full_name.replace('.', '__')

    @property
    def uncertainty(self):
        return self._uncertainty

    @uncertainty.setter
    def uncertainty(self, value):
        self._uncertainty = value

    @property
    def free(self):
        return self._free

    @free.setter
    def free(self, value):
        self._free = value

    @property
    def value(self) -> Any:
        return self._value

    @value.setter
    def value(self, new_value: Any) -> None:
        if self._value == new_value:
            return
        # Auto-cast int to float
        if isinstance(new_value, int):
            new_value = float(new_value)  # TODO: think of a better way
        # Type check (reuse Descriptor's logic)
        if self.value_type and not isinstance(new_value, self.value_type):
            self._type_warning(self.name, self.value_type, new_value)
            return
        # Range check
        if not (self.physical_min <= new_value <= self.physical_max):
            self._range_warning(self.name, new_value, self.physical_min, self.physical_max)
            return
        self._value = new_value


# Technique-specific mixin & concrete classes


class CifMixin:
    """Mixin providing CIF-related attributes and methods."""

    _readonly_attributes = {'full_cif_names', 'cif_uid'}

    def __init__(self, full_cif_names: list[str], *args, **kwargs):
        self._full_cif_names = full_cif_names
        super().__init__(*args, **kwargs)

    @property
    def full_cif_names(self):
        return self._full_cif_names

    @full_cif_names.setter
    def full_cif_names(self, _):
        self._readonly_error()

    @property
    def cif_uid(self):
        return self.full_name

    @cif_uid.setter
    def cif_uid(self, _):
        self._readonly_error()

    def from_cif(self, block: Any, idx: int = 0) -> None:
        """Populate the value from a CIF datablock.

        Strategy:
        * Iterate candidate tags; take first producing one or more
          values.
        * Fallback to ``default_value`` if none yield results.
        * For float descriptors: parse `(value, sigma)` via
          ``str_to_ufloat``.
        * For string descriptors: strip a single symmetrical quote pair.
        """
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
            if (len(raw) >= 2) and (raw[0] == raw[-1]) and (raw[0] in {"'", '"'}):
                self.value = raw[1:-1]
            else:
                self.value = raw
        else:
            self.value = raw


class Descriptor(CifMixin, GenericDescriptor):
    """Concrete descriptor with CIF import support."""

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
    """Concrete floating point parameter with CIF import support."""

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
        physical_min: Optional[float] = -np.inf,
        physical_max: Optional[float] = np.inf,
        fit_min: Optional[float] = -np.inf,
        fit_max: Optional[float] = np.inf,
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
