from __future__ import annotations

import secrets
import string
from typing import TYPE_CHECKING
from typing import Any
from typing import Optional

import numpy as np

from easydiffraction.core.guards import GuardedBase
from easydiffraction.core.guards import Validator
from easydiffraction.core.guards import checktype

if TYPE_CHECKING:
    from easydiffraction.crystallography.cif import CifHandler


class ValidatedBase(GuardedBase):
    _expected_type: type = Any  # TODO: not in use yet

    def __init__(
        self,
        *,
        name: str,
        validator: Validator,
        value: Any,
    ) -> None:
        super().__init__()
        self._name: str = name
        self._validator: Validator = validator
        self._value: Any = self._validator.validate(
            name=self.unique_name,
            new=value,
            current=None,
        )

    @property
    def _log_name(self) -> str:
        return f'{type(self).__name__} {self.name}'

    @property
    def name(self) -> str:
        return self._name

    @property
    def value(self) -> Any:
        return self._value

    @value.setter
    @checktype
    def value(self, new: Any) -> None:
        self._value = self._validator.validate(
            name=self.unique_name,
            new=new,
            current=self._value,
        )


class GenericDescriptorBase(ValidatedBase):
    def __init__(
        self,
        *,
        description: str = '',
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._description: str = description
        self._uid: str = self._generate_uid()

    def __str__(self) -> str:
        return f'<{self._log_name} = {self.value!r}>'

    @staticmethod
    def _generate_uid() -> str:
        length: int = 16
        return ''.join(secrets.choice(string.ascii_lowercase) for _ in range(length))

    @property
    def description(self) -> str:
        return self._description

    @property
    def uid(self):
        return self._uid

    @property
    def unique_name(self):
        parts = [
            self._identity.datablock_entry_name,
            self._identity.category_code,
            self._identity.category_entry_name,
            self.name,
        ]
        return '.'.join(p for p in parts if p is not None)

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


class GenericDescriptorStr(GenericDescriptorBase):
    _expected_type = str  # TODO: not in use yet

    def __init__(
        self,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)


class GenericDescriptorFloat(GenericDescriptorBase):
    _expected_type = float  # TODO: not in use yet

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
    """Numeric parameter with runtime validation and safe assignment."""

    def __init__(
        self,
        *,
        free: bool = False,
        uncertainty: Optional[float] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._free: bool = free
        self._uncertainty: Optional[float] = uncertainty
        self._fit_min: float = -np.inf  # TODO: consider renaming
        self._fit_max: float = np.inf  # TODO: consider renaming
        self._start_value: float
        self._constrained: bool = False  # TODO: freeze

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
    def free(self) -> bool:
        return self._free

    @free.setter
    @checktype
    def free(self, new: bool) -> None:
        self._free = new

    @property
    def uncertainty(self) -> Optional[float]:
        return self._uncertainty

    @uncertainty.setter
    @checktype
    def uncertainty(self, new: Optional[float]) -> None:
        self._uncertainty = new

    @property
    def fit_min(self) -> float:
        return -np.inf

    @fit_min.setter
    @checktype
    def fit_min(self, new: float) -> None:
        self._fit_min = new

    @property
    def fit_max(self) -> float:
        return np.inf

    @fit_max.setter
    @checktype
    def fit_max(self, new: float) -> None:
        self._fit_max = new

    @property
    def constrained(self) -> bool:
        return self._constrained

    @property
    def _minimizer_uid(self):
        """Return variant of uid safe for minimizer engines."""
        # return self.unique_name.replace('.', '__')
        return self.uid


class DescriptorStr(GenericDescriptorStr):
    def __init__(
        self,
        *,
        cif_handler: CifHandler,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._cif_handler = cif_handler


class DescriptorFloat(GenericDescriptorFloat):
    def __init__(
        self,
        *,
        cif_handler: CifHandler,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._cif_handler = cif_handler


class Parameter(GenericParameter):
    def __init__(
        self,
        *,
        cif_handler: CifHandler,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._cif_handler = cif_handler
