import pytest
import numpy as np

# expected vs actual helpers

def _assert_equal(expected, actual):
    assert expected == actual


# Module under test: easydiffraction.experiments.datastore.sc

def test_module_import():
    import easydiffraction.experiments.datastore.sc as MUT
    expected_module_name = "easydiffraction.experiments.datastore.sc"
    actual_module_name = MUT.__name__
    _assert_equal(expected_module_name, actual_module_name)
