# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for the project structure_view factory."""

from __future__ import annotations

import pytest


def test_module_import():
    import easydiffraction.project.categories.structure_view.factory as MUT

    expected_module_name = 'easydiffraction.project.categories.structure_view.factory'
    assert MUT.__name__ == expected_module_name


def test_default_rules_universal_fallback():
    from easydiffraction.project.categories.structure_view.factory import (
        StructureViewFactory,
    )

    # The factory declares a single universal-fallback rule.
    assert StructureViewFactory._default_rules == {frozenset(): 'default'}


def test_supported_tags_lists_default():
    from easydiffraction.project.categories.structure_view.factory import (
        StructureViewFactory,
    )

    tags = StructureViewFactory.supported_tags()
    assert isinstance(tags, list)
    assert 'default' in tags


def test_default_tag_without_conditions():
    from easydiffraction.project.categories.structure_view.factory import (
        StructureViewFactory,
    )

    assert StructureViewFactory.default_tag() == 'default'


def test_default_tag_with_unmatched_conditions_falls_back():
    from easydiffraction.project.categories.structure_view.factory import (
        StructureViewFactory,
    )

    # Extra conditions still match the empty-key universal fallback.
    assert StructureViewFactory.default_tag(scattering_type='bragg') == 'default'


def test_create_returns_structure_view():
    from easydiffraction.project.categories.structure_view.default import StructureView
    from easydiffraction.project.categories.structure_view.factory import (
        StructureViewFactory,
    )

    structure_view = StructureViewFactory.create('default')
    assert isinstance(structure_view, StructureView)


def test_create_rejects_unknown_tag():
    from easydiffraction.project.categories.structure_view.factory import (
        StructureViewFactory,
    )

    with pytest.raises(ValueError, match=r"Unsupported type: 'missing'"):
        StructureViewFactory.create('missing')


def test_create_default_for_returns_structure_view():
    from easydiffraction.project.categories.structure_view.default import StructureView
    from easydiffraction.project.categories.structure_view.factory import (
        StructureViewFactory,
    )

    structure_view = StructureViewFactory.create_default_for()
    assert isinstance(structure_view, StructureView)


def test_supported_for_includes_registered_class():
    from easydiffraction.project.categories.structure_view.default import StructureView
    from easydiffraction.project.categories.structure_view.factory import (
        StructureViewFactory,
    )

    supported = StructureViewFactory.supported_for()
    assert StructureView in supported


def test_show_supported_lists_default(capsys):
    from easydiffraction.project.categories.structure_view.factory import (
        StructureViewFactory,
    )

    StructureViewFactory.show_supported()
    out = capsys.readouterr().out
    assert 'Supported types' in out
    assert 'default' in out


def test_registry_is_independent_from_base():
    from easydiffraction.core.factory import FactoryBase
    from easydiffraction.project.categories.structure_view.default import StructureView
    from easydiffraction.project.categories.structure_view.factory import (
        StructureViewFactory,
    )

    # __init_subclass__ gives each factory its own registry; the
    # registered concrete class must not leak onto the shared base.
    assert StructureView in StructureViewFactory._registry
    assert StructureView not in FactoryBase._registry
