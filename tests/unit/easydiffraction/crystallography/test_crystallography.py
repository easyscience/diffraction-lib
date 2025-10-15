import pytest
import numpy as np

# expected vs actual helpers

def _assert_equal(expected, actual):
    assert expected == actual


# Module under test: easydiffraction.crystallography.crystallography

def test_module_import():
    import easydiffraction.crystallography.crystallography as MUT
    expected_module_name = "easydiffraction.crystallography.crystallography"
    actual_module_name = MUT.__name__
    _assert_equal(expected_module_name, actual_module_name)
