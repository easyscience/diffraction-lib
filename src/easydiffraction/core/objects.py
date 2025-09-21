# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause
"""Core object model primitives.

Foundational building blocks for the EasyDiffraction data model:

* Guarded mixins for safe attribute access and diagnostics.
* ``Descriptor``: metadata/value holder (non refinable).
* ``Parameter``: refinable numerical descriptor with bounds & sigma.
* ``CategoryItem``: grouping of descriptors / parameters (e.g. cell).
* ``Datablock``: container aggregating components / collections.

Design goals:
* Explicit allowed attribute sets (defensive API surface).
* Read only enforcement for identity / metadata fields.
* Lazy providers for defaults and allowed values.
* CIF import / export convenience helpers.

Collection refactor intentionally deferred.
"""

from __future__ import annotations

import difflib
import inspect
import secrets
import string
from abc import ABC
from abc import abstractmethod
from collections.abc import MutableMapping
from typing import Any
from typing import Iterator
from typing import List
from typing import Optional
from typing import TypeVar
from typing import Union

import numpy as np

from easydiffraction import log
from easydiffraction.utils.utils import str_to_ufloat

__all__ = [
    'Descriptor',
    'Parameter',
    'CategoryItem',
    'Datablock',
    'CategoryCollection',
    'DatablockCollection',
]

T = TypeVar('T')


