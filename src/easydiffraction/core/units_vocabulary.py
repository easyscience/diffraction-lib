# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Validated unit codes for descriptor metadata."""

from __future__ import annotations

VALID_UNITS_CODES: frozenset[str] = frozenset(
    {
        'angstrom_squared',
        'angstroms',
        'arcminutes',
        'degrees',
        'degrees_squared',
        'kelvins',
        'kilopascals',
        'microsecond_angstroms',
        'microseconds',
        'microseconds_per_angstrom',
        'microseconds_per_angstrom_squared',
        'microseconds_squared',
        'microseconds_squared_per_angstrom_squared',
        'micrometres',
        'none',
        'reciprocal_angstrom_squared',
        'reciprocal_angstroms',
        'teslas',
        'volts_per_metre',
    }
)

_LEGACY_UNITS_ALIASES: dict[str, str] = {
    '': 'none',
}


def normalize_units_code(code: str) -> str:
    """
    Return the canonical units code for a descriptor.

    Parameters
    ----------
    code : str
        Units code. Empty strings are treated as ``'none'``.

    Returns
    -------
    str
        Canonical units code.

    Raises
    ------
    ValueError
        If the normalized code is not a known units code.
    """
    normalized = _LEGACY_UNITS_ALIASES.get(code, code)
    validate_units_code(normalized)
    return normalized


def validate_units_code(code: str) -> None:
    """
    Validate one descriptor units code.

    Parameters
    ----------
    code : str
        Units code to validate.

    Raises
    ------
    ValueError
        If ``code`` is not a known units code.
    """
    if code not in VALID_UNITS_CODES:
        msg = f'Unknown units code: {code!r}. Valid: {sorted(VALID_UNITS_CODES)}'
        raise ValueError(msg)
