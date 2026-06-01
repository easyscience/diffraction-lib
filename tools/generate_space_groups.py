# SPDX-FileCopyrightText: 2026 EasyDiffraction contributors
# SPDX-License-Identifier: BSD-3-Clause
"""Generate the bundled crystallographic space-group database."""

from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path
from typing import Any

ORTHORHOMBIC_ORIGIN_CHOICE_NUMBERS = frozenset({48, 50, 59, 68, 70})


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
    if args.print_summary:
        index = build_record_index(records)
        print(f'records: {len(records)}')
        print(f'IT groups: {len({key[0] for key in index})}')


if __name__ == '__main__':
    main()
