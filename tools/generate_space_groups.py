# SPDX-FileCopyrightText: 2026 EasyDiffraction contributors
# SPDX-License-Identifier: BSD-3-Clause
"""Generate the bundled crystallographic space-group database."""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import re
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
THIRD_PARTY_RESOURCES = ROOT / 'tmp' / 'third-party-resources'
DEFAULT_OVERRIDES_PATH = ROOT / 'tools' / 'space_groups_overrides.yaml'

ORTHORHOMBIC_ORIGIN_CHOICE_NUMBERS = frozenset({48, 50, 59, 68, 70})
SOURCE_CCTBX = 'cctbx'
SOURCE_CRYSPY_WYCKOFF = 'cryspy wyckoff.dat'
SOURCE_GEMMI = 'gemmi'
SOURCE_RASPA = 'RASPA excerpt'
SOURCE_SGINFO = 'SgInfo sginfo.dat'


@dataclass
class ReportEntry:
    """A source disagreement that needs maintainer review."""

    case: str
    field: str
    values: dict[str, Any]
    recommendation: str
    override: dict[str, Any] | None = None


def _import_sgtbx() -> Any:
    try:
        from cctbx import sgtbx
    except ImportError as exc:
        message = (
            'cctbx is required to generate the space-group database. '
            'Run this script in a temporary environment such as '
            '`pixi exec --spec cctbx python tools/generate_space_groups.py`.'
        )
        raise RuntimeError(message) from exc
    return sgtbx


def _clean_cctbx_token(value: object) -> str:
    text = str(value).strip()
    if text == '\x00':
        return ''
    return text


def _coordinate_code_from_symbol(symbol: Any) -> str | None:
    number = int(symbol.number())
    qualifier = _clean_cctbx_token(symbol.qualifier())
    extension = _clean_cctbx_token(symbol.extension())

    if number <= 2:
        return None
    if qualifier:
        return _qualified_coordinate_code(number, extension, qualifier)
    if extension in {'1', '2'}:
        return _extension_coordinate_code(number, extension)
    if extension in {'H', 'R'}:
        return extension.lower()
    return _default_coordinate_code(number)


def _qualified_coordinate_code(number: int, extension: str, qualifier: str) -> str:
    if 3 <= number <= 15 and qualifier in {'a', 'b', 'c'}:
        return f'{qualifier}1'
    if 16 <= number <= 74 and extension in {'1', '2'}:
        return f'{extension}{qualifier}'
    return qualifier


def _extension_coordinate_code(number: int, extension: str) -> str:
    if 16 <= number <= 74 and number in ORTHORHOMBIC_ORIGIN_CHOICE_NUMBERS:
        return f'{extension}abc'
    return extension


def _default_coordinate_code(number: int) -> str:
    if 16 <= number <= 74:
        return 'abc'
    if 75 <= number <= 142:
        return '1'
    if 143 <= number <= 194:
        return 'h'
    if 195 <= number <= 230:
        return '1'
    msg = f'No coordinate-system code rule for IT number {number}.'
    raise ValueError(msg)


def _default_coordinate_code_or_none(number: int) -> str | None:
    if number <= 2:
        return None
    if 3 <= number <= 15:
        return 'b1'
    return _default_coordinate_code(number)


def _coordinate_code_from_source_token(token: str) -> tuple[int, str | None]:
    if ':' not in token:
        number = int(token)
        return number, _default_coordinate_code_or_none(number)

    number_text, raw_code = token.split(':', 1)
    number = int(number_text)
    code = raw_code.strip()
    if code in {'H', 'R'}:
        return number, code.lower()
    if code in {'1', '2'}:
        return number, _extension_coordinate_code(number, code)
    if 3 <= number <= 15 and code in {'a', 'b', 'c'}:
        return number, f'{code}1'
    return number, code


