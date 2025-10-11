# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import uuid
from typing import Any
from typing import final

import numpy as np

from easydiffraction.core.diagnostics import Diagnostics
from easydiffraction.core.guards import GuardedBase
from easydiffraction.core.singletons import UidMapHandler
from easydiffraction.core.validation import AttributeSpec
from easydiffraction.core.validation import RangeValidator
from easydiffraction.core.validation import TypeValidator


class GenericDescriptorBase(GuardedBase):
    """..."""

    _BOOL_SPEC_TEMPLATE = AttributeSpec(
        type_=bool,
        default=False,
    )

    def __init__(
        self,
        *,
        value_spec: AttributeSpec,
        name: str,
        description: str = None,
    ):
        super().__init__()

        expected_type = getattr(self, '_value_type', None)

        if expected_type:
            user_type = (
                value_spec._type_validator.expected_type
                if value_spec._type_validator is not None
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
                value_spec._type_validator = TypeValidator(expected_type)

        self._value_spec = value_spec
        self._name = name
        self._description = description
        self._uid: str = self._generate_uid()
        UidMapHandler.get().add_to_uid_map(self)

        # Initial validated states
        self._value = self._value_spec.validated(
            value_spec.value,
            name=self.unique_name,
        )

    def __str__(self) -> str:
        return f'<{self.unique_name} = {self.value!r}>'

    @staticmethod
    def _generate_uid() -> str:
        return uuid.uuid4().hex[:8]

    @property
    def uid(self):
        return self._uid

    @property
    def name(self) -> str:
        return self._name

    @property
    def unique_name(self):
        # 7c: Use filter(None, [...])
        parts = [
            self._identity.datablock_entry_name,
            self._identity.category_code,
            self._identity.category_entry_name,
            self.name,
        ]
        return '.'.join(filter(None, parts))

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, v):
        self._value = self._value_spec.validated(
            v,
            name=self.unique_name,
            current=self._value,
        )

    @property
    def description(self):
        return self._description

    @property
    def parameters(self):
        # For a single descriptor, itself is the only parameter.
        return [self]

    @property
    def as_cif(self) -> str:
        tags = self._cif_handler.names
        main_key = tags[0]
        value = self.value
        value = f'"{value}"' if isinstance(value, str) and ' ' in value else value
        return f'{main_key} {value}'


@final
class GenericDescriptorStr(GenericDescriptorBase):
    _value_type = str

    def __init__(
        self,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)


@final
class GenericDescriptorFloat(GenericDescriptorBase):
    _value_type = float

    def __init__(
        self,
        *,
        units: str = '',
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._units: str = units

    def __str__(self) -> str:
        s: str = super().__str__()
        s = s[1:-1]  # strip <>
        if self.units:
            s += f' {self.units}'
        return f'<{s}>'

    @property
    def units(self) -> str:
        return self._units


class GenericParameter(GenericDescriptorFloat):
    """..."""

    def __init__(
        self,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)

        # Initial validated states
        self._free_spec = self._BOOL_SPEC_TEMPLATE
        self._free = self._free_spec.default
        self._uncertainty_spec = AttributeSpec(
            type_=float,
            content_validator=RangeValidator(ge=0),
        )
        self._uncertainty = self._uncertainty_spec.default
        self._fit_min_spec = AttributeSpec(type_=float, default=-np.inf)
        self._fit_min = self._fit_min_spec.default
        self._fit_max_spec = AttributeSpec(type_=float, default=np.inf)
        self._fit_max = self._fit_max_spec.default
        self._start_value_spec = AttributeSpec(type_=float, default=0.0)
        self._start_value = self._start_value_spec.default
        self._constrained_spec = self._BOOL_SPEC_TEMPLATE
        self._constrained = self._constrained_spec.default

    def __str__(self) -> str:
        s = GenericDescriptorBase.__str__(self)
        s = s[1:-1]  # strip <>
        if self.uncertainty is not None:
            s += f' ± {self.uncertainty}'
        if self.units is not None:
            s += f' {self.units}'
        s += f' (free={self.free})'
        return f'<{s}>'

    @property
    def _minimizer_uid(self):
        """Return variant of uid safe for minimizer engines."""
        # return self.unique_name.replace('.', '__')
        return self.uid

    @property
    def name(self) -> str:
        return self._name

    @property
    def unique_name(self):
        parts = [
            self._identity.datablock_entry_name,
            self._identity.category_code,
            self._identity.category_entry_name,
            self.name,
        ]
        return '.'.join(filter(None, parts))

    @property
    def constrained(self):
        return self._constrained

    @property
    def free(self):
        return self._free

    @free.setter
    def free(self, v):
        self._free = self._free_spec.validated(
            v, name=f'{self.unique_name}.free', current=self._free
        )

    @property
    def uncertainty(self):
        return self._free

    @uncertainty.setter
    def uncertainty(self, v):
        self._uncertainty = self._uncertainty_spec.validated(
            v, name=f'{self.unique_name}.uncertainty', current=self._uncertainty
        )

    @property
    def fit_min(self):
        return self._fit_min

    @fit_min.setter
    def fit_min(self, v):
        self._fit_min = self._fit_min_spec.validated(
            v, name=f'{self.unique_name}.fit_min', current=self._fit_min
        )

    @property
    def fit_max(self):
        return self._fit_max

    @fit_max.setter
    def fit_max(self, v):
        self._fit_max = self._fit_max_spec.validated(
            v, name=f'{self.unique_name}.fit_max', current=self._fit_max
        )


class CifHandler:
    def __init__(self, *, names: list[str]) -> None:
        self._names = names
        self._owner = None  # will be linked later

    def attach(self, owner):
        """Attach handler to its owning descriptor or parameter."""
        self._owner = owner

    @property
    def names(self):
        return self._names

    @property
    def uid(self) -> str | None:
        """Return CIF UID derived from the owner's unique name."""
        if self._owner is None:
            return None
        return self._owner.unique_name


class DescriptorStr(GenericDescriptorStr):
    def __init__(
        self,
        *,
        cif_handler: CifHandler,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._cif_handler = cif_handler
        self._cif_handler.attach(self)


class DescriptorFloat(GenericDescriptorFloat):
    def __init__(
        self,
        *,
        cif_handler: CifHandler,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._cif_handler = cif_handler
        self._cif_handler.attach(self)


class Parameter(GenericParameter):
    def __init__(
        self,
        *,
        cif_handler: CifHandler,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._cif_handler = cif_handler
        self._cif_handler.attach(self)
