# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Minimal CIF tag handler used by descriptors/parameters."""

from __future__ import annotations


class CifHandler:
    """
    Canonical CIF handler used by descriptors/parameters.

    Holds persistence/import/export tags and attaches to an owning
    descriptor so it can derive a stable uid if needed.
    """

    def __init__(
        self,
        *,
        names: list[str],
        project_name: str | None = None,
        import_names: list[str] | None = None,
        iucr_name: str | None = None,
        docs_page: str | None = None,
        docs_anchor: str | None = None,
    ) -> None:
        self._names = names
        self._project_name = project_name
        self._import_names = import_names
        self._iucr_name = iucr_name
        self._docs_page = docs_page
        self._docs_anchor = docs_anchor
        self._owner = None  # set by attach

    def attach(self, owner: object) -> None:
        """Attach to a descriptor or parameter instance."""
        self._owner = owner

    @property
    def names(self) -> list[str]:
        """List of CIF tag names associated with the owner."""
        return self._names

    @property
    def project_name(self) -> str:
        """Edi project data name used by project persistence."""
        if self._project_name is not None:
            return self._project_name
        return self._names[0]

    @property
    def import_names(self) -> list[str]:
        """Accepted legacy or external names used by project import."""
        if self._import_names is not None:
            return self._import_names
        return self._names

    @property
    def read_names(self) -> list[str]:
        """Accepted project-load names in lookup order."""
        return list(dict.fromkeys([self.project_name, *self.import_names]))

    @property
    def iucr_name(self) -> str:
        """IUCr-side CIF tag name for export writers."""
        if self._iucr_name is not None:
            return self._iucr_name
        return self._names[0]

    @property
    def category_name(self) -> str:
        """Project data category name derived from the Edi tag."""
        return _split_data_name(self.project_name)[0]

    @property
    def category_entry_name(self) -> str:
        """Project data item name derived from the Edi tag."""
        return _split_data_name(self.project_name)[1]

    @property
    def docs_page(self) -> str:
        """Parameter documentation page name."""
        if self._docs_page is not None:
            return self._docs_page
        return self.category_name

    @property
    def docs_anchor(self) -> str:
        """Parameter documentation anchor."""
        if self._docs_anchor is not None:
            return self._docs_anchor
        return _docs_anchor(self.category_name, self.category_entry_name)

    @property
    def url(self) -> str:
        """Versioned online documentation URL for this handler."""
        from easydiffraction.utils.utils import parameter_docs_url  # noqa: PLC0415

        return parameter_docs_url(
            self.project_name,
            page=self._docs_page,
            anchor=self._docs_anchor,
        )

    @property
    def uid(self) -> str | None:
        """Unique identifier taken from the owner, if attached."""
        if self._owner is None:
            return None
        return self._owner.unique_name


def _split_data_name(data_name: str) -> tuple[str, str]:
    """Split a data name into category and item components."""
    category, _, item = data_name.strip().lstrip('_').partition('.')
    return category, item


def _docs_anchor(category: str, item: str) -> str:
    """Return the stable docs anchor for a category item."""
    parts = [part for part in (category, item) if part]
    return '-'.join(parts).replace('_', '-').lower()
