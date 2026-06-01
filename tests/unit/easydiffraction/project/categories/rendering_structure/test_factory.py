# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for the project rendering_structure factory."""

from __future__ import annotations

import pytest


def test_module_import():
    import easydiffraction.project.categories.rendering_structure.factory as MUT

    expected_module_name = 'easydiffraction.project.categories.rendering_structure.factory'
    assert MUT.__name__ == expected_module_name


def test_default_rules_universal_fallback():
    from easydiffraction.project.categories.rendering_structure.factory import (
        RenderingStructureFactory,
    )

    # The factory declares a single universal-fallback rule.
    assert RenderingStructureFactory._default_rules == {frozenset(): 'default'}


def test_supported_tags_lists_default():
    from easydiffraction.project.categories.rendering_structure.factory import (
        RenderingStructureFactory,
    )

    tags = RenderingStructureFactory.supported_tags()
    assert isinstance(tags, list)
    assert 'default' in tags


def test_default_tag_without_conditions():
    from easydiffraction.project.categories.rendering_structure.factory import (
        RenderingStructureFactory,
    )

    assert RenderingStructureFactory.default_tag() == 'default'


def test_default_tag_with_unmatched_conditions_falls_back():
    from easydiffraction.project.categories.rendering_structure.factory import (
        RenderingStructureFactory,
    )

    # Extra conditions still match the empty-key universal fallback.
    assert RenderingStructureFactory.default_tag(scattering_type='bragg') == 'default'


def test_create_returns_rendering_structure():
    from easydiffraction.project.categories.rendering_structure.default import RenderingStructure
    from easydiffraction.project.categories.rendering_structure.factory import (
        RenderingStructureFactory,
    )

    rendering_structure = RenderingStructureFactory.create('default')
    assert isinstance(rendering_structure, RenderingStructure)


def test_create_rejects_unknown_tag():
    from easydiffraction.project.categories.rendering_structure.factory import (
        RenderingStructureFactory,
    )

    with pytest.raises(ValueError, match=r"Unsupported type: 'missing'"):
        RenderingStructureFactory.create('missing')


def test_create_default_for_returns_rendering_structure():
    from easydiffraction.project.categories.rendering_structure.default import RenderingStructure
    from easydiffraction.project.categories.rendering_structure.factory import (
        RenderingStructureFactory,
    )

    rendering_structure = RenderingStructureFactory.create_default_for()
    assert isinstance(rendering_structure, RenderingStructure)


def test_supported_for_includes_registered_class():
    from easydiffraction.project.categories.rendering_structure.default import RenderingStructure
    from easydiffraction.project.categories.rendering_structure.factory import (
        RenderingStructureFactory,
    )

    supported = RenderingStructureFactory.supported_for()
    assert RenderingStructure in supported


def test_show_supported_lists_default(capsys):
    from easydiffraction.project.categories.rendering_structure.factory import (
        RenderingStructureFactory,
    )

    RenderingStructureFactory.show_supported()
    out = capsys.readouterr().out
    assert 'Supported types' in out
    assert 'default' in out


def test_registry_is_independent_from_base():
    from easydiffraction.core.factory import FactoryBase
    from easydiffraction.project.categories.rendering_structure.default import RenderingStructure
    from easydiffraction.project.categories.rendering_structure.factory import (
        RenderingStructureFactory,
    )

    # __init_subclass__ gives each factory its own registry; the
    # registered concrete class must not leak onto the shared base.
    assert RenderingStructure in RenderingStructureFactory._registry
    assert RenderingStructure not in FactoryBase._registry