class GuardedBase(ABC):
    @abstractmethod
    def __str__(self) -> str:
        """Subclasses must implement human-readable representation."""
        raise NotImplementedError

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

    def __repr__(self) -> str:
        # Reuse __str__; subclasses only override if needed
        return self.__str__()

    def _readonly_error(self) -> None:
        """Error for attempts to modify a read-only attribute."""
        caller = inspect.stack()[1].function
        message = f'Attribute {caller} of {self.uid} is read-only.'
        log.error(message, exc_type=AttributeError)

    def _set_error(self, key: str, allowed: set[str] | None = None) -> None:
        """Error for attempts to set a non-existent attribute."""
        suggestion = difflib.get_close_matches(key, allowed or [], n=1)
        hint = f' Did you mean "{suggestion[0]}"?' if suggestion else ''
        allowed_list = f' Allowed: {sorted(allowed)}' if allowed else ''
        message = f'Cannot set "{key}" on {type(self).__name__}.{hint}{allowed_list}'
        log.error(message, exc_type=AttributeError)

    def _get_error(self, key: str, allowed: set[str] | None = None) -> None:
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

    The union of ``_allowed_attributes`` across the class MRO and the
    instance's current public ``__dict__`` keys defines what can be
    assigned via normal attribute access.
    """

    _allowed_attributes: set[str] = set()
    _cached_allowed_attributes: set[str] = set()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        allowed = set()
        for base in cls.__mro__:
            allowed |= getattr(base, '_allowed_attributes', set())
        cls._cached_allowed_attributes = allowed

    def __getattr__(self, key: str) -> Any:
        """Fallback for missing attribute access (emits helpful
        diagnostics).
        """
        allowed = self._allowed_attribute_names
        self._get_error(key, allowed)

    @property
    def _allowed_attribute_names(self) -> set[str]:
        """Instance-level allowed attribute names."""
        allowed = set(type(self)._cached_allowed_attributes)
        allowed |= {n for n in self.__dict__ if not n.startswith('_')}
        return allowed


class Descriptor(
    DiagnosticsMixin,
    AttributeAccessGuardMixin,
    GuardedBase,
):
    @staticmethod
    def _make_callable(x):
        """Ensure a value is returned via a callable."""
        return x if callable(x) else (lambda: x)

    """Non-refinable attribute/metadata holder.

    Represents a fixed property (e.g. CIF tag, metadata field). Unlike
    :class:`Parameter`, descriptors cannot be refined. They support:

    * Guarded attribute set (prevents accidental API growth).
    * Type / value validation (optional enumerated allowed values).
    * CIF import convenience (``from_cif``).
    * Stable unique identifier (``uid``) used by optimizers.
    * Computed ``full_name`` from hierarchy context parts.
    """

    # ------------------------------------------------------------------
    # Class configuration
    # ------------------------------------------------------------------
    # Attributes that user may set directly
    _writable_attributes = {
        'value',
    }

    # Attributes exposed but read-only
    _readonly_attributes = {
        'name',
        'value_type',
        'full_cif_names',
        'default_value',
        'pretty_name',
        'datablock_name',
        'category_key',
        'entry_name',
        'units',
        'description',
        'editable',
        'allowed_values',
        'uid',
        'full_name',
    }

    # All allowed attributes
    _allowed_attributes = _readonly_attributes | _writable_attributes
    # TODO: Update guard mixin to use readonly attributes for allowed
    #  in getter, while writable attributes for allowed in setter.
    #  Think about caching, as it is currently done for all allowed
    #  attributes.
    #  Think on splitting for CategoryItem, CategoryCollection and
    #  Datablock and how to handle extensions in subclasses.

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------
    def __init__(
        self,
        value: Any,
        name: str,
        value_type: type,
        full_cif_names: list[str],
        default_value: Any,
        pretty_name: Optional[str] = None,
        datablock_name: Optional[str] = None,
        category_key: Optional[str] = None,
        entry_name: Optional[str] = None,
        units: Optional[str] = None,
        description: Optional[str] = None,
        editable: bool = True,
        allowed_values: Optional[List[T]] = None,
    ) -> None:
        """Create descriptor.

        Parameters
        ----------
        value:
            Initial value (uses default when empty or ``None``).
        name:
            Internal symbolic name.
        value_type:
            Expected Python type (e.g. ``str`` or ``float``).
        full_cif_names:
            Ordered CIF tag aliases (first tag providing data is used).
        default_value:
            Fallback value when CIF extraction yields no entry.
        pretty_name:
            Human-facing label (UI / reporting).
        datablock_name:
            Parent datablock name (injected later by container).
        category_key:
            Parent category key (component-level grouping).
        entry_name:
            Parent collection entry identifier.
        units:
            Physical units (if applicable).
        description:
            Long-form description or help text.
        editable:
            If false the value should not be manually changed by users.
        allowed_values:
            Optional list of enumerated allowed values.
        """
        # Identity
        self._name = name
        self._pretty_name = pretty_name
        self._datablock_name = datablock_name
        self._category_key = category_key
        self._entry_name = entry_name

        # Semantics
        self._value_type = value_type
        self._units = units
        self._description = description
        self._editable = editable
        self._default_value_provider = self._make_callable(default_value)
        self._allowed_values_provider = self._make_callable(allowed_values)
        self._full_cif_names = full_cif_names

        # Value
        self._value = value if value is not None else self._default_value_provider()

        # UID
        self._uid = self._generate_random_uid()

    # ------------------------------------------------------------------
    # Dunder methods
    # ------------------------------------------------------------------
    def __str__(self) -> str:
        """Return concise human-readable representation."""
        value_str = f'{self.__class__.__name__}: {self.full_name} = "{self.value}"'
        if self.units:
            value_str += f' {self.units}'
        return value_str

    def __setattr__(self, key: str, value: Any) -> None:
        """Controlled setting enforcing allowed public attribute
        names.
        """
        if key.startswith('_'):
            object.__setattr__(self, key, value)
            return

        allowed = self._allowed_attribute_names
        if key not in allowed:
            self._set_error(key, allowed)
            return

        object.__setattr__(self, key, value)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _generate_random_uid(self) -> str:
        """Generate stable random uid (sufficient collision resistance
        for session).
        """
        length = 16
        return ''.join(secrets.choice(string.ascii_lowercase) for _ in range(length))

    def _set_datablock_name(self, new_name: str):
        """Internal helper to assign datablock name (called by
        parent).
        """
        self._datablock_name = new_name

    def _set_entry_name(self, new_name):
        """Internal helper to assign entry name of CategoryCollection
        (called by parent).
        """
        self._entry_name = new_name

    def _set_category_key(self, category_key: str) -> None:
        self._category_key = category_key

    # ------------------------------------------------------------------
    # Public read-only properties
    # ------------------------------------------------------------------
    @property
    def parameters(self) -> list:  # noqa: D401 - compatibility shim
        """Return list with self (uniform interface with components)."""
        return [self]

    @property
    def uid(self) -> str:
        """Stable, non-human unique ID."""
        return self._uid

    @uid.setter
    def uid(self, _):
        self._readonly_error()

    @property
    def full_name(self) -> str:
        """Assemble hierarchical fully-qualified name.

        Parts (if present): ``datablock_name``, ``category_key``,
        ``entry_name`` and final ``name``.
        """
        parts = []
        if self.datablock_name is not None:
            parts.append(self.datablock_name)
        if self.category_key is not None:
            parts.append(self.category_key)
        if self.entry_name is not None:
            parts.append(self.entry_name)
        parts.append(self.name)
        return '.'.join(parts)

    @full_name.setter
    def full_name(self, _):  # pragma: no cover - defensive
        self._readonly_error()

    @property
    def datablock_name(self):
        """Read-only datablock name (injected by parent container)."""
        return self._datablock_name

    @datablock_name.setter
    def datablock_name(self, _):
        self._readonly_error()

    @property
    def entry_name(self):
        return self._entry_name

    @entry_name.setter
    def entry_name(self, _new_id):  # unused: interface compatibility
        self._readonly_error()

    @property
    def category_key(self):
        return self._category_key

    @category_key.setter
    def category_key(self, _):
        self._readonly_error()

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
    def units(self):
        return self._units

    @units.setter
    def units(self, _):
        self._readonly_error()

    @property
    def value_type(self):
        return self._value_type

    @value_type.setter
    def value_type(self, _):
        self._readonly_error()

    @property
    def full_cif_names(self):
        return self._full_cif_names

    @full_cif_names.setter
    def full_cif_names(self, _):
        self._readonly_error()

    @property
    def allowed_values(self) -> Optional[List[T]]:
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

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, _):
        self._readonly_error()

    @property
    def editable(self):
        return self._editable

    # ------------------------------------------------------------------
    # Public writable properties
    # ------------------------------------------------------------------
    @property
    def value(self) -> Any:
        """Return current value (fall back to ``default_value`` when
        empty).
        """
        if self._value in (None, ''):
            return self.default_value
        return self._value

    @value.setter
    def value(self, new_value: Any) -> None:
        """Set value with type and enumerated allowed-values
        validation.
        """
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

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------
    def from_cif(self, block: Any, idx: int = 0) -> None:
        """Populate the descriptor value from a CIF datablock.

        Strategy:
        * Iterate tags; take first with at least one value.
        * If none found use ``default_value``.
        * Floats: parse via ``str_to_ufloat``; store sigma.
        * Strings: strip a single matching quote pair.

        Args:
            block: CIF-like object with ``find_values(tag)``.
            idx: Value index (default: first).
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


