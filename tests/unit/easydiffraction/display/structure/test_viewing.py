# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for display/structure/viewing.py (Viewer and ViewerFactory)."""

from __future__ import annotations

import pytest

from easydiffraction.core.singleton import SingletonBase
from easydiffraction.display.base import RendererBase
from easydiffraction.display.base import RendererFactoryBase
from easydiffraction.display.structure.enums import ViewerEngineEnum
from easydiffraction.display.structure.renderers.ascii import AsciiStructureRenderer
from easydiffraction.display.structure.renderers.threejs import ThreeJsStructureRenderer
from easydiffraction.display.structure.scene import AtomSphere
from easydiffraction.display.structure.scene import StructureScene
from easydiffraction.display.structure.viewing import Viewer
from easydiffraction.display.structure.viewing import ViewerFactory


# ------------------------------------------------------------------
#  Test doubles and fixtures
# ------------------------------------------------------------------


class _StubBackend:
    """A renderer-shaped stub used to verify facade delegation."""

    def render(self, scene: StructureScene, *, features: frozenset[str]) -> str:
        return f'stub atoms={len(scene.atoms)} features={sorted(features)}'

    def supported_features(self) -> frozenset[str]:
        return frozenset({'atoms', 'cell'})


@pytest.fixture
def viewer(monkeypatch):
    """Yield a fresh Viewer with the singleton reset before and after."""
    monkeypatch.setattr(Viewer, '_instance', None)
    yield Viewer()
    monkeypatch.setattr(Viewer, '_instance', None)


def _minimal_scene() -> StructureScene:
    """Build a tiny renderer-neutral scene without any engine."""
    basis = (
        (1.0, 0.0, 0.0),
        (0.0, 1.0, 0.0),
        (0.0, 0.0, 1.0),
    )
    atom = AtomSphere(centre=(0.0, 0.0, 0.0), radius=0.5, colour=(255, 0, 0), label='Fe')
    return StructureScene(cell_basis=basis, atoms=(atom,))


# ------------------------------------------------------------------
#  Module / class identity
# ------------------------------------------------------------------


def test_module_import():
    import easydiffraction.display.structure.viewing as MUT

    expected_module_name = 'easydiffraction.display.structure.viewing'
    actual_module_name = MUT.__name__
    assert expected_module_name == actual_module_name


def test_viewer_is_renderer_base():
    assert issubclass(Viewer, RendererBase)


def test_viewer_is_singleton():
    assert issubclass(Viewer, SingletonBase)


def test_factory_is_renderer_factory_base():
    assert issubclass(ViewerFactory, RendererFactoryBase)


# ------------------------------------------------------------------
#  ViewerFactory
# ------------------------------------------------------------------


class TestViewerFactory:
    def test_registry_keys(self):
        registry = ViewerFactory._registry()
        assert set(registry) == {
            ViewerEngineEnum.ASCII.value,
            ViewerEngineEnum.THREEJS.value,
        }

    def test_registry_entries_have_description_and_class(self):
        registry = ViewerFactory._registry()
        for config in registry.values():
            assert isinstance(config['description'], str)
            assert config['description']
            assert isinstance(config['class'], type)

    def test_supported_engines(self):
        engines = ViewerFactory.supported_engines()
        assert engines == ['ascii', 'threejs']

    def test_descriptions_pairs(self):
        descriptions = dict(ViewerFactory.descriptions())
        assert descriptions['ascii'] == ViewerEngineEnum.ASCII.description()
        assert descriptions['threejs'] == ViewerEngineEnum.THREEJS.description()

    def test_create_ascii(self):
        backend = ViewerFactory.create('ascii')
        assert isinstance(backend, AsciiStructureRenderer)

    def test_create_threejs(self):
        backend = ViewerFactory.create('threejs')
        assert isinstance(backend, ThreeJsStructureRenderer)

    def test_create_invalid_raises(self):
        with pytest.raises(ValueError, match='Unsupported engine'):
            ViewerFactory.create('nonexistent')


# ------------------------------------------------------------------
#  Construction / defaults
# ------------------------------------------------------------------


class TestViewerConstruction:
    def test_factory_classmethod_returns_viewer_factory(self):
        assert Viewer._factory() is ViewerFactory

    def test_default_engine_classmethod_matches_enum_default(self):
        assert Viewer._default_engine() == ViewerEngineEnum.default().value

    def test_default_engine_is_a_supported_engine(self):
        assert Viewer._default_engine() in ViewerFactory.supported_engines()

    def test_new_instance_uses_default_engine(self, viewer):
        assert viewer.engine == Viewer._default_engine()

    def test_new_instance_backend_matches_default_engine(self, viewer):
        # Outside Jupyter the default engine is ASCII.
        assert viewer.engine == ViewerEngineEnum.ASCII.value
        assert isinstance(viewer._backend, AsciiStructureRenderer)


# ------------------------------------------------------------------
#  engine property (getter / setter)
# ------------------------------------------------------------------


