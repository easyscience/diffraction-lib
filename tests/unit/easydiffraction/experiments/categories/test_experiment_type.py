import pytest
import numpy as np

# expected vs actual helpers

def _assert_equal(expected, actual):
    assert expected == actual


# Module under test: easydiffraction.experiments.categories.experiment_type

def test_module_import():
    import easydiffraction.experiments.categories.experiment_type as MUT
    expected_module_name = "easydiffraction.experiments.categories.experiment_type"
    actual_module_name = MUT.__name__
    _assert_equal(expected_module_name, actual_module_name)


def test_experiment_type_properties_and_validation(monkeypatch):
    from easydiffraction.experiments.categories.experiment_type import ExperimentType
    from easydiffraction.experiments.experiment.enums import (
        BeamModeEnum,
        RadiationProbeEnum,
        SampleFormEnum,
        ScatteringTypeEnum,
    )
    from easydiffraction.utils.logging import log

    log.configure(reaction=log.Reaction.WARN)

    et = ExperimentType(
        sample_form=SampleFormEnum.POWDER.value,
        beam_mode=BeamModeEnum.CONSTANT_WAVELENGTH.value,
        radiation_probe=RadiationProbeEnum.NEUTRON.value,
        scattering_type=ScatteringTypeEnum.BRAGG.value,
    )
    # getters nominal
    assert et.sample_form.value == SampleFormEnum.POWDER.value
    assert et.beam_mode.value == BeamModeEnum.CONSTANT_WAVELENGTH.value
    assert et.radiation_probe.value == RadiationProbeEnum.NEUTRON.value
    assert et.scattering_type.value == ScatteringTypeEnum.BRAGG.value

    # try invalid value should fall back to previous (membership validator)
    et.sample_form = "invalid"
    assert et.sample_form.value == SampleFormEnum.POWDER.value
