# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Functional tests for structure workflow: create, set properties, verify params."""

from __future__ import annotations

import pytest

from easydiffraction import Project


def _make_project():
    Project._loading = True
    try:
        return Project()
    finally:
        Project._loading = False


class TestStructureCreation:
    def test_create_structure(self):
        project = _make_project()
        project.structures.create(name='test')
        assert len(project.structures) == 1
        assert 'test' in project.structures.names

    def test_access_structure_by_name(self):
        project = _make_project()
        project.structures.create(name='lbco')
        structure = project.structures['lbco']
        assert structure is not None

    def test_access_nonexistent_structure_raises(self):
        project = _make_project()
        with pytest.raises(KeyError):
            _ = project.structures['nonexistent']


class TestSpaceGroup:
    def test_set_space_group(self):
        project = _make_project()
        project.structures.create(name='test')
        s = project.structures['test']
        s.space_group.name_h_m = 'P m -3 m'
        assert s.space_group.name_h_m.value == 'P m -3 m'


class TestCell:
    def test_set_cell_parameters(self):
        project = _make_project()
        project.structures.create(name='test')
        s = project.structures['test']
        s.cell.length_a = 5.0
        s.cell.length_b = 6.0
        s.cell.length_c = 7.0
        assert s.cell.length_a.value == pytest.approx(5.0)
        assert s.cell.length_b.value == pytest.approx(6.0)
        assert s.cell.length_c.value == pytest.approx(7.0)

    def test_cell_parameters_are_fittable(self):
        project = _make_project()
        project.structures.create(name='test')
        s = project.structures['test']
        s.cell.length_a.free = True
        assert s.cell.length_a.free is True


class TestAtomSites:
    def test_create_atom_site(self):
        project = _make_project()
        project.structures.create(name='test')
        s = project.structures['test']
        s.atom_sites.create(
            label='La',
            type_symbol='La',
            fract_x=0,
            fract_y=0,
            fract_z=0,
            wyckoff_letter='a',
            b_iso=0.5,
        )
        assert len(s.atom_sites) == 1

    def test_access_atom_site_by_label(self):
        project = _make_project()
        project.structures.create(name='test')
        s = project.structures['test']
        s.atom_sites.create(
            label='La',
            type_symbol='La',
            fract_x=0,
            fract_y=0,
            fract_z=0,
            wyckoff_letter='a',
            b_iso=0.5,
        )
        atom = s.atom_sites['La']
        assert atom.fract_x.value == pytest.approx(0)
        assert atom.b_iso.value == pytest.approx(0.5)

    def test_atom_site_fract_is_fittable(self):
        project = _make_project()
        project.structures.create(name='test')
        s = project.structures['test']
        s.atom_sites.create(
            label='La',
            type_symbol='La',
            fract_x=0.1,
            fract_y=0.2,
            fract_z=0.3,
            wyckoff_letter='a',
            b_iso=0.5,
        )
        s.atom_sites['La'].fract_x.free = True
        assert s.atom_sites['La'].fract_x.free is True

    def test_multiple_atom_sites(self):
        project = _make_project()
        project.structures.create(name='test')
        s = project.structures['test']
        s.atom_sites.create(
            label='La',
            type_symbol='La',
            fract_x=0,
            fract_y=0,
            fract_z=0,
            wyckoff_letter='a',
            b_iso=0.5,
        )
        s.atom_sites.create(
            label='O',
            type_symbol='O',
            fract_x=0.5,
            fract_y=0.5,
            fract_z=0,
            wyckoff_letter='c',
            b_iso=0.3,
        )
        assert len(s.atom_sites) == 2
