# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for the bundled per-element radii and colour palettes."""

from __future__ import annotations

import easydiffraction.display.structure.assets.elements as elements_module
from easydiffraction.display.structure.assets.elements import ELEMENT_COLORS
from easydiffraction.display.structure.assets.elements import ELEMENT_RADII

# Model/scheme keys every entry must carry, matching the consumers in
# radii.py (radius_for) and colors.py (color_for).
RADIUS_MODELS = ('vdw', 'covalent', 'ionic', 'atomic')
COLOR_SCHEMES = ('jmol', 'vesta')


def test_module_import():
    expected_module_name = 'easydiffraction.display.structure.assets.elements'
    actual_module_name = elements_module.__name__
    assert expected_module_name == actual_module_name


# ------------------------------------------------------------------
#  ELEMENT_RADII — container shape
# ------------------------------------------------------------------


class TestElementRadiiContainer:
    def test_is_dict(self):
        assert isinstance(ELEMENT_RADII, dict)

    def test_not_empty(self):
        assert len(ELEMENT_RADII) > 0

    def test_covers_full_periodic_table(self):
        # Hydrogen through oganesson: 118 elements.
        assert len(ELEMENT_RADII) == 118

    def test_first_and_last_symbols(self):
        symbols = list(ELEMENT_RADII)
        assert symbols[0] == 'H'
        assert symbols[-1] == 'Og'

    def test_known_symbols_present(self):
        for symbol in ('H', 'C', 'N', 'O', 'Fe', 'Si', 'U', 'Og'):
            assert symbol in ELEMENT_RADII

    def test_keys_are_titlecase_element_symbols(self):
        for symbol in ELEMENT_RADII:
            assert isinstance(symbol, str)
            assert 1 <= len(symbol) <= 2
            assert symbol[0].isupper()
            assert symbol.istitle()


# ------------------------------------------------------------------
#  ELEMENT_RADII — per-entry contract
# ------------------------------------------------------------------


class TestElementRadiiEntries:
    def test_every_entry_is_a_dict(self):
        for entry in ELEMENT_RADII.values():
            assert isinstance(entry, dict)

    def test_every_entry_has_exactly_the_model_keys(self):
        expected_keys = set(RADIUS_MODELS)
        for symbol, entry in ELEMENT_RADII.items():
            assert set(entry) == expected_keys, symbol

    def test_values_are_float_or_none(self):
        for symbol, entry in ELEMENT_RADII.items():
            for model in RADIUS_MODELS:
                value = entry[model]
                assert value is None or isinstance(value, (int, float)), (symbol, model)

    def test_non_none_values_are_positive(self):
        for symbol, entry in ELEMENT_RADII.items():
            for model in RADIUS_MODELS:
                value = entry[model]
                if value is not None:
                    assert value > 0.0, (symbol, model)

    def test_covalent_radius_always_present(self):
        # radius_for() relies on covalent as the universal fallback, so
        # no bundled element may have a None covalent radius.
        for symbol, entry in ELEMENT_RADII.items():
            assert entry['covalent'] is not None, symbol
            assert entry['covalent'] > 0.0, symbol


# ------------------------------------------------------------------
#  ELEMENT_RADII — spot-checked known values
# ------------------------------------------------------------------


class TestElementRadiiKnownValues:
    def test_hydrogen(self):
        assert ELEMENT_RADII['H'] == {
            'vdw': 1.1,
            'covalent': 0.31,
            'ionic': None,
            'atomic': 0.25,
        }

    def test_iron(self):
        assert ELEMENT_RADII['Fe'] == {
            'vdw': 1.72,
            'covalent': 1.32,
            'ionic': 0.78,
            'atomic': 1.4,
        }

    def test_helium_has_no_ionic_or_atomic(self):
        assert ELEMENT_RADII['He']['ionic'] is None
        assert ELEMENT_RADII['He']['atomic'] is None
        assert ELEMENT_RADII['He']['covalent'] == 0.28


# ------------------------------------------------------------------
#  ELEMENT_COLORS — container shape
# ------------------------------------------------------------------


class TestElementColorsContainer:
    def test_is_dict(self):
        assert isinstance(ELEMENT_COLORS, dict)

    def test_not_empty(self):
        assert len(ELEMENT_COLORS) > 0

    def test_covers_full_periodic_table(self):
        assert len(ELEMENT_COLORS) == 118

    def test_first_and_last_symbols(self):
        symbols = list(ELEMENT_COLORS)
        assert symbols[0] == 'H'
        assert symbols[-1] == 'Og'

    def test_keys_are_titlecase_element_symbols(self):
        for symbol in ELEMENT_COLORS:
            assert isinstance(symbol, str)
            assert 1 <= len(symbol) <= 2
            assert symbol[0].isupper()
            assert symbol.istitle()


# ------------------------------------------------------------------
#  ELEMENT_COLORS — per-entry contract
# ------------------------------------------------------------------


def _assert_valid_rgb(value, context):
    assert isinstance(value, tuple), context
    assert len(value) == 3, context
    for component in value:
        assert isinstance(component, int), context
        assert 0 <= component <= 255, context


class TestElementColorsEntries:
    def test_every_entry_is_a_dict(self):
        for entry in ELEMENT_COLORS.values():
            assert isinstance(entry, dict)

    def test_every_entry_has_exactly_the_scheme_keys(self):
        expected_keys = set(COLOR_SCHEMES)
        for symbol, entry in ELEMENT_COLORS.items():
            assert set(entry) == expected_keys, symbol

    def test_jmol_always_present_and_valid_rgb(self):
        # color_for() falls back to the jmol colour, so every element
        # must have a usable jmol RGB triple.
        for symbol, entry in ELEMENT_COLORS.items():
            assert entry['jmol'] is not None, symbol
            _assert_valid_rgb(entry['jmol'], symbol)

    def test_vesta_is_rgb_or_none(self):
        for symbol, entry in ELEMENT_COLORS.items():
            value = entry['vesta']
            if value is not None:
                _assert_valid_rgb(value, symbol)


# ------------------------------------------------------------------
#  ELEMENT_COLORS — spot-checked known values
# ------------------------------------------------------------------


class TestElementColorsKnownValues:
    def test_hydrogen_is_white_in_jmol(self):
        assert ELEMENT_COLORS['H']['jmol'] == (255, 255, 255)

    def test_oxygen_is_red_in_jmol(self):
        assert ELEMENT_COLORS['O']['jmol'] == (255, 13, 13)

    def test_nobelium_has_no_vesta_entry(self):
        # No has a jmol colour but no VESTA override (falls back to jmol).
        assert ELEMENT_COLORS['No']['vesta'] is None
        assert ELEMENT_COLORS['No']['jmol'] == (189, 13, 135)

    def test_some_elements_have_a_vesta_override(self):
        # At least one element must carry a non-None VESTA colour,
        # otherwise the second scheme would be dead data.
        with_vesta = [s for s, e in ELEMENT_COLORS.items() if e['vesta'] is not None]
        assert with_vesta


# ------------------------------------------------------------------
#  Cross-dictionary consistency
# ------------------------------------------------------------------


class TestRadiiAndColorsConsistency:
    def test_same_element_set(self):
        # Every element resolvable for a radius must also resolve for a
        # colour, and vice versa.
        assert set(ELEMENT_RADII) == set(ELEMENT_COLORS)

    def test_same_ordering(self):
        assert list(ELEMENT_RADII) == list(ELEMENT_COLORS)
