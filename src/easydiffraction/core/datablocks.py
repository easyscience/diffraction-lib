# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from typeguard import typechecked

from easydiffraction.core.categories import CategoryCollection
from easydiffraction.core.categories import CategoryItem
from easydiffraction.core.collections import CollectionBase
from easydiffraction.core.guards import GuardedBase
from easydiffraction.core.parameters import Parameter


class DatablockItem(GuardedBase):
    """Base class for items in a datablock collection."""

    def __str__(self) -> str:
        """Human-readable representation of this component."""
        name = self._log_name
        items = self._items
        return f'<{name} ({items})>'

    @property
    def unique_name(self):
        return self._identity.datablock_entry_name

    @property
    def parameters(self):
        """All parameters from all categories contained in this
        datablock.
        """
        params = []
        for v in self.__dict__.values():
            if isinstance(v, (CategoryItem, CategoryCollection)):
                params.extend(v.parameters)
        return params

    @property
    def as_cif(self) -> str:
        """Return CIF representation of this object."""
        lines = [f'data_{self._identity.datablock_entry_name}']
        for category in self.__dict__.values():
            if isinstance(category, (CategoryItem, CategoryCollection)):
                lines.append(category.as_cif)
        return '\n'.join(lines)


class DatablockCollection(CollectionBase):
    """Handles top-level collections (e.g. SampleModels, Experiments).

    Each item is a DatablockItem.
    """

    def __str__(self) -> str:
        """Human-readable representation of this component."""
        name = self._log_name
        size = len(self)
        return f'<{name} collection ({size} items)>'

    @property
    def unique_name(self):
        return None

    @property
    def parameters(self):
        """All parameters from all datablocks in this collection."""
        params = []
        for db in self._items:
            params.extend(db.parameters)
        return params

    # was in class AbstractDatablock(ABC):
    @property
    def fittable_parameters(self) -> list:
        return [p for p in self.parameters if isinstance(p, Parameter) and not p.constrained]

    # was in class AbstractDatablock(ABC):
    @property
    def free_parameters(self) -> list:
        return [p for p in self.fittable_parameters if p.free]

    @property
    def as_cif(self) -> str:
        """Return CIF representation of this object."""
        parts = [
            datablock.as_cif for datablock in self.values() if isinstance(datablock, DatablockItem)
        ]
        return '\n'.join(parts)

    @typechecked
    def add(self, item) -> None:
        """Add an item to the collection."""
        self[item._identity.datablock_entry_name] = item
