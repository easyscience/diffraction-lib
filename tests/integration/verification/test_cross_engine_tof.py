# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause
"""Strict cross-engine gate for the time-of-flight verification pages.

The Al2O3 and Si time-of-flight Verification notebooks
(``docs/docs/verification/{al2o3,si}-bragg-tof.py``) report the cryspy
discrepancy with ``raise_on_failure=False`` so the docs build stays
green. This test is the strict regression gate for those cases: it
calculates each pattern with both engines and checks agreement against
the FullProf reference.

``crysfml`` reproduces FullProf and passes. ``cryspy`` currently diverges
for the Jorgensen-Von Dreele profile when the Lorentzian
(``broad_lorentz_gamma``) term is non-zero, so its cases fail until the
cryspy backend is fixed (tracked in ``docs/dev/issues/open.md``). The
failure is intentional and localises the regression to the cryspy engine.
"""

from __future__ import annotations

import pytest

import easydiffraction as ed
from easydiffraction import ExperimentFactory
from easydiffraction import StructureFactory
from easydiffraction.analysis import verification as verify


def _build_al2o3_tof() -> tuple[object, object, object]:
    """Build the Al2O3 time-of-flight project and FullProf reference."""
    _, calc_fullprof = verify.load_fullprof_profile(
        str(verify.bundled_reference_dir() / 'al2o3_tof.sim')
    )
    project = ed.Project()
    structure = StructureFactory.from_scratch(name='al2o3')
    structure.space_group.name_h_m = 'R -3 c'
    structure.cell.length_a = 4.754000
    structure.cell.length_b = 4.754000
    structure.cell.length_c = 12.990000
    structure.cell.angle_gamma = 120.0
    structure.atom_sites.create(
        label='Al', type_symbol='Al', fract_x=0.0, fract_y=0.0, fract_z=0.35228, adp_iso=0.40
    )
    structure.atom_sites.create(
        label='O', type_symbol='O', fract_x=0.30640, fract_y=0.0, fract_z=0.25, adp_iso=0.60
    )
    project.structures.add(structure)

    x, _ = verify.load_fullprof_profile(str(verify.bundled_reference_dir() / 'al2o3_tof.sim'))
    experiment = ExperimentFactory.from_scratch(
        name='al2o3',
        sample_form='powder',
        beam_mode='time-of-flight',
        radiation_probe='neutron',
        scattering_type='bragg',
    )
    verify.set_reference_as_measured(experiment, x, calc_fullprof)
    experiment.instrument.setup_twotheta_bank = 90.0
    experiment.instrument.calib_d_to_tof_linear = 4570.60010
    experiment.instrument.calib_d_to_tof_quad = 0.0
    experiment.instrument.calib_d_to_tof_offset = 0.0
    experiment.peak.type = 'jorgensen-von-dreele'
    experiment.peak.broad_gauss_sigma_0 = 3.5190
    experiment.peak.broad_gauss_sigma_1 = 63.3850
    experiment.peak.broad_gauss_sigma_2 = 1.5880
    experiment.peak.broad_lorentz_gamma_1 = 4.6950
    experiment.peak.exp_rise_alpha_1 = 0.716993
    experiment.peak.exp_decay_beta_0 = 0.050835
    experiment.peak.exp_decay_beta_1 = 0.010232
    experiment.linked_phases.create(id='al2o3', scale=1.0)
    project.experiments.add(experiment)
    return project, experiment, calc_fullprof


def _build_si_tof() -> tuple[object, object, object]:
    """Build the Si time-of-flight project and FullProf reference."""
    x, calc_fullprof = verify.load_fullprof_profile(
        str(verify.bundled_reference_dir() / 'si_tof.sub')
    )
    project = ed.Project()
    structure = StructureFactory.from_scratch(name='si')
    structure.space_group.name_h_m = 'F d -3 m'
    structure.space_group.it_coordinate_system_code = '2'
    structure.cell.length_a = 5.431342
    structure.cell.length_b = 5.431342
    structure.cell.length_c = 5.431342
    structure.atom_sites.create(
        label='Si', type_symbol='Si', fract_x=0.125, fract_y=0.125, fract_z=0.125, adp_iso=0.52451
    )
    project.structures.add(structure)

    experiment = ExperimentFactory.from_scratch(
        name='si',
        sample_form='powder',
        beam_mode='time-of-flight',
        radiation_probe='neutron',
        scattering_type='bragg',
    )
    verify.set_reference_as_measured(experiment, x, calc_fullprof)
    experiment.instrument.setup_twotheta_bank = 144.845
    experiment.instrument.calib_d_to_tof_linear = 7476.91016
    experiment.instrument.calib_d_to_tof_quad = -1.54
    experiment.instrument.calib_d_to_tof_offset = 0.0
    experiment.peak.type = 'jorgensen-von-dreele'
    experiment.peak.broad_gauss_sigma_0 = 3.5541
    experiment.peak.broad_gauss_sigma_1 = 33.0418
    experiment.peak.broad_lorentz_gamma_1 = 2.5432
    experiment.peak.exp_rise_alpha_1 = 0.5971
    experiment.peak.exp_decay_beta_0 = 0.04221
    experiment.peak.exp_decay_beta_1 = 0.00946
    experiment.linked_phases.create(id='si', scale=1.0)
    project.experiments.add(experiment)
    return project, experiment, calc_fullprof


_BUILDERS = {'al2o3': _build_al2o3_tof, 'si': _build_si_tof}


@pytest.mark.parametrize('case', ['al2o3', 'si'])
@pytest.mark.parametrize('engine', ['crysfml', 'cryspy'])
def test_tof_engine_matches_fullprof(case: str, engine: str) -> None:
    """Each engine's TOF pattern must match the FullProf reference.

    ``cryspy`` cases fail until the TOF Jorgensen-Von Dreele Lorentzian
    handling is fixed (see module docstring).
    """
    project, experiment, calc_fullprof = _BUILDERS[case]()
    calc = verify.calculate_pattern(project, experiment, engine)
    metrics = verify.pattern_closeness(calc_fullprof, calc)
    tolerances = verify.AgreementTolerances()

    assert metrics.profile_difference_percent < tolerances.max_profile_difference_percent, (
        f'{engine} vs FullProf ({case}) profile difference '
        f'{metrics.profile_difference_percent:.2f}% exceeds '
        f'{tolerances.max_profile_difference_percent}%'
    )
    assert (
        tolerances.min_intensity_ratio < metrics.intensity_ratio < tolerances.max_intensity_ratio
    )
    assert metrics.correlation > tolerances.min_correlation
