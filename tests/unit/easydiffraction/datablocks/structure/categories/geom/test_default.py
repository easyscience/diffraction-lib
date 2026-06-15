# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for the geom category default module (Geom)."""

from __future__ import annotations

import pytest

from easydiffraction.core.category import CategoryItem
from easydiffraction.core.metadata import TypeInfo
from easydiffraction.core.variable import NumericDescriptor
from easydiffraction.datablocks.structure.categories.geom.default import Geom
from easydiffraction.utils.logging import Logger


def test_module_import():
    import easydiffraction.datablocks.structure.categories.geom.default as MUT

    expected_module_name = 'easydiffraction.datablocks.structure.categories.geom.default'
    assert MUT.__name__ == expected_module_name


# ----------------------------------------------------------------------
#  Class-level metadata
# ----------------------------------------------------------------------


class TestGeomClass:
    def test_is_category_item_subclass(self):
        assert issubclass(Geom, CategoryItem)

    def test_category_code(self):
        assert Geom._category_code == 'geom'

    def test_type_info_is_type_info(self):
        assert isinstance(Geom.type_info, TypeInfo)

    def test_type_info_tag(self):
        assert Geom.type_info.tag == 'default'

    def test_type_info_description(self):
        assert Geom.type_info.description == 'Structure bond-geometry cutoffs'


# ----------------------------------------------------------------------
#  Construction and defaults
# ----------------------------------------------------------------------


class TestGeomConstruction:
    def test_instantiation(self):
        geom = Geom()
        assert geom is not None

    def test_instantiation_returns_fresh_instances(self):
        first = Geom()
        second = Geom()
        assert first is not second

    def test_identity_category_code(self):
        geom = Geom()
        assert geom._identity.category_code == 'geom'

    def test_min_bond_distance_cutoff_is_numeric_descriptor(self):
        geom = Geom()
        assert isinstance(geom.min_bond_distance_cutoff, NumericDescriptor)

    def test_bond_distance_inc_is_numeric_descriptor(self):
        geom = Geom()
        assert isinstance(geom.bond_distance_inc, NumericDescriptor)

    def test_default_min_bond_distance_cutoff(self):
        geom = Geom()
        assert geom.min_bond_distance_cutoff.value == 0.0

    def test_default_bond_distance_inc(self):
        geom = Geom()
        assert geom.bond_distance_inc.value == 0.25

    def test_descriptor_names(self):
        geom = Geom()
        assert geom.min_bond_distance_cutoff.name == 'min_bond_distance_cutoff'
        assert geom.bond_distance_inc.name == 'bond_distance_inc'

    def test_descriptor_descriptions(self):
        geom = Geom()
        assert geom.min_bond_distance_cutoff.description == (
            'Minimum permitted bonded distance (angstrom).'
        )
        assert geom.bond_distance_inc.description == (
            'Increment added to the summed bonding radii (angstrom).'
        )

    def test_parameters_lists_both_descriptors(self):
        geom = Geom()
        names = {p.name for p in geom.parameters}
        assert names == {'min_bond_distance_cutoff', 'bond_distance_inc'}


# ----------------------------------------------------------------------
#  CIF handler names (cif_core ``_geom``)
# ----------------------------------------------------------------------


class TestGeomTagSpecs:
    def test_min_bond_distance_cutoff_cif_name(self):
        geom = Geom()
        assert geom.min_bond_distance_cutoff._tags.edi_names == [
            '_geom.min_bond_distance_cutoff',
        ]

    def test_bond_distance_inc_cif_name(self):
        geom = Geom()
        assert geom.bond_distance_inc._tags.edi_names == [
            '_geom.bond_distance_inc',
        ]


# ----------------------------------------------------------------------
#  Setters — valid values
# ----------------------------------------------------------------------


