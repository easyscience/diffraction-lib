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
    assert hasattr(ex, 'type') and ex.type.sample_form.value == SampleFormEnum.POWDER.value
