# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for the structure-view colour palette module."""

from __future__ import annotations

import pytest

from easydiffraction.display.structure.assets import colors
from easydiffraction.display.structure.assets.colors import AXIS_COLORS
from easydiffraction.display.structure.assets.colors import DARK_THEME
from easydiffraction.display.structure.assets.colors import DEFAULT_COLOR
from easydiffraction.display.structure.assets.colors import LIGHT_THEME
from easydiffraction.display.structure.assets.colors import VACANCY_COLOR
from easydiffraction.display.structure.assets.colors import color_for
from easydiffraction.display.structure.assets.colors import theme_colors
from easydiffraction.display.structure.assets.elements import ELEMENT_COLORS


def _is_rgb(value):
    """Return True when value is an in-range 0-255 RGB triple."""
    return (
        isinstance(value, tuple)
        and len(value) == 3
        and all(isinstance(channel, int) for channel in value)
        and all(0 <= channel <= 255 for channel in value)
    )


# ------------------------------------------------------------------
#  Module surface
# ------------------------------------------------------------------


class TestModule:
    def test_module_import(self):
        expected_module_name = 'easydiffraction.display.structure.assets.colors'
        assert colors.__name__ == expected_module_name

    def test_public_callables_present(self):
        assert callable(colors.color_for)
        assert callable(colors.theme_colors)


# ------------------------------------------------------------------
#  Module-level constants
# ------------------------------------------------------------------


class TestConstants:
    def test_default_color_value(self):
        assert DEFAULT_COLOR == (255, 192, 203)

    def test_default_color_is_rgb(self):
        assert _is_rgb(DEFAULT_COLOR)

    def test_vacancy_color_value(self):
        assert VACANCY_COLOR == (210, 210, 210)

    def test_vacancy_color_is_rgb(self):
        assert _is_rgb(VACANCY_COLOR)

    def test_axis_colors_keys(self):
        assert set(AXIS_COLORS) == {'a', 'b', 'c'}

    def test_axis_colors_values(self):
        assert AXIS_COLORS['a'] == (220, 40, 40)
        assert AXIS_COLORS['b'] == (40, 180, 40)
        assert AXIS_COLORS['c'] == (40, 80, 220)

    def test_axis_colors_all_rgb(self):
        assert all(_is_rgb(value) for value in AXIS_COLORS.values())

    def test_axis_colors_red_green_blue_dominance(self):
        # a=red, b=green, c=blue (VESTA convention): the named channel
        # is the strongest component of each axis colour.
        assert AXIS_COLORS['a'][0] == max(AXIS_COLORS['a'])
        assert AXIS_COLORS['b'][1] == max(AXIS_COLORS['b'])
        assert AXIS_COLORS['c'][2] == max(AXIS_COLORS['c'])

    def test_light_theme_keys(self):
        assert set(LIGHT_THEME) == {'background', 'foreground'}

    def test_dark_theme_keys(self):
        assert set(DARK_THEME) == {'background', 'foreground'}

    def test_light_theme_values(self):
        # Derived from display/theme.py (#ffffff / #222222).
        assert LIGHT_THEME['background'] == (255, 255, 255)
        assert LIGHT_THEME['foreground'] == (34, 34, 34)

    def test_dark_theme_values(self):
        # Derived from display/theme.py (#111111 / #e6e8ee).
        assert DARK_THEME['background'] == (17, 17, 17)
        assert DARK_THEME['foreground'] == (230, 232, 238)

    def test_theme_values_all_rgb(self):
        for theme in (LIGHT_THEME, DARK_THEME):
            assert all(_is_rgb(value) for value in theme.values())

    def test_light_and_dark_backgrounds_differ(self):
        assert LIGHT_THEME['background'] != DARK_THEME['background']

    def test_rgb_type_alias(self):
        assert colors.Rgb == tuple[int, int, int]


# ------------------------------------------------------------------
#  color_for
# ------------------------------------------------------------------


class TestColorFor:
    def test_known_element_known_scheme_returns_scheme_color(self):
        # Si has distinct jmol and vesta entries; requesting vesta must
        # return the vesta value, not the jmol fallback.
        assert color_for('Si', 'vesta') == (27, 59, 250)

    def test_jmol_scheme_returns_jmol_color(self):
        assert color_for('Si', 'jmol') == (240, 200, 160)

    def test_scheme_colors_can_differ(self):
        assert color_for('Si', 'jmol') != color_for('Si', 'vesta')

    def test_returns_exact_palette_reference(self):
        # The function returns the stored tuple, not a copy or recolour.
        assert color_for('Fe', 'vesta') == ELEMENT_COLORS['Fe']['vesta']
        assert color_for('Fe', 'jmol') == ELEMENT_COLORS['Fe']['jmol']

    def test_unknown_scheme_falls_back_to_jmol(self):
        # 'cpk' is not a stored scheme key, so the element's jmol colour
        # is used as the fallback.
        assert color_for('Fe', 'cpk') == ELEMENT_COLORS['Fe']['jmol']

    def test_none_scheme_value_falls_back_to_jmol(self):
        # Some heavy elements store vesta=None; requesting vesta must
        # fall through to the jmol colour rather than return None.
        element = next(el for el, data in ELEMENT_COLORS.items() if data.get('vesta') is None)
        result = color_for(element, 'vesta')
        assert result == ELEMENT_COLORS[element]['jmol']
        assert result is not None

    def test_unknown_element_returns_default(self):
        assert color_for('Xx', 'jmol') == DEFAULT_COLOR

    def test_unknown_element_returns_default_for_any_scheme(self):
        assert color_for('Zz', 'vesta') == DEFAULT_COLOR

    def test_empty_element_returns_default(self):
        assert color_for('', 'jmol') == DEFAULT_COLOR

    def test_case_sensitive_lookup(self):
        # Symbols are stored title-cased; a lower-cased symbol is unknown.
        assert color_for('fe', 'jmol') == DEFAULT_COLOR

    @pytest.mark.parametrize('scheme', ['jmol', 'vesta'])
    def test_all_elements_return_rgb(self, scheme):
        for element in ELEMENT_COLORS:
            assert _is_rgb(color_for(element, scheme))

    def test_never_returns_none(self):
        # Covers the `entry.get('jmol') or DEFAULT_COLOR` guard for every
        # element under both schemes.
        for element in ELEMENT_COLORS:
            assert color_for(element, 'vesta') is not None
            assert color_for(element, 'jmol') is not None


# ------------------------------------------------------------------
#  theme_colors
# ------------------------------------------------------------------


class TestThemeColors:
    def test_dark_returns_dark_theme(self):
        assert theme_colors(dark=True) == DARK_THEME

    def test_light_returns_light_theme(self):
        assert theme_colors(dark=False) == LIGHT_THEME

    def test_dark_returns_module_dict_reference(self):
        assert theme_colors(dark=True) is DARK_THEME

    def test_light_returns_module_dict_reference(self):
        assert theme_colors(dark=False) is LIGHT_THEME

    def test_result_has_background_and_foreground(self):
        result = theme_colors(dark=False)
        assert set(result) == {'background', 'foreground'}

    def test_dark_is_keyword_only(self):
        # `dark` is a keyword-only parameter; passing it positionally
        # is a TypeError.
        dark_flag = True
        with pytest.raises(TypeError):
            theme_colors(dark_flag)
