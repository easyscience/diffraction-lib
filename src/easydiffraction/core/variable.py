# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from easydiffraction.core.diagnostic import Diagnostics
from easydiffraction.core.guard import GuardedBase
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import DataTypes
from easydiffraction.core.validation import RangeValidator
from easydiffraction.core.validation import TypeValidator
from easydiffraction.io.cif.serialize import param_from_cif
from easydiffraction.io.cif.serialize import param_to_cif

if TYPE_CHECKING:
    from easydiffraction.io.cif.handler import CifHandler

# ======================================================================


class GenericDescriptorBase(GuardedBase):
    """
    Base class for all parameter-like descriptors.

    A descriptor encapsulates a typed value with validation,
    human-readable name/description and a globally unique identifier
    that is stable across the session. Concrete subclasses specialize
    the expected data type and can extend the public API with additional
    behavior (e.g. units).
    """

    _BOOL_SPEC_TEMPLATE = AttributeSpec(
        data_type=DataTypes.BOOL,
        default=False,
    )

    def __init__(
        self,
        *,
        value_spec: AttributeSpec,
        name: str,
        description: str = None,
    ) -> None:
        """
        Initialize the descriptor with validation and identity.

        Parameters
        ----------
        value_spec : AttributeSpec
            Validation specification for the value.
        name : str
            Local name of the descriptor within its category.
        description : str, default=None
            Optional human-readable description.
        """
        super().__init__()

        expected_type = getattr(self, '_value_type', None)

        if expected_type:
            user_type = (
                value_spec._data_type_validator.expected_type
                if value_spec._data_type_validator is not None
                else None
            )
            if user_type and user_type is not expected_type:
                Diagnostics.type_override_error(
                    type(self).__name__,
                    expected_type,
                    user_type,
                )
            else:
                # Enforce descriptor's own type if not already defined
                value_spec._data_type_validator = TypeValidator(expected_type)

        self._value_spec = value_spec
        self._name = name
        self._description = description

        # Initial validated states
        # self._value = self._value_spec.validated(
        #    value_spec.value,
        #    name=self.unique_name,
        # )

        # Assign default directly.
        # Skip validation — defaults are trusted.
        # Callable is needed for dynamic defaults like SpaceGroup
        # it_coordinate_system_code, and similar cases.
        default = value_spec.default
        self._value = default() if callable(default) else default

    def __str__(self) -> str:
        """Return the string representation of this descriptor."""
        return f'<{self.unique_name} = {self.value!r}>'

    @property
    def name(self) -> str:
        """Local name of the descriptor (without category/datablock)."""
        return self._name

    @property
    def unique_name(self) -> str:
        """Fully qualified name: datablock, category and entry."""
        parts = [
            self._identity.datablock_entry_name,
            self._identity.category_code,
            self._identity.category_entry_name,
            self.name,
        ]
        return '.'.join(filter(None, parts))

    def _parent_of_type(self, cls: type) -> object | None:
        """Traverse parents and return the first of type cls."""
        obj = getattr(self, '_parent', None)
        visited = set()
        while obj is not None and id(obj) not in visited:
            visited.add(id(obj))
            if isinstance(obj, cls):
                return obj
            obj = getattr(obj, '_parent', None)
        return None

    def _datablock_item(self) -> object | None:
        """Return the DatablockItem ancestor, if any."""
        from easydiffraction.core.datablock import DatablockItem  # noqa: PLC0415

        return self._parent_of_type(DatablockItem)

    @property
    def value(self) -> object:
        """Current validated value."""
        return self._value

    @value.setter
    def value(self, v: object) -> None:
        """Set a new value after validating against the spec."""
        # Do nothing if the value is unchanged
        if self._value == v:
            return

        # Validate and set the new value
        self._value = self._value_spec.validated(
            v,
            name=self.unique_name,
            current=self._value,
        )

        # Mark parent datablock as needing categories update
        # TODO: Check if it is actually in use?
        parent_datablock = self._datablock_item()
        if parent_datablock is not None:
            parent_datablock._need_categories_update = True

    def _set_value_from_minimizer(self, v: object) -> None:
        """
        Set the value from a minimizer, bypassing validation.

        Writes ``_value`` directly — no type or range checks — but still
        marks the owning :class:`DatablockItem` dirty so that
        ``_update_categories()`` knows work is needed.

        This exists because:

        1. Physical-range validators (e.g. intensity ≥ 0) would reject
        trial values the minimizer needs to explore. 2. Validation
        overhead is measurable over thousands of    objective-function
        evaluations.
        """
        self._value = v
        parent_datablock = self._datablock_item()
        if parent_datablock is not None:
            parent_datablock._need_categories_update = True

    @property
    def description(self) -> str | None:
        """Optional human-readable description."""
        return self._description

    @property
    def parameters(self) -> list[GenericDescriptorBase]:
        """
        Return a flat list of parameters contained by this object.

        For a single descriptor, it returns a one-element list with
        itself. Composite objects override this to flatten nested
        structures.
        """
        return [self]

    @property
    def as_cif(self) -> str:
        """Serialize this descriptor to a CIF-formatted string."""
        return param_to_cif(self)

    def from_cif(self, block: object, idx: int = 0) -> None:
        """Populate this parameter from a CIF block."""
        param_from_cif(self, block, idx)


