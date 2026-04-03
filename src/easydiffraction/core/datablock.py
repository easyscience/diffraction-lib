# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from easydiffraction.core.category import CategoryCollection
from easydiffraction.core.category import CategoryItem
from easydiffraction.core.collection import CollectionBase
from easydiffraction.core.guard import GuardedBase
from easydiffraction.core.variable import Parameter


class DatablockItem(GuardedBase):
    """Base class for items in a datablock collection."""

    def __init__(self) -> None:
        super().__init__()
        self._need_categories_update = True

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

    def _update_categories(
        self,
        called_by_minimizer: bool = False,
    ) -> None:
        # TODO: Make abstract method and implement in subclasses.
        # This should call apply_symmetry and apply_constraints in the
        # case of structures. In the case of experiments, it should
        # run calculations to update the "data" categories.
        # Any parameter change should set _need_categories_update to
        # True.
        # Calling as_cif or data getter should first check this flag
        # and call this method if True.
        # Should this be also called when parameters are accessed? E.g.
        # if one change background coefficients, then access the
        # background points in the data category?
        #
        # Dirty-flag guard: skip if no parameter has changed since the
        # last update.  Minimisers use _set_value_from_minimizer()
        # which bypasses validation but still sets this flag.
        # During fitting the guard is bypassed because experiment
        # calculations depend on structure parameters owned by a
        # different DatablockItem whose flag changes are invisible here.
        if not called_by_minimizer and not self._need_categories_update:
            return

        for category in self.categories:
            category._update(called_by_minimizer=called_by_minimizer)

        self._need_categories_update = False

    @property
    def unique_name(self) -> str | None:
        """Unique name of this datablock item (from identity)."""
        return self._identity.datablock_entry_name

    @property
    def categories(self) -> list:
        """All category objects in this datablock by priority."""
        cats = [
            v for v in vars(self).values() if isinstance(v, (CategoryItem, CategoryCollection))
        ]
        # Sort by _update_priority (lower values first)
        return sorted(cats, key=lambda c: type(c)._update_priority)

    @property
    def parameters(self) -> list:
        """All parameters from all categories in this datablock."""
        params = []
        for v in self.categories:
            params.extend(v.parameters)
        return params

    @property
    def as_cif(self) -> str:
        """Return CIF representation of this object."""
        from easydiffraction.io.cif.serialize import datablock_item_to_cif  # noqa: PLC0415

        self._update_categories()
        return datablock_item_to_cif(self)

    def _cif_for_display(self, max_loop_display: int = 20) -> str:
        """
        Return CIF text with loop categories truncated for display.

        Parameters
        ----------
        max_loop_display : int, default=20
            Maximum number of rows to show per loop category.
        """
        from easydiffraction.io.cif.serialize import datablock_item_to_cif  # noqa: PLC0415

        self._update_categories()
        return datablock_item_to_cif(self, max_loop_display=max_loop_display)

    def help(self) -> None:
        """Print a summary of public attributes and categories."""
        super().help()

        from easydiffraction.utils.logging import console  # noqa: PLC0415
        from easydiffraction.utils.utils import render_table  # noqa: PLC0415

        cats = self.categories
        if cats:
            console.paragraph('Categories')
            rows = []
            for c in cats:
                code = c._identity.category_code or type(c).__name__
                type_name = type(c).__name__
                num_params = len(c.parameters)
                rows.append([code, type_name, str(num_params)])
            render_table(
                columns_headers=['Category', 'Type', '# Parameters'],
                columns_alignment=['left', 'left', 'right'],
                columns_data=rows,
            )


# ======================================================================


class DatablockCollection(CollectionBase):
    """
    Collection of top-level datablocks (e.g. Structures, Experiments).

    Each item is a DatablockItem.

    Subclasses provide explicit ``add_from_*`` convenience methods that
    delegate to the corresponding factory classmethods, then call
    :meth:`add` with the resulting item.
    """

    def _key_for(self, item: object) -> str | None:
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
        """Return None; collections have no unique name."""
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
        """All non-constrained Parameters in this collection."""
        return [p for p in self.parameters if isinstance(p, Parameter) and not p.constrained]

    @property
    def free_parameters(self) -> list:
        """All fittable parameters that are currently marked as free."""
        return [p for p in self.fittable_parameters if p.free]

    @property
    def as_cif(self) -> str:
        """Return CIF representation of this object."""
        from easydiffraction.io.cif.serialize import datablock_collection_to_cif  # noqa: PLC0415

        return datablock_collection_to_cif(self)
