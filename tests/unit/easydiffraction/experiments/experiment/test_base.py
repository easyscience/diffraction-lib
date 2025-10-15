# Auto-generated scaffold. Replace TODOs with concrete tests.
import pytest
import numpy as np

# expected vs actual helpers

def _assert_equal(expected, actual):
    assert expected == actual


# Module under test: easydiffraction.experiments.experiment.base

# TODO: Replace with real, small tests per class/method.
# Keep names explicit: expected_*, actual_*; compare in a single assert.

def test_module_import():
    import easydiffraction.experiments.experiment.base as MUT
    expected_module_name = "easydiffraction.experiments.experiment.base"
    actual_module_name = MUT.__name__
    _assert_equal(expected_module_name, actual_module_name)


def test_pd_experiment_peak_profile_type_switch(capsys):
    from easydiffraction.experiments.experiment.base import PdExperimentBase
    from easydiffraction.experiments.categories.experiment_type import ExperimentType
    from easydiffraction.experiments.experiment.enums import (
        BeamModeEnum,
        RadiationProbeEnum,
        SampleFormEnum,
        ScatteringTypeEnum,
        PeakProfileTypeEnum,
    )

    class ConcretePd(PdExperimentBase):
        def _load_ascii_data_to_experiment(self, data_path: str) -> None:
            pass

    et = ExperimentType(
        sample_form=SampleFormEnum.POWDER.value,
        beam_mode=BeamModeEnum.CONSTANT_WAVELENGTH.value,
        radiation_probe=RadiationProbeEnum.NEUTRON.value,
        scattering_type=ScatteringTypeEnum.BRAGG.value,
    )
    ex = ConcretePd(name="ex1", type=et)
    # valid switch using enum
    ex.peak_profile_type = PeakProfileTypeEnum.PSEUDO_VOIGT
    assert ex.peak_profile_type == PeakProfileTypeEnum.PSEUDO_VOIGT
    # invalid string should warn and keep previous
    ex.peak_profile_type = "non-existent"
    captured = capsys.readouterr().out
    assert "Unsupported" in captured or "Unknown" in captured