class Parameter(Descriptor):
    """Refinable numerical descriptor.

    Extends :class:`Descriptor` adding:

    * Refinement flags (``free`` / ``constrained``).
    * Physical bounds (``physical_min`` / ``physical_max``).
    * Numerical uncertainty (``uncertainty``).
    """

    # ------------------------------------------------------------------
    # Class configuration
    # ------------------------------------------------------------------
    # Extend writable attributes
    _writable_attributes = Descriptor._writable_attributes | {
        'free',
    }

    # Extend read-only attributes
    _readonly_attributes = Descriptor._readonly_attributes | {
        'uncertainty',
        'constrained',
        'physical_min',
        'physical_max',
    }

    # All allowed attributes
    _allowed_attributes = _readonly_attributes | _writable_attributes

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------
    def __init__(
        self,
        value: Any,
        name: str,
        full_cif_names: list[str],
        default_value: Any,
        pretty_name: Optional[str] = None,
        datablock_name: Optional[str] = None,
        category_key: Optional[str] = None,
        entry_name: Optional[str] = None,
        units: Optional[str] = None,
        description: Optional[str] = None,
        editable: bool = True,
        uncertainty: float = np.nan,
        free: bool = False,
        constrained: bool = False,
        physical_min: Optional[float] = -np.inf,
        physical_max: Optional[float] = np.inf,
    ) -> None:
        """Initialize a Parameter.

        Args:
            value: Initial floating value.
            name: Internal symbolic name.
            full_cif_names: Ordered CIF tag aliases.
            default_value: Fallback when CIF extraction fails.
            pretty_name: Human readable label.
            datablock_name: Parent datablock (if known).
            category_key: Parent category key.
            entry_name: Identifier inside owning collection.
            units: Display / physical units.
            description: Long form description.
            editable: Whether user may manually edit value.
            uncertainty: Standard uncertainty (sigma).
            free: True if parameter is free during refinement.
            constrained: True if constrained by symmetry.
            physical_min: Physical lower bound.
            physical_max: Physical upper bound.
        """
        super().__init__(
            value=value,
            name=name,
            value_type=float,
            full_cif_names=full_cif_names,
            default_value=default_value,
            pretty_name=pretty_name,
            datablock_name=datablock_name,
            category_key=category_key,
            entry_name=entry_name,
            units=units,
            description=description,
            editable=editable,
        )

        # Refinement attributes
        self._uncertainty = uncertainty
        self._free = free
        self._constrained = constrained
        self._physical_min = physical_min
        self._physical_max = physical_max

    # ------------------------------------------------------------------
    # Dunder methods
    # ------------------------------------------------------------------
    def __str__(self) -> str:
        """Return human-readable string with value, uncertainty &
        units.
        """
        value_str = f'{self.__class__.__name__}: {self.full_name} = "{self.value}"'
        if not np.isnan(self.uncertainty) and self.uncertainty != 0.0:
            value_str += f' ± {self.uncertainty}'
        if self.units:
            value_str += f' {self.units}'
        return value_str

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @property
    def _minimizer_uid(self):  # n?o?q?a: D401 - simple delegation
        """Return variant of uid safe for minimizer engines."""
        return self.full_name.replace('.', '__')

    # ------------------------------------------------------------------
    # Public read-only properties
    # ------------------------------------------------------------------

    @property
    def uncertainty(self):
        return self._uncertainty

    @uncertainty.setter
    def uncertainty(self, _):
        self._readonly_error()

    @property
    def free(self):
        return self._free

    @free.setter
    def free(self, _):
        self._readonly_error()

    @property
    def constrained(self):
        return self._constrained

    @constrained.setter
    def constrained(self, _):
        self._readonly_error()

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

    # ------------------------------------------------------------------
    # Public writable properties
    # ------------------------------------------------------------------

    # Redefine value from Descriptor with extra range check
    @property
    def value(self) -> Any:
        """Return current value, or default if unset."""
        if self._value in (None, ''):
            return self.default_value
        return self._value

    @value.setter
    def value(self, new_value: Any) -> None:
        """Set value with type & physical range validation."""
        if self._value == new_value:
            return
        # Type check (reuse Descriptor's logic)
        if self.value_type and not isinstance(new_value, self.value_type):
            self._type_warning(self.name, self.value_type, new_value)
            return
        # Range check
        if not (self.physical_min <= new_value <= self.physical_max):
            self._range_warning(self.name, new_value, self.physical_min, self.physical_max)
            return
        self._value = new_value


