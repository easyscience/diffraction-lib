# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for the project structure_style category (default)."""

from __future__ import annotations

import gemmi
import pytest


def test_module_import():
    import easydiffraction.project.categories.structure_style.default as MUT

    expected_module_name = 'easydiffraction.project.categories.structure_style.default'
    assert MUT.__name__ == expected_module_name


# ----------------------------------------------------------------------
#  Factory registration
# ----------------------------------------------------------------------


class TestStructureStyleFactory:
    def test_supported_tags(self):
        from easydiffraction.project.categories.structure_style.factory import (
            StructureStyleFactory,
        )

        assert 'default' in StructureStyleFactory.supported_tags()

    def test_default_tag(self):
        from easydiffraction.project.categories.structure_style.factory import (
            StructureStyleFactory,
        )

        assert StructureStyleFactory.default_tag() == 'default'

    def test_create_returns_structure_style(self):
        from easydiffraction.project.categories.structure_style.default import StructureStyle
        from easydiffraction.project.categories.structure_style.factory import (
            StructureStyleFactory,
        )

        obj = StructureStyleFactory.create('default')
        assert isinstance(obj, StructureStyle)


# ----------------------------------------------------------------------
#  Identity, type_info and defaults
# ----------------------------------------------------------------------


class TestStructureStyleIdentityAndDefaults:
    def test_type_info(self):
        from easydiffraction.project.categories.structure_style.default import StructureStyle

        assert StructureStyle.type_info.tag == 'default'
        assert StructureStyle.type_info.description != ''

    def test_category_code(self):
        from easydiffraction.project.categories.structure_style.default import StructureStyle

        style = StructureStyle()
        assert style._identity.category_code == 'structure_style'

    def test_instantiation(self):
        from easydiffraction.project.categories.structure_style.default import StructureStyle

        style = StructureStyle()
        assert style is not None

    def test_default_values(self):
        from easydiffraction.project.categories.structure_style.default import StructureStyle

        style = StructureStyle()
        assert style.atom_view.value == 'covalent'
        assert style.color_scheme.value == 'jmol'
        assert style.adp_probability.value == 0.99
        assert style.atom_scale.value == 0.3

    def test_defaults_track_enum_defaults(self):
        from easydiffraction.display.structure.enums import AtomViewEnum
        from easydiffraction.display.structure.enums import ColorSchemeEnum
        from easydiffraction.project.categories.structure_style.default import StructureStyle

        style = StructureStyle()
        assert style.atom_view.value == AtomViewEnum.default().value
        assert style.color_scheme.value == ColorSchemeEnum.default().value

    def test_enum_descriptors_expose_backing_enum(self):
        from easydiffraction.display.structure.enums import AtomViewEnum
        from easydiffraction.display.structure.enums import ColorSchemeEnum
        from easydiffraction.project.categories.structure_style.default import StructureStyle

        style = StructureStyle()
        assert style.atom_view.enum is AtomViewEnum
        assert style.color_scheme.enum is ColorSchemeEnum

    def test_parameters_collects_all_descriptors(self):
        from easydiffraction.project.categories.structure_style.default import StructureStyle

        style = StructureStyle()
        names = {param.name for param in style.parameters}
        assert names == {'atom_view', 'color_scheme', 'adp_probability', 'atom_scale'}


# ----------------------------------------------------------------------
#  CIF handler names
# ----------------------------------------------------------------------


class TestStructureStyleTagSpecNames:
    def test_tags_names(self):
        from easydiffraction.project.categories.structure_style.default import StructureStyle

        style = StructureStyle()
        assert style.atom_view._tags.edi_names == ['_structure_style.atom_view']
        assert style.color_scheme._tags.edi_names == ['_structure_style.color_scheme']
        assert style.adp_probability._tags.edi_names == ['_structure_style.adp_probability']
        assert style.atom_scale._tags.edi_names == ['_structure_style.atom_scale']


# ----------------------------------------------------------------------
#  atom_view selector
# ----------------------------------------------------------------------


