# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from easydiffraction.core.diagnostic import Diagnostics
from easydiffraction.core.guard import GuardedBase
from easydiffraction.core.units_vocabulary import normalize_units_code
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import DataTypes
from easydiffraction.core.validation import MembershipValidator
from easydiffraction.core.validation import RangeValidator
from easydiffraction.core.validation import TypeValidator
from easydiffraction.io.cif.serialize import param_from_cif
from easydiffraction.io.cif.serialize import param_to_cif
from easydiffraction.utils.logging import log

if TYPE_CHECKING:
    from enum import StrEnum

    from easydiffraction.core.display_handler import DisplayHandler
    from easydiffraction.core.posterior import PosteriorParameterSummary
    from easydiffraction.io.cif.handler import CifHandler

# ======================================================================

DEFAULT_FIT_BOUNDS_MULTIPLIER = 4.0


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
        description: str | None = None,
        display_handler: DisplayHandler | None = None,
    ) -> None:
        """
        Initialize the descriptor with validation and identity.

        Parameters
        ----------
        value_spec : AttributeSpec
            Validation specification for the value.
        name : str
            Local name of the descriptor within its category.
        description : str | None, default=None
            Optional human-readable description.
        display_handler : DisplayHandler | None, default=None
            Optional labels and units for display contexts.
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
        self._display_handler = display_handler

        # Initial validated states
        # self._value = self._value_spec.validated(
        #    value_spec.value,
        #    name=self.unique_name,
        # )

        # Assign default directly.
        # Skip validation — defaults are trusted.
        # Callable is needed for dynamic defaults like SpaceGroup
        # it_coordinate_system_code, and similar cases.
        self._value = value_spec.default_value()

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

    def _category_owner(self) -> object | None:
        """Return the CategoryOwner ancestor, if any."""
        from easydiffraction.core.category_owner import CategoryOwner  # noqa: PLC0415

        return self._parent_of_type(CategoryOwner)

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

        # Mark the owning category owner as needing an update
        # TODO: Check if it is actually in use?
        parent_owner = self._category_owner()
        if parent_owner is not None:
            parent_owner._need_categories_update = True

    def _set_value_from_minimizer(self, v: object) -> None:
        """
        Set the value from a minimizer, bypassing validation.

        Writes ``_value`` directly — no type or range checks — but still
        marks the owning category owner dirty so that
        ``_update_categories()`` knows work is needed.

        This exists because:

        1. Physical-range validators (e.g. intensity ≥ 0) would reject
        trial values the minimizer needs to explore. 2. Validation
        overhead is measurable over thousands of    objective-function
        evaluations.
        """
        self._value = v
        parent_owner = self._category_owner()
        if parent_owner is not None:
            parent_owner._need_categories_update = True

    @property
    def description(self) -> str | None:
        """Optional human-readable description."""
        return self._description

    @property
    def display_handler(self) -> DisplayHandler | None:
        """Optional labels and units for display contexts."""
        return self._display_handler

    def resolve_display_name(self, context: str) -> str:
        """
        Return the display label for the requested context.

        Parameters
        ----------
        context : str
            One of ``'latex'``, ``'html'``, or ``'gui'``.

        Returns
        -------
        str
            Resolved display label.
        """
        self._validate_display_context(context)
        if self._display_handler is None:
            return self.name
        if context == 'latex':
            return self._display_handler.latex_name or self.name
        return self._display_handler.display_name or self.name

    def resolve_display_units(self, context: str) -> str:
        """
        Return the display units for the requested context.

        Parameters
        ----------
        context : str
            One of ``'latex'``, ``'html'``, or ``'gui'``.

        Returns
        -------
        str
            Resolved display units.
        """
        self._validate_display_context(context)
        fallback = str(getattr(self, '_units', ''))
        if fallback == 'none':
            fallback = ''
        if self._display_handler is None:
            return fallback
        if context == 'latex':
            return self._display_handler.latex_units or fallback
        return self._display_handler.display_units or fallback

    @staticmethod
    def _validate_display_context(context: str) -> None:
        """Validate a descriptor display context."""
        if context not in {'latex', 'html', 'gui'}:
            msg = "context must be one of 'latex', 'html', or 'gui'."
            raise ValueError(msg)

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


class GenericBoolDescriptor(GenericDescriptorBase):
    """Base descriptor that constrains values to booleans."""

    _value_type = DataTypes.BOOL

    def __init__(
        self,
        *,
        value_spec: AttributeSpec | None = None,
        **kwargs: object,
    ) -> None:
        if value_spec is None:
            value_spec = AttributeSpec(
                data_type=DataTypes.BOOL,
                default=False,
            )
        super().__init__(value_spec=value_spec, **kwargs)


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
        self._units: str = normalize_units_code(units)

    def __str__(self) -> str:
        """Return the string representation including units."""
        s: str = super().__str__()
        s = s[1:-1]  # strip <>
        if self.units != 'none':
            s += f' {self.units}'
        return f'<{s}>'

    @property
    def units(self) -> str:
        """Units associated with the numeric value, if any."""
        return self._units


# ======================================================================


class GenericIntegerDescriptor(GenericNumericDescriptor):
    """Base descriptor that constrains values to integers."""

    _value_type = DataTypes.INTEGER


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
        self._fit_bounds_uncertainty_multiplier: float | None = None
        self._start_value_spec = AttributeSpec(data_type=DataTypes.NUMERIC, default=0.0)
        self._start_value = self._start_value_spec.default
        self._user_constrained_spec = self._BOOL_SPEC_TEMPLATE
        self._user_constrained = self._user_constrained_spec.default
        self._symmetry_constrained_spec = self._BOOL_SPEC_TEMPLATE
        self._symmetry_constrained = self._symmetry_constrained_spec.default
        self._posterior: PosteriorParameterSummary | None = None

    def _physical_lower_bound(self) -> float:
        """
        Return the lower physical limit from the value spec, or -inf.
        """
        validator = getattr(self._value_spec, '_validator', None)
        if isinstance(validator, RangeValidator):
            return validator.ge
        return -np.inf

    def _physical_upper_bound(self) -> float:
        """
        Return the upper physical limit from the value spec, or inf.
        """
        validator = getattr(self._value_spec, '_validator', None)
        if isinstance(validator, RangeValidator):
            return validator.le
        return np.inf

    def __str__(self) -> str:
        """Return string representation with uncertainty and free."""
        s = GenericDescriptorBase.__str__(self)
        s = s[1:-1]  # strip <>
        if self.uncertainty is not None:
            s += f' ± {self.uncertainty}'
        if self.units != 'none':
            s += f' {self.units}'
        s += f' (free={self.free})'
        return f'<{s}>'

    @property
    def _minimizer_uid(self) -> str:
        """Variant of unique_name that is safe for minimizer engines."""
        return self.unique_name.replace('.', '__')

    @property
    def user_constrained(self) -> bool:
        """Whether this parameter is part of a constraint expression."""
        return self._user_constrained

    def _set_value_user_constrained(self, v: object) -> None:
        """
        Set the value from a constraint expression.

        Bypasses validation and marks the parent category owner dirty,
        like ``_set_value_from_minimizer``, because constraints are
        applied inside the minimizer loop where trial values may exceed
        physical-range validators. Flags the parameter as user
        constrained. Used exclusively by ``ConstraintsHandler.apply()``.
        """
        self._value = v
        self._user_constrained = True
        parent_owner = self._category_owner()
        if parent_owner is not None:
            parent_owner._need_categories_update = True

    @property
    def free(self) -> bool:
        """Whether this parameter is currently varied during fitting."""
        return self._free

    @free.setter
    def free(self, v: bool) -> None:
        """Set the "free" flag after validation."""
        validated = self._free_spec.validated(
            v, name=f'{self.unique_name}.free', current=self._free
        )
        if validated and self._symmetry_constrained:
            log.warning(
                f"Parameter '{self.unique_name}' is constrained by symmetry. Ignoring free=True."
            )
            self._free = False
            return
        self._free = validated

    @property
    def symmetry_constrained(self) -> bool:
        """
        Return whether symmetry constrains this parameter.
        """
        return self._symmetry_constrained

    def _set_symmetry_constrained(self, *, value: bool) -> None:
        """
        Mark or unmark this parameter as constrained by symmetry.

        When set to True, ``free`` is forced to False and any subsequent
        attempt to set ``free = True`` is ignored with a warning. When
        cleared (set to False), the parameter becomes refinable again
        but ``free`` is left at its current value.

        Parameters
        ----------
        value : bool
            New symmetry-constrained state.
        """
        validated = self._symmetry_constrained_spec.validated(
            value,
            name=f'{self.unique_name}.symmetry_constrained',
            current=self._symmetry_constrained,
        )
        self._symmetry_constrained = validated
        if validated:
            self._free = False

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
    def posterior(self) -> PosteriorParameterSummary | None:
        """Posterior summary from a Bayesian fit, if available."""
        return self._posterior

    def _set_posterior(self, value: PosteriorParameterSummary | None) -> None:
        """Set the posterior summary for internal callers."""
        self._posterior = value

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
        self._fit_bounds_uncertainty_multiplier = None

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
        self._fit_bounds_uncertainty_multiplier = None

    @property
    def fit_bounds_uncertainty_multiplier(self) -> float | None:
        """
        Multiplier used for uncertainty-derived fit bounds, if known.
        """
        return self._fit_bounds_uncertainty_multiplier

    def _set_fit_bounds_uncertainty_multiplier(self, value: float | None) -> None:
        """Set the cached uncertainty-derived fit-bounds multiplier."""
        self._fit_bounds_uncertainty_multiplier = value

    def set_fit_bounds_from_uncertainty(
        self,
        multiplier: float = DEFAULT_FIT_BOUNDS_MULTIPLIER,
        *,
        clip_to_limits: bool = True,
    ) -> None:
        """
        Set fit bounds from the current standard uncertainty.

        Parameters
        ----------
        multiplier : float, default=DEFAULT_FIT_BOUNDS_MULTIPLIER
            Positive finite factor applied symmetrically to the current
            parameter uncertainty.
        clip_to_limits : bool, default=True
            Whether to clip the resolved fit bounds to the parameter's
            physical lower and upper limits when those are finite.

        Raises
        ------
        ValueError
            If the current value, uncertainty, or multiplier is missing,
            invalid, or produces non-increasing bounds.
        """
        name = self.unique_name
        value = self.value
        uncertainty = self.uncertainty

        if value is None or not np.isfinite(float(value)):
            msg = f'Cannot set fit bounds for {name}: current value is missing or invalid.'
            raise ValueError(msg)

        resolved_multiplier = float(multiplier)
        if isinstance(multiplier, bool) or not np.isfinite(resolved_multiplier):
            msg = 'multiplier must be a positive finite number.'
            raise ValueError(msg)
        if resolved_multiplier <= 0:
            msg = 'multiplier must be a positive finite number.'
            raise ValueError(msg)

        if uncertainty is None or uncertainty <= 0 or not np.isfinite(float(uncertainty)):
            msg = f'Cannot set fit bounds for {name}: uncertainty is missing or invalid.'
            raise ValueError(msg)

        lower = float(value) - resolved_multiplier * float(uncertainty)
        upper = float(value) + resolved_multiplier * float(uncertainty)

        if clip_to_limits:
            physical_lower = float(self._physical_lower_bound())
            physical_upper = float(self._physical_upper_bound())
            if np.isfinite(physical_lower):
                lower = max(lower, physical_lower)
            if np.isfinite(physical_upper):
                upper = min(upper, physical_upper)

        if lower >= upper:
            msg = (
                f'Cannot set fit bounds for {name}: resolved lower bound {lower} '
                f'is not below upper bound {upper}.'
            )
            raise ValueError(msg)

        self.fit_min = lower
        self.fit_max = upper
        self._fit_bounds_uncertainty_multiplier = resolved_multiplier


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


class EnumDescriptor(StringDescriptor):
    """
    String descriptor bound to a closed ``(str, Enum)`` value set.

    Derives validation and the default from ``enum`` and exposes
    ``show_supported()`` listing the members with the active one marked,
    matching the switchable-category table (value-selector-discovery
    ADR).
    """

    def __init__(
        self,
        *,
        name: str,
        enum: type[StrEnum],
        cif_handler: CifHandler,
        description: str | None = None,
        default: str | None = None,
        display_handler: DisplayHandler | None = None,
    ) -> None:
        """
        Initialize an enum-backed string descriptor.

        Parameters
        ----------
        name : str
            Local name of the descriptor within its category.
        enum : type[StrEnum]
            The ``(str, Enum)`` class whose members are the allowed
            values.
        cif_handler : CifHandler
            Object that tracks CIF identifiers.
        description : str | None, default=None
            Optional human-readable description.
        default : str | None, default=None
            Default value; falls back to ``enum.default()`` when
            omitted.
        display_handler : DisplayHandler | None, default=None
            Optional labels and units for display contexts.
        """
        self._enum = enum
        resolved_default = enum.default().value if default is None else default
        value_spec = AttributeSpec(
            default=resolved_default,
            validator=MembershipValidator(allowed=[member.value for member in enum]),
        )
        super().__init__(
            name=name,
            description=description,
            value_spec=value_spec,
            cif_handler=cif_handler,
            display_handler=display_handler,
        )

    @property
    def enum(self) -> type[StrEnum]:
        """Return the ``(str, Enum)`` class backing this selector."""
        return self._enum

    def show_supported(self) -> None:
        """List the accepted values, marking the active one."""
        # Lazy display imports keep core/ free of heavy imports on this
        # rarely-called path (mirrors help()).
        from easydiffraction.utils.logging import console  # noqa: PLC0415
        from easydiffraction.utils.utils import render_table  # noqa: PLC0415

        current = self.value
        columns_data = [
            ['*' if member.value == current else '', member.value, member.description()]
            for member in self._enum
        ]
        title = self._name.replace('_', ' ').title()
        console.paragraph(f'{title} types')
        render_table(
            columns_headers=['', 'Value', 'Description'],
            columns_alignment=['left', 'left', 'left'],
            columns_data=columns_data,
        )


# ======================================================================


class BoolDescriptor(GenericBoolDescriptor):
    """Boolean descriptor bound to a CIF handler."""

    def __init__(
        self,
        *,
        cif_handler: CifHandler,
        **kwargs: object,
    ) -> None:
        """
        Initialize a boolean descriptor bound to a CIF handler.

        Parameters
        ----------
        cif_handler : CifHandler
            Object that tracks CIF identifiers.
        **kwargs : object
            Forwarded to GenericBoolDescriptor.
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


class IntegerDescriptor(GenericIntegerDescriptor):
    """Integer descriptor bound to a CIF handler."""

    def __init__(
        self,
        *,
        cif_handler: CifHandler,
        **kwargs: object,
    ) -> None:
        """
        Integer descriptor bound to a CIF handler.

        Parameters
        ----------
        cif_handler : CifHandler
            Object that tracks CIF identifiers.
        **kwargs : object
            Forwarded to GenericIntegerDescriptor.
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
