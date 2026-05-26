# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""IUCr journal-submission CIF writer."""

from __future__ import annotations

import math
import pathlib
import textwrap
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC
from datetime import datetime

from easydiffraction.io.cif.serialize import format_value
from easydiffraction.utils.utils import package_version

_BLOCK_SEPARATOR = '#====================================================='
_TEXT_WRAP_WIDTH = 80
_ITEM_WIDTH = 38

_JOURNAL_TAGS = (
    '_journal.name_full',
    '_journal.year',
    '_journal.volume',
    '_journal.issue',
    '_journal.page_first',
    '_journal.page_last',
    '_journal.paper_category',
    '_journal.paper_DOI',
    '_journal.coden_ASTM',
    '_journal.suppl_publ_number',
)

_JOURNAL_DATE_TAGS = (
    '_journal_date.accepted',
    '_journal_date.from_coeditor',
    '_journal_date.printers_final',
)

_JOURNAL_COEDITOR_TAGS = (
    '_journal_coeditor.code',
    '_journal_coeditor.name',
    '_journal_coeditor.notes',
)

_PUBL_CONTACT_AUTHOR_TAGS = (
    '_publ_contact_author.name',
    '_publ_contact_author.address',
    '_publ_contact_author.email',
    '_publ_contact_author.phone',
    '_publ_contact_author.id_ORCID',
    '_publ_contact_author.id_IUCr',
)

_PUBL_AUTHOR_TAGS = (
    '_publ_author.name',
    '_publ_author.address',
    '_publ_author.footnote',
    '_publ_author.id_ORCID',
    '_publ_author.id_IUCr',
)

_PUBL_BODY_TAGS = (
    '_publ_body.title',
    '_publ_body.contents',
)

_PACKAGE_BY_ENGINE = {
    'cryspy': 'cryspy',
    'crysfml': 'crysfml',
    'pdffit': 'diffpy.pdffit2',
    'lmfit': 'lmfit',
    'dfols': 'dfols',
    'bumps': 'bumps',
    'emcee': 'emcee',
}