class TestAtomViewSelector:
    def test_setter_accepts_valid_values(self):
        from easydiffraction.project.categories.structure_style.default import StructureStyle

        style = StructureStyle()
        for value in ('vdw', 'covalent', 'ionic', 'adp'):
            style.atom_view = value
            assert style.atom_view.value == value

    def test_setter_rejects_invalid_value(self):
        from easydiffraction.project.categories.structure_style.default import StructureStyle

        style = StructureStyle()
        with pytest.raises(ValueError, match='not a valid AtomViewEnum'):
            style.atom_view = 'bogus'

    def test_invalid_value_keeps_previous(self):
        from easydiffraction.project.categories.structure_style.default import StructureStyle

        style = StructureStyle()
        style.atom_view = 'vdw'
        with pytest.raises(ValueError, match='not a valid AtomViewEnum'):
            style.atom_view = 'bogus'
        assert style.atom_view.value == 'vdw'

    def test_show_supported_lists_all_enum_values(self, capsys):
        from easydiffraction.display.structure.enums import AtomViewEnum
        from easydiffraction.project.categories.structure_style.default import StructureStyle

        style = StructureStyle()
        style.atom_view.show_supported()

        out = capsys.readouterr().out
        for member in AtomViewEnum:
            assert member.value in out

    def test_show_supported_marks_active_value(self, capsys):
        from easydiffraction.project.categories.structure_style.default import StructureStyle

        style = StructureStyle()
        style.atom_view = 'ionic'
        style.atom_view.show_supported()

        out = capsys.readouterr().out
        # Active value is annotated with an asterisk in its row.
        marked_line = next(line for line in out.splitlines() if 'ionic' in line)
        assert '*' in marked_line


# ----------------------------------------------------------------------
#  color_scheme selector
# ----------------------------------------------------------------------


class TestColorSchemeSelector:
    def test_setter_accepts_valid_values(self):
        from easydiffraction.project.categories.structure_style.default import StructureStyle

        style = StructureStyle()
        for value in ('jmol', 'vesta'):
            style.color_scheme = value
            assert style.color_scheme.value == value

    def test_setter_rejects_invalid_value(self):
        from easydiffraction.project.categories.structure_style.default import StructureStyle

        style = StructureStyle()
        with pytest.raises(ValueError, match='not a valid ColorSchemeEnum'):
            style.color_scheme = 'bogus'

    def test_invalid_value_keeps_previous(self):
        from easydiffraction.project.categories.structure_style.default import StructureStyle

        style = StructureStyle()
        style.color_scheme = 'vesta'
        with pytest.raises(ValueError, match='not a valid ColorSchemeEnum'):
            style.color_scheme = 'bogus'
        assert style.color_scheme.value == 'vesta'

    def test_show_supported_lists_all_enum_values(self, capsys):
        from easydiffraction.display.structure.enums import ColorSchemeEnum
        from easydiffraction.project.categories.structure_style.default import StructureStyle

        style = StructureStyle()
        style.color_scheme.show_supported()

        out = capsys.readouterr().out
        for member in ColorSchemeEnum:
            assert member.value in out


# ----------------------------------------------------------------------
#  adp_probability numeric descriptor
# ----------------------------------------------------------------------


class TestAdpProbability:
    def test_setter_accepts_value_in_open_interval(self):
        from easydiffraction.project.categories.structure_style.default import StructureStyle

        style = StructureStyle()
        style.adp_probability = 0.5
        assert style.adp_probability.value == 0.5

    def test_out_of_range_raises_in_raise_mode(self, monkeypatch):
        from easydiffraction.project.categories.structure_style.default import StructureStyle
        from easydiffraction.utils.logging import Logger

        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.RAISE, raising=True)
        style = StructureStyle()

        with pytest.raises(TypeError, match='outside'):
            style.adp_probability = 1.5

    def test_boundaries_are_exclusive(self, monkeypatch):
        from easydiffraction.project.categories.structure_style.default import StructureStyle
        from easydiffraction.utils.logging import Logger

        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.RAISE, raising=True)
        style = StructureStyle()

        with pytest.raises(TypeError, match='outside'):
            style.adp_probability = 0.0
        with pytest.raises(TypeError, match='outside'):
            style.adp_probability = 1.0

    def test_out_of_range_keeps_current_in_warn_mode(self, monkeypatch):
        from easydiffraction.project.categories.structure_style.default import StructureStyle
        from easydiffraction.utils.logging import Logger

        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)
        style = StructureStyle()

        style.adp_probability = 1.5  # rejected, current value kept
        assert style.adp_probability.value == 0.99

    def test_wrong_type_raises_in_raise_mode(self, monkeypatch):
        from easydiffraction.project.categories.structure_style.default import StructureStyle
        from easydiffraction.utils.logging import Logger

        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.RAISE, raising=True)
        style = StructureStyle()

        with pytest.raises(TypeError, match='Type mismatch'):
            style.adp_probability = 'not-a-number'


