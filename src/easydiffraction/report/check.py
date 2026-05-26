# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Validation helpers for IUCr submission reports."""

from __future__ import annotations

import pathlib
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import NoReturn

import gemmi

from easydiffraction.core.errors import EasyDiffractionWriterError

if TYPE_CHECKING:
    from collections.abc import Iterable

_REPORT_TAG_RE = re.compile(r'(?m)^\s*(_[A-Za-z][A-Za-z0-9_.-]*)\b')
_DICT_SAVE_RE = re.compile(r'(?m)^save_(_[^\s]+)\s*$')
_WRITER_ERROR_HINT = 'Please file a bug with the full diagnostic.'


@dataclass(frozen=True)
class ReportCheckResult:
    """Result of an IUCr report validation pass."""

    path: pathlib.Path
    errors: tuple[str, ...]
    warnings: tuple[str, ...]

    @property
    def ok(self) -> bool:
        """Return whether the validation pass found no errors."""
        return not self.errors


def check_report(
    path: str | pathlib.Path,
    *,
    dictionary_paths: Iterable[str | pathlib.Path] | None = None,
) -> ReportCheckResult:
    """
    Validate an IUCr report CIF.

    Parameters
    ----------
    path : str | pathlib.Path
        Report CIF path.
    dictionary_paths : Iterable[str | pathlib.Path] | None, default=None
        Dictionary files to load. Defaults to local ``tmp/iucr-dicts``
        copies when present.

    Returns
    -------
    ReportCheckResult
        Validation errors and warnings.
    """
    report_path = pathlib.Path(path)
    errors: list[str] = []
    warnings: list[str] = []

    try:
        document = gemmi.cif.read_file(str(report_path))
    except Exception as exc:  # noqa: BLE001
        errors.append(f'Failed to parse report CIF: {exc}')
        return ReportCheckResult(report_path, tuple(errors), tuple(warnings))

    dictionaries = _dictionary_paths(dictionary_paths)
    if dictionaries:
        warnings.extend(_gemmi_dictionary_warnings(document, dictionaries))
        warnings.extend(_unknown_tag_warnings(report_path, dictionaries))
    else:
        warnings.append('Dictionary validation skipped: no CIF dictionaries found.')

    return ReportCheckResult(report_path, tuple(errors), tuple(warnings))


def _dictionary_paths(
    dictionary_paths: Iterable[str | pathlib.Path] | None,
) -> tuple[pathlib.Path, ...]:
    """Return dictionary paths to use for validation."""
    if dictionary_paths is not None:
        return tuple(pathlib.Path(path) for path in dictionary_paths)

    repo_root = pathlib.Path(__file__).resolve().parents[3]
    candidates = (
        repo_root / 'tmp' / 'iucr-dicts' / 'cif_core.dic',
        repo_root / 'tmp' / 'iucr-dicts' / 'cif_pow.dic',
    )
    return tuple(path for path in candidates if path.is_file())


def _read_dictionary_documents(
    dictionary_paths: tuple[pathlib.Path, ...],
) -> tuple[tuple[gemmi.cif.Document, ...], tuple[str, ...]]:
    """Return parsed dictionaries and any load diagnostics."""
    documents = []
    errors = []
    for dictionary_path in dictionary_paths:
        try:
            documents.append(gemmi.cif.read_file(str(dictionary_path)))
        except Exception as exc:  # noqa: BLE001
            errors.append(f'Failed to load CIF dictionary {dictionary_path}: {exc}')
    return tuple(documents), tuple(errors)


def _gemmi_dictionary_warnings(
    document: gemmi.cif.Document,
    dictionary_paths: tuple[pathlib.Path, ...],
) -> list[str]:
    """Return warnings from gemmi dictionary validation."""
    logger = _GemmiLogger()
    ddl = gemmi.cif.Ddl(logger, print_unknown_tags=False)
    try:
        for dictionary_path in dictionary_paths:
            ddl.read_ddl(gemmi.cif.read_file(str(dictionary_path)))
        ddl.validate_cif(document)
    except Exception as exc:  # noqa: BLE001
        return [f'Gemmi dictionary validation skipped: {exc}']
    return logger.messages