def _coordinate_code_from_cell_choice(number: int, value: str) -> str | None:
    text = value.strip().lower()
    if number <= 2:
        return None

    unique_axis_match = re.fullmatch(r'unique axis ([abc])', text)
    if unique_axis_match:
        return f'{unique_axis_match.group(1)}1'

    choice_match = re.search(r'cell choice ([123])', text)
    if choice_match is None:
        return _default_coordinate_code_or_none(number)

    choice = choice_match.group(1)
    axis_text = text.split(',', 1)[0].strip()
    if axis_text in {'a', 'b', 'c', '-a', '-b', '-c'}:
        return f'{axis_text}{choice}'
    if number in ORTHORHOMBIC_ORIGIN_CHOICE_NUMBERS:
        return f'{choice}abc'
    if 75 <= number <= 142 or 195 <= number <= 230:
        return choice
    return _default_coordinate_code_or_none(number)


def _record_key(record: dict[str, Any]) -> tuple[int, str | None]:
    return int(record['IT_number']), record['IT_coordinate_system_code']


def _normalize_text(value: object) -> str:
    return ' '.join(str(value).strip().split())


def _normalize_hall_symbol(value: object) -> str:
    return _normalize_text(value).replace(' ', '')


def _normalize_centring(value: object) -> str:
    text = _normalize_text(value)
    return {
        'primitive': 'P',
        'body': 'I',
        'face': 'F',
        'a': 'A',
        'b': 'B',
        'c': 'C',
        'r': 'R',
    }.get(text.lower(), text)


def _normalize_operation(value: object) -> str:
    text = _normalize_text(value).replace(' ', '')
    parts = text.split(',')
    if len(parts) != 3:
        return text
    return ','.join(_normalize_operation_component(part) for part in parts)


@lru_cache(maxsize=None)
def _normalize_operation_component(value: str) -> str:
    from sympy import Rational
    from sympy import simplify
    from sympy import symbols
    from sympy import sympify

    variables = symbols('x y z')
    expr = sympify(value, locals={str(variable): variable for variable in variables})
    linear = 0
    constant = expr
    for variable in variables:
        coefficient = expr.coeff(variable)
        linear += coefficient * variable
        constant -= coefficient * variable

    constant = simplify(constant)
    if constant.is_Rational:
        constant = Rational(int(constant.p) % int(constant.q), int(constant.q))

    return str(simplify(linear + constant)).replace(' ', '')


def _normalize_operation_list(values: Iterable[object]) -> list[str]:
    return sorted({_normalize_operation(value) for value in values})


def _json_value(value: Any) -> str:
    return json.dumps(value, sort_keys=True)


def _operation_summary(values: Iterable[str]) -> dict[str, Any]:
    value_list = list(values)
    return {
        'count': len(value_list),
        'sample': value_list[:5],
    }


def _values_differ(values: dict[str, Any]) -> bool:
    encoded_values = {_json_value(value) for value in values.values()}
    return len(values) >= 2 and len(encoded_values) > 1


def _add_disagreement(
    entries: list[ReportEntry],
    *,
    case: str,
    field: str,
    values: dict[str, Any],
    recommendation: str,
) -> None:
    if _values_differ(values):
        entries.append(
            ReportEntry(
                case=case,
                field=field,
                values=values,
                recommendation=recommendation,
            ),
        )


def _format_rt_mx_list(operators: tuple[Any, ...]) -> list[str]:
    return [operator.as_xyz() for operator in operators]


def _format_wyckoff_orbit(operators: tuple[Any, ...]) -> list[str]:
    return [f'({operator.as_xyz()})' for operator in operators]


def _extract_wyckoff_positions(
    space_group: Any,
    wyckoff_table: Any,
) -> dict[str, dict[str, Any]]:
    positions: dict[str, dict[str, Any]] = {}
    for index in range(wyckoff_table.size()):
        position = wyckoff_table.position(index)
        letter = str(position.letter())
        positions[letter] = {
            'multiplicity': int(position.multiplicity()),
            'site_symmetry': str(position.point_group_type()),
            'coords_xyz': _format_wyckoff_orbit(position.unique_ops(space_group)),
        }
    return positions


