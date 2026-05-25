# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

from __future__ import annotations

import tempfile

import numpy as np

from easydiffraction import ExperimentFactory
from easydiffraction import Project
from easydiffraction import StructureFactory
from easydiffraction import download_data
from easydiffraction.analysis.fitting import FitterFitOptions

TEMP_DIR = tempfile.gettempdir()


def _create_lbco_project() -> Project:
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
    experiment = ExperimentFactory.from_data_path(name='hrpt', data_path=data_path)
    experiment.instrument.setup_wavelength = 1.494
    experiment.instrument.calib_twotheta_offset = 0.0
    experiment.peak.broad_gauss_u = 0.1
    experiment.peak.broad_gauss_v = -0.1
    experiment.peak.broad_gauss_w = 0.2
    experiment.peak.broad_lorentz_x = 0.0
    experiment.peak.broad_lorentz_y = 0.0
    experiment.linked_phases.create(id='lbco', scale=5.0)
    experiment.background.create(id='1', x=10, y=170)
    experiment.background.create(id='2', x=165, y=170)

    project = Project(name='lbco_bayesian')
    project.structures.add(model)
    project.experiments.add(experiment)
    return project


def _dream_parameters(project: Project) -> tuple[object, object, object]:
    structure = project.structures['lbco']
    experiment = project.experiments['hrpt']
    return (
        structure.cell.length_a,
        experiment.linked_phases['lbco'].scale,
        experiment.instrument.calib_twotheta_offset,
    )


def _configure_small_dream(project: Project) -> None:
    project.analysis.minimizer.type = 'bumps (dream)'
    minimizer = project.analysis.minimizer
    minimizer.sampling_steps = 20
    minimizer.burn_in_steps = 5
    minimizer.thinning_interval = 1
    minimizer.population_size = 4
    minimizer.parallel_workers = 1
    minimizer.initialization_method = 'latin_hypercube'


def _run_single_fit(project: Project, *, random_seed: int | None = None) -> None:
    project.verbosity = 'silent'
    prepared = project.analysis._prepare_fit_run()
    assert prepared is not None
    verb, structures, experiments = prepared
    project.analysis._fit_single(
        verb,
        structures,
        experiments,
        fit_options=FitterFitOptions(random_seed=random_seed),
    )


def test_small_bounded_dream_refinement_produces_posterior_results():
    project = _create_lbco_project()
    length_a, scale, offset = _dream_parameters(project)
    for parameter in (length_a, scale, offset):
        parameter.free = True

    length_a.fit_min = 3.84
    length_a.fit_max = 3.92
    scale.fit_min = 1.0
    scale.fit_max = 12.0
    offset.fit_min = -1.0
    offset.fit_max = 1.0

    _configure_small_dream(project)
    _run_single_fit(project, random_seed=11)

    results = project.analysis.fit_results
    assert results.success is True
    assert results.sampler_completed is True
    assert results.sampler_name == 'dream'
    assert results.posterior_samples is not None
    assert results.posterior_samples.parameter_samples.ndim == 3
    assert results.sampler_settings['random_seed'] == 11
    assert results.sampler_settings['init'] == 'lhs'
    assert len(results.posterior_parameter_summaries) == 3


def test_lm_prefit_followed_by_dream_uses_uncertainty_based_bounds():
    project = _create_lbco_project()
    length_a, scale, offset = _dream_parameters(project)
    for parameter in (length_a, scale, offset):
        parameter.free = True

    project.analysis.minimizer.type = 'bumps (lm)'
    _run_single_fit(project)

    for parameter in (length_a, scale, offset):
        assert parameter.uncertainty is not None
        parameter.set_fit_bounds_from_uncertainty(multiplier=4)
        assert np.isfinite(parameter.fit_min)
        assert np.isfinite(parameter.fit_max)

    _configure_small_dream(project)
    _run_single_fit(project, random_seed=13)

    results = project.analysis.fit_results
    assert results.success is True
    assert results.posterior_samples is not None
    assert results.sampler_settings['random_seed'] == 13
    assert len(results.posterior_parameter_summaries) == 3


def test_bayesian_fit_results_reload_from_persisted_fit_state(tmp_path):
    project = _create_lbco_project()
    length_a, scale, offset = _dream_parameters(project)
    for parameter in (length_a, scale, offset):
        parameter.free = True

    length_a.fit_min = 3.84
    length_a.fit_max = 3.92
    scale.fit_min = 1.0
    scale.fit_max = 12.0
    offset.fit_min = -1.0
    offset.fit_max = 1.0

    _configure_small_dream(project)
    _run_single_fit(project, random_seed=17)

    assert project.analysis.fit_results.posterior_samples is not None

    proj_dir = tmp_path / 'dream_project'
    project.save_as(str(proj_dir))

    analysis_cif = proj_dir / 'analysis' / 'analysis.cif'
    results_sidecar = proj_dir / 'analysis' / 'results.h5'
    assert analysis_cif.is_file()
    assert results_sidecar.is_file()

    loaded = Project.load(str(proj_dir))
    loaded_results = loaded.analysis.fit_results
    assert loaded_results is not None
    assert loaded_results.sampler_completed is True
    assert loaded_results.posterior_samples is not None
    assert loaded_results.posterior_samples.parameter_samples.ndim == 3
