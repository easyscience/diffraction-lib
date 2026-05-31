# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for rendering_structure category (default switchable engine)."""

from __future__ import annotations

import gemmi
import pytest

from easydiffraction.display.structure.enums import ViewerEngineEnum
from easydiffraction.display.structure.viewing import Viewer
from easydiffraction.display.structure.viewing import ViewerFactory
from easydiffraction.project.categories.rendering_structure import default as rs_mod
from easydiffraction.project.categories.rendering_structure.default import AUTO_DESCRIPTION
from easydiffraction.project.categories.rendering_structure.default import AUTO_ENGINE
from easydiffraction.project.categories.rendering_structure.default import VIEW_ENGINE_OPTIONS
from easydiffraction.project.categories.rendering_structure.default import RenderingStructure
from easydiffraction.project.categories.rendering_structure.factory import (
    RenderingStructureFactory,
)
from easydiffraction.utils.logging import Logger


def _default_engine() -> str:
    """Resolve the environment default engine deterministically."""
    return ViewerEngineEnum.default().value


# ----------------------------------------------------------------------
# Module-level constants
# ----------------------------------------------------------------------


class TestModuleConstants:
    def test_auto_engine_constant(self):
        assert AUTO_ENGINE == 'auto'

    def test_auto_description_is_nonempty_str(self):
        assert isinstance(AUTO_DESCRIPTION, str)
        assert AUTO_DESCRIPTION

    def test_view_engine_options_lists_auto_first(self):
        assert VIEW_ENGINE_OPTIONS[0] == AUTO_ENGINE

    def test_view_engine_options_includes_every_enum_member(self):
        for member in ViewerEngineEnum:
            assert member.value in VIEW_ENGINE_OPTIONS

    def test_view_engine_options_has_no_extra_entries(self):
        expected = {AUTO_ENGINE, *(m.value for m in ViewerEngineEnum)}
        assert set(VIEW_ENGINE_OPTIONS) == expected


# ----------------------------------------------------------------------
# Factory registration
# ----------------------------------------------------------------------


class TestRenderingStructureFactory:
    def test_supported_tags(self):
        assert 'default' in RenderingStructureFactory.supported_tags()

    def test_default_tag(self):
        assert RenderingStructureFactory.default_tag() == 'default'

    def test_create_returns_rendering_structure(self):
        obj = RenderingStructureFactory.create('default')
        assert isinstance(obj, RenderingStructure)


# ----------------------------------------------------------------------
# Construction / defaults
# ----------------------------------------------------------------------


class TestConstructionAndDefaults:
    def test_type_info_tag(self):
        assert RenderingStructure.type_info.tag == 'default'

    def test_category_class_attrs(self):
        assert RenderingStructure._category_code == 'rendering_structure'
        assert RenderingStructure._owner_attr_name == 'rendering_structure'
        assert RenderingStructure._swap_method_name == '_swap_rendering_structure'

    def test_identity_category_code(self):
        rs = RenderingStructure()
        assert rs._identity.category_code == 'rendering_structure'

    def test_default_type_is_auto(self):
        rs = RenderingStructure()
        assert rs.type == AUTO_ENGINE

    def test_default_type_descriptor_value(self):
        rs = RenderingStructure()
        assert rs._type.value == AUTO_ENGINE

    def test_viewer_is_viewer_instance(self):
        rs = RenderingStructure()
        assert isinstance(rs.viewer, Viewer)

    def test_viewer_engine_is_environment_default(self):
        rs = RenderingStructure()
        assert rs.viewer.engine == _default_engine()

    def test_viewer_engine_is_supported(self):
        rs = RenderingStructure()
        assert rs.viewer.engine in ViewerFactory.supported_engines()

    def test_type_cif_handler_name(self):
        rs = RenderingStructure()
        assert rs._type._cif_handler.names == ['_rendering_structure.type']

    def test_parent_starts_detached(self):
        rs = RenderingStructure()
        assert rs._parent is None


# ----------------------------------------------------------------------
# viewer property
# ----------------------------------------------------------------------


class TestViewerProperty:
    def test_viewer_is_stable_reference(self):
        rs = RenderingStructure()
        assert rs.viewer is rs.viewer

    def test_distinct_instances_have_distinct_viewers(self):
        first = RenderingStructure()
        second = RenderingStructure()
        # Viewer is constructed (not fetched as singleton) per category,
        # so each category owns an independent facade.
        assert first.viewer is not second.viewer


