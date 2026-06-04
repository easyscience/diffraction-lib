# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Coverage tests for space_groups.py: query-surface parity and IT spot-checks."""

from cryspy.A_functions_base.function_2_space_group import ACCESIBLE_NAME_HM_SHORT
from cryspy.A_functions_base.function_2_space_group import (
    get_it_coordinate_system_codes_by_it_number,
)
from cryspy.A_functions_base.function_2_space_group import get_it_number_by_name_hm_short

from easydiffraction.crystallography.space_groups import SPACE_GROUPS


def _multiplicities(it_number: int, coord_code):
    record = SPACE_GROUPS[it_number, coord_code]
    return {
        letter: position['multiplicity']
        for letter, position in record['Wyckoff_positions'].items()
    }


def test_every_cryspy_coordinate_code_resolves():
    """Every (IT number, coordinate code) the SpaceGroup category can produce
    is a key in the database (parity with today's query surface).
    """
    missing = []
    for name_hm in ACCESIBLE_NAME_HM_SHORT:
        it_number = get_it_number_by_name_hm_short(name_hm)
        if it_number is None:
            continue
        codes = get_it_coordinate_system_codes_by_it_number(it_number)
        # SpaceGroup uses ``codes or ['']``; '' normalises to None (the
        # no-setting key) exactly as wyckoff-letter-detection specifies.
        for code in list(codes) if codes else ['']:
            key = (it_number, None if code == '' else code)
            if key not in SPACE_GROUPS:
                missing.append(key)
    assert not missing, f'coordinate codes absent from SPACE_GROUPS: {sorted(set(missing))}'


def test_hm_short_symbol_resolves_to_present_it_number():
    """Every cryspy H-M short symbol maps to an IT number present in the DB."""
    db_it_numbers = {key[0] for key in SPACE_GROUPS}
    for name_hm in ACCESIBLE_NAME_HM_SHORT:
        it_number = get_it_number_by_name_hm_short(name_hm)
        if it_number is None:
            continue
        assert it_number in db_it_numbers, name_hm


def test_spot_check_multiplicities_against_international_tables():
    """Wyckoff multiplicities match International Tables for representatives."""
    expected = {
        (75, '1'): {'a': 1, 'b': 1, 'c': 2, 'd': 4},  # P4
        (143, 'h'): {'a': 1, 'b': 1, 'c': 1, 'd': 3},  # P3
        (168, 'h'): {'a': 1, 'b': 2, 'c': 3, 'd': 6},  # P6
        (14, 'b1'): {'a': 2, 'b': 2, 'c': 2, 'd': 2, 'e': 4},  # P2_1/c
        (200, '1'): {  # Pm-3
            'a': 1,
            'b': 1,
            'c': 3,
            'd': 3,
            'e': 6,
            'f': 6,
            'g': 6,
            'h': 6,
            'i': 8,
            'j': 12,
            'k': 12,
            'l': 24,
        },
    }
    for key, mults in expected.items():
        assert _multiplicities(*key) == mults, key


def test_origin_choice_settings_share_multiplicities_but_differ_in_coordinates():
    """Fd-3m (227) origin choices 1 and 2 share multiplicities, differ in coords."""
    assert (227, '1') in SPACE_GROUPS
    assert (227, '2') in SPACE_GROUPS
    assert _multiplicities(227, '1') == _multiplicities(227, '2')
    pos1 = SPACE_GROUPS[227, '1']['Wyckoff_positions']
    pos2 = SPACE_GROUPS[227, '2']['Wyckoff_positions']
    # The origin shift changes the special-position coordinates.
    assert pos1['c']['coords_xyz'][0] != pos2['c']['coords_xyz'][0]
