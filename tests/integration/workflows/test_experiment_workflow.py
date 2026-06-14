# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Functional tests for experiment workflow: create, configure, verify params."""

from __future__ import annotations

import tempfile

import pytest

from easydiffraction import Project
from easydiffraction import download_data

TEMP_DIR = tempfile.gettempdir()


def _make_project_with_experiment():
    Project._loading = True
    try:
        project = Project()
    finally:
        Project._loading = False

    # Add a structure (required for experiment linking)
    project.structures.create(name='lbco')
    s = project.structures['lbco']
    s.space_group.name_h_m = 'P m -3 m'
    s.cell.length_a = 3.89
    s.atom_sites.create(
        id='La',
        type_symbol='La',
        fract_x=0,
        fract_y=0,
        fract_z=0,
        wyckoff_letter='a',
        occupancy=0.5,
        adp_iso=0.5,
    )

    # Add experiment from data file
    data_path = download_data('measured/lbco-hrpt', destination=TEMP_DIR)
    project.experiments.add_from_data_path(
        name='hrpt',
        data_path=data_path,
    )
    return project


class TestExperimentCreation:
    def test_add_experiment_from_data_path(self):
        project = _make_project_with_experiment()
        assert len(project.experiments) == 1
        assert 'hrpt' in project.experiments.names

    def test_access_experiment_by_name(self):
        project = _make_project_with_experiment()
        expt = project.experiments['hrpt']
        assert expt is not None


class TestInstrument:
    def test_set_wavelength(self):
        project = _make_project_with_experiment()
        expt = project.experiments['hrpt']
        expt.instrument.setup_wavelength = 1.494
        assert expt.instrument.setup_wavelength.value == pytest.approx(1.494)

    def test_set_twotheta_offset(self):
        project = _make_project_with_experiment()
        expt = project.experiments['hrpt']
        expt.instrument.calib_twotheta_offset = 0.5
        assert expt.instrument.calib_twotheta_offset.value == pytest.approx(0.5)

    def test_twotheta_offset_is_fittable(self):
        project = _make_project_with_experiment()
        expt = project.experiments['hrpt']
        expt.instrument.calib_twotheta_offset.free = True
        assert expt.instrument.calib_twotheta_offset.free is True


class TestPeakProfile:
    def test_set_peak_profile_params(self):
        project = _make_project_with_experiment()
        expt = project.experiments['hrpt']
        expt.peak.broad_gauss_u = 0.1
        expt.peak.broad_gauss_v = -0.2
        expt.peak.broad_gauss_w = 0.3
        assert expt.peak.broad_gauss_u.value == pytest.approx(0.1)
        assert expt.peak.broad_gauss_v.value == pytest.approx(-0.2)
        assert expt.peak.broad_gauss_w.value == pytest.approx(0.3)


class TestBackground:
    def test_create_background_points(self):
        project = _make_project_with_experiment()
        expt = project.experiments['hrpt']
        expt.background.create(id='1', position=10, intensity=170)
        expt.background.create(id='2', position=165, intensity=170)
        assert len(expt.background) == 2

    def test_background_y_is_fittable(self):
        project = _make_project_with_experiment()
        expt = project.experiments['hrpt']
        expt.background.create(id='1', position=10, intensity=170)
        expt.background['1'].intensity.free = True
        assert expt.background['1'].intensity.free is True


class TestLinkedPhases:
    def test_create_linked_phase(self):
        project = _make_project_with_experiment()
        expt = project.experiments['hrpt']
        expt.linked_structures.create(structure_id='lbco', scale=9.0)
        assert len(expt.linked_structures) == 1

    def test_linked_phase_scale_is_fittable(self):
        project = _make_project_with_experiment()
        expt = project.experiments['hrpt']
        expt.linked_structures.create(structure_id='lbco', scale=9.0)
        expt.linked_structures['lbco'].scale.free = True
        assert expt.linked_structures['lbco'].scale.free is True


class TestExcludedRegions:
    def test_create_excluded_regions(self):
        project = _make_project_with_experiment()
        expt = project.experiments['hrpt']
        expt.excluded_regions.create(id='1', start=0, end=10)
        expt.excluded_regions.create(id='2', start=160, end=180)
        assert len(expt.excluded_regions) == 2
