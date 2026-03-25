# SPDX-FileCopyrightText: 2021-2026 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from easydiffraction.core.collection import CollectionBase
from easydiffraction.core.guard import GuardedBase
from easydiffraction.core.variable import GenericDescriptorBase
from easydiffraction.core.variable import GenericStringDescriptor
from easydiffraction.io.cif.serialize import category_collection_from_cif
from easydiffraction.io.cif.serialize import category_collection_to_cif
from easydiffraction.io.cif.serialize import category_item_from_cif
from easydiffraction.io.cif.serialize import category_item_to_cif

# ======================================================================


class CategoryItem(GuardedBase):
    """Base class for items in a category collection."""

    # TODO: Set different default priorities for CategoryItem and
    #  CategoryCollection and use them when serializing to CIF!
    # TODO: Common for all categories
    _update_priority = 10  # Default. Lower values run first.

    def __str__(self) -> str:
        """Human-readable representation of this component."""
        name = self._log_name
        params = ', '.join(f'{p.name}={p.value!r}' for p in self.parameters)
        return f'<{name} ({params})>'

    # TODO: Common for all categories
    def _update(self, called_by_minimizer=False):
        del called_by_minimizer
        pass

    @property
    def unique_name(self):
        parts = [
            self._identity.datablock_entry_name,
            self._identity.category_code,
            self._identity.category_entry_name,
        ]
        # Convert all parts to strings and filter out None/empty values
        str_parts = [str(part) for part in parts if part is not None]
        return '.'.join(str_parts)

    @property
    def parameters(self):
        return [v for v in vars(self).values() if isinstance(v, GenericDescriptorBase)]

    @property
    def as_cif(self) -> str:
        """Return CIF representation of this object."""
        return category_item_to_cif(self)

    def from_cif(self, block, idx=0):
        """Populate this item from a CIF block."""
        category_item_from_cif(self, block, idx)

    def help(self) -> None:
        """Print parameters, other properties, and methods."""
        from easydiffraction.utils.logging import console
        from easydiffraction.utils.utils import render_table

        cls = type(self)
        console.paragraph(f"Help for '{cls.__name__}'")

        # Deduplicate properties
        seen: dict = {}
        for key, prop in cls._iter_properties():
            if key not in seen:
                seen[key] = prop

        # Split into descriptor-backed and other
        param_rows = []
        other_rows = []
        p_idx = 0
        o_idx = 0
        for key in sorted(seen):
            prop = seen[key]
            try:
                val = getattr(self, key)
            except Exception:
                val = None
            if isinstance(val, GenericDescriptorBase):
                p_idx += 1
                type_str = 'string' if isinstance(val, GenericStringDescriptor) else 'numeric'
                writable = '✓' if prop.fset else '✗'
                param_rows.append([
                    str(p_idx),
                    key,
                    type_str,
                    str(val.value),
                    writable,
                    val.description or '',
                ])
            else:
                o_idx += 1
                writable = '✓' if prop.fset else '✗'
                doc = self._first_sentence(prop.fget.__doc__ if prop.fget else None)
                other_rows.append([str(o_idx), key, writable, doc])

        if param_rows:
            console.paragraph('Parameters')
            render_table(
                columns_headers=[
                    '#',
                    'Name',
                    'Type',
                    'Value',
                    'Writable',
                    'Description',
                ],
                columns_alignment=[
                    'right',
                    'left',
                    'left',
                    'right',
                    'center',
                    'left',
                ],
                columns_data=param_rows,
            )

        if other_rows:
            console.paragraph('Other properties')
            render_table(
                columns_headers=[
                    '#',
                    'Name',
                    'Writable',
                    'Description',
                ],
                columns_alignment=[
                    'right',
                    'left',
                    'center',
                    'left',
                ],
                columns_data=other_rows,
            )

        methods = dict(cls._iter_methods())
        method_rows = []
        for i, key in enumerate(sorted(methods), 1):
            doc = self._first_sentence(getattr(methods[key], '__doc__', None))
            method_rows.append([str(i), f'{key}()', doc])

        if method_rows:
            console.paragraph('Methods')
            render_table(
                columns_headers=['#', 'Method', 'Description'],
                columns_alignment=['right', 'left', 'left'],
                columns_data=method_rows,
            )


# ======================================================================


class CategoryCollection(CollectionBase):
    """Handles loop-style category containers (e.g. AtomSites).

    Each item is a CategoryItem (component).
    """

    # TODO: Common for all categories
    _update_priority = 10  # Default. Lower values run first.

    def _key_for(self, item):
        """Return the category-level identity key for *item*."""
        return item._identity.category_entry_name

    def __str__(self) -> str:
        """Human-readable representation of this component."""
        name = self._log_name
        size = len(self)
        return f'<{name} collection ({size} items)>'

    # TODO: Common for all categories
    def _update(self, called_by_minimizer=False):
        del called_by_minimizer
        pass

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
        return category_collection_to_cif(self)

    def from_cif(self, block):
        """Populate this collection from a CIF block."""
        category_collection_from_cif(self, block)

    def add(self, item) -> None:
        """Insert or replace a pre-built item into the collection.

        Args:
            item: A ``CategoryItem`` instance to add.
        """
        self[item._identity.category_entry_name] = item

    def create(self, **kwargs) -> None:
        """Create a new item with the given attributes and add it.

        A default instance of the collection's item type is created,
        then each keyword argument is applied via ``setattr``.

        Args:
            **kwargs: Attribute names and values for the new item.
        """
        child_obj = self._item_type()

        for attr, val in kwargs.items():
            setattr(child_obj, attr, val)

        self.add(child_obj)