def write_iucr_cif(
    project: object,
    path: str | pathlib.Path | None = None,
) -> pathlib.Path:
    """
    Write the project as an IUCr journal-submission CIF.

    Parameters
    ----------
    project : object
        Project instance to export.
    path : str or pathlib.Path, optional
        Target CIF path. When omitted, the report is written to
        ``<project.info.path>/reports/<project.name>.cif``.

    Returns
    -------
    pathlib.Path
        Path of the written report CIF.
    """
    output_path = _report_path(project, path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(_render_iucr_cif(project), encoding='utf-8')
    return output_path


def _render_iucr_cif(project: object) -> str:
    """Render all IUCr CIF blocks for *project*."""
    blocks = [_write_global_block(project)]
    return f'\n{_BLOCK_SEPARATOR}\n'.join(blocks) + '\n'


def _write_global_block(project: object) -> str:
    """Render the leading ``data_global`` metadata block."""
    lines = ['data_global']
    _write_audit_section(lines)
    _write_computing_section(lines, project)
    _write_publication_sections(lines)
    _write_formula_section(lines, project)
    return '\n'.join(lines)


def _write_audit_section(lines: list[str]) -> None:
    """Append audit metadata."""
    method = _software_label('EasyDiffraction', package_name='easydiffraction')
    _section(lines, 'Audit')
    _write_item(lines, '_audit.creation_method', method)
    _write_item(lines, '_audit.creation_date', _iso_creation_datetime())


def _write_computing_section(lines: list[str], project: object) -> None:
    """Append software-stack metadata."""
    framework = _software_label('EasyDiffraction', package_name='easydiffraction')
    calculator = _calculator_label(project)
    minimizer = _minimizer_label(project)
    refinement = (
        f'{framework} with {minimizer} minimizer and {calculator} calculator'
    )

    _section(lines, 'Computing')
    _write_item(lines, '_computing.structure_refinement', refinement)

    _section(lines, 'EasyDiffraction software')
    _write_item(lines, '_easydiffraction_software.framework', framework)
    _write_item(lines, '_easydiffraction_software.calculator', calculator)
    _write_item(lines, '_easydiffraction_software.minimizer', minimizer)


def _write_publication_sections(lines: list[str]) -> None:
    """Append publication placeholders."""
    _write_placeholder_items(lines, 'Journal', _JOURNAL_TAGS)
    _write_placeholder_items(lines, 'Journal dates', _JOURNAL_DATE_TAGS)
    _write_placeholder_items(lines, 'Journal coeditor', _JOURNAL_COEDITOR_TAGS)
    _write_placeholder_items(
        lines,
        'Publication contact author',
        _PUBL_CONTACT_AUTHOR_TAGS,
    )

    _section(lines, 'Publication authors')
    _write_loop(lines, _PUBL_AUTHOR_TAGS, [tuple('?' for _ in _PUBL_AUTHOR_TAGS)])

    _write_placeholder_items(lines, 'Publication body', _PUBL_BODY_TAGS)


def _write_formula_section(lines: list[str], project: object) -> None:
    """Append chemical-formula summary metadata."""
    formula = _chemical_formula_values(project)
    _section(lines, 'Chemical formula')
    _write_item(lines, '_chemical_formula.sum', formula.sum_formula)
    _write_item(lines, '_chemical_formula.moiety', formula.moiety)
    _write_item(lines, '_chemical_formula.weight', formula.weight)
    _write_item(lines, '_chemical_formula.IUPAC', formula.iupac)


def _write_placeholder_items(
    lines: list[str],
    title: str,
    tags: Iterable[str],
) -> None:
    """Append one placeholder category section."""
    _section(lines, title)
    for tag in tags:
        _write_item(lines, tag, '?')


def _write_loop(
    lines: list[str],
    tags: Iterable[str],
    rows: Iterable[tuple[object, ...]],
) -> None:
    """Append a CIF loop with aligned columns."""
    tag_list = list(tags)
    formatted_rows = [
        tuple(_format_loop_value(value) for value in row)
        for row in rows
    ]
    widths = _loop_widths(tag_list, formatted_rows)

    lines.append('loop_')
    lines.extend(tag_list)
    for row in formatted_rows:
        cells = [
            cell.ljust(widths[index])
            for index, cell in enumerate(row)
        ]
        lines.append(f'  {"  ".join(cells).rstrip()}')


def _write_item(lines: list[str], tag: str, value: object) -> None:
    """Append one tag-value item."""
    formatted = _format_item_value(value)
    if formatted.startswith(';\n'):
        lines.append(tag)
        lines.extend(formatted.splitlines())
        return
    lines.append(f'{tag.ljust(_ITEM_WIDTH)} {formatted}')


def _section(lines: list[str], title: str) -> None:
    """Append a logical section header."""
    if lines and lines[-1] != '':
        lines.append('')
    lines.append(f'# ---- {title} ----')


def _format_item_value(value: object) -> str:
    """Format a CIF item value for report output."""
    if not isinstance(value, str):
        return format_value(value)
    if value in {'?', '.'}:
        return value
    if '\n' in value or len(value) > _TEXT_WRAP_WIDTH:
        return _format_text_field(value)
    if not value.strip():
        return '?'
    if _needs_quotes(value):
        return _quote_string(value)
    return value


def _format_loop_value(value: object) -> str:
    """Format a loop value."""
    formatted = _format_item_value(value)
    if formatted.startswith(';\n'):
        msg = 'Long text fields are not supported in IUCr report loops.'
        raise ValueError(msg)
    return formatted


def _format_text_field(value: str) -> str:
    """Format a long string as a CIF text field."""
    wrapped_lines: list[str] = []
    for line in value.splitlines():
        wrapped_lines.extend(textwrap.wrap(line, width=_TEXT_WRAP_WIDTH) or [''])
    return ';\n' + '\n'.join(wrapped_lines) + '\n;'


def _needs_quotes(value: str) -> bool:
    """Return whether *value* needs CIF quotes."""
    return any(char.isspace() for char in value) or value.startswith(('_', '#'))


def _quote_string(value: str) -> str:
    """Quote a CIF string using the shortest safe delimiter."""
    if "'" not in value:
        return f"'{value}'"
    if '"' not in value:
        return f'"{value}"'
    return _format_text_field(value)


def _loop_widths(
    tags: list[str],
    rows: list[tuple[str, ...]],
) -> list[int]:
    """Return per-column widths for loop rows."""
    widths = [len(tag) for tag in tags]
    for row in rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))
    return widths


