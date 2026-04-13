# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Functional tests for ADP type switching workflows."""

from __future__ import annotations

import math

import pytest

from easydiffraction import Project

_FACTOR = 8.0 * math.pi**2


def _make_project_with_structure():
    """Build a project with a simple cubic structure."""
    Project._loading = True
    try:
        project = Project()
    finally:
        Project._loading = False
    project.structures.create(name='cubic')
    s = project.structures['cubic']
    s.space_group.name_h_m = 'P m -3 m'
    s.cell.length_a = 3.89
    s.atom_sites.create(
        label='A',
        type_symbol='La',
        fract_x=0,
        fract_y=0,
        fract_z=0,
        wyckoff_letter='a',
        adp_iso=0.5,
    )
    s.atom_sites.create(
        label='B',
        type_symbol='Co',
        fract_x=0.5,
        fract_y=0.5,
        fract_z=0.5,
        wyckoff_letter='b',
        adp_iso=0.3,
    )
    return project


# ------------------------------------------------------------------
#  ADP type switching: value correctness
# ------------------------------------------------------------------


class TestAdpTypeSwitchingValues:
    def test_biso_to_bani_preserves_value(self):
        project = _make_project_with_structure()
        s = project.structures['cubic']
        s.atom_sites['A'].adp_type = 'Bani'
        aniso = s.atom_site_aniso['A']
        assert aniso.adp_11.value == pytest.approx(0.5)
        assert aniso.adp_22.value == pytest.approx(0.5)
        assert aniso.adp_33.value == pytest.approx(0.5)
        assert aniso.adp_12.value == pytest.approx(0.0)

    def test_biso_to_uiso_converts(self):
        project = _make_project_with_structure()
        s = project.structures['cubic']
        s.atom_sites['A'].adp_type = 'Uiso'
        expected = 0.5 / _FACTOR
        assert s.atom_sites['A'].adp_iso.value == pytest.approx(expected)

    def test_biso_to_uani_converts_and_seeds(self):
        project = _make_project_with_structure()
        s = project.structures['cubic']
        s.atom_sites['A'].adp_type = 'Uani'
        aniso = s.atom_site_aniso['A']
        expected = 0.5 / _FACTOR
        assert aniso.adp_11.value == pytest.approx(expected)
        assert aniso.adp_22.value == pytest.approx(expected)
        assert aniso.adp_33.value == pytest.approx(expected)

    def test_uiso_to_biso_converts(self):
        project = _make_project_with_structure()
        s = project.structures['cubic']
        s.atom_sites['A'].adp_type = 'Uiso'
        u_val = s.atom_sites['A'].adp_iso.value
        s.atom_sites['A'].adp_type = 'Biso'
        assert s.atom_sites['A'].adp_iso.value == pytest.approx(u_val * _FACTOR)

    def test_uani_to_bani_converts_tensor(self):
        project = _make_project_with_structure()
        s = project.structures['cubic']
        s.atom_sites['A'].adp_type = 'Uani'
        u11 = s.atom_site_aniso['A'].adp_11.value
        s.atom_sites['A'].adp_type = 'Bani'
        b11 = s.atom_site_aniso['A'].adp_11.value
        assert b11 == pytest.approx(u11 * _FACTOR)

    def test_bani_to_uani_converts_tensor(self):
        project = _make_project_with_structure()
        s = project.structures['cubic']
        s.atom_sites['A'].adp_type = 'Bani'
        b11 = s.atom_site_aniso['A'].adp_11.value
        s.atom_sites['A'].adp_type = 'Uani'
        u11 = s.atom_site_aniso['A'].adp_11.value
        assert u11 == pytest.approx(b11 / _FACTOR)


# ------------------------------------------------------------------
#  Round trips
# ------------------------------------------------------------------


class TestAdpRoundTrips:
    def test_biso_bani_biso(self):
        project = _make_project_with_structure()
        s = project.structures['cubic']
        s.atom_sites['A'].adp_type = 'Bani'
        s.atom_sites['A'].adp_type = 'Biso'
        assert s.atom_sites['A'].adp_iso.value == pytest.approx(0.5)

    def test_biso_uani_biso(self):
        project = _make_project_with_structure()
        s = project.structures['cubic']
        s.atom_sites['A'].adp_type = 'Uani'
        s.atom_sites['A'].adp_type = 'Biso'
        assert s.atom_sites['A'].adp_iso.value == pytest.approx(0.5)

    def test_uiso_uani_uiso(self):
        project = _make_project_with_structure()
        s = project.structures['cubic']
        s.atom_sites['A'].adp_type = 'Uiso'
        u_val = s.atom_sites['A'].adp_iso.value
        s.atom_sites['A'].adp_type = 'Uani'
        s.atom_sites['A'].adp_type = 'Uiso'
        assert s.atom_sites['A'].adp_iso.value == pytest.approx(u_val)

    def test_biso_uiso_biso(self):
        project = _make_project_with_structure()
        s = project.structures['cubic']
        s.atom_sites['A'].adp_type = 'Uiso'
        s.atom_sites['A'].adp_type = 'Biso'
        assert s.atom_sites['A'].adp_iso.value == pytest.approx(0.5)

    def test_full_cycle_biso_uiso_uani_bani_biso(self):
        project = _make_project_with_structure()
        s = project.structures['cubic']
        s.atom_sites['A'].adp_type = 'Uiso'
        s.atom_sites['A'].adp_type = 'Uani'
        s.atom_sites['A'].adp_type = 'Bani'
        s.atom_sites['A'].adp_type = 'Biso'
        assert s.atom_sites['A'].adp_iso.value == pytest.approx(0.5)


