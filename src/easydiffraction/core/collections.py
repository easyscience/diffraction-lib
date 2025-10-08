from __future__ import annotations

from easydiffraction.core.guards import GuardedBase


class CollectionBase(GuardedBase):
    def __init__(self, item_type) -> None:
        super().__init__()
        self._items: list = []
        self._index: dict = {}
        self._item_type = item_type

    def __getitem__(self, name: str):
        try:
            return self._index[name]
        except KeyError:
            self._rebuild_index()
            return self._index[name]

    def __setitem__(self, name: str, item) -> None:
        # Check if item with same identity exists; if so, replace it
        for i, existing_item in enumerate(self._items):
            if existing_item._identity.category_entry_name == name:
                self._items[i] = item
                self._rebuild_index()
                return
        # Otherwise append new item
        item._parent = self  # Explicitly set the parent for the item
        self._items.append(item)
        self._rebuild_index()

    def __delitem__(self, name: str) -> None:
        # Remove from _items by identity entry name
        for i, item in enumerate(self._items):
            if item._identity.category_entry_name == name:
                object.__setattr__(item, '_parent', None)  # Unlink the parent before removal
                del self._items[i]
                self._rebuild_index()
                return
        raise KeyError(name)

    def __iter__(self):
        return iter(self._items)

    def __len__(self) -> int:
        return len(self._items)

    def _key_for(self, item):
        """Private helper to get the key for an item."""
        return item._identity.category_entry_name or item._identity.datablock_entry_name

    def _rebuild_index(self) -> None:
        self._index.clear()
        for item in self._items:
            key = self._key_for(item)
            if key:
                self._index[key] = item

    def keys(self):
        return (self._key_for(item) for item in self._items)

    def values(self):
        return (item for item in self._items)

    def items(self):
        return ((self._key_for(item), item) for item in self._items)

    @property
    def names(self):
        """Return a list of all item keys in the collection."""
        return list(self.keys())
