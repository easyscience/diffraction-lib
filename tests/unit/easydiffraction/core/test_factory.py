# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for FactoryBase: registration, creation, defaults, and querying."""

from __future__ import annotations

import pytest

from easydiffraction.core.factory import FactoryBase
from easydiffraction.core.metadata import CalculatorSupport
from easydiffraction.core.metadata import Compatibility
from easydiffraction.core.metadata import TypeInfo

# ------------------------------------------------------------------
#  Helpers: a fresh factory + stub classes for each test
# ------------------------------------------------------------------


def _make_factory():
    """Return a fresh FactoryBase subclass with its own registry."""

    class _Factory(FactoryBase):
        _default_rules = {frozenset(): 'alpha'}

    return _Factory


def _make_stub(tag, description='', compatibility=None, calculator_support=None):
    """Return a stub class with the given TypeInfo."""

    class _Stub:
        type_info = TypeInfo(tag=tag, description=description)

    if compatibility is not None:
        _Stub.compatibility = compatibility
    if calculator_support is not None:
        _Stub.calculator_support = calculator_support
    return _Stub


# ------------------------------------------------------------------
#  Registration
# ------------------------------------------------------------------


class TestRegister:
    def test_register_adds_class_to_registry(self):
        factory = _make_factory()
        stub = _make_stub('alpha')
        factory.register(stub)
        assert stub in factory._registry

    def test_register_returns_class_unmodified(self):
        factory = _make_factory()
        stub = _make_stub('alpha')
        result = factory.register(stub)
        assert result is stub

    def test_register_multiple_classes(self):
        factory = _make_factory()
        stub_a = _make_stub('a')
        stub_b = _make_stub('b')
        factory.register(stub_a)
        factory.register(stub_b)
        assert len(factory._registry) == 2

    def test_subclass_registries_are_independent(self):
        class _FactoryA(FactoryBase):
            _default_rules = {frozenset(): 'a'}

        class _FactoryB(FactoryBase):
            _default_rules = {frozenset(): 'b'}

        stub_a = _make_stub('a')
        stub_b = _make_stub('b')
        _FactoryA.register(stub_a)
        _FactoryB.register(stub_b)
        assert stub_a in _FactoryA._registry
        assert stub_a not in _FactoryB._registry
        assert stub_b in _FactoryB._registry
        assert stub_b not in _FactoryA._registry


# ------------------------------------------------------------------
#  Supported tags
# ------------------------------------------------------------------


class TestSupportedTags:
    def test_returns_empty_list_for_empty_registry(self):
        factory = _make_factory()
        assert factory.supported_tags() == []

    def test_returns_tags_from_registered_classes(self):
        factory = _make_factory()
        factory.register(_make_stub('alpha'))
        factory.register(_make_stub('beta'))
        tags = factory.supported_tags()
        assert 'alpha' in tags
        assert 'beta' in tags
        assert len(tags) == 2


# ------------------------------------------------------------------
#  Default tag resolution
# ------------------------------------------------------------------


class TestDefaultTag:
    def test_universal_fallback(self):
        factory = _make_factory()
        factory.register(_make_stub('alpha'))
        assert factory.default_tag() == 'alpha'

    def test_specific_rule_wins_over_universal(self):
        class _Factory(FactoryBase):
            _default_rules = {
                frozenset(): 'fallback',
                frozenset({('mode', 'fast')}): 'fast_impl',
            }

        assert _Factory.default_tag(mode='fast') == 'fast_impl'

    def test_largest_subset_wins(self):
        class _Factory(FactoryBase):
            _default_rules = {
                frozenset(): 'fallback',
                frozenset({('a', 1)}): 'one_match',
                frozenset({('a', 1), ('b', 2)}): 'two_match',
            }

        assert _Factory.default_tag(a=1, b=2) == 'two_match'

    def test_raises_when_no_rule_matches(self):
        class _Factory(FactoryBase):
            _default_rules = {
                frozenset({('mode', 'fast')}): 'fast_impl',
            }

        with pytest.raises(ValueError, match='No default rule matches'):
            _Factory.default_tag(mode='slow')

    def test_raises_for_empty_rules(self):
        class _Factory(FactoryBase):
            _default_rules = {}

        with pytest.raises(ValueError, match='No default rule matches'):
            _Factory.default_tag()


# ------------------------------------------------------------------
#  Creation
# ------------------------------------------------------------------


class TestCreate:
    def test_creates_instance_of_registered_class(self):
        factory = _make_factory()
        stub = _make_stub('alpha')
        factory.register(stub)
        instance = factory.create('alpha')
        assert isinstance(instance, stub)

    def test_raises_for_unknown_tag(self):
        factory = _make_factory()
        factory.register(_make_stub('alpha'))
        with pytest.raises(ValueError, match="Unsupported type: 'unknown'"):
            factory.create('unknown')

    def test_raises_for_empty_registry(self):
        factory = _make_factory()
        with pytest.raises(ValueError, match="Unsupported type: 'anything'"):
            factory.create('anything')


# ------------------------------------------------------------------
#  create_default_for
# ------------------------------------------------------------------


class TestCreateDefaultFor:
    def test_creates_default_instance(self):
        factory = _make_factory()
        stub = _make_stub('alpha')
        factory.register(stub)
        instance = factory.create_default_for()
        assert isinstance(instance, stub)


# ------------------------------------------------------------------
#  supported_for (filtering by compatibility and calculator)
# ------------------------------------------------------------------


class TestSupportedFor:
    def test_returns_all_when_no_filters(self):
        factory = _make_factory()
        factory.register(_make_stub('a'))
        factory.register(_make_stub('b'))
        result = factory.supported_for()
        assert len(result) == 2

    def test_filters_by_compatibility(self):
        factory = _make_factory()
        compat_a = Compatibility(sample_form=frozenset({'powder'}))
        compat_b = Compatibility(sample_form=frozenset({'single_crystal'}))
        factory.register(
            _make_stub('a', compatibility=compat_a),
        )
        factory.register(
            _make_stub('b', compatibility=compat_b),
        )
        result = factory.supported_for(sample_form='powder')
        assert len(result) == 1
        assert result[0].type_info.tag == 'a'

    def test_filters_by_calculator(self):
        factory = _make_factory()
        calc_a = CalculatorSupport(calculators=frozenset({'cryspy'}))
        calc_b = CalculatorSupport(calculators=frozenset({'crysfml'}))
        factory.register(
            _make_stub('a', calculator_support=calc_a),
        )
        factory.register(
            _make_stub('b', calculator_support=calc_b),
        )
        result = factory.supported_for(calculator='cryspy')
        assert len(result) == 1
        assert result[0].type_info.tag == 'a'

    def test_no_compat_means_accepts_all(self):
        factory = _make_factory()
        factory.register(_make_stub('a'))  # no compatibility attr
        result = factory.supported_for(sample_form='anything')
        assert len(result) == 1

    def test_empty_compat_frozenset_means_accepts_all(self):
        factory = _make_factory()
        compat = Compatibility()  # all frozensets empty
        factory.register(_make_stub('a', compatibility=compat))
        result = factory.supported_for(
            sample_form='powder',
            scattering_type='bragg',
        )
        assert len(result) == 1
