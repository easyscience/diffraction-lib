# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import tempfile

from numpy.testing import assert_almost_equal

import easydiffraction as ed
from easydiffraction import ExperimentFactory
from easydiffraction import Project
from easydiffraction import StructureFactory
from easydiffraction import download_data

TEMP_DIR = tempfile.gettempdir()


def test_single_fit_neutron_pd_tof_mcstas_lbco_si() -> None:
    # Set structures
    model_1 = StructureFactory.from_scratch(name='lbco')
    model_1.space_group.name_h_m = 'P m -3 m'
    model_1.space_group.it_coordinate_system_code = '1'
    model_1.cell.length_a = 3.8909
    model_1.atom_sites.create(
        label='La',
        type_symbol='La',
        fract_x=0,
        fract_y=0,
        fract_z=0,
        wyckoff_letter='a',
        adp_iso=0.2,
        occupancy=0.5,
    )
    model_1.atom_sites.create(
        label='Ba',
        type_symbol='Ba',
        fract_x=0,
        fract_y=0,
        fract_z=0,
        wyckoff_letter='a',
        adp_iso=0.2,
        occupancy=0.5,
    )
    model_1.atom_sites.create(
        label='Co',
        type_symbol='Co',
        fract_x=0.5,
        fract_y=0.5,
        fract_z=0.5,
        wyckoff_letter='b',
        adp_iso=0.2567,
    )
    model_1.atom_sites.create(
        label='O',
        type_symbol='O',
        fract_x=0,
        fract_y=0.5,
        fract_z=0.5,
        wyckoff_letter='c',
        adp_iso=1.4041,
    )

    model_2 = StructureFactory.from_scratch(name='si')
    model_2.space_group.name_h_m = 'F d -3 m'
    model_2.space_group.it_coordinate_system_code = '2'
    model_2.cell.length_a = 5.43146
    model_2.atom_sites.create(
        label='Si',
        type_symbol='Si',
        fract_x=0.0,
        fract_y=0.0,
        fract_z=0.0,
        wyckoff_letter='a',
        adp_iso=0.0,
    )

    # Set experiment
    data_path = download_data(id=8, destination=TEMP_DIR)
    expt = ExperimentFactory.from_data_path(
        name='mcstas',
        data_path=data_path,
        beam_mode='time-of-flight',
    )
    expt.instrument.setup_twotheta_bank = 94.90931761529106
    expt.instrument.calib_d_to_tof_offset = 0.0
    expt.instrument.calib_d_to_tof_linear = 58724.76869981215
    expt.instrument.calib_d_to_tof_quad = -0.00001
    expt.peak_profile_type = 'jorgensen'
    expt.peak.broad_gauss_sigma_0 = 45137
    expt.peak.broad_gauss_sigma_1 = -52394
    expt.peak.broad_gauss_sigma_2 = 22998
    expt.peak.exp_decay_beta_0 = 0.0055
    expt.peak.exp_decay_beta_1 = 0.0041
    expt.peak.exp_rise_alpha_0 = 0.0
    expt.peak.exp_rise_alpha_1 = 0.0097
    expt.linked_phases.create(id='lbco', scale=4.0)
    expt.linked_phases.create(id='si', scale=0.2)
    for x in range(45000, 115000, 5000):
        expt.background.create(id=str(x), x=x, y=0.2)

    # Create project
    project = Project()
    project.structures.add(model_1)
    project.structures.add(model_2)
    project.experiments.add(expt)

    # Exclude regions from fitting
    project.experiments['mcstas'].excluded_regions.create(start=108000, end=200000)

    # Prepare for fitting
    project.analysis.minimizer_type = 'lmfit'

    # Select fitting parameters
    model_1.cell.length_a.free = True
    model_1.atom_sites['La'].adp_iso.free = True
    model_1.atom_sites['Ba'].adp_iso.free = True
    model_1.atom_sites['Co'].adp_iso.free = True
    model_1.atom_sites['O'].adp_iso.free = True
    model_2.cell.length_a.free = True
    model_2.atom_sites['Si'].adp_iso.free = True
    expt.linked_phases['lbco'].scale.free = True
    expt.linked_phases['si'].scale.free = True
    expt.peak.broad_gauss_sigma_0.free = True
    expt.peak.broad_gauss_sigma_1.free = True
    expt.peak.broad_gauss_sigma_2.free = True
    expt.peak.exp_rise_alpha_1.free = True
    expt.peak.exp_decay_beta_0.free = True
    expt.peak.exp_decay_beta_1.free = True
    for point in expt.background:
        point.y.free = True

    # Perform fit
    project.analysis.fit()

    # Compare fit quality
    assert_almost_equal(
        project.analysis.fit_results.reduced_chi_square,
        desired=2.87,
        decimal=1,
    )


