# SPDX-FileCopyrightText: 2021-2026 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

import tempfile

import pytest

import easydiffraction as ed

TEMP_DIR = tempfile.gettempdir()


@pytest.mark.fast
def test_single_fit_neut_sc_cwl_tbti() -> None:
    project = ed.Project()

    # Set sample model
    model_path = ed.download_data(id=20, destination=TEMP_DIR)
    project.sample_models.add(cif_path=model_path)

    # Set experiment
    data_path = ed.download_data(id=19, destination=TEMP_DIR)
    project.experiments.add(
        name='heidi',
        data_path=data_path,
        sample_form='single crystal',
        beam_mode='constant wavelength',
        radiation_probe='neutron',
        scattering_type='bragg',
    )
    experiment = project.experiments['heidi']
    experiment.linked_crystal.id = 'tbti'
    experiment.linked_crystal.scale = 3
    experiment.instrument.setup_wavelength = 0.793
    experiment.extinction.mosaicity = 29820
    experiment.extinction.radius = 27

    # Select fitting parameters (experiment only)
    # Sample model parameters are selected in the loaded CIF file
    experiment.linked_crystal.scale.free = True
    experiment.extinction.radius.free = True

    # Perform fit
    project.analysis.fit()

    # Compare fit quality
    chi2 = project.analysis.fit_results.reduced_chi_square
    assert chi2 == pytest.approx(expected=12.9, abs=0.1)


@pytest.mark.fast
def test_single_fit_neut_sc_tof_taurine() -> None:
    project = ed.Project()

    # Set sample model
    model_path = ed.download_data(id=21, destination=TEMP_DIR)
    project.sample_models.add(cif_path=model_path)

    # Set experiment
    data_path = ed.download_data(id=22, destination=TEMP_DIR)
    project.experiments.add(
        name='senju',
        data_path=data_path,
        sample_form='single crystal',
        beam_mode='time-of-flight',
        radiation_probe='neutron',
        scattering_type='bragg',
    )
    experiment = project.experiments['senju']
    experiment.linked_crystal.id = 'taurine'
    experiment.linked_crystal.scale = 1.4
    experiment.extinction.mosaicity = 1000.0
    experiment.extinction.radius = 2.0

    # Select fitting parameters (experiment only)
    # Sample model parameters are selected in the loaded CIF file
    experiment.linked_crystal.scale.free = True
    experiment.extinction.radius.free = True

    # Perform fit
    project.analysis.fit()

    # Compare fit quality
    chi2 = project.analysis.fit_results.reduced_chi_square
    assert chi2 == pytest.approx(expected=23.6, abs=0.1)


if __name__ == '__main__':
    test_single_fit_neut_sc_cwl_tbti()
    test_single_fit_neut_sc_tof_taurine()
