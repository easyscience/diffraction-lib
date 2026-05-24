# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

"""Shared fixtures for integration tests."""

import tempfile

import pytest

from easydiffraction import ExperimentFactory
from easydiffraction import Project
from easydiffraction import StructureFactory
from easydiffraction import download_data

TEMP_DIR = tempfile.gettempdir()


@pytest.fixture(scope='session')
def lbco_fitted_project():
    """Build and fit an LBCO CWL project (session-scoped for reuse)."""
    model = StructureFactory.from_scratch(name='lbco')
    model.space_group.name_h_m = 'P m -3 m'
    model.cell.length_a = 3.88
    model.atom_sites.create(
        label='La',
        type_symbol='La',
        fract_x=0,
        fract_y=0,
        fract_z=0,
        wyckoff_letter='a',
        occupancy=0.5,
        adp_iso=0.1,
    )
    model.atom_sites.create(
        label='Ba',
        type_symbol='Ba',
        fract_x=0,
        fract_y=0,
        fract_z=0,
        wyckoff_letter='a',
        occupancy=0.5,
        adp_iso=0.1,
    )
    model.atom_sites.create(
        label='Co',
        type_symbol='Co',
        fract_x=0.5,
        fract_y=0.5,
        fract_z=0.5,
        wyckoff_letter='b',
        adp_iso=0.1,
    )
    model.atom_sites.create(
        label='O',
        type_symbol='O',
        fract_x=0,
        fract_y=0.5,
        fract_z=0.5,
        wyckoff_letter='c',
        adp_iso=0.1,
    )

    data_path = download_data(id=3, destination=TEMP_DIR)
    expt = ExperimentFactory.from_data_path(name='hrpt', data_path=data_path)
    expt.instrument.setup_wavelength = 1.494
    expt.instrument.calib_twotheta_offset = 0
    expt.peak.broad_gauss_u = 0.1
    expt.peak.broad_gauss_v = -0.1
    expt.peak.broad_gauss_w = 0.2
    expt.peak.broad_lorentz_x = 0
    expt.peak.broad_lorentz_y = 0
    expt.linked_phases.create(id='lbco', scale=5.0)
    expt.background.create(id='1', x=10, y=170)
    expt.background.create(id='2', x=165, y=170)

    project = Project()
    project.structures.add(model)
    project.experiments.add(expt)
    project.analysis.minimizer.type = 'lmfit'

    model.cell.length_a.free = True
    expt.linked_phases['lbco'].scale.free = True
    expt.instrument.calib_twotheta_offset.free = True
    expt.background['1'].y.free = True
    expt.background['2'].y.free = True

    project.verbosity = 'silent'
    project.analysis.fit()

    return project
