# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
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
    _category_code: str | None = None
    _category_entry_name: str | None = None

    def __init__(self) -> None:
        super().__init__()
        if self._category_code is not None:
            self._identity.category_code = self._category_code

    def __str__(self) -> str:
        """Human-readable representation of this component."""
        name = self._log_name
        params = ', '.join(f'{p.name}={p.value!r}' for p in self.parameters)
        return f'<{name} ({params})>'

    # TODO: Common for all categories
    def _update(  # noqa: PLR6301
        self,
        *,
        called_by_minimizer: bool = False,
    ) -> None:
        del called_by_minimizer

    def _resolve_category_entry_name(self) -> str | None:
        """Resolve the declared category entry value for this item."""
        attr_name = self._category_entry_name
        if attr_name is None:
            return None

        value = getattr(self, attr_name)
        if isinstance(value, GenericDescriptorBase):
            value = value.value
        return str(value)

    @property
    def unique_name(self) -> str:
        """Fully qualified name: datablock, category, entry."""
        parts = [
            self._identity.datablock_entry_name,
            self._identity.category_code,
            self._identity.category_entry_name,
        ]
        # Convert all parts to strings and filter out None/empty values
        str_parts = [str(part) for part in parts if part is not None]
        return '.'.join(str_parts)

    @property
    def parameters(self) -> list:
        """All GenericDescriptorBase instances on this item."""
        return [v for v in vars(self).values() if isinstance(v, GenericDescriptorBase)]

    @property
    def as_cif(self) -> str:
        """Return CIF representation of this object."""
        return category_item_to_cif(self)

    def from_cif(self, block: object, idx: int = 0) -> None:
        """Populate this item from a CIF block."""
        category_item_from_cif(self, block, idx)

    def help(self) -> None:
        """Print parameters, other properties, and methods."""
        from easydiffraction.utils.logging import console  # noqa: PLC0415
        from easydiffraction.utils.utils import render_table  # noqa: PLC0415

        cls = type(self)

        # Deduplicate properties
        seen: dict = {}
        for key, prop in cls._iter_properties():
            if key not in seen:
                seen[key] = prop

        # Split into descriptor-backed and other
        param_rows = []
        other_rows = []
        for key in sorted(seen):
            prop = seen[key]
            try:
                val = getattr(self, key)
            except (AttributeError, TypeError, ValueError):
                val = None
            if isinstance(val, GenericDescriptorBase):
                type_str = 'string' if isinstance(val, GenericStringDescriptor) else 'numeric'
                writable = '✓' if prop.fset else ''
                param_rows.append([
                    key,
                    type_str,
                    str(val.value),
                    writable,
                    val.description or '',
                ])
            else:
                writable = '✓' if prop.fset else ''
                doc = self._first_sentence(prop.fget.__doc__ if prop.fget else None)
                other_rows.append([key, writable, doc])

        if param_rows:
            console.paragraph('Parameters')
            render_table(
                columns_headers=[
                    'Name',
                    'Type',
                    'Value',
                    'Writable',
                    'Description',
                ],
                columns_alignment=[
                    'left',
                    'left',
                    'right',
                    'center',
                    'left',
                ],
                columns_data=param_rows,
            )

        if other_rows:
            console.paragraph('Properties')
            render_table(
                columns_headers=[
                    'Name',
                    'Writable',
                    'Description',
                ],
                columns_alignment=[
                    'left',
                    'center',
                    'left',
                ],
                columns_data=other_rows,
            )

        methods = dict(cls._iter_methods())
        method_rows = []
        for key in sorted(methods):
            doc = self._first_sentence(getattr(methods[key], '__doc__', None))
            method_rows.append([f'{key}()', doc])

        if method_rows:
            console.paragraph('Methods')
            render_table(
                columns_headers=['Name', 'Description'],
                columns_alignment=['left', 'left'],
                columns_data=method_rows,
            )


# ======================================================================


class CategoryCollection(CollectionBase):
    """
    Handles loop-style category containers (e.g. AtomSites).

    Each item is a CategoryItem (component).
    """

    # TODO: Common for all categories
    _update_priority = 10  # Default. Lower values run first.

    def _key_for(self, item: object) -> str | None:  # noqa: PLR6301
        """Return the category-level identity key for *item*."""
        return item._identity.category_entry_name

    def _mark_parent_dirty(self) -> None:
        """
        Set ``_need_categories_update`` on the parent datablock.

        Called whenever the collection content changes (items added or
        removed) so that subsequent ``_update_categories()`` calls re-
        run all category updates.
        """
        parent = getattr(self, '_parent', None)
        if parent is not None and hasattr(parent, '_need_categories_update'):
            parent._need_categories_update = True

    def __str__(self) -> str:
        """Human-readable representation of this component."""
        name = self._log_name
        size = len(self)
        return f'<{name} collection ({size} items)>'

    # TODO: Common for all categories
    def _update(  # noqa: PLR6301
        self,
        *,
        called_by_minimizer: bool = False,
    ) -> None:
        del called_by_minimizer

    @property
    def unique_name(self) -> str | None:
        """Return None; collections have no unique name."""
        return None

    @property
    def parameters(self) -> list:
        """All parameters from all items in this collection."""
        params = []
        for item in self._items:
            params.extend(item.parameters)
        return params

    @property
    def scalar_descriptors(self) -> list:
        """Collection-level descriptors serialized outside the loop."""
        return [v for v in vars(self).values() if isinstance(v, GenericDescriptorBase)]

    @property
    def as_cif(self) -> str:
        """Return CIF representation of this object."""
        return category_collection_to_cif(self)

    def from_cif(self, block: object) -> None:
        """Populate this collection from a CIF block."""
        category_collection_from_cif(self, block)

    def add(self, item: object) -> None:
        """
        Insert or replace a pre-built item into the collection.

        Parameters
        ----------
        item : object
            A ``CategoryItem`` instance to add.
        """
        self[item._identity.category_entry_name] = item
        self._mark_parent_dirty()

    def create(self, **kwargs: object) -> None:
        """
        Create a new item with the given attributes and add it.

        A default instance of the collection's item type is created,
        then each keyword argument is applied via ``setattr``.

        Parameters
        ----------
        **kwargs : object
            Attribute names and values for the new item.
        """
        child_obj = self._item_type()

        for attr, val in kwargs.items():
            setattr(child_obj, attr, val)

        self.add(child_obj)
