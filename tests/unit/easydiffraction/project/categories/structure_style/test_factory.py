# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for the project structure_style factory."""

from __future__ import annotations

import gemmi
import pytest

from easydiffraction.utils.logging import Logger


@pytest.fixture
def raise_on_error(monkeypatch):
    """Force Logger into RAISE mode for invalid-input assertions.

    Another test may have leaked WARN mode onto the shared Logger,
    so validators that route through ``log.error()`` would silently
    fall back instead of raising. Pin RAISE for the test body.
    """
    monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.RAISE, raising=True)


# ----------------------------------------------------------------------
#  Module / factory surface
# ----------------------------------------------------------------------


def test_module_import():
    import easydiffraction.project.categories.structure_style.factory as MUT

    expected_module_name = 'easydiffraction.project.categories.structure_style.factory'
    assert MUT.__name__ == expected_module_name


def test_default_rules_universal_fallback():
    from easydiffraction.project.categories.structure_style.factory import StructureStyleFactory

    # The factory declares a single universal-fallback rule.
    assert StructureStyleFactory._default_rules == {frozenset(): 'default'}


def test_supported_tags_lists_default():
    from easydiffraction.project.categories.structure_style.factory import StructureStyleFactory

    tags = StructureStyleFactory.supported_tags()
    assert isinstance(tags, list)
    assert tags == ['default']


def test_default_tag_without_conditions():
    from easydiffraction.project.categories.structure_style.factory import StructureStyleFactory

    assert StructureStyleFactory.default_tag() == 'default'


def test_default_tag_with_unmatched_conditions_falls_back():
    from easydiffraction.project.categories.structure_style.factory import StructureStyleFactory

    # Extra conditions still match the empty-key universal fallback.
    assert StructureStyleFactory.default_tag(scattering_type='bragg') == 'default'


def test_create_returns_structure_style():
    from easydiffraction.project.categories.structure_style.default import StructureStyle
    from easydiffraction.project.categories.structure_style.factory import StructureStyleFactory

    structure_style = StructureStyleFactory.create('default')
    assert isinstance(structure_style, StructureStyle)


def test_create_rejects_unknown_tag():
    from easydiffraction.project.categories.structure_style.factory import StructureStyleFactory

    with pytest.raises(ValueError, match=r"Unsupported type: 'missing'"):
        StructureStyleFactory.create('missing')


def test_create_default_for_returns_structure_style():
    from easydiffraction.project.categories.structure_style.default import StructureStyle
    from easydiffraction.project.categories.structure_style.factory import StructureStyleFactory

    structure_style = StructureStyleFactory.create_default_for()
    assert isinstance(structure_style, StructureStyle)


def test_supported_for_includes_registered_class():
    from easydiffraction.project.categories.structure_style.default import StructureStyle
    from easydiffraction.project.categories.structure_style.factory import StructureStyleFactory

    supported = StructureStyleFactory.supported_for()
    assert StructureStyle in supported


def test_show_supported_lists_default(capsys):
    from easydiffraction.project.categories.structure_style.factory import StructureStyleFactory

    StructureStyleFactory.show_supported()
    out = capsys.readouterr().out
    assert 'Supported types' in out
    assert 'default' in out


def test_registry_is_independent_from_base():
    from easydiffraction.core.factory import FactoryBase
    from easydiffraction.project.categories.structure_style.default import StructureStyle
    from easydiffraction.project.categories.structure_style.factory import StructureStyleFactory

    # __init_subclass__ gives each factory its own registry; the
    # registered concrete class must not leak onto the shared base.
    assert StructureStyle in StructureStyleFactory._registry
    assert StructureStyle not in FactoryBase._registry


# ----------------------------------------------------------------------
#  Created StructureStyle instance: identity, defaults, CIF handlers
# ----------------------------------------------------------------------


def _make_style():
    from easydiffraction.project.categories.structure_style.factory import StructureStyleFactory

    return StructureStyleFactory.create('default')


def test_created_instance_identity():
    structure_style = _make_style()

    assert structure_style.type_info.tag == 'default'
    assert structure_style._category_code == 'structure_style'


def test_created_instance_defaults():
    structure_style = _make_style()

    assert structure_style.atom_view.value == 'covalent'
    assert structure_style.color_scheme.value == 'jmol'
    assert structure_style.adp_probability.value == 0.99
    assert structure_style.atom_scale.value == 0.3


def test_cif_handler_names():
    structure_style = _make_style()

    assert structure_style.atom_view._cif_handler.names == ['_structure_style.atom_view']
    assert structure_style.color_scheme._cif_handler.names == ['_structure_style.color_scheme']
    assert structure_style.adp_probability._cif_handler.names == [
        '_structure_style.adp_probability',
    ]
    assert structure_style.atom_scale._cif_handler.names == ['_structure_style.atom_scale']


# ----------------------------------------------------------------------
#  Enum-backed selectors: valid setters and show_supported()
# ----------------------------------------------------------------------


def test_atom_view_enum_backing():
    from easydiffraction.display.structure.enums import AtomViewEnum

    structure_style = _make_style()

    assert structure_style.atom_view.enum is AtomViewEnum


