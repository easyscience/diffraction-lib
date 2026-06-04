# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Packaging regression for the bundled space-group database.

Inspects a built wheel (not an installed package) so the check is independent
of the project's full dependency tree: it opens the wheel, reads
``space_groups.json.gz`` straight from it, and asserts the data is shipped as
package data, that the obsolete ``space_groups.pkl.gz`` is gone, and that the
archive covers all 230 IT groups plus the cryspy coordinate-code alias
surface, and that no Wyckoff ``coords_xyz`` template is in cctbx operator form
(canonical ITA form only). Exits non-zero on any problem so a packaging
regression fails the caller.

Usage: ``python tools/check_packaged_db.py [path/to/wheel]`` (defaults to the
newest wheel in ``dist/``).
"""

from __future__ import annotations

import gzip
import json
import re
import sys
import zipfile
from pathlib import Path

_DATA_MEMBER = 'easydiffraction/crystallography/space_groups.json.gz'
_OBSOLETE_MEMBER = 'easydiffraction/crystallography/space_groups.pkl.gz'
_REQUIRED_KEYS = [(14, '-b1'), (3, '-a1'), (1, None)]
# Accepted seed record count (see the space-group-database ADR provenance).
_EXPECTED_RECORD_COUNT = 816
# Wyckoff coords_xyz must be canonical ITA form, never cctbx operator form
# (e.g. ``1/2*x-1/2*y``), which breaks symmetry-constraint detection.
_OPERATOR_FORM = re.compile(r'[0-9.]\s*\*\s*[xyz]|[xyz]\s*\*')


def _wheel_path(argv: list[str]) -> Path:
    if len(argv) > 1:
        return Path(argv[1])
    wheels = sorted(Path('dist').glob('*.whl'))
    if not wheels:
        sys.exit('no wheel found in dist/; build one with `pixi run dist-build`')
    return wheels[-1]


def main(argv: list[str]) -> None:
    wheel = _wheel_path(argv)
    with zipfile.ZipFile(wheel) as archive:
        members = set(archive.namelist())
        if _DATA_MEMBER not in members:
            sys.exit(f'{wheel.name} does not ship {_DATA_MEMBER}')
        if _OBSOLETE_MEMBER in members:
            sys.exit(f'{wheel.name} still ships obsolete {_OBSOLETE_MEMBER}')
        records = json.loads(gzip.decompress(archive.read(_DATA_MEMBER)).decode('utf-8'))

    keys = {(record['IT_number'], record['IT_coordinate_system_code']) for record in records}
    missing_groups = sorted(set(range(1, 231)) - {key[0] for key in keys})
    if missing_groups:
        sys.exit(f'packaged database missing IT numbers: {missing_groups}')
    missing_keys = [key for key in _REQUIRED_KEYS if key not in keys]
    if missing_keys:
        sys.exit(f'packaged database missing expected keys: {missing_keys}')
    if len(records) != _EXPECTED_RECORD_COUNT:
        sys.exit(f'packaged database has {len(records)} records, expected {_EXPECTED_RECORD_COUNT}')
    if len(keys) != _EXPECTED_RECORD_COUNT:
        sys.exit(f'packaged database has {len(keys)} unique keys, expected {_EXPECTED_RECORD_COUNT}')

    operator_form = [
        (record['IT_number'], record['IT_coordinate_system_code'], letter, template)
        for record in records
        for letter, position in record['Wyckoff_positions'].items()
        for template in position['coords_xyz']
        if _OPERATOR_FORM.search(template)
    ]
    if operator_form:
        sys.exit(
            f'packaged database has {len(operator_form)} operator-form coords_xyz '
            f'(canonical ITA form required); first: {operator_form[0]}'
        )

    print(
        f'packaged DB OK in {wheel.name}: '
        f'{len({key[0] for key in keys})} IT groups, {len(records)} settings'
    )


if __name__ == '__main__':
    main(sys.argv)