def _extract_generators(info: Any) -> dict[str, list[str]]:
    generators = info.any_generator_set()
    return {
        'primitive': _format_rt_mx_list(generators.primitive_generators),
        'non_primitive': _format_rt_mx_list(generators.non_primitive_generators),
    }


def _extract_record(symbol: Any, setting: int) -> dict[str, Any]:
    sgtbx = _import_sgtbx()
    info = sgtbx.space_group_info(symbol=f"Hall:{symbol.hall()}")
    space_group = info.group()
    coord_code = _coordinate_code_from_symbol(symbol)

    return {
        'IT_number': int(symbol.number()),
        'setting': setting,
        'IT_coordinate_system_code': coord_code,
        'name_H-M_alt': str(symbol.hermann_mauguin()).strip(),
        'crystal_system': str(symbol.crystal_system()).lower(),
        'hall_symbol': str(symbol.hall()).strip(),
        'symop': _format_rt_mx_list(space_group.all_ops()),
        'generators': _extract_generators(info),
        'point_group': str(symbol.point_group_type()),
        'laue_class': str(symbol.laue_group_type()),
        'centring': str(space_group.conventional_centring_type_symbol()),
        'Wyckoff_positions': _extract_wyckoff_positions(space_group, info.wyckoff_table()),
    }


def build_space_group_records() -> list[dict[str, Any]]:
    """Return records extracted from cctbx/sgtbx."""
    sgtbx = _import_sgtbx()
    setting_counts: dict[int, int] = {}
    records: list[dict[str, Any]] = []

    # cctbx yields its tabulated setting stream here. Phase 1 later
    # compares this against the wider cryspy coordinate-code alias surface.
    for symbol in sgtbx.space_group_symbol_iterator():
        number = int(symbol.number())
        setting = setting_counts.get(number, 0)
        records.append(_extract_record(symbol, setting))
        setting_counts[number] = setting + 1

    _validate_record_keys(records)
    return records


def build_record_index(
    records: list[dict[str, Any]],
) -> dict[tuple[int, str | None], dict[str, Any]]:
    """Return records keyed by ``(IT_number, IT_coordinate_system_code)``."""
    return {
        (int(record['IT_number']), record['IT_coordinate_system_code']): record
        for record in records
    }


def _validate_record_keys(records: list[dict[str, Any]]) -> None:
    index = build_record_index(records)
    if len(index) != len(records):
        msg = 'cctbx extraction produced duplicate EasyDiffraction setting keys.'
        raise ValueError(msg)

    numbers = {key[0] for key in index}
    missing = sorted(set(range(1, 231)) - numbers)
    if missing:
        msg = f'cctbx extraction missed IT numbers: {missing}'
        raise ValueError(msg)


def _records_by_key(records: list[dict[str, Any]]) -> dict[tuple[int, str | None], dict[str, Any]]:
    return {_record_key(record): record for record in records}


def _read_sginfo_settings(path: Path) -> dict[tuple[int, str | None], dict[str, Any]]:
    settings: dict[tuple[int, str | None], dict[str, Any]] = {}
    for line in path.read_text(encoding='utf-8').splitlines():
        if not line.strip():
            continue
        multiplicity_match = re.search(r'(\d+)\s*$', line)
        if multiplicity_match is None:
            msg = f'Could not parse SgInfo multiplicity from {line!r}.'
            raise ValueError(msg)
        multiplicity = multiplicity_match.group(1)
        token = line[:9].strip()
        number, coord_code = _coordinate_code_from_source_token(token)
        settings[number, coord_code] = {
            'multiplicity': int(multiplicity),
        }
    return settings


def _read_raspa_settings(path: Path) -> dict[tuple[int, str | None], dict[str, Any]]:
    settings: dict[tuple[int, str | None], dict[str, Any]] = {}
    with path.open('r', encoding='utf-8', newline='') as file_handle:
        reader = csv.DictReader(file_handle)
        for row in reader:
            number = int(row['Int. Nr.'])
            coord_code = _coordinate_code_from_cell_choice(number, row['cell choice'])
            settings[number, coord_code] = {
                'name_H-M_alt': _normalize_text(row['Hermann-Hall name']),
                'hall_symbol': _normalize_text(row['Mauguin name']),
                'crystal_system': _normalize_text(row['crystal system']).lower(),
                'centring': _normalize_centring(row['centered']),
            }
    return settings


