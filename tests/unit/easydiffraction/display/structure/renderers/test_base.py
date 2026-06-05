# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for display/structure/renderers/base.py (StructureRendererBase)."""

from __future__ import annotations

from abc import ABC

import pytest

from easydiffraction.display.structure.renderers.base import StructureRendererBase
from easydiffraction.display.structure.scene import AtomSphere
from easydiffraction.display.structure.scene import StructureScene

# ------------------------------------------------------------------
#  Test doubles
# ------------------------------------------------------------------


class _CompleteRenderer(StructureRendererBase):
    """A minimal concrete renderer overriding both abstract methods."""

    def render(self, scene: StructureScene, *, features: frozenset[str]) -> str:
        return f'atoms={len(scene.atoms)} features={sorted(features)}'

    def supported_features(self) -> frozenset[str]:
        return frozenset({'atoms', 'cell'})


class _RenderOnlyRenderer(StructureRendererBase):
    """Overrides only ``render`` so the class stays abstract."""

    def render(self, scene: StructureScene, *, features: frozenset[str]) -> str:
        return ''


class _FeaturesOnlyRenderer(StructureRendererBase):
    """Overrides only ``supported_features`` so the class stays abstract."""

    def supported_features(self) -> frozenset[str]:
        return frozenset()


class _DelegatingRenderer(StructureRendererBase):
    """Calls the base-class bodies via ``super()`` to hit their raises."""

    def render(self, scene: StructureScene, *, features: frozenset[str]) -> str:
        return super().render(scene, features=features)

    def supported_features(self) -> frozenset[str]:
        return super().supported_features()


# ------------------------------------------------------------------
#  Fixtures
# ------------------------------------------------------------------


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
    import easydiffraction.display.structure.renderers.base as MUT

    expected_module_name = 'easydiffraction.display.structure.renderers.base'
    actual_module_name = MUT.__name__
    assert expected_module_name == actual_module_name


def test_is_abstract_base_class():
    assert issubclass(StructureRendererBase, ABC)


def test_abstractmethods_are_exactly_render_and_supported_features():
    assert StructureRendererBase.__abstractmethods__ == frozenset({'render', 'supported_features'})


def test_render_marked_abstract():
    assert StructureRendererBase.render.__isabstractmethod__ is True


def test_supported_features_marked_abstract():
    assert StructureRendererBase.supported_features.__isabstractmethod__ is True


# ------------------------------------------------------------------
#  Instantiation contract
# ------------------------------------------------------------------


def test_cannot_instantiate_base_directly():
    with pytest.raises(TypeError):
        StructureRendererBase()


def test_cannot_instantiate_with_only_render_overridden():
    with pytest.raises(TypeError):
        _RenderOnlyRenderer()


def test_cannot_instantiate_with_only_supported_features_overridden():
    with pytest.raises(TypeError):
        _FeaturesOnlyRenderer()


def test_complete_subclass_instantiates():
    renderer = _CompleteRenderer()
    assert isinstance(renderer, StructureRendererBase)


# ------------------------------------------------------------------
#  Subclass honours the contract
# ------------------------------------------------------------------


def test_supported_features_returns_frozenset():
    renderer = _CompleteRenderer()
    result = renderer.supported_features()
    assert isinstance(result, frozenset)
    assert result == frozenset({'atoms', 'cell'})


def test_render_returns_string_using_scene_and_features():
    renderer = _CompleteRenderer()
    scene = _minimal_scene()
    output = renderer.render(scene, features=frozenset({'atoms', 'cell'}))
    assert isinstance(output, str)
    assert 'atoms=1' in output
    assert "features=['atoms', 'cell']" in output


def test_render_features_is_keyword_only():
    renderer = _CompleteRenderer()
    scene = _minimal_scene()
    with pytest.raises(TypeError):
        renderer.render(scene, frozenset({'atoms'}))


# ------------------------------------------------------------------
#  Base-class method bodies raise NotImplementedError
# ------------------------------------------------------------------


def test_super_render_raises_not_implemented():
    renderer = _DelegatingRenderer()
    scene = _minimal_scene()
    with pytest.raises(NotImplementedError):
        renderer.render(scene, features=frozenset())


def test_super_supported_features_raises_not_implemented():
    renderer = _DelegatingRenderer()
    with pytest.raises(NotImplementedError):
        renderer.supported_features()


# ------------------------------------------------------------------
#  Real concrete renderer satisfies the contract (no engine needed)
# ------------------------------------------------------------------


def test_ascii_renderer_is_a_structure_renderer_base():
    from easydiffraction.display.structure.renderers.ascii import AsciiStructureRenderer

    renderer = AsciiStructureRenderer()
    assert isinstance(renderer, StructureRendererBase)


def test_ascii_renderer_supported_features_is_a_subset_of_the_documented_names():
    from easydiffraction.display.structure.renderers.ascii import AsciiStructureRenderer

    documented = frozenset({'atoms', 'bonds', 'cell', 'axes', 'moments', 'labels'})
    features = AsciiStructureRenderer().supported_features()
    assert isinstance(features, frozenset)
    assert features <= documented


def test_ascii_renderer_render_returns_text():
    from easydiffraction.display.structure.renderers.ascii import AsciiStructureRenderer

    renderer = AsciiStructureRenderer()
    scene = _minimal_scene()
    output = renderer.render(scene, features=renderer.supported_features())
    assert isinstance(output, str)
    assert output != ''
