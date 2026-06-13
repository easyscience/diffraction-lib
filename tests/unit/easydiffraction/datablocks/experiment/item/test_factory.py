# SPDX-FileCopyrightText: 2026 EasyScience contributors <https://github.com/easyscience>
# SPDX-License-Identifier: BSD-3-Clause


def test_module_import():
    import easydiffraction.datablocks.experiment.item.factory as MUT

    expected_module_name = 'easydiffraction.datablocks.experiment.item.factory'
    actual_module_name = MUT.__name__
    assert expected_module_name == actual_module_name


def test_experiment_factory_from_scratch():
    import easydiffraction.datablocks.experiment.item.factory as EF
    from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
    from easydiffraction.datablocks.experiment.item.enums import RadiationProbeEnum
    from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
    from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum

    ex = EF.ExperimentFactory.from_scratch(
        name='ex1',
        sample_form=SampleFormEnum.POWDER.value,
        beam_mode=BeamModeEnum.CONSTANT_WAVELENGTH.value,
        radiation_probe=RadiationProbeEnum.NEUTRON.value,
        scattering_type=ScatteringTypeEnum.BRAGG.value,
    )
    # Instance should be created (BraggPdExperiment)
    assert hasattr(ex, 'experiment_type')
    assert ex.experiment_type.sample_form.value == SampleFormEnum.POWDER.value


def test_from_cif_str_restores_non_default_peak_profile_type():
    """
    Loading a CIF with a non-default peak profile type must reconstruct
    the correct profile (including profile-specific parameters).
    """
    from easydiffraction.datablocks.experiment.item.factory import ExperimentFactory

    expt = ExperimentFactory.from_scratch(
        name='test',
        sample_form='powder',
        beam_mode='constant wavelength',
        radiation_probe='xray',
        scattering_type='bragg',
    )
    expt.peak.type = 'pseudo-voigt + empirical asymmetry'
    expt.peak.asym_empir_1 = -0.005
    expt.peak.asym_empir_2 = 0.067
    expt.peak.broad_gauss_u = 0.039

    cif_str = expt.as_cif

    loaded = ExperimentFactory.from_cif_str(cif_str)

    assert loaded.peak.type == 'cwl-pseudo-voigt-empirical-asymmetry'
    assert loaded.peak.__class__.__name__ == 'CwlPseudoVoigtEmpiricalAsymmetry'
    assert abs(loaded.peak.asym_empir_1.value - (-0.005)) < 1e-6
    assert abs(loaded.peak.asym_empir_2.value - 0.067) < 1e-6
    assert abs(loaded.peak.broad_gauss_u.value - 0.039) < 1e-6