# ----------------------------------------------------------------------
#  atom_scale numeric descriptor
# ----------------------------------------------------------------------


class TestAtomScale:
    def test_setter_accepts_value_in_range(self):
        from easydiffraction.project.categories.structure_style.default import StructureStyle

        style = StructureStyle()
        style.atom_scale = 0.8
        assert style.atom_scale.value == 0.8

    def test_upper_boundary_is_inclusive(self):
        from easydiffraction.project.categories.structure_style.default import StructureStyle

        style = StructureStyle()
        style.atom_scale = 1.0
        assert style.atom_scale.value == 1.0

    def test_lower_boundary_is_exclusive(self, monkeypatch):
        from easydiffraction.project.categories.structure_style.default import StructureStyle
        from easydiffraction.utils.logging import Logger

        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.RAISE, raising=True)
        style = StructureStyle()

        with pytest.raises(TypeError, match='outside'):
            style.atom_scale = 0.0

    def test_above_upper_boundary_raises_in_raise_mode(self, monkeypatch):
        from easydiffraction.project.categories.structure_style.default import StructureStyle
        from easydiffraction.utils.logging import Logger

        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.RAISE, raising=True)
        style = StructureStyle()

        with pytest.raises(TypeError, match='outside'):
            style.atom_scale = 1.5

    def test_out_of_range_keeps_current_in_warn_mode(self, monkeypatch):
        from easydiffraction.project.categories.structure_style.default import StructureStyle
        from easydiffraction.utils.logging import Logger

        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)
        style = StructureStyle()

        style.atom_scale = 5.0  # rejected, current value kept
        assert style.atom_scale.value == 0.3


# ----------------------------------------------------------------------
#  CIF serialization / round-trip
# ----------------------------------------------------------------------


class TestStructureStyleCif:
    def test_as_cif_default_output(self):
        from easydiffraction.project.categories.structure_style.default import StructureStyle

        style = StructureStyle()
        cif = style.as_cif
        assert '_structure_style.atom_view covalent' in cif
        assert '_structure_style.color_scheme jmol' in cif
        assert '_structure_style.adp_probability 0.99' in cif
        assert '_structure_style.atom_scale 0.3' in cif

    def test_as_cif_reflects_updated_values(self):
        from easydiffraction.project.categories.structure_style.default import StructureStyle

        style = StructureStyle()
        style.atom_view = 'vdw'
        style.color_scheme = 'vesta'

        cif = style.as_cif
        assert '_structure_style.atom_view vdw' in cif
        assert '_structure_style.color_scheme vesta' in cif

    def test_from_cif_restores_all_fields(self):
        from easydiffraction.project.categories.structure_style.default import StructureStyle

        style = StructureStyle()
        block = gemmi.cif.read_string(
            'data_test\n'
            '_structure_style.atom_view vdw\n'
            '_structure_style.color_scheme vesta\n'
            '_structure_style.adp_probability 0.5\n'
            '_structure_style.atom_scale 0.7\n',
        ).sole_block()

        style.from_cif(block)

        assert style.atom_view.value == 'vdw'
        assert style.color_scheme.value == 'vesta'
        assert style.adp_probability.value == 0.5
        assert style.atom_scale.value == 0.7

    def test_cif_round_trip_is_stable(self):
        from easydiffraction.project.categories.structure_style.default import StructureStyle

        style = StructureStyle()
        style.atom_view = 'covalent'
        style.color_scheme = 'vesta'
        style.adp_probability = 0.5
        style.atom_scale = 0.7

        first_cif = style.as_cif
        block = gemmi.cif.read_string(f'data_test\n{first_cif}\n').sole_block()

        restored = StructureStyle()
        restored.from_cif(block)

        assert restored.as_cif == first_cif
