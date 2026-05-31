# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for the geom category factory."""

from __future__ import annotations

import pytest

from easydiffraction.core.factory import FactoryBase
from easydiffraction.datablocks.structure.categories.geom.default import Geom
from easydiffraction.datablocks.structure.categories.geom.factory import GeomFactory


def test_module_import():
    import easydiffraction.datablocks.structure.categories.geom.factory as MUT

    expected_module_name = 'easydiffraction.datablocks.structure.categories.geom.factory'
    assert MUT.__name__ == expected_module_name


class TestGeomFactoryClass:
    def test_is_factory_base_subclass(self):
        assert issubclass(GeomFactory, FactoryBase)

    def test_default_rules_universal_fallback(self):
        # The only rule is the universal (empty-condition) fallback.
        assert GeomFactory._default_rules == {frozenset(): 'default'}

    def test_registry_is_independent_from_base(self):
        # __init_subclass__ gives each subclass its own registry list.
        assert GeomFactory._registry is not FactoryBase._registry

    def test_geom_is_registered(self):
        assert Geom in GeomFactory._registry


class TestSupportedTags:
    def test_supported_tags_returns_list(self):
        tags = GeomFactory.supported_tags()
        assert isinstance(tags, list)

    def test_default_tag_is_supported(self):
        assert 'default' in GeomFactory.supported_tags()

    def test_supported_map_links_tag_to_class(self):
        supported = GeomFactory._supported_map()
        assert supported['default'] is Geom


class TestDefaultTag:
    def test_default_tag_no_conditions(self):
        assert GeomFactory.default_tag() == 'default'

    def test_default_tag_ignores_extra_conditions(self):
        # The universal fallback still wins for unrelated conditions.
        assert GeomFactory.default_tag(scattering_type='bragg') == 'default'


class TestCreate:
    def test_create_default_returns_geom(self):
        obj = GeomFactory.create('default')
        assert isinstance(obj, Geom)

    def test_create_returns_fresh_instances(self):
        first = GeomFactory.create('default')
        second = GeomFactory.create('default')
        assert first is not second

    def test_create_unknown_tag_raises_value_error(self):
        with pytest.raises(ValueError, match=r"Unsupported type: 'missing'"):
            GeomFactory.create('missing')

    def test_create_default_has_expected_defaults(self):
        geom = GeomFactory.create('default')
        assert geom.min_bond_distance_cutoff.value == 0.0
        assert geom.bond_distance_incr.value == 0.25


class TestCreateDefaultFor:
    def test_create_default_for_no_conditions(self):
        obj = GeomFactory.create_default_for()
        assert isinstance(obj, Geom)


class TestSupportedFor:
    def test_supported_for_no_filters_includes_geom(self):
        result = GeomFactory.supported_for()
        assert Geom in result

    def test_supported_for_calculator_filter_does_not_exclude(self):
        # Geom declares no calculator_support, so the filter cannot
        # exclude it.
        result = GeomFactory.supported_for(calculator='cryspy')
        assert Geom in result

    def test_supported_for_sample_form_filter_does_not_exclude(self):
        # Geom declares no compatibility, so axis filters cannot
        # exclude it.
        result = GeomFactory.supported_for(sample_form='powder')
        assert Geom in result


class TestShowSupported:
    def test_show_supported_prints_table(self, capsys):
        GeomFactory.show_supported()
        out = capsys.readouterr().out
        assert 'Supported types' in out

    def test_show_supported_lists_default_tag(self, capsys):
        GeomFactory.show_supported()
        out = capsys.readouterr().out
        assert 'default' in out
