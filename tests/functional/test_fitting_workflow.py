# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Functional tests for analysis: aliases, constraints, fitting."""

from __future__ import annotations

import tempfile

import pytest

from easydiffraction import Project
from easydiffraction import download_data

TEMP_DIR = tempfile.gettempdir()


def _make_fit_ready_project():
    """Build a minimal project ready for fitting."""
    Project._loading = True
    try:
        project = Project()
    finally:
        Project._loading = False

    # Structure
    project.structures.create(name='lbco')
    s = project.structures['lbco']
    s.space_group.name_h_m = 'P m -3 m'
    s.cell.length_a = 3.89
    s.atom_sites.create(
        label='La',
        type_symbol='La',
        fract_x=0,
        fract_y=0,
        fract_z=0,
        wyckoff_letter='a',
        occupancy=0.5,
        adp_iso=0.5,
    )
    s.atom_sites.create(
        label='Ba',
        type_symbol='Ba',
        fract_x=0,
        fract_y=0,
        fract_z=0,
        wyckoff_letter='a',
        occupancy=0.5,
        adp_iso=0.5,
    )
    s.atom_sites.create(
        label='Co',
        type_symbol='Co',
        fract_x=0.5,
        fract_y=0.5,
        fract_z=0.5,
        wyckoff_letter='b',
        adp_iso=0.5,
    )
    s.atom_sites.create(
        label='O',
        type_symbol='O',
        fract_x=0,
        fract_y=0.5,
        fract_z=0.5,
        wyckoff_letter='c',
        adp_iso=0.5,
    )

    # Experiment
    data_path = download_data(id=3, destination=TEMP_DIR)
    project.experiments.add_from_data_path(
        name='hrpt',
        data_path=data_path,
    )
    expt = project.experiments['hrpt']
    expt.instrument.setup_wavelength = 1.494
    expt.instrument.calib_twotheta_offset = 0.6225
    expt.peak.broad_gauss_u = 0.0834
    expt.peak.broad_gauss_v = -0.1168
    expt.peak.broad_gauss_w = 0.123
    expt.peak.broad_lorentz_x = 0
    expt.peak.broad_lorentz_y = 0.0797
    expt.background.create(id='1', x=10, y=170)
    expt.background.create(id='2', x=165, y=170)
    expt.linked_phases.create(id='lbco', scale=9.0)

    # Free parameters
    s.cell.length_a.free = True
    expt.linked_phases['lbco'].scale.free = True
    expt.instrument.calib_twotheta_offset.free = True
    expt.background['1'].y.free = True
    expt.background['2'].y.free = True

    return project


class TestAliases:
    def test_create_alias(self):
        project = _make_fit_ready_project()
        s = project.structures['lbco']
        project.analysis.aliases.create(
            label='biso_La',
            param=s.atom_sites['La'].adp_iso,
        )
        assert len(project.analysis.aliases) == 1

    def test_create_multiple_aliases(self):
        project = _make_fit_ready_project()
        s = project.structures['lbco']
        project.analysis.aliases.create(
            label='biso_La',
            param=s.atom_sites['La'].adp_iso,
        )
        project.analysis.aliases.create(
            label='biso_Ba',
            param=s.atom_sites['Ba'].adp_iso,
        )
        assert len(project.analysis.aliases) == 2


class TestConstraints:
    def test_create_constraint(self):
        project = _make_fit_ready_project()
        s = project.structures['lbco']
        project.analysis.aliases.create(
            label='biso_La',
            param=s.atom_sites['La'].adp_iso,
        )
        project.analysis.aliases.create(
            label='biso_Ba',
            param=s.atom_sites['Ba'].adp_iso,
        )
        project.analysis.constraints.create(
            expression='biso_Ba = biso_La',
        )
        assert len(project.analysis.constraints) == 1


class TestFitting:
    def test_fit_produces_results(self):
        project = _make_fit_ready_project()
        project.analysis.fit(verbosity='silent')
        assert project.analysis.fit_results is not None
        assert project.analysis.fit_results.success is True

    def test_fit_improves_chi_squared(self):
        project = _make_fit_ready_project()
        project.analysis.fit(verbosity='silent')
        results = project.analysis.fit_results
        assert results.reduced_chi_square is not None
        # A well-configured fit should get reasonable chi-squared
        assert results.reduced_chi_square < 100

    def test_fit_updates_parameter_values(self):
        project = _make_fit_ready_project()
        initial_a = project.structures['lbco'].cell.length_a.value
        project.analysis.fit(verbosity='silent')
        fitted_a = project.structures['lbco'].cell.length_a.value
        # Fitting should have adjusted the cell parameter
        assert fitted_a != pytest.approx(initial_a, abs=1e-6)

    def test_fit_with_constraints(self):
        project = _make_fit_ready_project()
        s = project.structures['lbco']
        s.atom_sites['La'].adp_iso.free = True
        s.atom_sites['Ba'].adp_iso.free = True

        project.analysis.aliases.create(
            label='biso_La',
            param=s.atom_sites['La'].adp_iso,
        )
        project.analysis.aliases.create(
            label='biso_Ba',
            param=s.atom_sites['Ba'].adp_iso,
        )
        project.analysis.constraints.create(
            expression='biso_Ba = biso_La',
        )

        project.analysis.fit(verbosity='silent')
        assert project.analysis.fit_results.success is True
        # Constrained params should be equal after fitting
        la_biso = s.atom_sites['La'].adp_iso.value
        ba_biso = s.atom_sites['Ba'].adp_iso.value
        assert la_biso == pytest.approx(ba_biso, rel=1e-3)