class CategoryItem(
    DiagnosticsMixin,
    AttributeAccessGuardMixin,
    GuardedBase,
):
    """Base class for logical model components.

    Examples:
        Cell, Peak, SpaceGroup.

    Responsibilities:
        * Guard public attribute surface.
        * Propagate datablock / entry identifiers to children.
        * Provide uniform access to contained descriptors/parameters.
        * Offer CIF and dictionary export helpers.
    """

    # ------------------------------------------------------------------
    # Class configuration
    # ------------------------------------------------------------------
    _allowed_attributes = {
        'datablock_name',
    }
    _MISSING_ATTR = object()

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------
    def __init__(self):
        """Initialize component with unset datablock and entry
        identifiers.
        """
        self._datablock_name = None
        self._entry_name = None

    # ------------------------------------------------------------------
    # Abstract API
    # ------------------------------------------------------------------
    @property
    @abstractmethod
    def category_key(self) -> str:
        """Category key for this component (e.g., 'cell',
        'space_group').

        Must be implemented in subclasses to specify the EasyDiffraction
        category name. Distinct from CIF category names, which are tied
        to descriptors.
        """
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Dunder methods
    # ------------------------------------------------------------------
    def __str__(self) -> str:
        """Human-readable representation of this component."""
        s = f'{self.__class__.__name__} ({len(self.parameters)} parameters)'
        for base in type(self).__mro__:
            if base is CategoryItem:
                s = f'{base.__name__}: {s}'
                break
        return s

    def __setattr__(self, key: str, value: Any) -> None:
        """Controlled attribute assignment.

        Logic:
        * Private names: direct set.
        * Public names: must be allowed.
        * New descriptor: inject category if unset.
        * Plain value for existing descriptor: update its value.
        """
        if key.startswith('_'):
            object.__setattr__(self, key, value)
            return

        allowed = self._allowed_attribute_names
        if key not in allowed:
            self._set_error(key, allowed)
            return

        try:
            attr = object.__getattribute__(self, key)
        except AttributeError:
            attr = self._MISSING_ATTR

        # If replacing or assigning a Descriptor instance
        if isinstance(value, Descriptor):
            if value._category_key is None:  # auto-inject only if unset
                value._set_category_key(self.category_key)
            object.__setattr__(self, key, value)

        # If updating the value of an existing Descriptor
        elif attr is not self._MISSING_ATTR and isinstance(attr, Descriptor):
            attr.value = value
        else:
            object.__setattr__(self, key, value)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _set_datablock_name(self, new_name: str):
        """Set datablock name and propagate to children (internal)."""
        self._datablock_name = new_name
        for param in self.parameters:
            param._set_datablock_name(new_name)

    def _set_entry_name(self, new_name: str) -> None:
        """Set entry ID and propagate to child parameters."""
        self._entry_name = new_name
        for param in self.parameters:
            param._set_entry_name(new_name)

    # ------------------------------------------------------------------
    # Public read-only properties
    # ------------------------------------------------------------------
    @property
    def parameters(self) -> list[Descriptor]:
        """Return all descriptor/parameter instances owned by this
        component.
        """
        return [v for v in self.__dict__.values() if isinstance(v, Descriptor)]

    @property
    def datablock_name(self) -> Optional[str]:
        """Read-only datablock name (set by parent datablock)."""
        return self._datablock_name

    @datablock_name.setter
    def datablock_name(self, _):
        self._readonly_error()

    @property
    def entry_name(self) -> Optional[str]:
        """Entry identifier (injected by parent collection)."""
        return self._entry_name

    @entry_name.setter
    def entry_name(self, _new_id: str) -> None:  # unused: interface compatibility
        self._readonly_error()

    @property
    def as_dict(self) -> dict[str, Any]:
        """Return mapping from parameter ``name`` to its current
        ``value``.
        """
        return {p.name: p.value for p in self.parameters if p.name is not None}

    @property
    def as_cif(self) -> str:
        """Return CIF tag/value lines for parameters with defined
        tags.
        """
        lines: list[str] = []
        for param in self.parameters:
            tags = getattr(param, 'full_cif_names', []) or []
            if not tags:
                continue
            value = param.value
            if value is None:
                continue
            key = tags[0]
            out_value = f'"{value}"' if isinstance(value, str) and ' ' in value else value
            lines.append(f'{key}  {out_value}')
        return '\n'.join(lines)

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def from_cif(self, block: Any, idx: int = 0) -> None:
        """Populate each parameter from CIF block at given loop
        index.
        """
        for param in self.parameters:
            param.from_cif(block, idx=idx)


