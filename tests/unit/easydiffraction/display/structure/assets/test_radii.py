# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for per-element radius lookup with covalent fallback."""

from __future__ import annotations

import easydiffraction.display.structure.assets.radii as radii_module
from easydiffraction.display.structure.assets.elements import ELEMENT_RADII
from easydiffraction.display.structure.assets.radii import DEFAULT_RADIUS
from easydiffraction.display.structure.assets.radii import radius_for


def test_module_import():
    expected_module_name = 'easydiffraction.display.structure.assets.radii'
    actual_module_name = radii_module.__name__
    assert expected_module_name == actual_module_name


class TestDefaultRadius:
    def test_value(self):
        assert DEFAULT_RADIUS == 1.0

    def test_is_float(self):
        assert isinstance(DEFAULT_RADIUS, float)


class TestRadiusForDirectModelHit:
    """Element present and the requested model has a value: no fallback."""

    def test_vdw(self):
        radius, substituted = radius_for('Fe', 'vdw')
        assert radius == ELEMENT_RADII['Fe']['vdw']
        assert radius == 1.72
        assert substituted is False

    def test_covalent(self):
        radius, substituted = radius_for('Fe', 'covalent')
        assert radius == ELEMENT_RADII['Fe']['covalent']
        assert radius == 1.32
        assert substituted is False

    def test_ionic(self):
        radius, substituted = radius_for('Fe', 'ionic')
        assert radius == ELEMENT_RADII['Fe']['ionic']
        assert radius == 0.78
        assert substituted is False

    def test_atomic(self):
        radius, substituted = radius_for('Fe', 'atomic')
        assert radius == ELEMENT_RADII['Fe']['atomic']
        assert radius == 1.4
        assert substituted is False

    def test_returns_tuple_of_float_and_bool(self):
        result = radius_for('Fe', 'vdw')
        assert isinstance(result, tuple)
        assert len(result) == 2
        radius, substituted = result
        assert isinstance(radius, float)
        assert isinstance(substituted, bool)


class TestRadiusForCovalentFallback:
    """Element present but the requested model is None: covalent is used."""

    def test_ionic_missing_falls_back_to_covalent(self):
        # H has ionic=None but covalent=0.31.
        assert ELEMENT_RADII['H']['ionic'] is None
        radius, substituted = radius_for('H', 'ionic')
        assert radius == ELEMENT_RADII['H']['covalent']
        assert radius == 0.31
        assert substituted is True

    def test_atomic_missing_falls_back_to_covalent(self):
        # He has atomic=None but covalent=0.28.
        assert ELEMENT_RADII['He']['atomic'] is None
        radius, substituted = radius_for('He', 'atomic')
        assert radius == ELEMENT_RADII['He']['covalent']
        assert radius == 0.28
        assert substituted is True


class TestRadiusForUnknownElement:
    """Element absent from the database: DEFAULT_RADIUS, substituted."""

    def test_unknown_symbol(self):
        radius, substituted = radius_for('Zz', 'vdw')
        assert radius == DEFAULT_RADIUS
        assert substituted is True

    def test_empty_symbol(self):
        radius, substituted = radius_for('', 'vdw')
        assert radius == DEFAULT_RADIUS
        assert substituted is True

    def test_unknown_element_ignores_model(self):
        # Model is irrelevant once the element is unknown.
        for model in ('vdw', 'covalent', 'ionic', 'atomic', 'nonsense'):
            radius, substituted = radius_for('Qq', model)
            assert radius == DEFAULT_RADIUS
            assert substituted is True


class TestRadiusForUnknownModel:
    """Element present but the model key is unknown: covalent fallback."""

    def test_unknown_model_falls_back_to_covalent(self):
        # 'bogus' is not a key in any entry, so entry.get returns None
        # and the covalent radius is substituted.
        radius, substituted = radius_for('Fe', 'bogus')
        assert radius == ELEMENT_RADII['Fe']['covalent']
        assert substituted is True


class TestRadiusForDefaultFallback:
    """Entry exists, requested model None, and covalent also None.

    No real element has a None covalent radius, so this last-resort
    branch is exercised by patching the database with a synthetic
    entry whose every radius is None.
    """

    def test_default_radius_when_covalent_is_none(self, monkeypatch):
        patched = dict(ELEMENT_RADII)
        patched['Xx'] = {'vdw': None, 'covalent': None, 'ionic': None, 'atomic': None}
        monkeypatch.setattr(radii_module, 'ELEMENT_RADII', patched)

        radius, substituted = radius_for('Xx', 'vdw')
        assert radius == DEFAULT_RADIUS
        assert substituted is True

    def test_default_radius_when_model_and_covalent_none(self, monkeypatch):
        patched = dict(ELEMENT_RADII)
        patched['Xx'] = {'vdw': 2.0, 'covalent': None, 'ionic': None, 'atomic': None}
        monkeypatch.setattr(radii_module, 'ELEMENT_RADII', patched)

        # ionic is None and covalent is None -> last-resort default.
        radius, substituted = radius_for('Xx', 'ionic')
        assert radius == DEFAULT_RADIUS
        assert substituted is True

    def test_still_uses_model_value_when_present(self, monkeypatch):
        patched = dict(ELEMENT_RADII)
        patched['Xx'] = {'vdw': 2.0, 'covalent': None, 'ionic': None, 'atomic': None}
        monkeypatch.setattr(radii_module, 'ELEMENT_RADII', patched)

        # The requested model has a value, so no fallback happens.
        radius, substituted = radius_for('Xx', 'vdw')
        assert radius == 2.0
        assert substituted is False


class TestRadiusForAllRealElements:
    """Smoke check across the whole bundled database."""

    def test_every_element_resolves_to_positive_radius(self):
        # A handful of bundled entries store integer literals (e.g. Pa
        # covalent=2, Cn vdw=2), and radius_for passes the stored value
        # through unchanged, so accept any real number here.
        for element in ELEMENT_RADII:
            for model in ('vdw', 'covalent', 'ionic', 'atomic'):
                radius, substituted = radius_for(element, model)
                assert isinstance(radius, (int, float))
                assert radius > 0.0
                assert isinstance(substituted, bool)

    def test_substituted_flag_matches_database(self):
        # When the model value is present, substituted must be False;
        # otherwise (covalent fallback) it must be True, because no
        # bundled element has a None covalent radius.
        for element, entry in ELEMENT_RADII.items():
            for model in ('vdw', 'covalent', 'ionic', 'atomic'):
                _, substituted = radius_for(element, model)
                assert substituted is (entry.get(model) is None)
