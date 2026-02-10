# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2026 DMSC
"""Tests for analyzing reduced diffraction data using
easydiffraction.
"""

from pathlib import Path
from typing import Any

import pytest

import easydiffraction as ed
from easydiffraction import Project
from easydiffraction import SampleModelFactory

# Experiment type tags required for easydiffraction
EXPT_TYPE_TAGS = {
    '_expt_type.sample_form': 'powder',
    '_expt_type.beam_mode': 'time-of-flight',
    '_expt_type.radiation_probe': 'neutron',
    '_expt_type.scattering_type': 'bragg',
}


@pytest.fixture(scope='module')
def sample_model() -> Any:
    """Create a Silicon sample model for fitting."""
    model = SampleModelFactory.create(name='si')
    model.space_group.name_h_m = 'F d -3 m'
    model.space_group.it_coordinate_system_code = '1'
    model.cell.length_a = 5.43146
    model.atom_sites.add(
        label='Si',
        type_symbol='Si',
        fract_x=0.125,
        fract_y=0.125,
        fract_z=0.125,
        wyckoff_letter='c',
        b_iso=1.1,
    )
    return model


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

    # Replace zero ESDs with finite values (required for fitting)
    content = content.replace(' 0.0 0.0', ' 0.0 1.0')

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
    sample_model: Any,
    prepared_cif_path: str,
) -> Project:
    """Create project with sample model and loaded experiment data."""
    project = ed.Project()
    project.sample_models.add(sample_model=sample_model)
    project.experiments.add(cif_path=prepared_cif_path)
    return project


@pytest.fixture(scope='module')
def configured_project(project_with_data: Project) -> Project:
    """Configure project with instrument and peak parameters for
    fitting.
    """
    project = project_with_data
    experiment = project.experiments['reduced_tof']

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
def fit_results(
    configured_project: Project,
) -> dict[str, Any]:
    """Perform fit and return results."""
    project = configured_project
    model = project.sample_models['si']
    experiment = project.experiments['reduced_tof']

    # Set free parameters for background
    for point in experiment.background:
        point.y.free = True

    # Set free parameters for fitting
    model.atom_sites['Si'].b_iso.free = True
    experiment.linked_phases['si'].scale.free = True
    experiment.instrument.calib_d_to_tof_linear.free = True
    experiment.peak.broad_gauss_sigma_0.free = True
    experiment.peak.broad_gauss_sigma_1.free = True
    experiment.peak.broad_mix_beta_0.free = True

    # Run fit
    project.analysis.fit()

    return {
        'success': project.analysis.fit_results.success,
        'reduced_chi': project.analysis.fit_results.reduced_chi_square,
        'n_free_params': len(project.analysis.fittable_params),
    }


# ======================================================================
# Test: Data Loading
# ======================================================================


def test_analyze_reduced_data__load_cif(
    project_with_data: Project,
) -> None:
    """Verify CIF data loads into project correctly."""
    assert 'reduced_tof' in project_with_data.experiments.names


def test_analyze_reduced_data__data_size(
    project_with_data: Project,
) -> None:
    """Verify loaded data has expected size."""
    experiment = project_with_data.experiments['reduced_tof']
    # Data should have substantial number of points
    assert experiment.data.x.size > 100


# ======================================================================
# Test: Configuration
# ======================================================================


def test_analyze_data__phase_linked(
    configured_project: Project,
) -> None:
    """Verify phase is correctly linked to experiment."""
    experiment = configured_project.experiments['reduced_tof']
    # Extract actual id values from linked_phases
    phase_ids = [
        p.id.value if hasattr(p.id, 'value') else str(p.id) for p in experiment.linked_phases
    ]
    assert 'si' in phase_ids


def test_analyze_data__background_set(
    configured_project: Project,
) -> None:
    """Verify background points are configured."""
    experiment = configured_project.experiments['reduced_tof']
    assert len(list(experiment.background)) >= 5


# ======================================================================
# Test: Fitting
# ======================================================================


def test_analyze_data__fit_success(
    fit_results: dict[str, Any],
) -> None:
    """Verify fitting completes successfully."""
    assert fit_results['success'] is True


def test_analyze_data__fit_quality(
    fit_results: dict[str, Any],
) -> None:
    """Verify fit quality is reasonable (chi-square < threshold)."""
    # Reduced chi-square should be reasonable for a good fit
    assert fit_results['reduced_chi'] < 10.0