def _read_gemmi_settings(
    records: list[dict[str, Any]],
) -> tuple[dict[tuple[int, str | None], dict[str, Any]], list[str]]:
    try:
        import gemmi
    except ImportError as exc:
        message = 'gemmi is required for the space-group cross-check report.'
        raise RuntimeError(message) from exc

    cctbx_hall_index = {
        (
            int(record['IT_number']),
            _normalize_hall_symbol(record['hall_symbol']),
        ): _record_key(record)
        for record in records
    }
    settings: dict[tuple[int, str | None], dict[str, Any]] = {}
    unmapped: list[str] = []

    for space_group in gemmi.spacegroup_table():
        hall_key = (int(space_group.number), _normalize_hall_symbol(space_group.hall))
        data = {
            'name_H-M_alt': _normalize_text(space_group.hm),
            'hall_symbol': _normalize_text(space_group.hall),
            'crystal_system': _normalize_text(space_group.crystal_system_str()).lower(),
            'centring': _normalize_centring(space_group.centring_type()),
            'symop': _normalize_operation_list(
                operator.triplet() for operator in space_group.operations()
            ),
        }
        if hall_key in cctbx_hall_index:
            settings[cctbx_hall_index[hall_key]] = data
        else:
            unmapped.append(
                f'{space_group.number}: {space_group.hm} [{space_group.hall}]',
            )

    return settings, unmapped


def _read_cryspy_wyckoff(
    path: Path,
    records: list[dict[str, Any]],
) -> dict[tuple[int, str | None, str], dict[str, set[str]]]:
    values: dict[tuple[int, str | None, str], dict[str, set[str]]] = defaultdict(
        lambda: {
            'multiplicity': set(),
            'site_symmetry': set(),
            'coords_count': set(),
        },
    )

    blocks_by_number: dict[int, list[list[dict[str, Any]]]] = defaultdict(list)
    blocks = path.read_text(encoding='utf-8').strip().split('\n\n')
    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        header_parts = lines[0].split()
        if len(header_parts) < 5 or not all(part.isdigit() for part in header_parts[:5]):
            continue

        number = int(header_parts[0])
        blocks_by_number[number].append(_parse_cryspy_block_positions(lines[1:]))

    for number, keys in _record_keys_by_number(records).items():
        for key, positions in zip(keys, blocks_by_number[number]):
            for position in positions:
                _store_cryspy_position(values, key, position)

    return values


def _record_keys_by_number(
    records: list[dict[str, Any]],
) -> dict[int, list[tuple[int, str | None]]]:
    keys_by_number: dict[int, list[tuple[int, str | None]]] = defaultdict(list)
    for record in records:
        keys_by_number[int(record['IT_number'])].append(_record_key(record))
    return keys_by_number


def _parse_cryspy_block_positions(lines: list[str]) -> list[dict[str, Any]]:
    positions: list[dict[str, Any]] = []
    current_position: dict[str, Any] | None = None

    for line in lines:
        parts = line.split()
        if parts[0].isdigit():
            if current_position is not None:
                positions.append(current_position)
            current_position = {
                'multiplicity': parts[0],
                'letter': parts[1],
                'site_symmetry': parts[2],
                'coords': [],
            }
            continue

        if current_position is not None:
            current_position['coords'].extend(parts)

    if current_position is not None:
        positions.append(current_position)
    return positions


def _store_cryspy_position(
    values: dict[tuple[int, str | None, str], dict[str, set[str]]],
    key: tuple[int, str | None],
    position: dict[str, Any],
) -> None:
    position_key = (key[0], key[1], str(position['letter']))
    values[position_key]['multiplicity'].add(str(position['multiplicity']))
    values[position_key]['site_symmetry'].add(str(position['site_symmetry']))
    values[position_key]['coords_count'].add(str(len(position['coords'])))


