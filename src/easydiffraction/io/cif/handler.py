# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Minimal CIF tag handler used by descriptors/parameters."""

from __future__ import annotations


class CifHandler:
    """
    Canonical CIF handler used by descriptors/parameters.

    Holds CIF tags (names) and attaches to an owning descriptor so it
    can derive a stable uid if needed.
    """

    def __init__(self, *, names: list[str], iucr_name: str | None = None) -> None:
        self._names = names
        self._iucr_name = iucr_name
        self._owner = None  # set by attach

    def attach(self, owner: object) -> None:
        """Attach to a descriptor or parameter instance."""
        self._owner = owner

    @property
    def names(self) -> list[str]:
        """List of CIF tag names associated with the owner."""
        return self._names

    @property
    def iucr_name(self) -> str:
        """IUCr-side CIF tag name for export writers."""
        if self._iucr_name is not None:
            return self._iucr_name
        return self._names[0]

    @property
    def uid(self) -> str | None:
        """Unique identifier taken from the owner, if attached."""
        if self._owner is None:
            return None
        return self._owner.unique_name