class Datablock(
    DiagnosticsMixin,
    AttributeAccessGuardMixin,
    GuardedBase,
):
    """Base container for sample model or experiment categories.

    Responsibilities:
    * Guard public attribute additions
    * Propagate datablock name to contained components/collections
    * Provide aggregated parameter access
    """

    # ------------------------------------------------------------------
    # Class configuration
    # ------------------------------------------------------------------
    _allowed_attributes = {
        'name',
    }  # extend in subclasses with real children

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------
    def __init__(self) -> None:
        # TODO: check how name is set in subclasses
        self._name = None  # set later via property

    # ------------------------------------------------------------------
    # Dunder methods
    # ------------------------------------------------------------------
    def __str__(self) -> str:
        """Human-readable representation of this component."""
        s = f"{self.__class__.__name__} '{self.name}' ({len(self.parameters)} parameters)"
        for base in type(self).__mro__:
            if base is Datablock:
                s = f'{base.__name__}: {s}'
                break
        return s

    def __setattr__(self, key: str, value: Any) -> None:
        """Controlled attribute setting (with datablock propagation)."""
        if key.startswith('_'):
            object.__setattr__(self, key, value)
            return

        allowed = self._allowed_attribute_names
        if key not in allowed:
            self._set_error(key, allowed)
            return

        if isinstance(value, (CategoryItem, CategoryCollection)):
            object.__setattr__(self, key, value)
            if hasattr(value, '_set_datablock_name'):
                value._set_datablock_name(self._name)
            else:
                value.datablock_name = self._name
        else:
            object.__setattr__(self, key, value)

    # ------------------------------------------------------------------
    # Public read-only properties
    # ------------------------------------------------------------------
    @property
    def parameters(self) -> list[Descriptor]:
        """Return flattened list of parameters from all contained
        categories.
        """
        params = []
        for _attr_name, attr_obj in self.__dict__.items():
            if isinstance(attr_obj, (CategoryItem, CategoryCollection)):
                params.extend(attr_obj.parameters)
        return params

    @property
    def categories(self) -> list[Union[CategoryItem, CategoryCollection]]:
        """Return all component / collection category objects in the
        datablock.
        """
        attr_objs = []
        for attr_obj in self.__dict__.values():
            if isinstance(attr_obj, (CategoryItem, CategoryCollection)):
                attr_objs.append(attr_obj)
        return attr_objs

    @property
    def name(self) -> Optional[str]:
        """Return datablock name (may be ``None`` if unset)."""
        return self._name

    @name.setter
    def name(self, new_name: str) -> None:
        """Assign datablock name and propagate to children."""
        if not isinstance(new_name, str):
            self._type_warning('name', str, new_name)
            return
        self._name = new_name
        for category in self.categories:
            category._set_datablock_name(new_name)


