from __future__ import annotations

from typing import Any
from typing import Generic
from typing import Iterator
from typing import List
from typing import Optional
from typing import TypeVar

from easydiffraction.core.guards import GuardedBase

T = TypeVar('T')


class CollectionBase(GuardedBase, Generic[T]):
    """Base class for collections of named items.

    Internally, items are stored in a list to ensure safety and
    robustness when items can be renamed dynamically. Using a list
    prevents issues that arise from mutable keys in a dictionary, such
    as stale or inconsistent indices.

    Despite the internal list storage, this class exposes a
    dictionary-like API for convenient access by item name.

    Algorithmic complexity notes:
    - __getitem__: O(1) average if index is up-to-date; O(n) worst-case
      if index needs rebuilding.
    - __setitem__: O(n) due to potential search for existing item by
      name.
    - __delitem__: O(n) due to search and removal from the list.
    - __iter__, keys, values, items: O(n) iteration over items.
    """

    def __init__(self, item_type: type[T]) -> None:
        self._parent: Optional[Any] = None
        self._items: list[Any] = []
        self._index: dict[str, Any] = {}
        # TODO: item_type seems can be replaced by using TypeVar T
        self._item_type = item_type

    def __setattr__(self, key: str, value: Any) -> None:
        """Controlled attribute setting (with parent propagation)."""
        super().__setattr__(key, value)  # enforces guard

    def __getitem__(self, name: str) -> T:
        try:
            return self._index[name]
        except KeyError:
            self._rebuild_index()
            return self._index[name]

    def __setitem__(self, name: str, item: T) -> None:
        item._parent = self
        # Check if item with same name exists; if so, replace it
        for i, existing_item in enumerate(self._items):
            if existing_item.name == name:
                self._items[i] = item
                self._rebuild_index()
                return
        # Otherwise append new item
        self._items.append(item)
        self._rebuild_index()

    def __delitem__(self, name):
        # Remove from _items by name
        for i, item in enumerate(self._items):
            if item.name == name:
                del self._items[i]
                self._rebuild_index()
                return
        raise KeyError(name)

    def __iter__(self) -> Iterator[T]:
        return iter(self._items)

    def __len__(self) -> int:
        return len(self._items)

    def _rebuild_index(self) -> None:
        self._index.clear()
        for item in self._items:
            if item.name is not None:
                self._index[item.name] = item

    def keys(self) -> Iterator[str]:
        return (item.name for item in self._items)

    def values(self) -> Iterator[T]:
        return (item for item in self._items)

    def items(self) -> Iterator[tuple[str, T]]:
        return ((item.name, item) for item in self._items)

    @property
    def names(self) -> List[str]:
        """Return a list of all model names in the collection."""
        return list(self.keys())