def _cctbx_wyckoff_aggregates(
    records: list[dict[str, Any]],
) -> dict[tuple[int, str | None, str], dict[str, set[str]]]:
    values: dict[tuple[int, str | None, str], dict[str, set[str]]] = defaultdict(
        lambda: {
            'multiplicity': set(),
            'site_symmetry': set(),
            'coords_count': set(),
        },
    )

    for record in records:
        setting_key = _record_key(record)
        for letter, position in record['Wyckoff_positions'].items():
            position_key = (setting_key[0], setting_key[1], letter)
            values[position_key]['multiplicity'].add(str(position['multiplicity']))
            values[position_key]['site_symmetry'].add(str(position['site_symmetry']))
            values[position_key]['coords_count'].add(str(len(position['coords_xyz'])))

    return values


def _add_setting_presence_disagreements(
    entries: list[ReportEntry],
    source_settings: dict[str, dict[tuple[int, str | None], dict[str, Any]]],
) -> None:
    required_sources = {
        source: settings
        for source, settings in source_settings.items()
        if source in {SOURCE_CCTBX, SOURCE_GEMMI, SOURCE_SGINFO}
    }
    keys = sorted(set().union(*(settings.keys() for settings in required_sources.values())))

    for key in keys:
        values = {
            source: 'present' if key in settings else 'missing'
            for source, settings in required_sources.items()
        }
        _add_disagreement(
            entries,
            case=_format_setting_key(key),
            field='setting presence',
            values=values,
            recommendation='Review whether this setting belongs in the final table.',
        )


def _add_setting_field_disagreements(
    entries: list[ReportEntry],
    cctbx_settings: dict[tuple[int, str | None], dict[str, Any]],
    source: str,
    settings: dict[tuple[int, str | None], dict[str, Any]],
    fields: tuple[str, ...],
) -> None:
    for key in sorted(cctbx_settings.keys() & settings.keys()):
        for field in fields:
            if field not in settings[key]:
                continue
            cctbx_value = _reportable_field_value(cctbx_settings[key], field)
            source_value = _reportable_field_value(settings[key], field)
            _add_disagreement(
                entries,
                case=_format_setting_key(key),
                field=field,
                values={
                    SOURCE_CCTBX: cctbx_value,
                    source: source_value,
                },
                recommendation=_field_recommendation(field),
            )


def _reportable_field_value(record: dict[str, Any], field: str) -> Any:
    if field == 'symop':
        return _operation_summary(_normalize_operation_list(record[field]))
    if field == 'centring':
        return _normalize_centring(record[field])
    value = record[field]
    if isinstance(value, str):
        return _normalize_text(value)
    return value


def _add_wyckoff_disagreements(
    entries: list[ReportEntry],
    records: list[dict[str, Any]],
    cryspy_wyckoff: dict[tuple[int, str | None, str], dict[str, set[str]]],
) -> None:
    cctbx_wyckoff = _cctbx_wyckoff_aggregates(records)
    keys = sorted(set(cctbx_wyckoff) | set(cryspy_wyckoff))
    for key in keys:
        for field in ('multiplicity', 'site_symmetry'):
            cctbx_values = sorted(cctbx_wyckoff.get(key, {}).get(field, set()))
            cryspy_values = sorted(cryspy_wyckoff.get(key, {}).get(field, set()))
            _add_disagreement(
                entries,
                case=f'{_format_setting_key((key[0], key[1]))} Wyckoff {key[2]}',
                field=field,
                values={
                    SOURCE_CCTBX: cctbx_values,
                    SOURCE_CRYSPY_WYCKOFF: cryspy_values,
                },
                recommendation=_field_recommendation(field),
            )