def _gemmi_dictionary_errors(
    document: gemmi.cif.Document,
    dictionary_documents: tuple[gemmi.cif.Document, ...],
) -> list[str]:
    """Return gemmi dictionary-validation diagnostics."""
    logger = _GemmiLogger()
    ddl = gemmi.cif.Ddl(logger, print_unknown_tags=False)
    try:
        for dictionary_document in dictionary_documents:
            ddl.read_ddl(dictionary_document)
        ddl.validate_cif(document)
    except Exception as exc:  # noqa: BLE001
        return [f'Gemmi dictionary validation failed: {exc}']
    return logger.messages


def _unknown_tag_warnings(
    report_path: pathlib.Path,
    dictionary_paths: tuple[pathlib.Path, ...],
) -> list[str]:
    """Return unknown-tag warnings from a dictionary text scan."""
    known_tags = _known_dictionary_tags(dictionary_paths)
    if not known_tags:
        return ['Unknown-tag scan skipped: no dictionary tags were found.']

    report_tags = set(_REPORT_TAG_RE.findall(report_path.read_text(encoding='utf-8')))
    unknown_tags = sorted(
        tag
        for tag in report_tags
        if not tag.startswith('_easydiffraction_') and tag not in known_tags
    )
    return [f'Unknown IUCr tag: {tag}' for tag in unknown_tags]


def _unknown_tag_errors(content: str, known_tags: set[str]) -> list[str]:
    """Return unknown-tag diagnostics from CIF content."""
    if not known_tags:
        return []

    report_tags = set(_REPORT_TAG_RE.findall(content))
    unknown_tags = sorted(
        tag
        for tag in report_tags
        if not tag.startswith('_easydiffraction_') and tag not in known_tags
    )
    return [f'Unknown IUCr tag: {tag}' for tag in unknown_tags]


def _known_dictionary_tags(dictionary_paths: tuple[pathlib.Path, ...]) -> set[str]:
    """Return item names declared by dictionary save frames."""
    tags: set[str] = set()
    for dictionary_path in dictionary_paths:
        text = dictionary_path.read_text(encoding='utf-8')
        tags.update(_DICT_SAVE_RE.findall(text))
    return tags


_CACHED_DICTIONARY_PATHS = _dictionary_paths(None)
_CACHED_DICTIONARY_DOCUMENTS, _CACHED_DICTIONARY_LOAD_ERRORS = (
    _read_dictionary_documents(_CACHED_DICTIONARY_PATHS)
)
_CACHED_DICTIONARY_TAGS = _known_dictionary_tags(_CACHED_DICTIONARY_PATHS)


def _validate_iucr_cif(content: str) -> None:
    """Validate IUCr CIF content before it is written."""
    try:
        document = gemmi.cif.read_string(content)
    except Exception as exc:  # noqa: BLE001
        _raise_writer_error(f'Failed to parse generated IUCr CIF: {exc}')

    diagnostics = list(_CACHED_DICTIONARY_LOAD_ERRORS)
    if _CACHED_DICTIONARY_DOCUMENTS:
        diagnostics.extend(
            _gemmi_dictionary_errors(document, _CACHED_DICTIONARY_DOCUMENTS)
        )
        diagnostics.extend(_unknown_tag_errors(content, _CACHED_DICTIONARY_TAGS))

    if diagnostics:
        _raise_writer_error('\n'.join(diagnostics))


def _raise_writer_error(diagnostic: str) -> NoReturn:
    """Raise a writer error with bug-report guidance."""
    msg = f'Generated IUCr CIF failed validation. {_WRITER_ERROR_HINT}\n{diagnostic}'
    raise EasyDiffractionWriterError(msg)


class _GemmiLogger:
    """Collect gemmi validation messages."""

    def __init__(self) -> None:
        self.messages: list[str] = []

    def __call__(self, message: object) -> None:
        self.messages.append(str(message))
