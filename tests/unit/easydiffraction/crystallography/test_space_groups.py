# SPDX-FileCopyrightText: 2025 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for the space-group reference-data loader."""

import re

from easydiffraction.crystallography.space_groups import SPACE_GROUPS

_EXPECTED_RECORD_KEYS = {
    'IT_number',
    'IT_coordinate_system_code',
    'setting',
    'name_H-M_alt',
    'crystal_system',
    'Wyckoff_positions',
    'hall_symbol',
    'symop',
    'generators',
    'point_group',
    'laue_class',
    'centring',
}
_EXPECTED_WYCKOFF_KEYS = {'multiplicity', 'site_symmetry', 'coords_xyz'}

# Accepted seed: 530 cctbx settings + 226 reference-settings aliases + 60
# runtime coordinate-code aliases. A deliberate regeneration updates this.
_EXPECTED_RECORD_COUNT = 816

# Canonical coords_xyz forbids operator form (``1/2*x``) and fractional
# coefficients (``5/4x``); integer coefficients (``2x``) and rational
# constants (``x+1/2``) are allowed.
_NONCANONICAL_COORD = re.compile(r'[0-9.]\s*\*\s*[xyz]|[xyz]\s*\*|\d+/\d+\s*[xyz]')


def test_module_import():
    import easydiffraction.crystallography.space_groups as MUT

    assert MUT.__name__ == 'easydiffraction.crystallography.space_groups'


def test_space_groups_is_dict_keyed_by_it_and_code():
    """SPACE_GROUPS is a non-empty dict keyed by (IT number, coord code)."""
    assert isinstance(SPACE_GROUPS, dict)
    assert SPACE_GROUPS
    for it_number, coord_code in SPACE_GROUPS:
        assert isinstance(it_number, int)
        assert coord_code is None or isinstance(coord_code, str)


def test_all_230_groups_present():
    """Every International Tables group 1-230 is present (no coverage gap)."""
    it_numbers = {key[0] for key in SPACE_GROUPS}
    assert it_numbers == set(range(1, 231))


def test_record_count_matches_accepted_seed():
    """The loaded table keeps its full setting/alias surface (no silent loss).

    SPACE_GROUPS is keyed by ``(IT_number, IT_coordinate_system_code)``, so this
    also pins the number of unique setting keys.
    """
    assert len(SPACE_GROUPS) == _EXPECTED_RECORD_COUNT


def test_triclinic_groups_keep_none_coordinate_code():
    """Triclinic P1/P-1 keep the ``None`` coordinate-system-code key."""
    assert (1, None) in SPACE_GROUPS
    assert (2, None) in SPACE_GROUPS


def test_every_record_has_the_expected_schema():
    """Each setting record carries the full symmetry-core schema."""
    for key, record in SPACE_GROUPS.items():
        assert set(record) >= _EXPECTED_RECORD_KEYS, key
        assert record['IT_number'] == key[0]
        assert record['IT_coordinate_system_code'] == key[1]
        for letter, position in record['Wyckoff_positions'].items():
            assert set(position) >= _EXPECTED_WYCKOFF_KEYS, (key, letter)
            assert isinstance(position['multiplicity'], int)
            assert isinstance(position['coords_xyz'], list)
            assert position['coords_xyz']


def test_coords_xyz_are_canonical_distinct_full_orbits():
    """Every Wyckoff coords_xyz is a canonical, distinct, full orbit.

    Regression guard for the canonical-templates fix: no operator-form or
    fractional-coefficient spelling, no duplicate template, and a length
    equal to the multiplicity (the full centered orbit).
    """
    for key, record in SPACE_GROUPS.items():
        for letter, position in record['Wyckoff_positions'].items():
            coords = position['coords_xyz']
            for template in coords:
                assert not _NONCANONICAL_COORD.search(template), (key, letter, template)
            assert len(set(coords)) == len(coords), (key, letter)
            assert len(coords) == position['multiplicity'], (key, letter)