# ----------------------------------------------------------------------
# _resolved_engine
# ----------------------------------------------------------------------


class TestResolvedEngine:
    def test_auto_resolves_to_environment_default(self):
        assert RenderingStructure._resolved_engine(AUTO_ENGINE) == _default_engine()

    def test_explicit_ascii_passes_through(self):
        assert RenderingStructure._resolved_engine('ascii') == 'ascii'

    def test_explicit_threejs_passes_through(self):
        assert RenderingStructure._resolved_engine('threejs') == 'threejs'


# ----------------------------------------------------------------------
# _set_type (validator: valid + invalid)
# ----------------------------------------------------------------------


class TestSetType:
    def test_set_explicit_engine_updates_type_and_viewer(self):
        rs = RenderingStructure()
        rs._set_type('threejs')
        assert rs.type == 'threejs'
        assert rs.viewer.engine == 'threejs'

    def test_set_ascii_updates_viewer_engine(self):
        rs = RenderingStructure()
        rs._set_type('ascii')
        assert rs.type == 'ascii'
        assert rs.viewer.engine == 'ascii'

    def test_set_auto_resolves_viewer_to_environment_default(self):
        rs = RenderingStructure()
        rs._set_type('threejs')
        rs._set_type('auto')
        assert rs.type == 'auto'
        assert rs.viewer.engine == _default_engine()

    def test_invalid_type_strict_raises_value_error(self):
        rs = RenderingStructure()
        initial = rs.type
        with pytest.raises(ValueError, match='Unsupported rendering_structure type'):
            rs._set_type('bogus-engine')
        assert rs.type == initial

    def test_invalid_type_strict_leaves_viewer_unchanged(self):
        rs = RenderingStructure()
        engine_before = rs.viewer.engine
        with pytest.raises(ValueError, match='Unsupported rendering_structure type'):
            rs._set_type('bogus-engine')
        assert rs.viewer.engine == engine_before

    def test_invalid_type_non_strict_warns_and_keeps_value(self, monkeypatch):
        rs = RenderingStructure()
        warnings: list[str] = []
        monkeypatch.setattr(rs_mod.log, 'warning', warnings.append)
        rs._set_type('bogus-engine', strict=False)
        assert rs.type == AUTO_ENGINE
        assert any('Unsupported rendering_structure type' in w for w in warnings)

    def test_strict_error_message_points_to_show_supported(self):
        rs = RenderingStructure()
        with pytest.raises(ValueError, match=r'rendering_structure\.show_supported'):
            rs._set_type('nope')


# ----------------------------------------------------------------------
# _supported_types
# ----------------------------------------------------------------------


class TestSupportedTypes:
    def test_includes_auto_pair_first(self):
        pairs = RenderingStructure._supported_types({})
        assert pairs[0] == (AUTO_ENGINE, AUTO_DESCRIPTION)

    def test_lists_every_engine_from_factory(self):
        pairs = RenderingStructure._supported_types({})
        tags = [tag for tag, _ in pairs]
        for engine in ViewerFactory.supported_engines():
            assert engine in tags

    def test_descriptions_are_strings(self):
        pairs = RenderingStructure._supported_types({})
        assert all(isinstance(desc, str) and desc for _, desc in pairs)

    def test_filters_argument_is_ignored(self):
        with_filters = RenderingStructure._supported_types({'anything': object()})
        without_filters = RenderingStructure._supported_types({})
        assert with_filters == without_filters


# ----------------------------------------------------------------------
# show_supported (inherited; lists enum values)
# ----------------------------------------------------------------------


class TestShowSupported:
    def test_runs_without_parent(self, capsys):
        rs = RenderingStructure()
        rs.show_supported()
        out = capsys.readouterr().out
        assert out  # produced a table

    def test_lists_auto_and_every_engine(self, capsys):
        rs = RenderingStructure()
        rs.show_supported()
        out = capsys.readouterr().out
        assert AUTO_ENGINE in out
        for member in ViewerEngineEnum:
            assert member.value in out

    def test_marks_active_type(self, capsys):
        rs = RenderingStructure()
        rs._set_type('threejs')
        rs.show_supported()
        out = capsys.readouterr().out
        assert '*' in out
        assert 'threejs' in out


