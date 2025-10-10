# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from easydiffraction.core.collections import CollectionBase
from easydiffraction.core.guards import GuardedBase
from easydiffraction.core.parameters import GenericDescriptorBase
from easydiffraction.core.validation import checktype


class CategoryItem(GuardedBase):
    """Base class for items in a category collection."""

    def __str__(self) -> str:
        """Human-readable representation of this component."""
        name = self._log_name
        params = ', '.join(f'{p.name}={p.value!r}' for p in self.parameters)
        return f'<{name} ({params})>'

    @property
    def unique_name(self):
        parts = [
            self.identity.datablock_entry_name,
            self.identity.category_code,
            self.identity.category_entry_name,
        ]
        return '.'.join(filter(None, parts))

    @property
    def parameters(self):
        return [v for v in vars(self).values() if isinstance(v, GenericDescriptorBase)]

    @property
    def as_cif(self) -> str:
        """Return CIF representation of this object."""
        lines: list[str] = ['']
        for param in self.parameters:
            tags = param._cif_handler.names
            main_key = tags[0]
            value = param.value
            value = f'"{value}"' if isinstance(value, str) and ' ' in value else value
            lines.append(f'{main_key} {value}')
        return '\n'.join(lines)


class CategoryCollection(CollectionBase):
    """Handles loop-style category containers (e.g. AtomSites).

    Each item is a CategoryItem (component).
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
        """All parameters from all items in this collection."""
        params = []
        for item in self._items:
            params.extend(item.parameters)
        return params

    @property
    def as_cif(self) -> str:
        """Return CIF representation of this object."""
        if not self:
            return ''  # Empty collection
        lines: list[str] = ['']
        # Add header using the first item
        first_item = list(self.values())[0]
        lines.append('loop_')
        for param in first_item.parameters:
            tags = param._cif_handler.names
            main_key = tags[0]
            lines.append(main_key)
        # Add data from all items one by one
        for item in self.values():
            line = []
            for param in item.parameters:
                value = param.value
                line.append(str(value))
            line = ' '.join(line)
            lines.append(line)
        return '\n'.join(lines)

    @checktype
    def add(self, item) -> None:
        """Add an item to the collection."""
        self[item._identity.category_entry_name] = item

    @checktype
    def add_from_args(self, *args, **kwargs) -> None:
        """Create and add a new child instance from the provided
        arguments.
        """
        child_obj = self._item_type(*args, **kwargs)
        self.add(child_obj)
