# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Packaging regression check for the bundled space-group database.

Run against an *installed* wheel (not the source tree) to confirm the
renamed ``space_groups.json.gz`` is shipped as package data and loads. Exits
non-zero on any problem so a packaging regression fails the calling command.
"""

from __future__ import annotations

import sys

from easydiffraction.crystallography.space_groups import SPACE_GROUPS

it_numbers = {key[0] for key in SPACE_GROUPS}
missing = sorted(set(range(1, 231)) - it_numbers)
if missing:
    sys.exit(f'space_groups.json.gz is missing IT numbers: {missing}')

# The alias-expanded surface must ship too (regression for the monoclinic
# negative-direction aliases and the triclinic no-setting keys).
for expected_key in [(14, '-b1'), (3, '-a1'), (1, None)]:
    if expected_key not in SPACE_GROUPS:
        sys.exit(f'space_groups.json.gz is missing expected key: {expected_key}')

print(
    f'packaged DB OK: {len(it_numbers)} IT groups, {len(SPACE_GROUPS)} settings'
)
