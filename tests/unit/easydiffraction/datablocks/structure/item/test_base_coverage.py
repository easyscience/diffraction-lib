# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for Structure switchable-category wiring."""

import pytest
from typeguard import TypeCheckError

from easydiffraction.datablocks.structure.categories.atom_sites import AtomSites
from easydiffraction.datablocks.structure.categories.atom_sites.factory import AtomSitesFactory
from easydiffraction.datablocks.structure.categories.cell import Cell
from easydiffraction.datablocks.structure.categories.cell.factory import CellFactory
from easydiffraction.datablocks.structure.categories.space_group import SpaceGroup
from easydiffraction.datablocks.structure.categories.space_group.factory import SpaceGroupFactory
from easydiffraction.datablocks.structure.item.base import Structure

# ------------------------------------------------------------------
# Fixture
# ------------------------------------------------------------------


@pytest.fixture
def structure():
    return Structure(name='test_struct')


# ------------------------------------------------------------------
# Name property
# ------------------------------------------------------------------


class TestStructureName:
    def test_initial_name(self, structure):
        assert structure.name == 'test_struct'

    def test_setter(self, structure):
        structure.name = 'renamed'
        assert structure.name == 'renamed'

    def test_setter_type_check(self, structure):
        with pytest.raises(TypeCheckError):
            structure.name = 123


# ------------------------------------------------------------------
# Cell (read-only, single type)
# ------------------------------------------------------------------


class TestStructureCell:
    def test_cell_returns_cell_instance(self, structure):
        assert isinstance(structure.cell, Cell)

    def test_cell_setter_replaces_instance(self, structure):
        new_cell = CellFactory.create(CellFactory.default_tag())
        structure.cell = new_cell
        assert structure.cell is new_cell


# ------------------------------------------------------------------
# Space group (read-only, single type)
# ------------------------------------------------------------------


class TestStructureSpaceGroup:
    def test_space_group_returns_instance(self, structure):
        assert isinstance(structure.space_group, SpaceGroup)

    def test_space_group_setter_replaces_instance(self, structure):
        new_sg = SpaceGroupFactory.create(SpaceGroupFactory.default_tag())
        structure.space_group = new_sg
        assert structure.space_group is new_sg


# ------------------------------------------------------------------
# Atom sites (read-only, single type)
# ------------------------------------------------------------------


class TestStructureAtomSites:
    def test_atom_sites_returns_instance(self, structure):
        assert isinstance(structure.atom_sites, AtomSites)

    def test_atom_sites_setter_replaces_instance(self, structure):
        new_as = AtomSitesFactory.create(AtomSitesFactory.default_tag())
        structure.atom_sites = new_as
        assert structure.atom_sites is new_as


# ------------------------------------------------------------------
# Display methods
# ------------------------------------------------------------------


class TestStructureDisplay:
    def test_show_as_text(self, structure, capsys):
        structure.show_as_text()
        out = capsys.readouterr().out
        assert 'test_struct' in out