# ------------------------------------------------------------------
#  Mixed ADP types in the same structure
# ------------------------------------------------------------------


class TestMixedAdpTypes:
    def test_mixed_types_coexist(self):
        project = _make_project_with_structure()
        s = project.structures['cubic']
        s.atom_sites['A'].adp_type = 'Uani'  # Auto-changed to Bani by next line
        s.atom_sites['B'].adp_type = 'Biso'
        assert s.atom_sites['A'].adp_type.value == 'Bani'
        assert s.atom_sites['B'].adp_type.value == 'Biso'

    def test_mixed_cif_has_question_marks_for_iso(self):
        project = _make_project_with_structure()
        s = project.structures['cubic']
        s.atom_sites['A'].adp_type = 'Bani'
        cif = s.atom_site_aniso.as_cif
        # A is Bani → numerical values
        # B is Biso → ? markers
        lines = cif.strip().split('\n')
        data_lines = [l for l in lines if not l.startswith(('loop_', '_atom_site_aniso'))]
        b_line = next(l for l in data_lines if 'B ' in l or l.startswith('B '))
        assert '?' in b_line

    def test_all_iso_suppresses_aniso_cif(self):
        project = _make_project_with_structure()
        s = project.structures['cubic']
        cif = s.atom_site_aniso.as_cif
        assert cif == ''

    def test_adp_iso_syncs_from_aniso_on_update(self):
        project = _make_project_with_structure()
        s = project.structures['cubic']
        s.atom_sites['A'].adp_type = 'Bani'
        # In P m -3 m, Wyckoff 'a' constrains U11=U22=U33, U12=U13=U23=0
        # so any set of diagonal values collapses to U11 after update
        s.atom_site_aniso['A'].adp_11 = 0.3
        s.atom_site_aniso['A'].adp_22 = 0.6
        s.atom_site_aniso['A'].adp_33 = 0.9
        s._update_categories()
        # After symmetry constraints: all diags = 0.3 (first value wins)
        aniso = s.atom_site_aniso['A']
        assert aniso.adp_11.value == pytest.approx(aniso.adp_22.value)
        assert aniso.adp_11.value == pytest.approx(aniso.adp_33.value)
        # adp_iso should match the constrained diagonal mean
        expected = (aniso.adp_11.value + aniso.adp_22.value + aniso.adp_33.value) / 3.0
        assert s.atom_sites['A'].adp_iso.value == pytest.approx(expected)

    def test_adp_iso_unchanged_for_iso_atom_on_update(self):
        project = _make_project_with_structure()
        s = project.structures['cubic']
        s.atom_sites['A'].adp_type = 'Bani'
        s._update_categories()
        # B stays Biso → its adp_iso should not change
        assert s.atom_sites['B'].adp_iso.value == pytest.approx(0.3)


# ------------------------------------------------------------------
#  CIF name selection based on ADP type
# ------------------------------------------------------------------


class TestCifNamesByAdpType:
    def test_biso_uses_b_names(self):
        project = _make_project_with_structure()
        s = project.structures['cubic']
        site = s.atom_sites['A']
        assert '_atom_site.B_iso_or_equiv' in site._adp_iso._cif_handler.names[0]

    def test_uiso_uses_u_names(self):
        project = _make_project_with_structure()
        s = project.structures['cubic']
        s.atom_sites['A'].adp_type = 'Uiso'
        site = s.atom_sites['A']
        assert '_atom_site.U_iso_or_equiv' in site._adp_iso._cif_handler.names[0]

    def test_bani_uses_b_aniso_names(self):
        project = _make_project_with_structure()
        s = project.structures['cubic']
        s.atom_sites['A'].adp_type = 'Bani'
        aniso = s.atom_site_aniso['A']
        assert aniso._adp_11._cif_handler.names[0] == '_atom_site_aniso.B_11'

    def test_uani_uses_u_aniso_names(self):
        project = _make_project_with_structure()
        s = project.structures['cubic']
        s.atom_sites['A'].adp_type = 'Uani'
        aniso = s.atom_site_aniso['A']
        assert aniso._adp_11._cif_handler.names[0] == '_atom_site_aniso.U_11'