def _add_gemmi_orbit_disagreements(
    entries: list[ReportEntry],
    records: list[dict[str, Any]],
    gemmi_settings: dict[tuple[int, str | None], dict[str, Any]],
) -> None:
    for record in records:
        key = _record_key(record)
        if key not in gemmi_settings:
            continue
        first_letter = next(iter(record['Wyckoff_positions']))
        first_position = record['Wyckoff_positions'][first_letter]
        _add_disagreement(
            entries,
            case=f'{_format_setting_key(key)} general position {first_letter}',
            field='gemmi general-position orbit count',
            values={
                SOURCE_CCTBX: int(first_position['multiplicity']),
                SOURCE_GEMMI: len(gemmi_settings[key]['symop']),
            },
            recommendation='Review operation closure against International Tables.',
        )


def _field_recommendation(field: str) -> str:
    if field == 'site_symmetry':
        return (
            'Use International Tables as authority; cctbx provides a '
            'point-group candidate while cryspy carries IT-style symbols.'
        )
    if field == 'symop':
        return 'Review the operation set and prefer the International Tables setting.'
    if field == 'coords_count':
        return 'Review the representative orbit size against International Tables.'
    return 'Review source values and record the authoritative selection in overrides.'


def _format_setting_key(key: tuple[int, str | None]) -> str:
    number, coord_code = key
    return f'IT {number}, coordinate code {coord_code!r}'


def build_disagreement_entries(
    records: list[dict[str, Any]],
    overrides_path: Path = DEFAULT_OVERRIDES_PATH,
) -> tuple[list[ReportEntry], dict[str, Any]]:
    """Return source disagreements and report summary metadata."""
    cctbx_settings = _records_by_key(records)
    sginfo_settings = _read_sginfo_settings(THIRD_PARTY_RESOURCES / 'sginfo.dat')
    raspa_settings = _read_raspa_settings(THIRD_PARTY_RESOURCES / 'raspa-page_55_reference.csv')
    gemmi_settings, gemmi_unmapped = _read_gemmi_settings(records)
    cryspy_wyckoff = _read_cryspy_wyckoff(THIRD_PARTY_RESOURCES / 'wyckoff.dat', records)

    entries: list[ReportEntry] = []
    source_settings = {
        SOURCE_CCTBX: cctbx_settings,
        SOURCE_GEMMI: gemmi_settings,
        SOURCE_RASPA: raspa_settings,
        SOURCE_SGINFO: sginfo_settings,
    }
    _add_setting_presence_disagreements(entries, source_settings)
    _add_setting_field_disagreements(
        entries,
        cctbx_settings,
        SOURCE_GEMMI,
        gemmi_settings,
        ('hall_symbol', 'name_H-M_alt', 'crystal_system', 'centring', 'symop'),
    )
    _add_setting_field_disagreements(
        entries,
        cctbx_settings,
        SOURCE_RASPA,
        raspa_settings,
        ('hall_symbol', 'name_H-M_alt', 'crystal_system', 'centring'),
    )
    _add_wyckoff_disagreements(entries, records, cryspy_wyckoff)
    _add_gemmi_orbit_disagreements(entries, records, gemmi_settings)

    overrides = _read_overrides(overrides_path)
    _attach_overrides(entries, overrides)

    summary = {
        SOURCE_CCTBX: len(cctbx_settings),
        SOURCE_GEMMI: len(gemmi_settings),
        SOURCE_RASPA: len(raspa_settings),
        SOURCE_SGINFO: len(sginfo_settings),
        'gemmi_unmapped': gemmi_unmapped,
        'overrides_path': str(overrides_path.relative_to(ROOT)),
        'overrides_count': len(overrides),
    }
    return entries, summary