class CategoryCollection(
    DiagnosticsMixin,
    AttributeAccessGuardMixin,
    GuardedBase,
):
    """Handles loop-style category containers (e.g. AtomSites).

    Each item is a CategoryItem (component).
    """

    # ------------------------------------------------------------------
    # Class configuration
    # ------------------------------------------------------------------
    _allowed_attributes = {
        'datablock_name',
    }

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------
    def __init__(self, child_class=None):
        self._items = {}
        self._child_class = child_class
        self._datablock_name = None

    # ------------------------------------------------------------------
    # Dunder methods
    # ------------------------------------------------------------------
    def __str__(self) -> str:
        """Human-readable representation of this component."""
        return f'CategoryCollection: {self.__class__.__name__} ({len(self._items)} sites)'

    def __getitem__(self, key: str) -> CategoryItem:
        return self._items[key]

    def __iter__(self) -> Iterator[CategoryItem]:
        return iter(self._items.values())

    # TODO: implement __setattr__ with propagation of ??? to children
    def __setattr__(self, key: str, value: Any) -> None:
        if key.startswith('_'):
            object.__setattr__(self, key, value)
            return

        allowed = self._allowed_attribute_names
        if key not in allowed:
            self._set_error(key, allowed)
            return

        object.__setattr__(self, key, value)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _set_datablock_name(self, new_name: str):
        """Set datablock name and propagate to children (internal)."""
        self._datablock_name = new_name
        for item in self._items.values():
            item._set_datablock_name(new_name)

    # ------------------------------------------------------------------
    # Public read-only properties
    # ------------------------------------------------------------------
    @property
    def parameters(self) -> list[Descriptor]:
        params = []
        for item in self._items.values():
            if hasattr(item, 'parameters'):
                params.extend(item.parameters)
        return params

    @property
    def datablock_name(self):
        """Read-only datablock name (set by parent datablock)."""
        return self._datablock_name

    @datablock_name.setter
    def datablock_name(self, _):
        self._readonly_error()

    @property
    def as_cif(self) -> str:
        lines: list[str] = []
        if self._items:
            # Header from first item attributes that expose CIF tags
            first_item = next(iter(self._items.values()))
            tag_attr_pairs: list[tuple[str, str]] = []  # (tag, attr_name)
            for attr_name in dir(first_item):
                if attr_name.startswith('_'):
                    continue
                attr_obj = getattr(first_item, attr_name)
                if not isinstance(attr_obj, (Descriptor, Parameter)):
                    continue
                tags = getattr(attr_obj, 'full_cif_names', []) or []
                if not tags:
                    continue
                tag_attr_pairs.append((tags[0], attr_name))
            if not tag_attr_pairs:
                return ''
            lines.append('loop_')
            header = '\n'.join(t for t, _ in tag_attr_pairs)
            lines.append(header)
            # Rows
            for item in self._items.values():
                values: list[str] = []
                for _, attr_name in tag_attr_pairs:
                    attr_obj = getattr(item, attr_name)
                    v = getattr(attr_obj, 'value', None)
                    if v is None:
                        values.append('.')
                    else:
                        s = f'{v}'
                        if isinstance(v, str) and ' ' in v:
                            s = f'"{s}"'
                        values.append(s)
                lines.append(' '.join(values))
        return '\n'.join(lines)

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def add(self, item: CategoryItem):
        # Insert the item using its entry_name.value as key
        self._items[item.entry_name.value] = item

    def from_cif(self, block):
        # Derive loop size using entry_name first CIF tag alias
        if self._child_class is None:
            raise ValueError('Child class is not defined.')
        size = 0
        child_obj = self._child_class()
        attr_name = child_obj.entry_name.name
        attr = getattr(child_obj, attr_name)
        for name in attr.full_cif_names:
            size = len(block.find_values(name))
            break
        if not size:
            return
        for row_idx in range(size):
            child_obj = self._child_class()
            child_obj.from_cif(block, idx=row_idx)
            self.add(child_obj)


