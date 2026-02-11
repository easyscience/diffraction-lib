# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 DMSC
"""Tests for analyzing reduced diffraction data using easydiffraction.

These tests verify the complete workflow:
1. Define project
2. Add sample model manually defined
3. Modify experiment CIF file
4. Add experiment from modified CIF file
5. Modify default experiment configuration
6. Select parameters to be fitted
7. Do fitting
"""

from pathlib import Path

import pytest
from numpy.testing import assert_almost_equal

import easydiffraction as ed

# CIF experiment type tags required by easydiffraction to identify
# the experiment configuration (powder TOF neutron diffraction)
EXPT_TYPE_TAGS = {
    '_expt_type.sample_form': 'powder',
    '_expt_type.beam_mode': 'time-of-flight',
    '_expt_type.radiation_probe': 'neutron',
    '_expt_type.scattering_type': 'bragg',
}


@pytest.fixture(scope='module')
def prepared_cif_path(
    cif_path: str,
    tmp_path_factory: pytest.TempPathFactory,
) -> str:
    """Prepare CIF file with experiment type tags for
    easydiffraction.
    """
    with Path(cif_path).open() as f:
        content = f.read()

    # Add experiment type tags if missing
    for tag, value in EXPT_TYPE_TAGS.items():
        if tag not in content:
            content += f'\n{tag} {value}'

    # Write to temp file
    tmp_dir = tmp_path_factory.mktemp('dream_data')
    prepared_path = tmp_dir / 'dream_reduced_prepared.cif'
    prepared_path.write_text(content)

    return str(prepared_path)


@pytest.fixture(scope='module')
def project_with_data(
    prepared_cif_path: str,
) -> ed.Project:
    """Create project with sample model, experiment data, and
    configuration.

    1. Define project
    2. Add sample model manually defined
    3. Modify experiment CIF file
    4. Add experiment from modified CIF file
    5. Modify default experiment configuration
    """
    # Step 1: Define Project
    project = ed.Project()

    # Step 2: Define Sample Model manually
    project.sample_models.add(name='si')
    sample_model = project.sample_models['si']

    sample_model.space_group.name_h_m = 'F d -3 m'
    sample_model.space_group.it_coordinate_system_code = '1'

    sample_model.cell.length_a = 5.43146

    sample_model.atom_sites.add(
        label='Si',
        type_symbol='Si',
        fract_x=0.125,
        fract_y=0.125,
        fract_z=0.125,
        wyckoff_letter='c',
        b_iso=1.1,
    )

    # Step 3: Add experiment from modified CIF file
    project.experiments.add(cif_path=prepared_cif_path)
    experiment = project.experiments['reduced_tof']

    # Step 4: Configure experiment
    # Link phase
    experiment.linked_phases.add(id='si', scale=0.8)

    # Instrument setup
    experiment.instrument.setup_twotheta_bank = 90.0
    experiment.instrument.calib_d_to_tof_linear = 18630.0

    # Peak profile parameters
    experiment.peak.broad_gauss_sigma_0 = 48500.0
    experiment.peak.broad_gauss_sigma_1 = 3000.0
    experiment.peak.broad_gauss_sigma_2 = 0.0
    experiment.peak.broad_mix_beta_0 = 0.05
    experiment.peak.broad_mix_beta_1 = 0.0
    experiment.peak.asym_alpha_0 = 0.0
    experiment.peak.asym_alpha_1 = 0.26

    # Excluded regions
    experiment.excluded_regions.add(id='1', start=0, end=10000)
    experiment.excluded_regions.add(id='2', start=70000, end=200000)

    # Background points
    background_points = [
        ('2', 10000, 0.01),
        ('3', 14000, 0.2),
        ('4', 21000, 0.7),
        ('5', 27500, 0.6),
        ('6', 40000, 0.3),
        ('7', 50000, 0.6),
        ('8', 61000, 0.7),
        ('9', 70000, 0.6),
    ]
    for id_, x, y in background_points:
        experiment.background.add(id=id_, x=x, y=y)

    return project


@pytest.fixture(scope='module')
def fitted_project(
    project_with_data: ed.Project,
) -> ed.Project:
    """Perform fit and return project with results.

    6. Select parameters to be fitted
    7. Do fitting
    """
    project = project_with_data
    sample_model = project.sample_models['si']
    experiment = project.experiments['reduced_tof']

    # Step 5: Select parameters to be fitted
    # Set free parameters for sample model
    sample_model.atom_sites['Si'].b_iso.free = True

    # Set free parameters for experiment
    experiment.linked_phases['si'].scale.free = True
    experiment.instrument.calib_d_to_tof_linear.free = True

    experiment.peak.broad_gauss_sigma_0.free = True
    experiment.peak.broad_gauss_sigma_1.free = True
    experiment.peak.broad_mix_beta_0.free = True

    # Set free parameters for background
    for point in experiment.background:
        point.y.free = True

    # Step 6: Do fitting
    project.analysis.fit()

    return project


# Test: Data Loading


def test_analyze_reduced_data__load_cif(
    project_with_data: ed.Project,
) -> None:
    """Verify CIF data loads into project correctly."""
    assert 'reduced_tof' in project_with_data.experiments.names


def test_analyze_reduced_data__data_size(
    project_with_data: ed.Project,
) -> None:
    """Verify loaded data has expected size."""
    experiment = project_with_data.experiments['reduced_tof']
    # Data should have substantial number of points
    assert experiment.data.x.size > 100


# Test: Configuration


def test_analyze_reduced_data__phase_linked(
    project_with_data: ed.Project,
) -> None:
    """Verify phase is correctly linked to experiment."""
    experiment = project_with_data.experiments['reduced_tof']
    assert 'si' in experiment.linked_phases.names


def test_analyze_reduced_data__background_set(
    project_with_data: ed.Project,
) -> None:
    """Verify background points are configured."""
    experiment = project_with_data.experiments['reduced_tof']
    assert len(experiment.background.names) >= 5


# Test: Fitting


def test_analyze_reduced_data__fit_quality(
    fitted_project: ed.Project,
) -> None:
    """Verify fit quality is reasonable (chi-square value)."""
    assert_almost_equal(
        fitted_project.analysis.fit_results.reduced_chi_square,
        desired=16.0,
        decimal=1,
    )
