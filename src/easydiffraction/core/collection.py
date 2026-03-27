# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
Lightweight container for guarded items with name-based indexing.

``CollectionBase`` maintains an ordered list of items and a lazily
rebuilt index by the item's identity key. It supports dict-like access
for get, set and delete, along with iteration over the items.
"""

from __future__ import annotations

from typing import Generator
from typing import Iterator

from easydiffraction.core.guard import GuardedBase


class CollectionBase(GuardedBase):
    """
    A minimal collection with stable iteration and name indexing.

    Parameters
    ----------
    item_type : type
        Type of items accepted by the collection. Used for validation
        and tooling; not enforced at runtime here.
    """

    def __init__(self, item_type: type) -> None:
        super().__init__()
        self._items: list = []
        self._index: dict = {}
        self._item_type = item_type

    def __getitem__(self, name: str) -> GuardedBase:
        """
        Return an item by its identity key.

        Rebuilds the internal index on a cache miss to stay consistent
        with recent mutations.
        """
        try:
            return self._index[name]
        except KeyError:
            self._rebuild_index()
            return self._index[name]

    def __setitem__(self, name: str, item: GuardedBase) -> None:
        """Insert or replace an item under the given identity key."""
        # Check if item with same key exists; if so, replace it
        for i, existing_item in enumerate(self._items):
            if self._key_for(existing_item) == name:
                self._items[i] = item
                self._rebuild_index()
                return
        # Otherwise append new item
        item._parent = self  # Explicitly set the parent for the item
        self._items.append(item)
        self._rebuild_index()

    def __delitem__(self, name: str) -> None:
        """Delete an item by key or raise ``KeyError`` if missing."""
        for i, item in enumerate(self._items):
            if self._key_for(item) == name:
                object.__setattr__(item, '_parent', None)  # Unlink the parent before removal
                del self._items[i]
                self._rebuild_index()
                return
        raise KeyError(name)

    def __contains__(self, name: str) -> bool:
        """Check whether an item with the given key exists."""
        self._rebuild_index()
        return name in self._index

    def __iter__(self) -> Iterator[GuardedBase]:
        """Iterate over items in insertion order."""
        return iter(self._items)

    def __len__(self) -> int:
        """Return the number of items in the collection."""
        return len(self._items)

    def remove(self, name: str) -> None:
        """
        Remove an item by its key.

        Parameters
        ----------
        name : str
            Identity key of the item to remove.

        Raises
        ------
        KeyError
            If no item with the given key exists.
        """
        try:
            del self[name]
        except KeyError:
            raise

    def _key_for(self, item: GuardedBase) -> str | None:
        """
        Return the identity key for *item*.

        Subclasses must override to return the appropriate key
        (``category_entry_name`` or ``datablock_entry_name``).
        """
        return item._identity.category_entry_name or item._identity.datablock_entry_name

    def _rebuild_index(self) -> None:
        """Rebuild the name-to-item index from the ordered item list."""
        self._index.clear()
        for item in self._items:
            key = self._key_for(item)
            if key:
                self._index[key] = item

    def keys(self) -> Generator[str | None, None, None]:
        """Yield keys for all items in insertion order."""
        return (self._key_for(item) for item in self._items)

    def values(self) -> Generator[GuardedBase, None, None]:
        """Yield items in insertion order."""
        return (item for item in self._items)

    def items(self) -> Generator[tuple[str | None, GuardedBase], None, None]:
        """Yield ``(key, item)`` pairs in insertion order."""
        return ((self._key_for(item), item) for item in self._items)

    @property
    def names(self) -> list[str | None]:
        """List of all item keys in the collection."""
        return list(self.keys())

    def help(self) -> None:
        """Print a summary of public attributes and contained items."""
        super().help()

        from easydiffraction.utils.logging import console
        from easydiffraction.utils.utils import render_table

        if self._items:
            console.paragraph(f'Items ({len(self._items)})')
            rows = []
            for i, item in enumerate(self._items, 1):
                key = self._key_for(item)
                rows.append([str(i), str(key), f"['{key}']"])
            render_table(
                columns_headers=['#', 'Name', 'Access'],
                columns_alignment=['right', 'left', 'left'],
                columns_data=rows,
            )
        else:
            console.paragraph('Items')
            console.print('(empty)')
