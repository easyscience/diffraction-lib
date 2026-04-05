# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for metadata dataclasses: TypeInfo, Compatibility, CalculatorSupport."""

from __future__ import annotations

import pytest

from easydiffraction.core.metadata import CalculatorSupport
from easydiffraction.core.metadata import Compatibility
from easydiffraction.core.metadata import TypeInfo


# ------------------------------------------------------------------
#  TypeInfo
# ------------------------------------------------------------------


class TestTypeInfo:
    def test_tag_and_description(self):
        info = TypeInfo(tag='pseudo-voigt', description='Pseudo-Voigt peak')
        assert info.tag == 'pseudo-voigt'
        assert info.description == 'Pseudo-Voigt peak'

    def test_default_description_is_empty(self):
        info = TypeInfo(tag='test')
        assert info.description == ''

    def test_is_frozen(self):
        info = TypeInfo(tag='test')
        with pytest.raises(AttributeError):
            info.tag = 'other'


# ------------------------------------------------------------------
#  Compatibility
# ------------------------------------------------------------------


class TestCompatibility:
    def test_empty_compat_accepts_anything(self):
        compat = Compatibility()
        assert compat.supports(
            sample_form='powder',
            scattering_type='bragg',
            beam_mode='cwl',
            radiation_probe='neutron',
        )

    def test_matches_when_value_in_frozenset(self):
        compat = Compatibility(sample_form=frozenset({'powder', 'single_crystal'}))
        assert compat.supports(sample_form='powder')
        assert compat.supports(sample_form='single_crystal')

    def test_rejects_when_value_not_in_frozenset(self):
        compat = Compatibility(sample_form=frozenset({'powder'}))
        assert not compat.supports(sample_form='single_crystal')

    def test_none_values_are_ignored(self):
        compat = Compatibility(sample_form=frozenset({'powder'}))
        assert compat.supports(sample_form=None)
        assert compat.supports()

    def test_multiple_axes(self):
        compat = Compatibility(
            sample_form=frozenset({'powder'}),
            beam_mode=frozenset({'cwl'}),
        )
        assert compat.supports(sample_form='powder', beam_mode='cwl')
        assert not compat.supports(sample_form='powder', beam_mode='tof')

    def test_is_frozen(self):
        compat = Compatibility()
        with pytest.raises(AttributeError):
            compat.sample_form = frozenset({'powder'})


# ------------------------------------------------------------------
#  CalculatorSupport
# ------------------------------------------------------------------


class TestCalculatorSupport:
    def test_empty_calculators_accepts_any(self):
        support = CalculatorSupport()
        assert support.supports('cryspy')
        assert support.supports('anything')

    def test_matches_when_calculator_in_set(self):
        support = CalculatorSupport(calculators=frozenset({'cryspy', 'crysfml'}))
        assert support.supports('cryspy')
        assert support.supports('crysfml')

    def test_rejects_when_calculator_not_in_set(self):
        support = CalculatorSupport(calculators=frozenset({'cryspy'}))
        assert not support.supports('pdffit2')

    def test_is_frozen(self):
        support = CalculatorSupport()
        with pytest.raises(AttributeError):
            support.calculators = frozenset({'new'})
