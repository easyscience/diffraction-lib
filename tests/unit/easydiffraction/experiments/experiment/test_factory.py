# Auto-generated scaffold. Replace TODOs with concrete tests.
import pytest
import numpy as np

# expected vs actual helpers

def _assert_equal(expected, actual):
    assert expected == actual


# Module under test: easydiffraction.experiments.experiment.factory

# TODO: Replace with real, small tests per class/method.
# Keep names explicit: expected_*, actual_*; compare in a single assert.

def test_module_import():
    import easydiffraction.experiments.experiment.factory as MUT
    expected_module_name = "easydiffraction.experiments.experiment.factory"
    actual_module_name = MUT.__name__
    _assert_equal(expected_module_name, actual_module_name)


def test_experiment_factory_create_without_data_and_invalid_combo():
    import easydiffraction.experiments.experiment.factory as EF
    from easydiffraction.experiments.experiment.enums import (
        BeamModeEnum,
        RadiationProbeEnum,
        SampleFormEnum,
        ScatteringTypeEnum,
    )

    ex = EF.ExperimentFactory.create(
        name="ex1",
        sample_form=SampleFormEnum.POWDER.value,
        beam_mode=BeamModeEnum.CONSTANT_WAVELENGTH.value,
        radiation_probe=RadiationProbeEnum.NEUTRON.value,
        scattering_type=ScatteringTypeEnum.BRAGG.value,
    )
    # Instance should be created (BraggPdExperiment)
    assert hasattr(ex, "type") and ex.type.sample_form.value == SampleFormEnum.POWDER.value

    # invalid combination: unexpected key
    with pytest.raises(ValueError):
        EF.ExperimentFactory.create(name="ex2", unexpected=True)
