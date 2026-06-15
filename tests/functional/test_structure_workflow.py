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
            id='La',
            type_symbol='La',
            fract_x=0,
            fract_y=0,
            fract_z=0,
            wyckoff_letter='a',
            adp_iso=0.5,
        )
        assert len(s.atom_sites) == 1

    def test_access_atom_site_by_id(self):
        project = _make_project()
        project.structures.create(name='test')
        s = project.structures['test']
        s.atom_sites.create(
            id='La',
            type_symbol='La',
            fract_x=0,
            fract_y=0,
            fract_z=0,
            wyckoff_letter='a',
            adp_iso=0.5,
        )
        atom = s.atom_sites['La']
        assert atom.fract_x.value == pytest.approx(0)
        assert atom.adp_iso.value == pytest.approx(0.5)

    def test_atom_site_fract_is_fittable(self):
        project = _make_project()
        project.structures.create(name='test')
        s = project.structures['test']
        s.atom_sites.create(
            id='La',
            type_symbol='La',
            fract_x=0.1,
            fract_y=0.2,
            fract_z=0.3,
            wyckoff_letter='a',
            adp_iso=0.5,
        )
        s.atom_sites['La'].fract_x.free = True
        assert s.atom_sites['La'].fract_x.free is True

    def test_multiple_atom_sites(self):
        project = _make_project()
        project.structures.create(name='test')
        s = project.structures['test']
        s.atom_sites.create(
            id='La',
            type_symbol='La',
            fract_x=0,
            fract_y=0,
            fract_z=0,
            wyckoff_letter='a',
            adp_iso=0.5,
        )
        s.atom_sites.create(
            id='O',
            type_symbol='O',
            fract_x=0.5,
            fract_y=0.5,
            fract_z=0,
            wyckoff_letter='c',
            adp_iso=0.3,
        )
        assert len(s.atom_sites) == 2


class TestSymmetryFixedParameters:
    def test_special_position_fract_cannot_be_freed(self, monkeypatch):
        from easydiffraction.utils.logging import Logger

        project = _make_project()
        project.structures.create(name='test')
        s = project.structures['test']
        s.space_group.name_h_m = 'P m -3 m'
        s.atom_sites.create(
            id='La',
            type_symbol='La',
            fract_x=0,
            fract_y=0,
            fract_z=0,
            wyckoff_letter='a',
            adp_iso=0.5,
        )
        # Trigger symmetry-flag computation (normally done by display
        # / fitting, here we call it explicitly).
        s._need_categories_update = True
        s._update_categories()

        atom = s.atom_sites['La']
        assert atom.fract_x.symmetry_constrained is True
        assert atom.fract_y.symmetry_constrained is True
        assert atom.fract_z.symmetry_constrained is True

        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)
        for parameter in ('fract_x', 'fract_y', 'fract_z'):
            getattr(atom, parameter).free = True
        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.RAISE, raising=True)

        assert atom.fract_x.free is False
        assert atom.fract_y.free is False
        assert atom.fract_z.free is False

    def test_cubic_cell_has_only_a_free(self):
        project = _make_project()
        project.structures.create(name='test')
        s = project.structures['test']
        s.space_group.name_h_m = 'P m -3 m'
        s._need_categories_update = True
        s._update_categories()

        assert s.cell.length_a.symmetry_constrained is False
        assert s.cell.length_b.symmetry_constrained is True
        assert s.cell.length_c.symmetry_constrained is True
        assert s.cell.angle_alpha.symmetry_constrained is True
        assert s.cell.angle_beta.symmetry_constrained is True
        assert s.cell.angle_gamma.symmetry_constrained is True

    def test_general_position_remains_refinable(self):
        project = _make_project()
        project.structures.create(name='test')
        s = project.structures['test']
        # Default space group is P 1 -- general position 'a'
        s.atom_sites.create(
            id='La',
            type_symbol='La',
            fract_x=0.1,
            fract_y=0.2,
            fract_z=0.3,
            wyckoff_letter='a',
            adp_iso=0.5,
        )
        s._need_categories_update = True
        s._update_categories()

        atom = s.atom_sites['La']
        assert atom.fract_x.symmetry_constrained is False
        atom.fract_x.free = True
        assert atom.fract_x.free is True

    def test_changing_space_group_updates_flags(self, monkeypatch):
        from easydiffraction.utils.logging import Logger

        project = _make_project()
        project.structures.create(name='test')
        s = project.structures['test']

        # Start in P 1: cell free
        s._need_categories_update = True
        s._update_categories()
        assert s.cell.length_b.symmetry_constrained is False
        s.cell.length_b.free = True
        assert s.cell.length_b.free is True

        # Switch to cubic: length_b becomes fixed
        s.space_group.name_h_m = 'P m -3 m'
        s._update_categories()
        assert s.cell.length_b.symmetry_constrained is True
        assert s.cell.length_b.free is False

        # Setting free=True is now ignored with a warning
        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.WARN, raising=True)
        s.cell.length_b.free = True
        monkeypatch.setattr(Logger, '_reaction', Logger.Reaction.RAISE, raising=True)
        assert s.cell.length_b.free is False
