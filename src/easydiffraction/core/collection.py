# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
Lightweight container for guarded items with name-based indexing.

``CollectionBase`` maintains an ordered list of items and a lazily
rebuilt index by the item's identity key. It supports dict-like access
for get, set and delete, along with iteration over the items.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from easydiffraction.core.guard import GuardedBase

if TYPE_CHECKING:
    from collections.abc import Generator
    from collections.abc import Iterator


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

    def __getitem__(self, key: str | int) -> GuardedBase:
        """
        Return an item by name or positional index.

        Parameters
        ----------
        key : str | int
            Identity key (str) or zero-based positional index (int).

        Returns
        -------
        GuardedBase
            The item matching the given key or index.

        Raises
        ------
        TypeError
            If *key* is neither ``str`` nor ``int``.
        """
        if isinstance(key, int):
            return self._items[key]
        if isinstance(key, str):
            try:
                return self._index[key]
            except KeyError:
                self._rebuild_index()
                return self._index[key]
        msg = f'Collection indices must be str or int, not {type(key).__name__}'
        raise TypeError(msg)

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

    def _adopt_items(self, items: list[GuardedBase]) -> None:
        """
        Replace items and link each child to this collection.
        """
        for item in self._items:
            item._parent = None

        for item in items:
            item._parent = self

        self._items = items
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
        """
        del self[name]

    def clear(self) -> None:
        """
        Remove every item, unlinking each from this collection.

        Delegates to :meth:`_adopt_items` with an empty list: every
        child has ``_parent`` cleared, ``_items`` is emptied, and the
        index is rebuilt, matching the invariants ``__delitem__`` keeps.
        """
        self._adopt_items([])

    def _key_for(self, item: GuardedBase) -> str | None:  # noqa: PLR6301
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

        from easydiffraction.utils.logging import console  # noqa: PLC0415
        from easydiffraction.utils.utils import render_table  # noqa: PLC0415

        if self._items:
            console.paragraph(f'Items ({len(self._items)})')
            rows = []
            for item in self._items:
                key = self._key_for(item)
                rows.append([str(key), f"['{key}']"])
            render_table(
                columns_headers=['Name', 'Access'],
                columns_alignment=['left', 'left'],
                columns_data=rows,
            )
        else:
            console.paragraph('Items')
            console.print('(empty)')