def _read_overrides(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        import yaml
    except ImportError as exc:
        message = 'pyyaml is required to consume space-group overrides.'
        raise RuntimeError(message) from exc

    loaded = yaml.safe_load(path.read_text(encoding='utf-8'))
    if loaded is None:
        return []
    if not isinstance(loaded, list):
        msg = f'{path} must contain a YAML list of override records.'
        raise ValueError(msg)
    return [override for override in loaded if isinstance(override, dict)]


def _attach_overrides(entries: list[ReportEntry], overrides: list[dict[str, Any]]) -> None:
    override_index = {
        (str(override.get('case')), str(override.get('field'))): override
        for override in overrides
    }
    for entry in entries:
        entry.override = override_index.get((entry.case, entry.field))


def format_disagreement_report(entries: list[ReportEntry], summary: dict[str, Any]) -> str:
    """Return the disagreement report as Markdown."""
    lines = [
        '# Space-Group Database Disagreement Report',
        '',
        'Generated by `tools/generate_space_groups.py` during Phase 1.',
        '',
        '## Source Coverage',
        '',
        f'- cctbx/sgtbx extraction: {summary[SOURCE_CCTBX]} settings',
        f'- gemmi mapped settings: {summary[SOURCE_GEMMI]} settings',
        f'- SgInfo `sginfo.dat`: {summary[SOURCE_SGINFO]} settings',
        f'- RASPA CSV excerpt: {summary[SOURCE_RASPA]} settings',
        f'- Overrides loaded from `{summary["overrides_path"]}`: {summary["overrides_count"]}',
        '',
    ]

    if summary['gemmi_unmapped']:
        lines.extend(
            [
                '## Gemmi Settings Not Mapped to cctbx Keys',
                '',
                *[f'- {item}' for item in summary['gemmi_unmapped']],
                '',
            ],
        )

    lines.extend(['## Disagreements', ''])
    if not entries:
        lines.extend(['No source disagreements were detected.', ''])
        return '\n'.join(lines)

    for index, entry in enumerate(entries, start=1):
        lines.extend(_format_report_entry(index, entry))

    return '\n'.join(lines)


def _format_report_entry(index: int, entry: ReportEntry) -> list[str]:
    lines = [
        f'### {index}. {entry.case}',
        '',
        f'- Field: `{entry.field}`',
        '- Source values:',
    ]
    for source, value in entry.values.items():
        lines.append(f'  - {source}: `{_format_markdown_value(value)}`')
    lines.extend(
        [
            '- International Tables: ',
            f'- Recommendation: {entry.recommendation}',
        ],
    )
    if entry.override is not None:
        lines.append(f'- Override: `{_format_markdown_value(entry.override)}`')
    lines.append('')
    return lines


def _format_markdown_value(value: Any) -> str:
    text = _json_value(value) if not isinstance(value, str) else value
    return text.replace('`', '\\`')


def write_disagreement_report(
    records: list[dict[str, Any]],
    report_path: Path,
    overrides_path: Path = DEFAULT_OVERRIDES_PATH,
) -> None:
    """Write the source disagreement report."""
    entries, summary = build_disagreement_entries(records, overrides_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(format_disagreement_report(entries, summary), encoding='utf-8')


def _write_records(records: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.suffix == '.gz':
        with gzip.open(output_path, 'wt', encoding='utf-8') as file_handle:
            json.dump(records, file_handle, indent=2)
            file_handle.write('\n')
        return

    output_path.write_text(json.dumps(records, indent=2) + '\n', encoding='utf-8')


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Extract EasyDiffraction space-group records from cctbx/sgtbx.',
    )
    parser.add_argument(
        '--output-json',
        type=Path,
        help='Optional path for a JSON or JSON-gzip extraction snapshot.',
    )
    parser.add_argument(
        '--write-report',
        type=Path,
        help='Optional path for the Markdown source-disagreement report.',
    )
    parser.add_argument(
        '--overrides',
        type=Path,
        default=DEFAULT_OVERRIDES_PATH,
        help='Optional YAML overrides file consumed by report/final generation.',
    )
    parser.add_argument(
        '--print-summary',
        action='store_true',
        help='Print the extracted record count and group coverage.',
    )
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    records = build_space_group_records()

    if args.output_json is not None:
        _write_records(records, args.output_json)
    if args.write_report is not None:
        write_disagreement_report(records, args.write_report, args.overrides)
    if args.print_summary:
        index = build_record_index(records)
        print(f'records: {len(records)}')
        print(f'IT groups: {len({key[0] for key in index})}')


if __name__ == '__main__':
    main()
