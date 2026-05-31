# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for the crysview structure-view enumerations."""

from __future__ import annotations

from enum import StrEnum

import pytest

import easydiffraction.display.structure.enums as enums_mod
from easydiffraction.display.structure.enums import AtomViewEnum
from easydiffraction.display.structure.enums import ColorSchemeEnum
from easydiffraction.display.structure.enums import ViewerEngineEnum


def test_module_import():
    expected_module_name = 'easydiffraction.display.structure.enums'
    assert enums_mod.__name__ == expected_module_name


# ----------------------------------------------------------------------
# ViewerEngineEnum
# ----------------------------------------------------------------------


class TestViewerEngineEnum:
    def test_is_str_enum(self):
        assert issubclass(ViewerEngineEnum, StrEnum)

    def test_members(self):
        assert ViewerEngineEnum.ASCII == 'ascii'
        assert ViewerEngineEnum.THREEJS == 'threejs'

    def test_member_count(self):
        assert {member.value for member in ViewerEngineEnum} == {'ascii', 'threejs'}

    def test_from_string(self):
        assert ViewerEngineEnum('ascii') is ViewerEngineEnum.ASCII
        assert ViewerEngineEnum('threejs') is ViewerEngineEnum.THREEJS

    def test_invalid_string(self):
        with pytest.raises(ValueError, match='is not a valid ViewerEngineEnum'):
            ViewerEngineEnum('opengl')

    def test_default_is_ascii_outside_jupyter(self, monkeypatch):
        monkeypatch.setattr(enums_mod, 'in_jupyter', lambda: False)
        assert ViewerEngineEnum.default() is ViewerEngineEnum.ASCII

    def test_default_is_threejs_in_jupyter(self, monkeypatch):
        monkeypatch.setattr(enums_mod, 'in_jupyter', lambda: True)
        assert ViewerEngineEnum.default() is ViewerEngineEnum.THREEJS

    def test_description_ascii(self):
        assert ViewerEngineEnum.ASCII.description() == 'Console ASCII schematic structure view'

    def test_description_threejs(self):
        assert ViewerEngineEnum.THREEJS.description() == 'Interactive Three.js 3D structure view'

    def test_every_member_has_nonempty_description(self):
        for member in ViewerEngineEnum:
            assert member.description()


# ----------------------------------------------------------------------
# AtomViewEnum
# ----------------------------------------------------------------------


class TestAtomViewEnum:
    def test_is_str_enum(self):
        assert issubclass(AtomViewEnum, StrEnum)

    def test_members(self):
        assert AtomViewEnum.VDW == 'vdw'
        assert AtomViewEnum.COVALENT == 'covalent'
        assert AtomViewEnum.IONIC == 'ionic'
        assert AtomViewEnum.ADP == 'adp'

    def test_member_count(self):
        assert {member.value for member in AtomViewEnum} == {
            'vdw',
            'covalent',
            'ionic',
            'adp',
        }

    def test_from_string(self):
        assert AtomViewEnum('vdw') is AtomViewEnum.VDW
        assert AtomViewEnum('covalent') is AtomViewEnum.COVALENT
        assert AtomViewEnum('ionic') is AtomViewEnum.IONIC
        assert AtomViewEnum('adp') is AtomViewEnum.ADP

    def test_invalid_string(self):
        with pytest.raises(ValueError, match='is not a valid AtomViewEnum'):
            AtomViewEnum('atomic')

    def test_default_is_adp(self):
        assert AtomViewEnum.default() is AtomViewEnum.ADP

    def test_is_adp_true_only_for_adp(self):
        assert AtomViewEnum.ADP.is_adp is True
        assert AtomViewEnum.VDW.is_adp is False
        assert AtomViewEnum.COVALENT.is_adp is False
        assert AtomViewEnum.IONIC.is_adp is False

    def test_radius_model_radius_views_return_own_value(self):
        assert AtomViewEnum.VDW.radius_model() == 'vdw'
        assert AtomViewEnum.COVALENT.radius_model() == 'covalent'
        assert AtomViewEnum.IONIC.radius_model() == 'ionic'

    def test_radius_model_adp_falls_back_to_covalent(self):
        assert AtomViewEnum.ADP.radius_model() == AtomViewEnum.COVALENT.value
        assert AtomViewEnum.ADP.radius_model() == 'covalent'

    def test_description_per_member(self):
        assert AtomViewEnum.VDW.description() == 'Van der Waals radius balls'
        assert AtomViewEnum.COVALENT.description() == 'Covalent radius balls'
        assert AtomViewEnum.IONIC.description() == 'Ionic (Shannon) radius balls'
        assert AtomViewEnum.ADP.description() == 'ADP probability surfaces (spheres / ellipsoids)'

    def test_every_member_has_nonempty_description(self):
        for member in AtomViewEnum:
            assert member.description()


# ----------------------------------------------------------------------
# ColorSchemeEnum
# ----------------------------------------------------------------------


class TestColorSchemeEnum:
    def test_is_str_enum(self):
        assert issubclass(ColorSchemeEnum, StrEnum)

    def test_members(self):
        assert ColorSchemeEnum.JMOL == 'jmol'
        assert ColorSchemeEnum.VESTA == 'vesta'

    def test_member_count(self):
        assert {member.value for member in ColorSchemeEnum} == {'jmol', 'vesta'}

    def test_from_string(self):
        assert ColorSchemeEnum('jmol') is ColorSchemeEnum.JMOL
        assert ColorSchemeEnum('vesta') is ColorSchemeEnum.VESTA

    def test_invalid_string(self):
        with pytest.raises(ValueError, match='is not a valid ColorSchemeEnum'):
            ColorSchemeEnum('cpk')

    def test_default_is_jmol(self):
        assert ColorSchemeEnum.default() is ColorSchemeEnum.JMOL

    def test_description_jmol(self):
        assert ColorSchemeEnum.JMOL.description() == 'Jmol / CPK colour scheme'

    def test_description_vesta(self):
        assert ColorSchemeEnum.VESTA.description() == 'VESTA colour scheme'

    def test_every_member_has_nonempty_description(self):
        for member in ColorSchemeEnum:
            assert member.description()