# ======================================================================


class GenericStringDescriptor(GenericDescriptorBase):
    """Base descriptor that constrains values to strings."""

    _value_type = DataTypes.STRING

    def __init__(
        self,
        **kwargs: object,
    ) -> None:
        super().__init__(**kwargs)


# ======================================================================


class GenericNumericDescriptor(GenericDescriptorBase):
    """Base descriptor that constrains values to numbers."""

    _value_type = DataTypes.NUMERIC

    def __init__(
        self,
        *,
        units: str = '',
        **kwargs: object,
    ) -> None:
        super().__init__(**kwargs)
        self._units: str = units

    def __str__(self) -> str:
        """Return the string representation including units."""
        s: str = super().__str__()
        s = s[1:-1]  # strip <>
        if self.units:
            s += f' {self.units}'
        return f'<{s}>'

    @property
    def units(self) -> str:
        """Units associated with the numeric value, if any."""
        return self._units


# ======================================================================


class GenericParameter(GenericNumericDescriptor):
    """
    Numeric descriptor extended with fitting-related attributes.

    Adds standard attributes used by minimizers: "free" flag,
    uncertainty, bounds and an optional starting value. Subclasses can
    integrate with specific backends while preserving this interface.
    """

    def __init__(
        self,
        **kwargs: object,
    ) -> None:
        super().__init__(**kwargs)

        # Initial validated states
        self._free_spec = self._BOOL_SPEC_TEMPLATE
        self._free = self._free_spec.default
        self._uncertainty_spec = AttributeSpec(
            data_type=DataTypes.NUMERIC,
            validator=RangeValidator(ge=0),
            allow_none=True,
        )
        self._uncertainty = self._uncertainty_spec.default
        self._fit_min_spec = AttributeSpec(data_type=DataTypes.NUMERIC, default=-np.inf)
        self._fit_min = self._fit_min_spec.default
        self._fit_max_spec = AttributeSpec(data_type=DataTypes.NUMERIC, default=np.inf)
        self._fit_max = self._fit_max_spec.default
        self._start_value_spec = AttributeSpec(data_type=DataTypes.NUMERIC, default=0.0)
        self._start_value = self._start_value_spec.default
        self._constrained_spec = self._BOOL_SPEC_TEMPLATE
        self._constrained = self._constrained_spec.default

    def __str__(self) -> str:
        """Return string representation with uncertainty and free."""
        s = GenericDescriptorBase.__str__(self)
        s = s[1:-1]  # strip <>
        if self.uncertainty is not None:
            s += f' ± {self.uncertainty}'
        if self.units is not None:
            s += f' {self.units}'
        s += f' (free={self.free})'
        return f'<{s}>'

    @property
    def _minimizer_uid(self) -> str:
        """Variant of unique_name that is safe for minimizer engines."""
        return self.unique_name.replace('.', '__')

    @property
    def constrained(self) -> bool:
        """Whether this parameter is part of a constraint expression."""
        return self._constrained

    def _set_value_constrained(self, v: object) -> None:
        """
        Set the value from a constraint expression.

        Validates against the spec, marks the parent datablock dirty,
        and flags the parameter as constrained. Used exclusively by
        ``ConstraintsHandler.apply()``.
        """
        self.value = v
        self._constrained = True

    @property
    def free(self) -> bool:
        """Whether this parameter is currently varied during fitting."""
        return self._free

    @free.setter
    def free(self, v: bool) -> None:
        """Set the "free" flag after validation."""
        self._free = self._free_spec.validated(
            v, name=f'{self.unique_name}.free', current=self._free
        )

    @property
    def uncertainty(self) -> float | None:
        """Estimated standard uncertainty of the fitted value."""
        return self._uncertainty

    @uncertainty.setter
    def uncertainty(self, v: float | None) -> None:
        """Set the uncertainty value (must be non-negative or None)."""
        self._uncertainty = self._uncertainty_spec.validated(
            v, name=f'{self.unique_name}.uncertainty', current=self._uncertainty
        )

    @property
    def fit_min(self) -> float:
        """Lower fitting bound."""
        return self._fit_min

    @fit_min.setter
    def fit_min(self, v: float) -> None:
        """Set the lower bound for the parameter value."""
        self._fit_min = self._fit_min_spec.validated(
            v, name=f'{self.unique_name}.fit_min', current=self._fit_min
        )

    @property
    def fit_max(self) -> float:
        """Upper fitting bound."""
        return self._fit_max

    @fit_max.setter
    def fit_max(self, v: float) -> None:
        """Set the upper bound for the parameter value."""
        self._fit_max = self._fit_max_spec.validated(
            v, name=f'{self.unique_name}.fit_max', current=self._fit_max
        )


