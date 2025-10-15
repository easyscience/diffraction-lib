# Auto-generated scaffold. Replace TODOs with concrete tests.
import pytest
import numpy as np

# expected vs actual helpers

def _assert_equal(expected, actual):
    assert expected == actual


# Module under test: easydiffraction.experiments.experiment.enums

# TODO: Replace with real, small tests per class/method.
# Keep names explicit: expected_*, actual_*; compare in a single assert.

def test_module_import():
    import easydiffraction.experiments.experiment.enums as MUT
    expected_module_name = "easydiffraction.experiments.experiment.enums"
    actual_module_name = MUT.__name__
    _assert_equal(expected_module_name, actual_module_name)


def test_default_enums_consistency():
    import easydiffraction.experiments.experiment.enums as MUT
    assert MUT.SampleFormEnum.default() in list(MUT.SampleFormEnum)
    assert MUT.ScatteringTypeEnum.default() in list(MUT.ScatteringTypeEnum)
    assert MUT.RadiationProbeEnum.default() in list(MUT.RadiationProbeEnum)
    assert MUT.BeamModeEnum.default() in list(MUT.BeamModeEnum)
