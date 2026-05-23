# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import ClassVar

from easydiffraction.utils.logging import console
from easydiffraction.utils.utils import render_table


class SwitchableCategoryBase(ABC):
    """Behavior-only mixin for category-owned selectors."""

    _parent: object | None = None
    _category_code: ClassVar[str]
    _owner_attr_name: ClassVar[str]
    _swap_method_name: ClassVar[str]

    @property
    def type(self) -> str:
        """Active factory tag for this category."""
        return self._type.value

    @type.setter
    def type(self, value: str) -> None:
        """Request an owner-mediated switch to a new category type."""
        if self._parent is None:
            msg = (
                f'{type(self).__name__} is detached; '
                'cannot change type on a stale instance.'
            )
            raise RuntimeError(msg)

        live = getattr(self._parent, self._owner_attr_name)
        if live is not self:
            msg = (
                f'{type(self).__name__} is no longer the live category '
                f'on its owner; obtain a fresh reference via '
                f'owner.{self._owner_attr_name}.'
            )
            raise RuntimeError(msg)

        canonical = self._canonicalize(value)
        getattr(self._parent, self._swap_method_name)(canonical)

    def _canonicalize(self, value: str) -> str:
        """
        Resolve a user-supplied tag to its canonical factory tag.

        Parameters
        ----------
        value : str
            User-supplied selector value.

        Returns
        -------
        str
            Canonical selector value.
        """
        return value

    @abstractmethod
    def _supported_types(
        self,
        filters: dict[str, object],
    ) -> list[tuple[str, str]]:
        """
        Return supported ``(tag, description)`` pairs.

        Parameters
        ----------
        filters : dict[str, object]
            Owner-provided context filters for this category.

        Returns
        -------
        list[tuple[str, str]]
            Supported type tags and descriptions.
        """
        raise NotImplementedError

    def show_supported(self) -> None:
        """Print supported types and mark the active one."""
        filters = (
            self._parent._supported_filters_for(self)
            if self._parent is not None
            else {}
        )
        current = self.type
        columns_data = [
            ['*' if tag == current else '', tag, description]
            for tag, description in self._supported_types(filters)
        ]

        category_name = self._category_code.replace('_', ' ').title()
        console.paragraph(f'{category_name} types')
        render_table(
            columns_headers=['', 'Type', 'Description'],
            columns_alignment=['left', 'left', 'left'],
            columns_data=columns_data,
        )
