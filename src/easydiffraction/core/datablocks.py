from __future__ import annotations

from collections.abc import MutableMapping
from typing import Any
from typing import List
from typing import Optional
from typing import Union

from easydiffraction.core.categories import CategoryCollection
from easydiffraction.core.categories import CategoryItem
from easydiffraction.core.guards import GuardedBase
from easydiffraction.core.parameters import Descriptor
from easydiffraction.core.parameters import Parameter


class Datablock(GuardedBase):
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
        'datablock_name',  # for compatibility with parent delegation
    }  # extend in subclasses with real children

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------
    def __init__(self) -> None:
        self._parent: Optional[Any] = None
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
        if isinstance(value, (CategoryItem, CategoryCollection)):
            value._parent = self
        super().__setattr__(key, value)  # enforces guard

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

    # For compatibility with parent delegation.
    datablock_name = name


class DatablockCollection(GuardedBase, MutableMapping):
    """Handles top-level collections (e.g. SampleModels, Experiments).

    Each item is a Datablock.
    """

    # ------------------------------------------------------------------
    # Class configuration
    # ------------------------------------------------------------------
    _class_public_attrs = set()

    # ------------------------------------------------------------------
    # Initialization
    # ------------------------------------------------------------------
    def __init__(self):
        self._parent: Optional[Any] = None
        self._datablocks = {}

    # ------------------------------------------------------------------
    # Dunder methods
    # ------------------------------------------------------------------
    def __str__(self) -> str:
        """Human-readable representation of this component."""
        return f'DatablockCollection: {self.__class__.__name__} ({len(self)} items)'

    def __setattr__(self, key: str, value: Any) -> None:
        """Controlled attribute setting (with datablock propagation)."""
        if isinstance(value, (CategoryItem, CategoryCollection)):
            value._parent = self
        super.__setattr__(self, key, value)

    def __getitem__(self, name):
        return self._datablocks[name]

    def __setitem__(self, name, datablock):
        datablock._parent = self
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

    # TODO: Need refactoring to updated API
    def get_fittable_params(self) -> List[Parameter]:
        params = []
        for param in self.parameters:
            if isinstance(param, Parameter) and not param.constrained:
                params.append(param)
        return params

    # TODO: Need refactoring to updated API
    def get_free_params(self) -> List[Parameter]:
        params = []
        for param in self.get_fittable_params():
            if param.free:
                params.append(param)
        return params

    @property
    def as_cif(self) -> str:
        # Concatenate as_cif of all contained datablocks
        return '\n\n'.join(
            getattr(item, 'as_cif', '')
            for item in self._datablocks.values()
            if hasattr(item, 'as_cif')
        )

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------
    def add(self, item):
        # Insert the item using its name as key
        self._datablocks[item.name] = item
        item._parent = self