class DatablockCollection(
    DiagnosticsMixin,
    AttributeAccessGuardMixin,
    GuardedBase,
    MutableMapping,
):
    """Handles top-level collections (e.g. SampleModels, Experiments).

    Each item is a Datablock.
    """

    # ------------------------------------------------------------------
    # Class configuration
    # ------------------------------------------------------------------
    _allowed_attributes = set()

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------
    def __init__(self):
        self._datablocks = {}

    # ------------------------------------------------------------------
    # Dunder methods
    # ------------------------------------------------------------------
    def __str__(self) -> str:
        """Human-readable representation of this component."""
        return f'DatablockCollection: {self.__class__.__name__} ({len(self)} items)'

    def __setattr__(self, key: str, value: Any) -> None:
        """Controlled attribute setting (with datablock propagation)."""
        if key.startswith('_'):
            object.__setattr__(self, key, value)
            return

        allowed = self._allowed_attribute_names
        if key not in allowed:
            self._set_error(key, allowed)
            return

        object.__setattr__(self, key, value)

    def __getitem__(self, name):
        return self._datablocks[name]

    def __setitem__(self, name, datablock):
        self._datablocks[name] = datablock

    def __delitem__(self, name):
        del self._datablocks[name]

    def __iter__(self):
        return iter(self._datablocks)

    def __len__(self):
        return len(self._datablocks)

    # ------------------------------------------------------------------
    # Public read-only properties
    # ------------------------------------------------------------------
    @property
    def parameters(self) -> list[Descriptor]:
        params = []
        for datablock in self._datablocks.values():
            params.extend(datablock.parameters)
        return params

    @property
    def as_cif(self) -> str:
        # Concatenate as_cif of all contained datablocks
        return '\n\n'.join(
            getattr(item, 'as_cif', '') for item in self._items.values() if hasattr(item, 'as_cif')
        )

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------
    def add(self, item):
        # Insert the item using its name as key
        self._items[item.name] = item
