# Auto-generated scaffold. Replace TODOs with concrete tests.
import pytest
import numpy as np

# expected vs actual helpers

def _assert_equal(expected, actual):
    assert expected == actual


# Module under test: easydiffraction.core.factory

# TODO: Replace with real, small tests per class/method.
# Keep names explicit: expected_*, actual_*; compare in a single assert.

def test_module_import():
    import easydiffraction.core.factory as MUT
    expected_module_name = "easydiffraction.core.factory"
    actual_module_name = MUT.__name__
    _assert_equal(expected_module_name, actual_module_name)


def test_validate_args_valid_and_invalid():
    import easydiffraction.core.factory as MUT
    specs = [
        {"required": ["a"], "optional": ["b"]},
        {"required": ["x", "y"], "optional": []},
    ]
    # valid: only required
    MUT.FactoryBase._validate_args({"a"}, specs, "Thing")
    # valid: required + optional subset
    MUT.FactoryBase._validate_args({"a", "b"}, specs, "Thing")
    MUT.FactoryBase._validate_args({"x", "y"}, specs, "Thing")
    # invalid: unknown key
    with pytest.raises(ValueError):
        MUT.FactoryBase._validate_args({"a", "c"}, specs, "Thing")