class TestEngineProperty:
    def test_engine_getter_returns_str(self, viewer):
        assert isinstance(viewer.engine, str)

    def test_switch_to_threejs_updates_engine_and_backend(self, viewer):
        viewer.engine = 'threejs'
        assert viewer.engine == 'threejs'
        assert isinstance(viewer._backend, ThreeJsStructureRenderer)

    def test_switch_to_ascii_updates_engine_and_backend(self, viewer):
        viewer.engine = 'threejs'
        viewer.engine = 'ascii'
        assert viewer.engine == 'ascii'
        assert isinstance(viewer._backend, AsciiStructureRenderer)

    def test_switch_emits_change_notice(self, viewer, capsys):
        viewer.engine = 'threejs'
        out = capsys.readouterr().out
        assert 'threejs' in out.lower()

    def test_setting_same_engine_is_a_noop(self, viewer):
        original_backend = viewer._backend
        viewer.engine = viewer.engine
        # Engine unchanged and backend instance not rebuilt.
        assert viewer.engine == ViewerEngineEnum.ASCII.value
        assert viewer._backend is original_backend

    def test_invalid_engine_leaves_engine_unchanged(self, viewer):
        original_engine = viewer.engine
        original_backend = viewer._backend
        viewer.engine = 'bogus'
        assert viewer.engine == original_engine
        assert viewer._backend is original_backend

    def test_invalid_engine_does_not_raise(self, viewer):
        # The setter logs a friendly warning instead of raising.
        viewer.engine = 'bogus'

    def test_non_string_engine_treated_as_unsupported(self, viewer):
        # The setter is not @typechecked: a non-string value is simply an
        # unsupported engine, so it warns and leaves the engine unchanged.
        original_engine = viewer.engine
        original_backend = viewer._backend
        viewer.engine = 123
        assert viewer.engine == original_engine
        assert viewer._backend is original_backend


# ------------------------------------------------------------------
#  render (delegation + real ASCII engine)
# ------------------------------------------------------------------


class TestRender:
    def test_render_delegates_to_backend(self, viewer):
        viewer._backend = _StubBackend()
        scene = _minimal_scene()
        output = viewer.render(scene, features=frozenset({'atoms'}))
        assert output == "stub atoms=1 features=['atoms']"

    def test_render_features_is_keyword_only(self, viewer):
        viewer._backend = _StubBackend()
        scene = _minimal_scene()
        with pytest.raises(TypeError):
            viewer.render(scene, frozenset({'atoms'}))

    def test_render_with_real_ascii_engine_returns_text(self, viewer):
        # Default engine is ASCII outside Jupyter; render end to end with
        # no calculation engine and no network.
        scene = _minimal_scene()
        output = viewer.render(scene, features=viewer.supported_features())
        assert isinstance(output, str)
        assert output != ''


# ------------------------------------------------------------------
#  supported_features (delegation + real engines)
# ------------------------------------------------------------------


class TestSupportedFeatures:
    def test_supported_features_delegates_to_backend(self, viewer):
        viewer._backend = _StubBackend()
        assert viewer.supported_features() == frozenset({'atoms', 'cell'})

    def test_ascii_supported_features(self, viewer):
        assert viewer.engine == ViewerEngineEnum.ASCII.value
        features = viewer.supported_features()
        assert isinstance(features, frozenset)
        assert features == AsciiStructureRenderer.SUPPORTED

    def test_threejs_supported_features(self, viewer):
        viewer.engine = 'threejs'
        features = viewer.supported_features()
        assert isinstance(features, frozenset)
        assert features == ThreeJsStructureRenderer.SUPPORTED


# ------------------------------------------------------------------
#  show_config and inherited inspection helpers
# ------------------------------------------------------------------


class TestShowHelpers:
    def test_show_config_reports_current_engine(self, viewer, capsys):
        viewer.show_config()
        out = capsys.readouterr().out
        assert ViewerEngineEnum.ASCII.value in out.lower()

    def test_show_config_reflects_active_engine(self, viewer, capsys):
        viewer.engine = 'threejs'
        capsys.readouterr()  # drop the engine-change notice
        viewer.show_config()
        out = capsys.readouterr().out
        assert 'threejs' in out.lower()

    def test_show_current_engine_outputs_engine(self, viewer, capsys):
        viewer.show_current_engine()
        out = capsys.readouterr().out
        assert viewer.engine in out.lower()

    def test_show_supported_engines_lists_every_engine(self, viewer, capsys):
        viewer.show_supported_engines()
        out = capsys.readouterr().out.lower()
        for member in ViewerEngineEnum:
            assert member.value in out


# ------------------------------------------------------------------
#  ViewerEngineEnum (the value selector backing the engine setting)
# ------------------------------------------------------------------


class TestViewerEngineEnum:
    def test_members(self):
        assert ViewerEngineEnum.ASCII == 'ascii'
        assert ViewerEngineEnum.THREEJS == 'threejs'

    def test_default_is_a_member(self):
        assert ViewerEngineEnum.default() in set(ViewerEngineEnum)

    def test_every_member_has_a_nonempty_description(self):
        for member in ViewerEngineEnum:
            description = member.description()
            assert isinstance(description, str)
            assert description
