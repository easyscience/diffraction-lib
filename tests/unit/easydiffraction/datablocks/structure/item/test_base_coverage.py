# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for Structure switchable-category wiring."""

import pytest

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
        with pytest.raises(TypeError):
            structure.name = 123


# ------------------------------------------------------------------
# Cell (switchable-category)
# ------------------------------------------------------------------


class TestStructureCell:
    def test_default_cell_type(self, structure):
        assert structure.cell_type == CellFactory.default_tag()

    def test_cell_returns_cell_instance(self, structure):
        assert isinstance(structure.cell, Cell)

    def test_cell_type_setter_valid(self, structure, capsys):
        supported = CellFactory.supported_tags()
        assert len(supported) > 0
        tag = supported[0]
        structure.cell_type = tag
        assert structure.cell_type == tag

    def test_cell_type_setter_invalid_keeps_old(self, structure):
        old_type = structure.cell_type
        structure.cell_type = 'nonexistent-type'
        assert structure.cell_type == old_type

    def test_cell_setter_replaces_instance(self, structure):
        new_cell = CellFactory.create(CellFactory.default_tag())
        structure.cell = new_cell
        assert structure.cell is new_cell

    def test_show_supported_cell_types(self, structure, capsys):
        structure.show_supported_cell_types()
        out = capsys.readouterr().out
        assert len(out) > 0

    def test_show_current_cell_type(self, structure, capsys):
        structure.show_current_cell_type()
        out = capsys.readouterr().out
        assert structure.cell_type in out


# ------------------------------------------------------------------
# Space group (switchable-category)
# ------------------------------------------------------------------


class TestStructureSpaceGroup:
    def test_default_space_group_type(self, structure):
        assert structure.space_group_type == SpaceGroupFactory.default_tag()

    def test_space_group_returns_instance(self, structure):
        assert isinstance(structure.space_group, SpaceGroup)

    def test_space_group_type_setter_valid(self, structure, capsys):
        supported = SpaceGroupFactory.supported_tags()
        assert len(supported) > 0
        tag = supported[0]
        structure.space_group_type = tag
        assert structure.space_group_type == tag

    def test_space_group_type_setter_invalid_keeps_old(self, structure):
        old_type = structure.space_group_type
        structure.space_group_type = 'nonexistent-type'
        assert structure.space_group_type == old_type

    def test_space_group_setter_replaces_instance(self, structure):
        new_sg = SpaceGroupFactory.create(SpaceGroupFactory.default_tag())
        structure.space_group = new_sg
        assert structure.space_group is new_sg

    def test_show_supported_space_group_types(self, structure, capsys):
        structure.show_supported_space_group_types()
        out = capsys.readouterr().out
        assert len(out) > 0

    def test_show_current_space_group_type(self, structure, capsys):
        structure.show_current_space_group_type()
        out = capsys.readouterr().out
        assert structure.space_group_type in out


# ------------------------------------------------------------------
# Atom sites (switchable-category)
# ------------------------------------------------------------------


class TestStructureAtomSites:
    def test_default_atom_sites_type(self, structure):
        assert structure.atom_sites_type == AtomSitesFactory.default_tag()

    def test_atom_sites_returns_instance(self, structure):
        assert isinstance(structure.atom_sites, AtomSites)

    def test_atom_sites_type_setter_valid(self, structure, capsys):
        supported = AtomSitesFactory.supported_tags()
        assert len(supported) > 0
        tag = supported[0]
        structure.atom_sites_type = tag
        assert structure.atom_sites_type == tag

    def test_atom_sites_type_setter_invalid_keeps_old(self, structure):
        old_type = structure.atom_sites_type
        structure.atom_sites_type = 'nonexistent-type'
        assert structure.atom_sites_type == old_type

    def test_atom_sites_setter_replaces_instance(self, structure):
        new_as = AtomSitesFactory.create(AtomSitesFactory.default_tag())
        structure.atom_sites = new_as
        assert structure.atom_sites is new_as

    def test_show_supported_atom_sites_types(self, structure, capsys):
        structure.show_supported_atom_sites_types()
        out = capsys.readouterr().out
        assert len(out) > 0

    def test_show_current_atom_sites_type(self, structure, capsys):
        structure.show_current_atom_sites_type()
        out = capsys.readouterr().out
        assert structure.atom_sites_type in out


# ------------------------------------------------------------------
# Display methods
# ------------------------------------------------------------------


class TestStructureDisplay:
    def test_show(self, structure, capsys):
        structure.show()
        out = capsys.readouterr().out
        assert 'test_struct' in out

    def test_show_as_cif(self, structure, capsys):
        structure.show_as_cif()
        out = capsys.readouterr().out
        assert 'test_struct' in out
