# SPDX-FileCopyrightText: 2021-2025 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

from typing import Optional
from typing import Sequence

import numpy as np


def _format_value(value) -> str:
    """Format a single CIF value, quoting strings with whitespace."""
    if isinstance(value, str) and (' ' in value or '\t' in value):
        return f'"{value}"'
    return str(value)


def format_scalar(value) -> str:
    """Public helper to format a scalar CIF value consistently.

    - Quotes strings that contain whitespace.
    - Leaves numbers as-is.
    """
    return _format_value(value)


def param_to_cif_line(param) -> str:
    """Render a single descriptor/parameter to a CIF line.

    Expects ``param`` to expose ``_cif_handler.names`` and ``value``.
    """
    tags: Sequence[str] = param._cif_handler.names  # type: ignore[attr-defined]
    main_key: str = tags[0]
    return f'{main_key} {_format_value(param.value)}'


def category_item_to_cif(item) -> str:
    """Render a CategoryItem-like object to CIF text.

    Expects ``item.parameters`` iterable of params with
    ``_cif_handler.names`` and ``value``.
    """
    lines: list[str] = []
    for p in item.parameters:
        lines.append(param_to_cif_line(p))
    return '\n'.join(lines)


def category_collection_to_cif(collection) -> str:
    """Render a CategoryCollection-like object to CIF text.

    Uses first item to build loop header, then emits rows for each item.
    """
    if not len(collection):
        return ''

    lines: list[str] = []

    # Header
    first_item = list(collection.values())[0]
    lines.append('loop_')
    for p in first_item.parameters:
        tags = p._cif_handler.names  # type: ignore[attr-defined]
        lines.append(tags[0])

    # Rows
    for item in collection.values():
        row_vals = [_format_value(p.value) for p in item.parameters]
        lines.append(' '.join(row_vals))

    return '\n'.join(lines)


def datastore_to_cif(datastore, max_points: Optional[int] = None) -> str:
    """Render a datastore to CIF text.

    Expects ``datastore`` to have ``_cif_mapping()`` and attributes per
    mapping keys.
    """
    cif_lines: list[str] = ['loop_']

    mapping: dict[str, str] = datastore._cif_mapping()  # type: ignore[attr-defined]
    for cif_key in mapping.values():
        cif_lines.append(cif_key)

    data_arrays: list[np.ndarray] = []
    for attr_name in mapping:
        arr = getattr(datastore, attr_name, None)
        data_arrays.append(np.array([]) if arr is None else arr)

    if not data_arrays or not data_arrays[0].size:
        return ''

    n_points = len(data_arrays[0])

    def format_row(i: int) -> str:
        return ' '.join(str(data_arrays[j][i]) for j in range(len(data_arrays)))

    if max_points is not None and n_points > 2 * max_points:
        for i in range(max_points):
            cif_lines.append(format_row(i))
        cif_lines.append('...')
        for i in range(-max_points, 0):
            cif_lines.append(format_row(i))
    else:
        for i in range(n_points):
            cif_lines.append(format_row(i))

    return '\n'.join(cif_lines)
