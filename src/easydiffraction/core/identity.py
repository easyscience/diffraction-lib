# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from typing import Callable


class Identity:
    """Hierarchical identity resolver for datablock/category/entry
    relationships.
    """

    def __init__(
        self,
        *,
        owner: object,
        datablock_entry: Callable | None = None,
        category_code: str | None = None,
        category_entry: Callable | None = None,
    ):
        self._owner = owner
        self._datablock_entry = datablock_entry
        self._category_code = category_code
        self._category_entry = category_entry

    def _resolve_up(self, attr: str, visited=None):
        """Resolve attribute by walking up parent chain safely."""
        if visited is None:
            visited = set()
        if id(self) in visited:
            return None
        visited.add(id(self))

        # Direct callable or value on self
        value = getattr(self, f'_{attr}', None)
        if callable(value):
            return value()
        if isinstance(value, str):
            return value

        # Climb to parent if available
        parent = getattr(self._owner, '__dict__', {}).get('_parent')
        if parent and hasattr(parent, 'identity'):
            return parent.identity._resolve_up(attr, visited)
        return None

    @property
    def datablock_entry_name(self):
        return self._resolve_up('datablock_entry')

    @datablock_entry_name.setter
    def datablock_entry_name(self, func: callable):
        self._datablock_entry = func

    @property
    def category_code(self):
        return self._resolve_up('category_code')

    @category_code.setter
    def category_code(self, value: str):
        self._category_code = value

    @property
    def category_entry_name(self):
        return self._resolve_up('category_entry')

    @category_entry_name.setter
    def category_entry_name(self, func: callable):
        self._category_entry = func