def _test_joint_fit_bragg_pdf_neutron_pd_tof_si() -> None:
    # Set structure (shared between Bragg and PDF experiments)
    model = StructureFactory.from_scratch(name='si')
    model.space_group.name_h_m = 'F d -3 m'
    model.space_group.it_coordinate_system_code = '2'
    model.cell.length_a = 5.431
    model.atom_sites.create(
        label='Si',
        type_symbol='Si',
        fract_x=0.125,
        fract_y=0.125,
        fract_z=0.125,
        adp_iso=0.5,
    )

    # Set Bragg experiment (SEPD, TOF)
    bragg_data_path = download_data(id=7, destination=TEMP_DIR)
    bragg_expt = ExperimentFactory.from_data_path(
        name='sepd',
        data_path=bragg_data_path,
        beam_mode='time-of-flight',
    )
    bragg_expt.instrument.setup_twotheta_bank = 144.845
    bragg_expt.instrument.calib_d_to_tof_offset = 0.0
    bragg_expt.instrument.calib_d_to_tof_linear = 7476.91
    bragg_expt.instrument.calib_d_to_tof_quad = -1.54
    bragg_expt.peak_profile_type = 'jorgensen'
    bragg_expt.peak.broad_gauss_sigma_0 = 3.0
    bragg_expt.peak.broad_gauss_sigma_1 = 40.0
    bragg_expt.peak.broad_gauss_sigma_2 = 2.0
    bragg_expt.peak.exp_decay_beta_0 = 0.04221
    bragg_expt.peak.exp_decay_beta_1 = 0.00946
    bragg_expt.peak.exp_rise_alpha_0 = 0.0
    bragg_expt.peak.exp_rise_alpha_1 = 0.5971
    bragg_expt.linked_phases.create(id='si', scale=10.0)
    for x in range(0, 35000, 5000):
        bragg_expt.background.create(id=str(x), x=x, y=200)

    # Set PDF experiment (NOMAD, TOF)
    pdf_data_path = ed.download_data(id=5, destination=TEMP_DIR)
    pdf_expt = ExperimentFactory.from_data_path(
        name='nomad',
        data_path=pdf_data_path,
        beam_mode='time-of-flight',
        scattering_type='total',
    )
    pdf_expt.peak.damp_q = 0.02
    pdf_expt.peak.broad_q = 0.03
    pdf_expt.peak.cutoff_q = 35.0
    pdf_expt.peak.sharp_delta_1 = 0.0
    pdf_expt.peak.sharp_delta_2 = 4.0
    pdf_expt.peak.damp_particle_diameter = 0
    pdf_expt.linked_phases.create(id='si', scale=1.0)

    # Create project
    project = Project()
    project.structures.add(model)
    project.experiments.add(bragg_expt)
    project.experiments.add(pdf_expt)

    # Prepare for fitting
    project.analysis.fit_mode_type = 'joint'
    project.analysis.minimizer_type = 'lmfit'

    # Select fitting parameters — shared structure
    model.cell.length_a.free = True
    model.atom_sites['Si'].adp_iso.free = True

    # Select fitting parameters — Bragg experiment
    bragg_expt.linked_phases['si'].scale.free = True
    bragg_expt.instrument.calib_d_to_tof_offset.free = True
    for point in bragg_expt.background:
        point.y.free = True

    # Select fitting parameters — PDF experiment
    pdf_expt.linked_phases['si'].scale.free = True
    pdf_expt.peak.damp_q.free = True
    pdf_expt.peak.broad_q.free = True
    pdf_expt.peak.sharp_delta_1.free = True
    pdf_expt.peak.sharp_delta_2.free = True

    # Perform fit
    project.analysis.fit()

    # Compare fit quality
    assert_almost_equal(
        project.analysis.fit_results.reduced_chi_square,
        desired=8978.39,
        decimal=-2,
    )


if __name__ == '__main__':
    test_single_fit_neutron_pd_tof_mcstas_lbco_si()
    # test_joint_fit_bragg_pdf_neutron_pd_tof_si()
