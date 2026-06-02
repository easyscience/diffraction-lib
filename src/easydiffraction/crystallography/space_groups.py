# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""
Space group reference data.

Loads gzipped, packaged JSON with crystallographic space-group
information. The file is part of the distribution; user input is not
involved.
"""

from __future__ import annotations

import gzip
import json
from pathlib import Path
from typing import Any

_SpaceGroupKey = tuple[int, str | None]
_SpaceGroupRecord = dict[str, Any]


def _load() -> dict[_SpaceGroupKey, _SpaceGroupRecord]:
    """Load space-group data from the packaged archive."""
    path = Path(__file__).with_name('space_groups.json.gz')
    with gzip.open(path, 'rt', encoding='utf-8') as file_handle:
        records = json.load(file_handle)
    return {
        (
            record['IT_number'],
            record['IT_coordinate_system_code'],
        ): record
        for record in records
    }


SPACE_GROUPS: dict[_SpaceGroupKey, _SpaceGroupRecord] = _load()