def _report_path(
    project: object,
    path: str | pathlib.Path | None,
) -> pathlib.Path:
    """Return the target report path."""
    if path is not None:
        return pathlib.Path(path)

    project_path = getattr(getattr(project, 'info', None), 'path', None)
    if project_path is None:
        msg = 'Project has no saved path. Save the project first.'
        raise FileNotFoundError(msg)

    project_name = getattr(project, 'name', 'project')
    return pathlib.Path(project_path) / 'reports' / f'{project_name}.cif'


def _iso_creation_datetime() -> str:
    """Return an ISO-8601 UTC timestamp for report creation."""
    return datetime.now(tz=UTC).isoformat(timespec='seconds')


def _software_label(name: str, *, package_name: str | None = None) -> str:
    """Return a software label with an installed version when known."""
    normalized = _base_engine_name(name)
    package = package_name or _PACKAGE_BY_ENGINE.get(normalized)
    version = package_version(package) if package is not None else None
    return f'{name} {version}' if version else name


def _calculator_label(project: object) -> str:
    """Return the active calculator label for the report."""
    names: list[str] = []
    for experiment in _collection_values(getattr(project, 'experiments', None)):
        calculator = getattr(experiment, 'calculator', None)
        calculator_name = _descriptor_value(getattr(calculator, 'type', None))
        if calculator_name not in {None, ''}:
            names.append(str(calculator_name))

    unique_names = sorted(set(names))
    if not unique_names:
        return '?'
    return ', '.join(_software_label(name) for name in unique_names)


def _minimizer_label(project: object) -> str:
    """Return the active minimizer label for the report."""
    analysis = getattr(project, 'analysis', None)
    minimizer = getattr(analysis, 'minimizer', None)
    minimizer_name = _descriptor_value(getattr(minimizer, 'type', None))
    if minimizer_name in {None, ''}:
        return '?'
    return _software_label(str(minimizer_name))


def _base_engine_name(name: str) -> str:
    """Return the package-key part of a software label."""
    return name.split(' ', maxsplit=1)[0].split('(', maxsplit=1)[0].lower()


@dataclass(frozen=True)
class _FormulaValues:
    """Chemical formula fields for global report metadata."""

    sum_formula: str
    moiety: str
    weight: str
    iupac: str


def _chemical_formula_values(project: object) -> _FormulaValues:
    """Derive chemical formula values from atom sites where possible."""
    counts: dict[str, float] = {}
    for structure in _collection_values(getattr(project, 'structures', None)):
        for atom_site in _collection_values(getattr(structure, 'atom_sites', None)):
            symbol = _descriptor_value(getattr(atom_site, 'type_symbol', None))
            if not symbol:
                continue
            occupancy = _descriptor_value(getattr(atom_site, 'occupancy', None))
            counts[str(symbol)] = counts.get(str(symbol), 0.0) + _formula_count(
                occupancy
            )

    if not counts:
        return _FormulaValues(
            sum_formula='?',
            moiety='?',
            weight='?',
            iupac='?',
        )

    sum_formula = _format_formula(counts)
    return _FormulaValues(
        sum_formula=sum_formula,
        moiety=sum_formula,
        weight='?',
        iupac='?',
    )


def _formula_count(occupancy: object) -> float:
    """Return the site contribution for formula derivation."""
    if isinstance(occupancy, (int, float)):
        return float(occupancy)
    return 1.0


def _format_formula(counts: dict[str, float]) -> str:
    """Return a compact formula string."""
    parts: list[str] = []
    for symbol in sorted(counts, key=_formula_sort_key):
        count = counts[symbol]
        parts.append(f'{symbol}{_format_formula_suffix(count)}')
    return ' '.join(parts)


def _formula_sort_key(symbol: str) -> tuple[int, str]:
    """Return a Hill-style formula sort key."""
    if symbol == 'C':
        return (0, symbol)
    if symbol == 'H':
        return (1, symbol)
    return (2, symbol)


def _format_formula_suffix(count: float) -> str:
    """Return the formula count suffix."""
    if math.isclose(count, 1.0):
        return ''
    if math.isclose(count, round(count)):
        return str(int(round(count)))
    return f'{count:.4g}'


def _descriptor_value(value: object) -> object:
    """Return ``value.value`` for descriptors, otherwise *value*."""
    return getattr(value, 'value', value)


def _collection_values(collection: object) -> Iterable[object]:
    """Return collection values for project containers."""
    if collection is None:
        return ()
    values = getattr(collection, 'values', None)
    if callable(values):
        return values()
    if isinstance(collection, Iterable):
        return collection
    return (collection,)
