# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause

import tempfile

import pytest
from numpy.testing import assert_almost_equal

import easydiffraction as ed

TEMP_DIR = tempfile.gettempdir()


def test_single_fit_pdf_xray_pd_cw_nacl() -> None:
    project = ed.Project()

    # Set structure
    project.structures.create(name='nacl')
    structure = project.structures['nacl']
    structure.space_group.name_h_m = 'F m -3 m'
    structure.space_group.it_coordinate_system_code = '1'
    structure.cell.length_a = 5.6018
    structure.atom_sites.create(
        label='Na',
        type_symbol='Na',
        fract_x=0,
        fract_y=0,
        fract_z=0,
        wyckoff_letter='a',
        adp_iso=1.1053,
    )
    structure.atom_sites.create(
        label='Cl',
        type_symbol='Cl',
        fract_x=0.5,
        fract_y=0.5,
        fract_z=0.5,
        wyckoff_letter='b',
        adp_iso=0.5708,
    )

    # Set experiment
    data_path = ed.download_data(id=4, destination=TEMP_DIR)
    project.experiments.add_from_data_path(
        name='xray_pdf',
        data_path=data_path,
        sample_form='powder',
        beam_mode='constant wavelength',
        radiation_probe='xray',
        scattering_type='total',
    )
    experiment = project.experiments['xray_pdf']
    experiment.peak_profile_type = 'gaussian-damped-sinc'
    experiment.peak.damp_q = 0.0606
    experiment.peak.broad_q = 0
    experiment.peak.cutoff_q = 21
    experiment.peak.sharp_delta_1 = 0
    experiment.peak.sharp_delta_2 = 3.5041
    experiment.peak.damp_particle_diameter = 0
    experiment.linked_phases.create(id='nacl', scale=0.4254)

    # Select fitting parameters
    structure.cell.length_a.free = True
    structure.atom_sites['Na'].adp_iso.free = True
    structure.atom_sites['Cl'].adp_iso.free = True
    experiment.linked_phases['nacl'].scale.free = True
    experiment.peak.damp_q.free = True
    experiment.peak.sharp_delta_2.free = True

    # Perform fit
    project.analysis.fit()

    # Compare fit quality
    chi2 = project.analysis.fit_results.reduced_chi_square
    assert_almost_equal(chi2, desired=1.48, decimal=2)


@pytest.mark.fast
def test_single_fit_pdf_neutron_pd_cw_ni():
    project = ed.Project()

    # Set structure
    project.structures.create(name='ni')
    structure = project.structures['ni']
    structure.space_group.name_h_m.value = 'F m -3 m'
    structure.space_group.it_coordinate_system_code = '1'
    structure.cell.length_a = 3.526
    structure.atom_sites.create(
        label='Ni',
        type_symbol='Ni',
        fract_x=0,
        fract_y=0,
        fract_z=0,
        wyckoff_letter='a',
        adp_iso=0.4281,
    )

    # Set experiment
    data_path = ed.download_data(id=6, destination=TEMP_DIR)
    project.experiments.add_from_data_path(
        name='pdf',
        data_path=data_path,
        sample_form='powder',
        beam_mode='constant wavelength',
        radiation_probe='neutron',
        scattering_type='total',
    )
    experiment = project.experiments['pdf']
    experiment.peak.damp_q = 0
    experiment.peak.broad_q = 0.022
    experiment.peak.cutoff_q = 27.0
    experiment.peak.sharp_delta_1 = 0
    experiment.peak.sharp_delta_2 = 2.5587
    experiment.peak.damp_particle_diameter = 0
    experiment.linked_phases.create(id='ni', scale=0.9892)

    # Select fitting parameters
    structure.cell.length_a.free = True
    structure.atom_sites['Ni'].adp_iso.free = True
    experiment.linked_phases['ni'].scale.free = True
    experiment.peak.broad_q.free = True
    experiment.peak.sharp_delta_2.free = True

    # Perform fit
    project.analysis.fit()

    # Compare fit quality
    chi2 = project.analysis.fit_results.reduced_chi_square
    assert_almost_equal(chi2, desired=207.1, decimal=1)


def test_single_fit_pdf_neutron_pd_tof_si():
    project = ed.Project()

    # Set structure
    project.structures.create(name='si')
    structure = project.structures['si']
    structure.space_group.name_h_m.value = 'F d -3 m'
    structure.space_group.it_coordinate_system_code = '1'
    structure.cell.length_a = 5.4306
    structure.atom_sites.create(
        label='Si',
        type_symbol='Si',
        fract_x=0,
        fract_y=0,
        fract_z=0,
        wyckoff_letter='a',
        adp_iso=0.717,
    )

    # Set experiment
    data_path = ed.download_data(id=5, destination=TEMP_DIR)
    project.experiments.add_from_data_path(
        name='nomad',
        data_path=data_path,
        sample_form='powder',
        beam_mode='time-of-flight',
        radiation_probe='neutron',
        scattering_type='total',
    )
    experiment = project.experiments['nomad']
    experiment.peak.damp_q = 0.0251
    experiment.peak.broad_q = 0.0183
    experiment.peak.cutoff_q = 35.0
    experiment.peak.sharp_delta_1 = 2.54
    experiment.peak.sharp_delta_2 = -1.7525
    experiment.peak.damp_particle_diameter = 0
    experiment.linked_phases.create(id='si', scale=1.2728)

    # Select fitting parameters
    project.structures['si'].cell.length_a.free = True
    project.structures['si'].atom_sites['Si'].adp_iso.free = True
    experiment.linked_phases['si'].scale.free = True
    experiment.peak.damp_q.free = True
    experiment.peak.broad_q.free = True
    experiment.peak.sharp_delta_1.free = True
    experiment.peak.sharp_delta_2.free = True

    # Perform fit
    project.analysis.fit()

    # Compare fit quality
    chi2 = project.analysis.fit_results.reduced_chi_square
    assert_almost_equal(chi2, desired=170.54, decimal=1)


if __name__ == '__main__':
    test_single_fit_pdf_xray_pd_cw_nacl()
    test_single_fit_pdf_neutron_pd_cw_ni()
    test_single_fit_pdf_neutron_pd_tof_si()
