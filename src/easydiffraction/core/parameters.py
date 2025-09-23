from __future__ import annotations

import secrets
import string
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


class Descriptor(
    DiagnosticsMixin,
    AttributeAccessGuardMixin,
    AttributeSetGuardMixin,
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
        'category_entry_name',
        'units',
        'description',
        'editable',
        'allowed_values',
        'uid',
        'full_name',
    }

    # All allowed attributes
    _class_public_attrs = _readonly_attributes | _writable_attributes
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
        units:
            Physical units (if applicable).
        description:
            Long-form description or help text.
        editable:
            If false the value should not be manually changed by users.
        allowed_values:
            Optional list of enumerated allowed values.
        """
        self._parent: Optional[Any] = None

        # Identity
        self._name = name
        self._pretty_name = pretty_name

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
        UidMapHandler.get().add_to_uid_map(self)

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
        if self._guarded_setattr(key, value):
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
        ``category_entry_name`` and final ``name``.
        """
        parts = []
        if self.datablock_name is not None:
            parts.append(self.datablock_name)
        if self.category_key is not None:
            parts.append(self.category_key)
        if self.category_entry_name is not None:
            parts.append(str(self.category_entry_name))  # TODO: stringify (bkg)?
        parts.append(self.name)
        return '.'.join(parts)

    @full_name.setter
    def full_name(self, _):  # pragma: no cover - defensive
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

    @property
    def cif_uid(self):
        return self.name  # TODO: Modify to return CIF-specific names?

    @cif_uid.setter
    def cif_uid(self, _):
        self._readonly_error()

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
        # Try to find the value(s) from the CIF block iterating over
        # the possible cif names in order of preference.
        found_values: list[Any] = []
        for tag in self.full_cif_names:
            candidate = list(block.find_values(tag))
            if candidate:
                found_values = candidate
                break
        # Return default if no value(s) found in CIF
        if not found_values:
            self.value = self.default_value
            return
        # If found, extract the requested index for loop categories.
        # Use first value in case of single item category
        raw = found_values[idx]
        # Parse value and uncertainty in case of expected float type
        if self.value_type is float:
            u = str_to_ufloat(raw)
            self.value = u.n
            if hasattr(self, 'uncertainty'):
                self.uncertainty = u.s  # type: ignore[attr-defined]
        # Parse string value, stripping a single matching quote pair if
        # present
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
        'uncertainty',
        'start_value',
        'fit_min',
        'fit_max',
    }

    # Extend read-only attributes
    _readonly_attributes = Descriptor._readonly_attributes | {
        'physical_min',
        'physical_max',
    }

    # All allowed attributes
    _class_public_attrs = _readonly_attributes | _writable_attributes

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
        """Initialize a Parameter.

        Args:
            value: Initial floating value.
            name: Internal symbolic name.
            full_cif_names: Ordered CIF tag aliases.
            default_value: Fallback when CIF extraction fails.
            pretty_name: Human readable label.
            units: Display / physical units.
            description: Long form description.
            editable: Whether user may manually edit value.
            uncertainty: Standard uncertainty (sigma).
            free: True if parameter is free during refinement.
            constrained: True if constrained by symmetry.
            physical_min: Physical lower bound.
            physical_max: Physical upper bound.
            fit_min: Lower bound during refinement.
            fit_max: Upper bound during refinement.
        """
        super().__init__(
            value=value,
            name=name,
            value_type=float,
            full_cif_names=full_cif_names,
            default_value=default_value,
            pretty_name=pretty_name,
            units=units,
            description=description,
            editable=editable,
        )

        self._uncertainty = uncertainty
        self._free = free
        self._constrained = constrained
        self._physical_min = physical_min
        self._physical_max = physical_max
        self._fit_min = fit_min
        self._fit_max = fit_max

        # TODO: Used in minimization. Check if needed.
        self.start_value = None

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
    def _minimizer_uid(self):
        """Return variant of uid safe for minimizer engines."""
        return self.full_name.replace('.', '__')

    # ------------------------------------------------------------------
    # Public read-only properties
    # ------------------------------------------------------------------

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

    @property
    def fit_min(self):
        return self._fit_min

    @fit_min.setter
    def fit_min(self, value):
        self._fit_min = value

    @property
    def fit_max(self):
        return self._fit_max

    @fit_max.setter
    def fit_max(self, value):
        self._fit_max = value

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
        # Auto-cast int to float
        if isinstance(new_value, int):
            new_value = float(new_value)  # TODO: how to get rid of this?
        # Type check (reuse Descriptor's logic)
        if self.value_type and not isinstance(new_value, self.value_type):
            self._type_warning(self.name, self.value_type, new_value)
            return
        # Range check
        if not (self.physical_min <= new_value <= self.physical_max):
            self._range_warning(self.name, new_value, self.physical_min, self.physical_max)
            return
        self._value = new_value
