# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from easydiffraction.core.category import CategoryCollection
from easydiffraction.core.category import CategoryItem
from easydiffraction.core.guard import GuardedBase


class CategoryOwner(GuardedBase):
    """Base class for objects that own flat CIF-like categories."""

    def __init__(self) -> None:
        super().__init__()
        self._need_categories_update = True

    @property
    def categories(self) -> list:
        """
        All category objects owned by this object, sorted by priority.
        """
        categories = [
            value
            for value in vars(self).values()
            if isinstance(value, (CategoryItem, CategoryCollection))
        ]
        return sorted(categories, key=lambda category: type(category)._update_priority)

    def _serializable_categories(self) -> list:
        """Categories that should be serialized for this owner."""
        return self.categories

    @property
    def parameters(self) -> list:
        """All parameters from all owned categories."""
        parameters = []
        for category in self.categories:
            parameters.extend(category.parameters)
        return parameters

    def _update_categories(
        self,
        *,
        called_by_minimizer: bool = False,
    ) -> None:
        """Run update hooks on all owned categories."""
        if not called_by_minimizer and not self._need_categories_update:
            return

        for category in self.categories:
            category._update(called_by_minimizer=called_by_minimizer)

        self._need_categories_update = False

    def help(self) -> None:
        """Print a summary of public attributes and categories."""
        super().help()

        from easydiffraction.utils.logging import console  # noqa: PLC0415
        from easydiffraction.utils.utils import render_table  # noqa: PLC0415

        categories = self.categories
        if categories:
            console.paragraph('Categories')
            rows = []
            for category in categories:
                code = category._identity.category_code or type(category).__name__
                type_name = type(category).__name__
                num_params = len(category.parameters)
                rows.append([code, type_name, str(num_params)])
            render_table(
                columns_headers=['Category', 'Type', '# Parameters'],
                columns_alignment=['left', 'left', 'right'],
                columns_data=rows,
            )