class TestGeomSettersValid:
    def test_set_min_bond_distance_cutoff(self):
        geom = Geom()
        geom.min_bond_distance_cutoff = 0.5
        assert geom.min_bond_distance_cutoff.value == 0.5

    def test_set_bond_distance_inc(self):
        geom = Geom()
        geom.bond_distance_inc = 0.4
        assert geom.bond_distance_inc.value == 0.4

    def test_set_min_bond_distance_cutoff_to_zero_boundary(self):
        # The validator allows ge=0.0, so the lower boundary is valid.
        geom = Geom()
        geom.min_bond_distance_cutoff = 1.0
        geom.min_bond_distance_cutoff = 0.0
        assert geom.min_bond_distance_cutoff.value == 0.0

    def test_set_bond_distance_inc_to_zero_boundary(self):
        geom = Geom()
        geom.bond_distance_inc = 0.0
        assert geom.bond_distance_inc.value == 0.0

    def test_set_min_bond_distance_cutoff_accepts_int(self):
        geom = Geom()
        geom.min_bond_distance_cutoff = 2
        assert geom.min_bond_distance_cutoff.value == 2


# ----------------------------------------------------------------------
#  Setters — invalid values
#
#  RangeValidator routes out-of-range values through
#  ``Diagnostics.range_mismatch`` -> ``log.error(..., exc_type=TypeError)``.
#  In RAISE mode this raises ``TypeError``; in WARN mode the current
#  value is kept.  Tests pin the Logger reaction with monkeypatch so they
#  do not depend on global logger state leaked by other tests.
# ----------------------------------------------------------------------


class TestGeomSettersInvalid:
    def test_negative_min_bond_distance_cutoff_raises_in_raise_mode(self, monkeypatch):
        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.RAISE, raising=True)
        geom = Geom()
        with pytest.raises(TypeError):
            geom.min_bond_distance_cutoff = -1.0

    def test_negative_bond_distance_inc_raises_in_raise_mode(self, monkeypatch):
        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.RAISE, raising=True)
        geom = Geom()
        with pytest.raises(TypeError):
            geom.bond_distance_inc = -0.5

    def test_negative_min_bond_distance_cutoff_kept_in_warn_mode(self, monkeypatch):
        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)
        geom = Geom()
        geom.min_bond_distance_cutoff = -1.0
        # The out-of-range write is rejected; the default is retained.
        assert geom.min_bond_distance_cutoff.value == 0.0

    def test_negative_bond_distance_inc_kept_in_warn_mode(self, monkeypatch):
        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)
        geom = Geom()
        geom.bond_distance_inc = -0.5
        assert geom.bond_distance_inc.value == 0.25

    def test_wrong_type_min_bond_distance_cutoff_kept_in_warn_mode(self, monkeypatch):
        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)
        geom = Geom()
        geom.min_bond_distance_cutoff = 'not-a-number'
        assert geom.min_bond_distance_cutoff.value == 0.0

    def test_wrong_type_bond_distance_inc_raises_in_raise_mode(self, monkeypatch):
        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.RAISE, raising=True)
        geom = Geom()
        with pytest.raises(TypeError):
            geom.bond_distance_inc = 'not-a-number'


# ----------------------------------------------------------------------
#  CIF serialisation and round-trip
# ----------------------------------------------------------------------


class TestGeomAsCif:
    def test_as_cif_is_string(self):
        geom = Geom()
        assert isinstance(geom.as_cif, str)

    def test_as_cif_contains_both_tags(self):
        geom = Geom()
        cif = geom.as_cif
        assert '_geom.min_bond_distance_cutoff' in cif
        assert '_geom.bond_distance_inc' in cif

    def test_as_cif_default_lines(self):
        geom = Geom()
        lines = geom.as_cif.splitlines()
        assert lines == [
            '_geom.min_bond_distance_cutoff 0.',
            '_geom.bond_distance_inc 0.25',
        ]

    def test_as_cif_reflects_updated_values(self):
        geom = Geom()
        geom.min_bond_distance_cutoff = 0.8
        geom.bond_distance_inc = 0.3
        cif = geom.as_cif
        assert '_geom.min_bond_distance_cutoff 0.8' in cif
        assert '_geom.bond_distance_inc 0.3' in cif

    def test_from_cif_round_trip(self):
        import gemmi

        # All values are in range, so no validation error is triggered;
        # the round-trip is independent of the global Logger reaction.
        source = Geom()
        source.min_bond_distance_cutoff = 0.6
        source.bond_distance_inc = 0.45

        block = gemmi.cif.read_string(f'data_test\n\n{source.as_cif}\n').sole_block()

        restored = Geom()
        restored.from_cif(block)

        assert restored.min_bond_distance_cutoff.value == 0.6
        assert restored.bond_distance_inc.value == 0.45