# ----------------------------------------------------------------------
# type setter (SwitchableCategoryBase contract via parent)
# ----------------------------------------------------------------------


class TestTypeSetter:
    def test_detached_instance_raises_runtime_error(self):
        rs = RenderingStructure()
        with pytest.raises(RuntimeError, match='detached'):
            rs.type = 'threejs'

    def test_setter_routes_through_owner_swap(self):
        rs = RenderingStructure()

        class _Owner:
            rendering_structure = rs

            @staticmethod
            def _supported_filters_for(_category):
                return {}

            def _swap_rendering_structure(self, new_type, *, strict=True):
                rs._set_type(new_type, strict=strict)

        rs._parent = _Owner()
        rs.type = 'threejs'
        assert rs.type == 'threejs'
        assert rs.viewer.engine == 'threejs'

    def test_setter_on_stale_instance_raises(self):
        rs = RenderingStructure()
        live = RenderingStructure()

        class _Owner:
            # Owner's live category is a different instance.
            rendering_structure = live

            def _swap_rendering_structure(self, new_type, *, strict=True):  # pragma: no cover
                live._set_type(new_type, strict=strict)

        rs._parent = _Owner()
        with pytest.raises(RuntimeError, match='no longer the live category'):
            rs.type = 'threejs'


# ----------------------------------------------------------------------
# from_cif
# ----------------------------------------------------------------------


class TestFromCif:
    def _block(self, cif_text: str):
        return gemmi.cif.read_string(cif_text).sole_block()

    def test_restores_type_via_parent_swap(self):
        rs = RenderingStructure()
        swapped: list[tuple[str, dict]] = []

        class _Parent:
            def _swap_rendering_structure(self, new_type, *, strict):
                swapped.append((new_type, {'strict': strict}))
                rs._set_type(new_type, strict=strict)

        rs._parent = _Parent()
        block = self._block('data_test\n_rendering_structure.type threejs\n')
        rs.from_cif(block)
        assert swapped == [('threejs', {'strict': False})]
        assert rs.type == 'threejs'
        assert rs.viewer.engine == 'threejs'

    def test_tolerates_invalid_type(self, monkeypatch):
        # The descriptor's own from_cif validation routes through the
        # Logger; force WARN so it logs rather than raises (another test
        # may have left the Logger in RAISE mode).
        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)

        rs = RenderingStructure()

        class _Parent:
            def _swap_rendering_structure(self, new_type, *, strict):
                rs._set_type(new_type, strict=strict)

        rs._parent = _Parent()
        block = self._block('data_test\n_rendering_structure.type bogus-engine\n')
        warnings: list[str] = []
        monkeypatch.setattr(rs_mod.log, 'warning', warnings.append)
        rs.from_cif(block)
        assert rs.type == AUTO_ENGINE
        assert any('Unsupported rendering_structure type' in w for w in warnings)

    def test_missing_type_leaves_default(self):
        rs = RenderingStructure()
        called: list[str] = []

        class _Parent:
            def _swap_rendering_structure(self, new_type, *, strict):  # pragma: no cover
                called.append(new_type)

        rs._parent = _Parent()
        block = self._block('data_test\n_other.value 1\n')
        rs.from_cif(block)
        assert rs.type == AUTO_ENGINE
        assert called == []


# ----------------------------------------------------------------------
# as_cif (round-trip)
# ----------------------------------------------------------------------


class TestAsCif:
    def test_as_cif_contains_handler_name(self):
        rs = RenderingStructure()
        assert '_rendering_structure.type' in rs.as_cif

    def test_as_cif_reflects_explicit_engine(self):
        rs = RenderingStructure()
        rs._set_type('threejs')
        assert 'threejs' in rs.as_cif

    def test_as_cif_round_trip_restores_type(self):
        rs = RenderingStructure()
        rs._set_type('threejs')
        cif_text = rs.as_cif

        restored = RenderingStructure()

        class _Parent:
            def _swap_rendering_structure(self, new_type, *, strict):
                restored._set_type(new_type, strict=strict)

        restored._parent = _Parent()
        block = gemmi.cif.read_string(f'data_test\n{cif_text}\n').sole_block()
        restored.from_cif(block)
        assert restored.type == 'threejs'
