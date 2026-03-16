# SPDX-FileCopyrightText: 2021-2026 EasyDiffraction contributors <https://github.com/easyscience/diffraction>
# SPDX-License-Identifier: BSD-3-Clause

def test_module_import():
    import easydiffraction.datablocks.experiment.categories.experiment_type as MUT

    expected_module_name = 'easydiffraction.datablocks.experiment.categories.experiment_type'
    actual_module_name = MUT.__name__
    assert expected_module_name == actual_module_name


def test_experiment_type_properties_and_validation(monkeypatch):
    from easydiffraction.datablocks.experiment.categories.experiment_type import ExperimentType
    from easydiffraction.datablocks.experiment.item.enums import BeamModeEnum
    from easydiffraction.datablocks.experiment.item.enums import RadiationProbeEnum
    from easydiffraction.datablocks.experiment.item.enums import SampleFormEnum
    from easydiffraction.datablocks.experiment.item.enums import ScatteringTypeEnum
    from easydiffraction.utils.logging import log

    log.configure(reaction=log.Reaction.WARN)

    et = ExperimentType()
    et.sample_form = SampleFormEnum.POWDER.value
    et.beam_mode = BeamModeEnum.CONSTANT_WAVELENGTH.value
    et.radiation_probe = RadiationProbeEnum.NEUTRON.value
    et.scattering_type = ScatteringTypeEnum.BRAGG.value

    # getters nominal
    assert et.sample_form.value == SampleFormEnum.POWDER.value
    assert et.beam_mode.value == BeamModeEnum.CONSTANT_WAVELENGTH.value
    assert et.radiation_probe.value == RadiationProbeEnum.NEUTRON.value
    assert et.scattering_type.value == ScatteringTypeEnum.BRAGG.value

    # try invalid value should fall back to previous (membership validator)
    et.sample_form = 'invalid'
    assert et.sample_form.value == SampleFormEnum.POWDER.value
