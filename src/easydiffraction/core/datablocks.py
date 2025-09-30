# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import TYPE_CHECKING
from typing import Any
from typing import Generic
from typing import Optional
from typing import TypeVar
from typing import Union

from easydiffraction.core.categories import CategoryCollection
from easydiffraction.core.categories import CategoryItem
from easydiffraction.core.collections import CollectionBase
from easydiffraction.core.guards import GuardedBase

if TYPE_CHECKING:
    from easydiffraction.core.parameters import Descriptor
    from easydiffraction.core.parameters import Parameter

DatablockItemT = TypeVar('DatablockItemT', bound='DatablockItem')


class AbstractDatablock(ABC):
    # ------------------------------------------------------------------
    # Class configuration
    # ------------------------------------------------------------------
    _class_public_attrs = {
        'parameters',
    }

    # ------------------------------------------------------------------
    # Abstract API
    # ------------------------------------------------------------------
    @property
    @abstractmethod
    def parameters(self) -> list[Descriptor]:
        raise NotImplementedError

    @property
    def fittable_parameters(self) -> list[Parameter]:
        params = []
        for param in self.parameters:
            if hasattr(param, 'constrained') and not param.constrained:
                params.append(param)
        return params

    @property
    def free_parameters(self) -> list[Parameter]:
        params = []
        for param in self.fittable_parameters:
            if param.free:
                params.append(param)
        return params

    # TODO: Add abstract property 'as_cif'


class DatablockItem(
    GuardedBase,
    AbstractDatablock,
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
    _class_public_attrs = {
        'name',
        'datablock_name',
        'categories',
    }

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------
    def __init__(self) -> None:
        super().__init__()
        self._parent: Optional[Any] = None
        self._name = None  # set later via property

    # ------------------------------------------------------------------
    # Dunder methods
    # ------------------------------------------------------------------
    def __str__(self) -> str:
        """Human-readable representation of this component."""
        s = f"{self.__class__.__name__} '{self.name}' ({len(self.parameters)} parameters)"
        for base in type(self).__mro__:
            if base is DatablockItem:
                s = f'{base.__name__}: {s}'
                break
        return s

    def __setattr__(self, key: str, value: Any) -> None:
        """Controlled attribute setting (with datablock propagation)."""
        if isinstance(value, (CategoryItem, CategoryCollection)):
            value._parent = self
        super().__setattr__(key, value)  # enforces guard

    # ------------------------------------------------------------------
    # Public read-only properties
    # ------------------------------------------------------------------
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

    # For compatibility with parent delegation.
    @property
    def datablock_name(self) -> Optional[str]:
        """Return datablock name."""
        return self.name

    @property
    def full_name(self) -> str:
        return self.datablock_name

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
    def parameters(self) -> list[Descriptor]:
        """Return flattened list of parameters from all contained
        categories.
        """
        params = []
        for _attr_name, attr_obj in self.__dict__.items():
            if isinstance(attr_obj, (CategoryItem, CategoryCollection)):
                params.extend(attr_obj.parameters)
        return params


class DatablockCollection(
    CollectionBase[DatablockItemT],
    AbstractDatablock,
    Generic[DatablockItemT],
):
    """Handles top-level collections (e.g. SampleModels, Experiments).

    Each item is a Datablock.
    """

    # ------------------------------------------------------------------
    # Class configuration
    # ------------------------------------------------------------------
    _class_public_attrs = {
        'as_cif',
    }

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------
    def __init__(self, item_type: type[DatablockItemT]) -> None:
        super().__init__(item_type=item_type)

    # ------------------------------------------------------------------
    # Dunder methods
    # ------------------------------------------------------------------
    def __str__(self) -> str:
        """Human-readable representation of this component."""
        return f'{self.__class__.__name__} collection ({len(self)} items)'

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Public read-only properties
    # ------------------------------------------------------------------
    @property
    def full_name(self) -> str:
        return None  # Collections do not have names

    @property
    def parameters(self) -> list[Descriptor]:
        params = []
        for datablock in self:
            params.extend(datablock.parameters)
        return params

    # -----------
    # CIF methods
    # -----------
    @property
    def as_cif(self) -> str:
        # Concatenate as_cif of all contained datablocks
        return '\n\n'.join(
            getattr(item, 'as_cif', '') for item in self._items if hasattr(item, 'as_cif')
        )
