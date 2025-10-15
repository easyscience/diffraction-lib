def test_minimizer_factory_list_and_show(capsys):
    from easydiffraction.analysis.minimizers.factory import MinimizerFactory
    lst = MinimizerFactory.list_available_minimizers()
    assert isinstance(lst, list) and len(lst) >= 1
    MinimizerFactory.show_available_minimizers()
    out = capsys.readouterr().out
    assert 'Supported minimizers' in out


def test_minimizer_factory_unknown_raises():
    from easydiffraction.analysis.minimizers.factory import MinimizerFactory
    try:
        MinimizerFactory.create_minimizer('___unknown___')
    except ValueError as e:
        assert 'Unknown minimizer' in str(e)
    else:
        assert False, 'Expected ValueError'# Auto-generated scaffold. Replace TODOs with concrete tests.
import pytest
import numpy as np

# expected vs actual helpers

def _assert_equal(expected, actual):
    assert expected == actual


# Module under test: easydiffraction.analysis.minimizers.factory

# TODO: Replace with real, small tests per class/method.
# Keep names explicit: expected_*, actual_*; compare in a single assert.

def test_module_import():
    import easydiffraction.analysis.minimizers.factory as MUT
    expected_module_name = "easydiffraction.analysis.minimizers.factory"
    actual_module_name = MUT.__name__
    _assert_equal(expected_module_name, actual_module_name)