def test_color_scheme_enum_backing():
    from easydiffraction.display.structure.enums import ColorSchemeEnum

    structure_style = _make_style()

    assert structure_style.color_scheme.enum is ColorSchemeEnum


def test_atom_view_setter_accepts_each_member():
    from easydiffraction.display.structure.enums import AtomViewEnum

    structure_style = _make_style()
    for member in AtomViewEnum:
        structure_style.atom_view = member.value
        assert structure_style.atom_view.value == member.value


def test_color_scheme_setter_accepts_each_member():
    from easydiffraction.display.structure.enums import ColorSchemeEnum

    structure_style = _make_style()
    for member in ColorSchemeEnum:
        structure_style.color_scheme = member.value
        assert structure_style.color_scheme.value == member.value


def test_atom_view_setter_rejects_unknown_value():
    structure_style = _make_style()

    # The setter wraps the value in the enum constructor, which rejects
    # unknown strings with ValueError before the descriptor is touched.
    with pytest.raises(ValueError, match='not a valid AtomViewEnum'):
        structure_style.atom_view = 'nope'


def test_color_scheme_setter_rejects_unknown_value():
    structure_style = _make_style()

    with pytest.raises(ValueError, match='not a valid ColorSchemeEnum'):
        structure_style.color_scheme = 'nope'


def test_atom_view_show_supported_lists_all_members(capsys):
    from easydiffraction.display.structure.enums import AtomViewEnum

    structure_style = _make_style()
    structure_style.atom_view.show_supported()
    out = capsys.readouterr().out

    assert 'Atom View types' in out
    for member in AtomViewEnum:
        assert member.value in out
    # The active (default) value is marked.
    assert '*' in out


def test_color_scheme_show_supported_lists_all_members(capsys):
    from easydiffraction.display.structure.enums import ColorSchemeEnum

    structure_style = _make_style()
    structure_style.color_scheme.show_supported()
    out = capsys.readouterr().out

    assert 'Color Scheme types' in out
    for member in ColorSchemeEnum:
        assert member.value in out
    assert '*' in out


# ----------------------------------------------------------------------
#  Numeric selectors: range validation (valid + invalid)
# ----------------------------------------------------------------------


def test_adp_probability_setter_accepts_in_range():
    structure_style = _make_style()

    structure_style.adp_probability = 0.5
    assert structure_style.adp_probability.value == 0.5


def test_atom_scale_setter_accepts_in_range():
    structure_style = _make_style()

    structure_style.atom_scale = 1.0  # le=1.0 boundary is allowed
    assert structure_style.atom_scale.value == 1.0


def test_adp_probability_rejects_value_at_or_above_one(raise_on_error):
    structure_style = _make_style()

    with pytest.raises(TypeError, match=r'structure_style\.adp_probability'):
        structure_style.adp_probability = 1.0


def test_adp_probability_rejects_value_at_or_below_zero(raise_on_error):
    structure_style = _make_style()

    with pytest.raises(TypeError, match=r'structure_style\.adp_probability'):
        structure_style.adp_probability = 0.0


def test_atom_scale_rejects_value_above_one(raise_on_error):
    structure_style = _make_style()

    with pytest.raises(TypeError, match=r'structure_style\.atom_scale'):
        structure_style.atom_scale = 2.0


def test_atom_scale_rejects_value_at_or_below_zero(raise_on_error):
    structure_style = _make_style()

    with pytest.raises(TypeError, match=r'structure_style\.atom_scale'):
        structure_style.atom_scale = 0.0


# ----------------------------------------------------------------------
#  CIF serialisation round-trip
# ----------------------------------------------------------------------


def test_as_cif_emits_all_handlers():
    structure_style = _make_style()
    structure_style.atom_view = 'vdw'
    structure_style.color_scheme = 'vesta'
    structure_style.adp_probability = 0.5
    structure_style.atom_scale = 0.8

    cif = structure_style.as_cif

    assert '_structure_style.atom_view vdw' in cif
    assert '_structure_style.color_scheme vesta' in cif
    assert '_structure_style.adp_probability 0.5' in cif
    assert '_structure_style.atom_scale 0.8' in cif


def test_from_cif_restores_all_fields():
    structure_style = _make_style()
    block = gemmi.cif.read_string(
        'data_t\n'
        '_structure_style.atom_view covalent\n'
        '_structure_style.color_scheme vesta\n'
        '_structure_style.adp_probability 0.5\n'
        '_structure_style.atom_scale 0.8\n'
    ).sole_block()

    structure_style.from_cif(block)

    assert structure_style.atom_view.value == 'covalent'
    assert structure_style.color_scheme.value == 'vesta'
    assert structure_style.adp_probability.value == 0.5
    assert structure_style.atom_scale.value == 0.8


def test_cif_round_trip_preserves_values():
    structure_style = _make_style()
    structure_style.atom_view = 'ionic'
    structure_style.color_scheme = 'vesta'
    structure_style.adp_probability = 0.75
    structure_style.atom_scale = 0.6

    block = gemmi.cif.read_string(f'data_t\n{structure_style.as_cif}\n').sole_block()
    restored = _make_style()
    restored.from_cif(block)

    assert restored.atom_view.value == 'ionic'
    assert restored.color_scheme.value == 'vesta'
    assert restored.adp_probability.value == 0.75
    assert restored.atom_scale.value == 0.6
