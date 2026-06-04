# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import pytest


@pytest.mark.parametrize(
    'code',
    [
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
    ],
)
def test_units_vocabulary_accepts_known_codes(code):
    from easydiffraction.core.units_vocabulary import normalize_units_code
    from easydiffraction.core.units_vocabulary import validate_units_code

    validate_units_code(code)

    assert normalize_units_code(code) == code


def test_units_vocabulary_normalizes_empty_string_to_none():
    from easydiffraction.core.units_vocabulary import normalize_units_code

    assert normalize_units_code('') == 'none'


def test_units_vocabulary_rejects_unknown_code():
    from easydiffraction.core.units_vocabulary import validate_units_code

    with pytest.raises(ValueError, match="Unknown units code: 'deg'"):
        validate_units_code('deg')
