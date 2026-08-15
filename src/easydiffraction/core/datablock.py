# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Base classes for CIF datablock items and collections."""

from __future__ import annotations

from easydiffraction.core.category_owner import CategoryOwner
from easydiffraction.core.collection import CollectionBase
from easydiffraction.core.variable import Parameter

DEFAULT_LOOP_DISPLAY_LIMIT = 20


class DatablockItem(CategoryOwner):
    """Base class for items in a datablock collection."""

    def __str__(self) -> str:
        """Human-readable representation of this component."""
        name = self.unique_name
        cls = type(self).__name__
        categories = '\n'.join(f'  - {c}' for c in self.categories)
        return f"{cls} datablock '{name}':\n{categories}"

    def __repr__(self) -> str:
        """Developer-oriented representation of this component."""
        name = self.unique_name
        cls = type(self).__name__
        num_categories = len(self.categories)
        return f'<{cls} datablock "{name}" ({num_categories} categories)>'

    @property
    def unique_name(self) -> str | None:
        """Unique name of this datablock item (from identity)."""
        return self._identity.datablock_entry_name

    @property
    def as_cif(self) -> str:
        """CIF representation of this object."""
        from easydiffraction.io.cif.serialize import datablock_item_to_cif  # noqa: PLC0415

        self._update_categories()
        return datablock_item_to_cif(self)

    def _cif_for_display(
        self,
        max_loop_display: int = DEFAULT_LOOP_DISPLAY_LIMIT,
    ) -> str:
        """
        Return CIF text with loop categories truncated for display.

        Parameters
        ----------
        max_loop_display : int, default=DEFAULT_LOOP_DISPLAY_LIMIT
            Maximum number of rows to show per loop category.

        Returns
        -------
        str
            CIF representation of this object, with loop categories
            truncated to at most *max_loop_display* rows for display
            purposes.
        """
        from easydiffraction.io.cif.serialize import datablock_item_to_cif  # noqa: PLC0415

        self._update_categories()
        return datablock_item_to_cif(self, max_loop_display=max_loop_display)


# ======================================================================


class DatablockCollection(CollectionBase):
    """
    Collection of top-level datablocks (e.g. Structures, Experiments).

    Each item is a DatablockItem.

    Subclasses provide explicit ``add_from_*`` convenience methods that
    delegate to the corresponding factory classmethods, then call
    :meth:`add` with the resulting item.
    """

    def _key_for(self, item: object) -> str | None:  # noqa: PLR6301
        """Return the datablock-level identity key for *item*."""
        return item._identity.datablock_entry_name

    def add(self, item: object) -> None:
        """
        Add a pre-built item to the collection.

        Parameters
        ----------
        item : object
            A ``DatablockItem`` instance (e.g. a ``Structure`` or
            ``ExperimentBase`` subclass).
        """
        self[item._identity.datablock_entry_name] = item

    def __str__(self) -> str:
        """Human-readable representation of this component."""
        name = self._log_name
        size = len(self)
        return f'<{name} collection ({size} items)>'

    @property
    def unique_name(self) -> str | None:
        """Collections have no unique name."""
        return None

    @property
    def parameters(self) -> list:
        """All parameters from all datablocks in this collection."""
        params = []
        for db in self._items:
            params.extend(db.parameters)
        return params

    @property
    def fittable_parameters(self) -> list:
        """All Parameters not blocked by constraints or symmetry."""
        return [
            p
            for p in self.parameters
            if isinstance(p, Parameter) and not p.user_constrained and not p.symmetry_constrained
        ]

    @property
    def free_parameters(self) -> list:
        """All fittable parameters that are currently marked as free."""
        return [p for p in self.fittable_parameters if p.free]

    @property
    def as_cif(self) -> str:
        """CIF representation of this object."""
        from easydiffraction.io.cif.serialize import datablock_collection_to_cif  # noqa: PLC0415

        return datablock_collection_to_cif(self)
