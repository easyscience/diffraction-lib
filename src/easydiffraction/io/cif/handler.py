# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
Tag specification used by descriptors/parameters.

A :class:`TagSpec` records the names a single descriptor/parameter uses
across the two persistence/exchange formats, plus its documentation
location:

* ``edi_names`` — names searched and written for the **Edi** project
  format (``.edi`` files). ``edi_name`` (``edi_names[0]``) is the
  canonical name used when writing.
* ``cif_names`` — names searched and written for strict **CIF**
  import/export (``.cif`` files, including the report). ``cif_name``
  (``cif_names[0]``) is the canonical name used when exporting; it is
  an IUCr/pdCIF dictionary name where one exists and an
  ``_easydiffraction_*`` extension otherwise. Remaining entries are
  additional spellings accepted on CIF import. Defaults to ``edi_names``
  when not given.

Both lists are ordered by priority: the first entry is canonical for
writing, and the whole list is accepted on read.
"""

from __future__ import annotations


class TagSpec:
    """Per-descriptor tag specification across Edi and CIF formats."""

    def __init__(
        self,
        *,
        edi_names: list[str],
        edi_name: str | None = None,
        cif_names: list[str] | None = None,
        docs_page: str | None = None,
        docs_anchor: str | None = None,
    ) -> None:
        self._edi_names = edi_names
        self._explicit_edi_name = edi_name
        self._cif_names = cif_names
        self._docs_page = docs_page
        self._docs_anchor = docs_anchor
        self._owner = None  # set by attach

    def attach(self, owner: object) -> None:
        """Attach to a descriptor or parameter instance."""
        self._owner = owner

    @property
    def edi_names(self) -> list[str]:
        """Edi tag names accepted on read; first is canonical."""
        return self._edi_names

    @property
    def edi_name(self) -> str:
        """Canonical Edi tag used when writing ``.edi`` files."""
        if self._explicit_edi_name is not None:
            return self._explicit_edi_name
        return self._edi_names[0]

    @property
    def edi_read_names(self) -> list[str]:
        """Accepted ``.edi`` load names, in lookup order."""
        return list(dict.fromkeys([self.edi_name, *self._edi_names]))

    @property
    def cif_names(self) -> list[str]:
        """CIF tag names; first is canonical for export."""
        if self._cif_names is not None:
            return self._cif_names
        return self._edi_names

    @property
    def cif_name(self) -> str:
        """Canonical CIF tag used by report/strict-CIF export."""
        return self.cif_names[0]

    @property
    def cif_read_names(self) -> list[str]:
        """Accepted ``.cif`` import names, in lookup order."""
        return list(dict.fromkeys(self.cif_names))

    @property
    def read_names(self) -> list[str]:
        """Names accepted on read across both formats (union)."""
        return list(dict.fromkeys([self.edi_name, *self._edi_names, *self.cif_names]))

    @property
    def category_name(self) -> str:
        """Project data category name derived from the Edi tag."""
        return _split_data_name(self.edi_name)[0]

    @property
    def category_entry_name(self) -> str:
        """Project data item name derived from the Edi tag."""
        return _split_data_name(self.edi_name)[1]

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
        """Versioned online documentation URL for this descriptor."""
        from easydiffraction.utils.utils import parameter_docs_url  # noqa: PLC0415

        return parameter_docs_url(
            self.edi_name,
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
