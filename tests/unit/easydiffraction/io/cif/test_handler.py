# Auto-generated scaffold. Replace TODOs with concrete tests.
import pytest
import numpy as np

# expected vs actual helpers

def _assert_equal(expected, actual):
    assert expected == actual


# Module under test: easydiffraction.io.cif.handler

# TODO: Replace with real, small tests per class/method.
# Keep names explicit: expected_*, actual_*; compare in a single assert.

def test_module_import():
    import easydiffraction.io.cif.handler as MUT
    expected_module_name = "easydiffraction.io.cif.handler"
    actual_module_name = MUT.__name__
    _assert_equal(expected_module_name, actual_module_name)


def test_cif_handler_names_and_uid():
    import easydiffraction.io.cif.handler as MUT
    names = ["_cell_length_a", "_cell_length_b"]
    h = MUT.CifHandler(names=names)
    # names passthrough
    assert h.names == names
    # uid None before attach
    assert h.uid is None
    # attach owner stub with unique_name
    class Owner:
        unique_name = "db.cat.entry.param"

    h.attach(Owner())
    assert h.uid == "db.cat.entry.param"
