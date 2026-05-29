# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Load publication metadata from TOML or JSON files."""

from __future__ import annotations

import json
import pathlib
import tomllib
from collections.abc import Mapping
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from easydiffraction.project.categories.publication import Publication

_FIELD_MAP = {
    'journal_name_full': ('journal', 'name_full'),
    'journal_year': ('journal', 'year'),
    'journal_volume': ('journal', 'volume'),
    'journal_issue': ('journal', 'issue'),
    'journal_page_first': ('journal', 'page_first'),
    'journal_page_last': ('journal', 'page_last'),
    'journal_paper_category': ('journal', 'paper_category'),
    'journal_paper_doi': ('journal', 'paper_doi'),
    'journal_coden_astm': ('journal', 'coden_astm'),
    'journal_suppl_publ_number': ('journal', 'suppl_publ_number'),
    'journal_date_accepted': ('journal_date', 'accepted'),
    'journal_date_from_coeditor': ('journal_date', 'from_coeditor'),
    'journal_date_printers_final': ('journal_date', 'printers_final'),
    'journal_coeditor_code': ('journal_coeditor', 'code'),
    'journal_coeditor_name': ('journal_coeditor', 'name'),
    'journal_coeditor_notes': ('journal_coeditor', 'notes'),
    'contact_author_name': ('contact_author', 'name'),
    'contact_author_address': ('contact_author', 'address'),
    'contact_author_email': ('contact_author', 'email'),
    'contact_author_phone': ('contact_author', 'phone'),
    'contact_author_id_orcid': ('contact_author', 'id_orcid'),
    'contact_author_id_iucr': ('contact_author', 'id_iucr'),
    'body_title': ('body', 'title'),
    'body_synopsis': ('body', 'synopsis'),
    'body_abstract': ('body', 'abstract'),
}

_AUTHOR_FIELDS = {
    'name',
    'address',
    'footnote',
    'id_orcid',
    'id_iucr',
}


def _read_publication_data(path: pathlib.Path) -> Mapping[str, object]:
    """Read a publication metadata file by extension."""
    ext = path.suffix.lower()
    if ext == '.toml':
        data = tomllib.loads(path.read_text())
    elif ext == '.json':
        data = json.loads(path.read_text())
    else:
        msg = f'Unsupported publication-info format: {ext}. Use .toml or .json.'
        raise ValueError(msg)

    if not isinstance(data, Mapping):
        msg = 'Publication-info file must contain a top-level object.'
        raise ValueError(msg)
    return data


def _optional_text(key: str, value: object) -> str | None:
    """Validate an optional text field from the publication file."""
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    msg = f'Publication-info field {key!r} must be a string or null.'
    raise ValueError(msg)


def _required_text(key: str, value: object) -> str:
    """Validate a required text field from the publication file."""
    text = _optional_text(key, value)
    if text is None or not text:
        msg = f'Publication-info field {key!r} must be a non-empty string.'
        raise ValueError(msg)
    return text


def _keywords(value: object) -> list[str]:
    """Validate body keywords from the publication file."""
    if value is None:
        return []
    if not isinstance(value, list):
        msg = "Publication-info field 'body_keywords' must be a list of strings."
        raise ValueError(msg)

    keywords: list[str] = []
    for idx, keyword in enumerate(value):
        if not isinstance(keyword, str):
            msg = f"Publication-info field 'body_keywords[{idx}]' must be a string."
            raise ValueError(msg)
        keywords.append(keyword)
    return keywords


def _author_rows(value: object) -> list[dict[str, str | None]]:
    """Validate publication author rows from the publication file."""
    if not isinstance(value, list):
        msg = "Publication-info field 'authors' must be a list of objects."
        raise ValueError(msg)

    rows: list[dict[str, str | None]] = []
    for idx, row in enumerate(value):
        if not isinstance(row, Mapping):
            msg = f"Publication-info field 'authors[{idx}]' must be an object."
            raise ValueError(msg)

        for key in row:
            if key not in _AUTHOR_FIELDS:
                raise ValueError(f'authors.{key}')

        rows.append({
            'name': _required_text(f'authors[{idx}].name', row.get('name')),
            'address': _optional_text(f'authors[{idx}].address', row.get('address')),
            'footnote': _optional_text(f'authors[{idx}].footnote', row.get('footnote')),
            'id_orcid': _optional_text(f'authors[{idx}].id_orcid', row.get('id_orcid')),
            'id_iucr': _optional_text(f'authors[{idx}].id_iucr', row.get('id_iucr')),
        })
    return rows


def _validate_publication_data(
    data: Mapping[str, object],
) -> tuple[
    list[tuple[str, str, str | None]],
    list[str] | None,
    list[dict[str, str | None]] | None,
]:
    """Validate publication data and return normalized updates."""
    updates: list[tuple[str, str, str | None]] = []
    keywords: list[str] | None = None
    authors: list[dict[str, str | None]] | None = None

    for key, value in data.items():
        if key in _FIELD_MAP:
            category_name, attr_name = _FIELD_MAP[key]
            updates.append((category_name, attr_name, _optional_text(key, value)))
        elif key == 'body_keywords':
            keywords = _keywords(value)
        elif key == 'authors':
            authors = _author_rows(value)
        else:
            raise ValueError(key)

    return updates, keywords, authors


def _apply_author_rows(
    publication: Publication,
    authors: list[dict[str, str | None]],
) -> None:
    """
    Replace the publication author collection with normalized rows.
    """
    publication.authors._adopt_items([])
    publication.authors._mark_parent_dirty()
    for author in authors:
        publication.authors.add(
            name=author['name'],
            address=author['address'],
            footnote=author['footnote'],
            id_orcid=author['id_orcid'],
            id_iucr=author['id_iucr'],
        )


def load_publication(publication: Publication, path: str | pathlib.Path) -> None:
    """
    Load publication metadata into a Publication object.

    Parameters
    ----------
    publication : Publication
        Publication metadata facade to populate.
    path : str | pathlib.Path
        TOML or JSON file containing flat publication metadata keys.

    Raises
    ------
    ValueError
        If the file extension, top-level shape, or any key is invalid.
    """
    data = _read_publication_data(pathlib.Path(path))
    updates, keywords, authors = _validate_publication_data(data)

    for category_name, attr_name, value in updates:
        setattr(getattr(publication, category_name), attr_name, value)
    if keywords is not None:
        publication.body.keywords = keywords
    if authors is not None:
        _apply_author_rows(publication, authors)