# ======================================================================


class StringDescriptor(GenericStringDescriptor):
    """String descriptor bound to a CIF handler."""

    def __init__(
        self,
        *,
        cif_handler: CifHandler,
        **kwargs: object,
    ) -> None:
        """
        Initialize a string descriptor bound to a CIF handler.

        Parameters
        ----------
        cif_handler : CifHandler
            Object that tracks CIF identifiers.
        **kwargs : object
            Forwarded to GenericStringDescriptor.
        """
        super().__init__(**kwargs)
        self._cif_handler = cif_handler
        self._cif_handler.attach(self)


# ======================================================================


class NumericDescriptor(GenericNumericDescriptor):
    """Numeric descriptor bound to a CIF handler."""

    def __init__(
        self,
        *,
        cif_handler: CifHandler,
        **kwargs: object,
    ) -> None:
        """
        Numeric descriptor bound to a CIF handler.

        Parameters
        ----------
        cif_handler : CifHandler
            Object that tracks CIF identifiers.
        **kwargs : object
            Forwarded to GenericNumericDescriptor.
        """
        super().__init__(**kwargs)
        self._cif_handler = cif_handler
        self._cif_handler.attach(self)


# ======================================================================


class Parameter(GenericParameter):
    """Fittable parameter bound to a CIF handler."""

    def __init__(
        self,
        *,
        cif_handler: CifHandler,
        **kwargs: object,
    ) -> None:
        """
        Fittable parameter bound to a CIF handler.

        Parameters
        ----------
        cif_handler : CifHandler
            Object that tracks CIF identifiers.
        **kwargs : object
            Forwarded to GenericParameter.
        """
        super().__init__(**kwargs)
        self._cif_handler = cif_handler
        self._cif_handler.attach(self)
